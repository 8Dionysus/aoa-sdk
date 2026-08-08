from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from aoa_sdk.contracts.admission_keeper import (
    AdmissionEvidenceNodeStatement,
    AdmissionKeeperSpec,
    KeeperStageSpec,
)
from aoa_sdk.contracts.control_plane import canonical_digest
from aoa_sdk.contracts.organ_registry_v2 import (
    ContourSupplementEntry,
    ContourRuntimeIdentity,
    ContourRuntimeOverlay,
    OrganContourSupplement,
    OrganRegistryRuntimeOverlay,
)
from aoa_sdk.contracts.tasks import TaskInputRequest
from aoa_sdk.contracts.organs import QualifiedEvidenceRef
from aoa_sdk.organs import (
    AdmissionKeeperError,
    FileTaskStore,
    KeeperEvidenceStore,
    MCPTaskRequestContext,
    MCPTasksAdapter,
    MCPTasksAdapterError,
    TASKS_EXTENSION_ID,
    TaskStoreError,
    apply_contour_supplement,
    apply_registry_runtime_overlay,
    build_keeper_state,
    compile_registry_v2,
    load_registry_source,
    materialize_evidence_node,
    materialize_keeper_spec,
    migrate_registry_v1_to_v2,
    plan_keeper_refresh,
    run_keeper_cycle,
)
from aoa_sdk.organs.registry import sha256_digest


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "organ_registry.wave1-shadow.example.json"
NOW = datetime(2026, 8, 1, 12, 0, tzinfo=timezone.utc)


def digest(seed: str) -> str:
    return "sha256:" + (seed.encode().hex() + "0" * 64)[:64]


def test_v1_registry_migrates_to_independent_contour_projection() -> None:
    source = load_registry_source(EXAMPLE)
    migrated = migrate_registry_v1_to_v2(
        source,
        migration_decision_ref="owner://aoa-sdk/decision/contour-registry-v2",
    )
    projection = compile_registry_v2(migrated)

    identities = [(item.organ_id, item.contour_id) for item in projection.entries]
    assert len(identities) == len(set(identities))
    assert all(item.contour.credential_class for item in projection.entries)
    assert all(
        set(item.contour.allowlist)
        == {
            primitive.mcp_name or primitive.primitive_id
            for capability in item.contour.capabilities
            for primitive in capability.primitives
        }
        for item in projection.entries
    )
    assert migrated.expires_at == source.expires_at
    assert all(item.contour.last_good is None for item in projection.entries)


def test_runtime_overlay_corrects_identity_without_upgrading_owner_claims() -> None:
    source = load_registry_source(EXAMPLE)
    migrated = migrate_registry_v1_to_v2(
        source,
        migration_decision_ref="owner://aoa-sdk/decision/contour-registry-v2",
    )
    record = migrated.records[0]
    contour = record.contours[0]
    overlay = OrganRegistryRuntimeOverlay(
        overlay_id="wave1-exact-runtime",
        authored_at=migrated.authored_at,
        expires_at=migrated.expires_at,
        owner_decision_ref="owner://abyss-stack/decision/exact-runtime-overlay",
        contours=(
            ContourRuntimeOverlay(
                organ_id=record.organ_id,
                contour_id=contour.contour_id,
                principal_id=f"{record.organ_id}-{contour.contour_id}-principal",
                endpoint=contour.endpoint,
                runtime_identity=ContourRuntimeIdentity(
                    source_revision=contour.runtime_identity.source_revision,
                    package_name="owner-exact-mcp",
                    package_version="1.2.3",
                    package_digest=digest("package-exact"),
                    deployment_revision="stack-revision",
                    deployment_manifest_digest=digest("manifest-exact"),
                    deployed_tree_digest=digest("tree-exact"),
                ),
                runtime_evidence_refs=(
                    QualifiedEvidenceRef(
                        owner="abyss-stack",
                        evidence_ref="owner://abyss-stack/deployment/exact",
                        revision=digest("manifest-exact"),
                        observed_at=migrated.authored_at,
                        expires_at=migrated.expires_at,
                    ),
                ),
                observation_route="owner://abyss-stack/observation/exact",
                rollback_route="owner://abyss-stack/rollback/exact",
            ),
        ),
    )
    overlaid = apply_registry_runtime_overlay(migrated, overlay)
    updated = overlaid.records[0].contours[0]
    assert updated.runtime_identity.package_name == "owner-exact-mcp"
    assert updated.principal_id.endswith("-principal")
    assert updated.runtime_identity_evidence == overlay.contours[0].runtime_evidence_refs
    assert updated.registry_state == contour.registry_state
    assert updated.currentness == contour.currentness
    assert updated.currentness_expires_at == contour.currentness_expires_at
    assert updated.proof_refs == contour.proof_refs
    assert updated.acceptance_refs == contour.acceptance_refs
    assert overlaid.expires_at == migrated.expires_at


def test_owner_supplement_adds_only_an_unadmitted_contour_shape() -> None:
    source = load_registry_source(EXAMPLE)
    migrated = migrate_registry_v1_to_v2(
        source,
        migration_decision_ref="owner://aoa-sdk/decision/contour-registry-v2",
    )
    record = migrated.records[0]
    base = record.contours[0]
    capability = base.capabilities[0].model_copy(
        update={"credential_class": "kag-proof-read"}
    )
    supplement = OrganContourSupplement(
        supplement_id="kag-proof-shape",
        organ_id=record.organ_id,
        source_owner=record.owners.source_owner,
        source_evidence=QualifiedEvidenceRef(
            owner=record.owners.source_owner,
            evidence_ref="owner://aoa-kag/contours/proof-result",
            revision="shape-v1",
            observed_at=migrated.authored_at,
            expires_at=migrated.expires_at,
        ),
        owner_decision_ref="owner://aoa-kag/decision/proof-result-shape",
        contours=(
            ContourSupplementEntry(
                contour_id="proof-result",
                authority_class="proof_result",
                policy_family="read",
                credential_class="kag-proof-read",
                principal_id="aoa-kag-proof-result-principal",
                capabilities=(capability,),
                observation_route="owner://abyss-stack/observation/kag-proof",
                rollback_route="owner://abyss-stack/rollback/kag-proof",
            ),
        ),
    )
    extended = apply_contour_supplement(migrated, supplement)
    added = extended.records[0].contours[-1]
    assert added.contour_id == "proof-result"
    assert added.registry_state == "shadow"
    assert added.currentness == "unknown"
    assert not added.proof_refs
    assert not added.acceptance_refs
    assert not added.activation_preconditions
    assert all(
        value.state == "not_asserted"
        for _, value in added.maturity
    )


def test_task_store_is_durable_principal_bound_cas_and_idempotent(tmp_path: Path) -> None:
    store = FileTaskStore(tmp_path / "tasks")
    created = store.create(
        principal_id="principal-a",
        organ_id="abyss-stack",
        contour_id="read",
        tool_name="stack_snapshot",
        arguments={"detail": "bounded"},
        owner_run_ref="owner://abyss-stack/run/one",
        idempotency_key="request-one",
        ttl_seconds=600,
        poll_interval_ms=250,
        now=NOW,
    )
    task = created.record
    assert task.revision == 1
    assert FileTaskStore(tmp_path / "tasks").get(
        task.task_id,
        principal_id="principal-a",
        organ_id="abyss-stack",
        contour_id="read",
        now=NOW,
    ) == task
    with pytest.raises(TaskStoreError, match="not authorized"):
        store.get(
            task.task_id,
            principal_id="principal-b",
            organ_id="abyss-stack",
            contour_id="read",
            now=NOW,
        )

    requested = store.require_input(
        task.task_id,
        principal_id="principal-a",
        organ_id="abyss-stack",
        contour_id="read",
        expected_revision=1,
        request=TaskInputRequest(
            request_key="scope-choice",
            prompt_ref="owner://abyss-stack/task-input/scope",
            input_schema_ref="owner://abyss-stack/schema/scope",
            input_schema_digest=digest("scope"),
            requested_at=NOW + timedelta(seconds=1),
            expires_at=NOW + timedelta(seconds=120),
        ),
        now=NOW + timedelta(seconds=1),
    )
    assert requested.record.status == "input_required"
    applied = store.apply_input(
        task.task_id,
        principal_id="principal-a",
        organ_id="abyss-stack",
        contour_id="read",
        expected_revision=2,
        request_key="scope-choice",
        input_key="scope-choice-one",
        input_value={"scope": "runtime"},
        now=NOW + timedelta(seconds=2),
    )
    replay = store.apply_input(
        task.task_id,
        principal_id="principal-a",
        organ_id="abyss-stack",
        contour_id="read",
        expected_revision=2,
        request_key="scope-choice",
        input_key="scope-choice-one",
        input_value={"scope": "runtime"},
        now=NOW + timedelta(seconds=3),
    )
    assert applied.record.status == "working"
    assert replay.audit.outcome == "idempotent"
    assert replay.record.revision == applied.record.revision

    cancel = store.request_cancel(
        task.task_id,
        principal_id="principal-a",
        organ_id="abyss-stack",
        contour_id="read",
        expected_revision=3,
        now=NOW + timedelta(seconds=4),
    )
    cancelled = store.acknowledge_cancel(
        task.task_id,
        principal_id="principal-a",
        organ_id="abyss-stack",
        contour_id="read",
        expected_revision=cancel.record.revision,
        accepted=True,
        now=NOW + timedelta(seconds=5),
    )
    assert cancelled.record.status == "cancelled"
    assert FileTaskStore(tmp_path / "tasks").get(
        task.task_id,
        principal_id="principal-a",
        organ_id="abyss-stack",
        contour_id="read",
        now=NOW + timedelta(seconds=6),
    ).status == "cancelled"
    audits = list((tmp_path / "tasks" / "audit").glob("*.json"))
    assert any('"action":"get"' in path.read_text() for path in audits)


def test_task_store_normalizes_secret_policy_errors(tmp_path: Path) -> None:
    store = FileTaskStore(tmp_path / "tasks")
    with pytest.raises(TaskStoreError, match="secret-material policy"):
        store.create(
            principal_id="principal-a",
            organ_id="abyss-stack",
            contour_id="read",
            tool_name="snapshot",
            arguments={"access_token": "not-persistable"},
            owner_run_ref="owner://abyss-stack/run/rejected",
            idempotency_key="rejected-secret",
            ttl_seconds=60,
            poll_interval_ms=250,
            now=NOW,
        )

    adapter = MCPTasksAdapter(store, _OwnerPayloads(), enabled=True)
    with pytest.raises(MCPTasksAdapterError) as rejected:
        adapter.create_task_result(
            _tasks_context("tools/call", "snapshot"),
            tool_name="snapshot",
            arguments={"authorization": "Bearer forbidden"},
            owner_run_ref="owner://abyss-stack/run/rejected-adapter",
            idempotency_key="rejected-adapter-secret",
            ttl_seconds=60,
            poll_interval_ms=250,
            now=NOW,
        )
    assert rejected.value.code == -32602
    assert rejected.value.message == "Task request exceeds policy"


def test_task_store_rejects_symlink_roots_and_internal_directories(
    tmp_path: Path,
) -> None:
    target = tmp_path / "target"
    target.mkdir()
    root_link = tmp_path / "task-root-link"
    root_link.symlink_to(target, target_is_directory=True)
    with pytest.raises(TaskStoreError, match="non-symlink directory"):
        FileTaskStore(root_link)

    poisoned = tmp_path / "poisoned"
    poisoned.mkdir()
    external_records = tmp_path / "external-records"
    external_records.mkdir()
    (poisoned / "records").symlink_to(external_records, target_is_directory=True)
    with pytest.raises(TaskStoreError, match="records root"):
        FileTaskStore(poisoned)


class _OwnerPayloads:
    def __init__(self) -> None:
        self.results: dict[str, dict] = {}
        self.errors: dict[str, dict] = {}
        self.inputs: dict[str, dict] = {}

    def resolve_result(self, record):
        assert record.result_ref is not None
        return self.results[record.result_ref]

    def resolve_error(self, record):
        assert record.error_ref is not None
        return self.errors[record.error_ref]

    def resolve_input_request(self, record, request):
        del record
        return self.inputs[request.prompt_ref]


def _tasks_context(
    method: str,
    name: str,
    *,
    principal_id: str = "principal-a",
    declares_tasks: bool = True,
) -> MCPTaskRequestContext:
    capabilities = (
        {"extensions": {TASKS_EXTENSION_ID: {}}}
        if declares_tasks
        else {}
    )
    return MCPTaskRequestContext(
        principal_id=principal_id,
        organ_id="abyss-stack",
        contour_id="read",
        protocol_version="2026-07-28",
        client_capabilities=capabilities,
        transport="streamable_http",
        headers={"Mcp-Method": method, "Mcp-Name": name},
    )


def test_mcp_tasks_adapter_is_feature_gated_and_requires_wire_capability(
    tmp_path: Path,
) -> None:
    store = FileTaskStore(tmp_path / "tasks")
    payloads = _OwnerPayloads()
    disabled = MCPTasksAdapter(store, payloads)
    with pytest.raises(MCPTasksAdapterError) as disabled_error:
        disabled.create_task_result(
            _tasks_context("tools/call", "snapshot"),
            tool_name="snapshot",
            arguments={},
            owner_run_ref="owner://abyss-stack/run/disabled",
            idempotency_key="disabled-one",
            ttl_seconds=60,
            poll_interval_ms=250,
            now=NOW,
        )
    assert disabled_error.value.code == -32601

    adapter = MCPTasksAdapter(store, payloads, enabled=True)
    assert adapter.server_capabilities() == {
        "extensions": {TASKS_EXTENSION_ID: {}}
    }
    undeclared = _tasks_context(
        "tools/call",
        "snapshot",
        declares_tasks=False,
    )
    assert adapter.create_task_result(
        undeclared,
        tool_name="snapshot",
        arguments={},
        owner_run_ref="owner://abyss-stack/run/sync-fallback",
        idempotency_key="sync-fallback-one",
        ttl_seconds=60,
        poll_interval_ms=250,
        now=NOW,
    ) is None
    with pytest.raises(MCPTasksAdapterError) as missing:
        adapter.create_task_result(
            undeclared,
            tool_name="snapshot",
            arguments={},
            owner_run_ref="owner://abyss-stack/run/required",
            idempotency_key="required-one",
            ttl_seconds=60,
            poll_interval_ms=250,
            task_support="required",
            now=NOW,
        )
    assert missing.value.code == -32021
    assert missing.value.data == {
        "requiredCapabilities": {"extensions": {TASKS_EXTENSION_ID: {}}}
    }


def test_mcp_tasks_adapter_lifecycle_uses_owner_payloads_and_reauthorizes(
    tmp_path: Path,
) -> None:
    store = FileTaskStore(tmp_path / "tasks")
    payloads = _OwnerPayloads()
    cancellations: list[str] = []
    adapter = MCPTasksAdapter(
        store,
        payloads,
        enabled=True,
        cancel_sink=lambda record: cancellations.append(record.owner_run_ref),
    )
    created = adapter.create_task_result(
        _tasks_context("tools/call", "diagnostic_snapshot"),
        tool_name="diagnostic_snapshot",
        arguments={"scope": "bounded"},
        owner_run_ref="owner://abyss-stack/run/diagnostic-one",
        idempotency_key="diagnostic-one",
        ttl_seconds=600,
        poll_interval_ms=250,
        now=NOW,
    )
    assert created is not None
    assert created["resultType"] == "task"
    assert created["status"] == "working"
    assert created["ttlMs"] == 600_000
    assert "task" not in created
    task_id = created["taskId"]

    working = adapter.get_task(
        _tasks_context("tasks/get", task_id),
        task_id=task_id,
        now=NOW + timedelta(seconds=1),
    )
    assert working["resultType"] == "complete"
    assert working["status"] == "working"
    assert "result" not in working

    with pytest.raises(MCPTasksAdapterError) as hidden:
        adapter.get_task(
            _tasks_context("tasks/get", task_id, principal_id="principal-b"),
            task_id=task_id,
            now=NOW + timedelta(seconds=1),
        )
    assert hidden.value.code == -32602
    assert hidden.value.message == "Unknown task"

    input_ref = "owner://abyss-stack/task-input/scope"
    payloads.inputs[input_ref] = {
        "method": "elicitation/create",
        "params": {
            "mode": "form",
            "message": "Choose snapshot scope",
            "requestedSchema": {
                "type": "object",
                "properties": {"scope": {"type": "string"}},
                "required": ["scope"],
            },
        },
    }
    required = store.require_input(
        task_id,
        principal_id="principal-a",
        organ_id="abyss-stack",
        contour_id="read",
        expected_revision=1,
        request=TaskInputRequest(
            request_key="snapshot-scope",
            prompt_ref=input_ref,
            input_schema_ref="owner://abyss-stack/schema/snapshot-scope",
            input_schema_digest=digest("snapshot-scope"),
            requested_at=NOW + timedelta(seconds=2),
            expires_at=NOW + timedelta(minutes=2),
        ),
        now=NOW + timedelta(seconds=2),
    )
    assert required.record.status == "input_required"
    waiting = adapter.get_task(
        _tasks_context("tasks/get", task_id),
        task_id=task_id,
        now=NOW + timedelta(seconds=3),
    )
    assert waiting["status"] == "input_required"
    assert waiting["inputRequests"]["snapshot-scope"]["method"] == (
        "elicitation/create"
    )

    assert adapter.update_task(
        _tasks_context("tasks/update", task_id),
        task_id=task_id,
        input_responses={
            "unknown-key": {"action": "decline"},
            "snapshot-scope": {
                "action": "accept",
                "content": {"scope": "runtime"},
            },
        },
        now=NOW + timedelta(seconds=4),
    ) == {"resultType": "complete"}
    after_input = adapter.get_task(
        _tasks_context("tasks/get", task_id),
        task_id=task_id,
        now=NOW + timedelta(seconds=5),
    )
    assert after_input["status"] == "working"

    owner_result = {
        "content": [{"type": "text", "text": "bounded snapshot ready"}],
        "isError": False,
    }
    result_ref = "owner://abyss-stack/results/diagnostic-one"
    payloads.results[result_ref] = owner_result
    current = store.get(
        task_id,
        principal_id="principal-a",
        organ_id="abyss-stack",
        contour_id="read",
        now=NOW + timedelta(seconds=5),
    )
    store.complete(
        task_id,
        principal_id="principal-a",
        organ_id="abyss-stack",
        contour_id="read",
        expected_revision=current.revision,
        result_ref=result_ref,
        result_digest=sha256_digest(owner_result),
        evidence_refs=("owner://abyss-stack/evidence/diagnostic-one",),
        now=NOW + timedelta(seconds=6),
    )
    terminal = adapter.get_task(
        _tasks_context("tasks/get", task_id),
        task_id=task_id,
        now=NOW + timedelta(seconds=7),
    )
    assert terminal["status"] == "completed"
    assert terminal["result"] == owner_result
    assert "io.modelcontextprotocol/related-task" not in terminal["result"].get(
        "_meta", {}
    )

    # Cancelling a terminal task is an idempotent ack and does not invoke the
    # owner cancellation sink.
    assert adapter.cancel_task(
        _tasks_context("tasks/cancel", task_id),
        task_id=task_id,
        now=NOW + timedelta(seconds=8),
    ) == {"resultType": "complete"}
    assert cancellations == []

    cancellable = adapter.create_task_result(
        _tasks_context("tools/call", "diagnostic_snapshot"),
        tool_name="diagnostic_snapshot",
        arguments={"scope": "cancellable"},
        owner_run_ref="owner://abyss-stack/run/diagnostic-cancellable",
        idempotency_key="diagnostic-cancellable",
        ttl_seconds=600,
        poll_interval_ms=250,
        now=NOW + timedelta(seconds=9),
    )
    assert cancellable is not None
    cancellable_id = cancellable["taskId"]
    assert adapter.cancel_task(
        _tasks_context("tasks/cancel", cancellable_id),
        task_id=cancellable_id,
        now=NOW + timedelta(seconds=10),
    ) == {"resultType": "complete"}
    assert cancellations == ["owner://abyss-stack/run/diagnostic-cancellable"]


def test_task_store_status_is_aggregate_bounded_and_survives_restart(
    tmp_path: Path,
) -> None:
    root = tmp_path / "tasks"
    store = FileTaskStore(root)
    pending = store.create(
        principal_id="principal-a",
        organ_id="abyss-stack",
        contour_id="read",
        tool_name="diagnostic_snapshot",
        arguments={"scope": "pending-cancel"},
        owner_run_ref="owner://abyss-stack/run/pending-cancel",
        idempotency_key="pending-cancel",
        ttl_seconds=1_000,
        poll_interval_ms=250,
        now=NOW,
    ).record
    store.request_cancel(
        pending.task_id,
        principal_id="principal-a",
        organ_id="abyss-stack",
        contour_id="read",
        expected_revision=pending.revision,
        now=NOW + timedelta(seconds=1),
    )
    expiring = store.create(
        principal_id="principal-b",
        organ_id="abyss-stack",
        contour_id="read",
        tool_name="diagnostic_snapshot",
        arguments={"scope": "expires"},
        owner_run_ref="owner://abyss-stack/run/expires",
        idempotency_key="expires",
        ttl_seconds=60,
        poll_interval_ms=250,
        now=NOW,
    ).record

    status = FileTaskStore(root).status(
        now=NOW + timedelta(seconds=400),
        orphan_after_seconds=300,
    )

    assert status.record_count == 2
    assert status.active_count == 1
    assert status.pending_cancellation_count == 1
    assert status.orphan_candidate_count == 1
    assert status.expired_unpersisted_count == 1
    assert status.status_counts["working"] == 2
    assert status.quota.maximum_observed_active_per_principal == 1
    assert status.quota.global_remaining == 255
    rendered = status.model_dump(mode="json")
    assert pending.task_id not in str(rendered)
    assert expiring.task_id not in str(rendered)
    assert "principal-a" not in str(rendered)
    assert rendered["owner_execution_inferred"] is False
    assert rendered["admission_inferred"] is False


def test_mcp_tasks_adapter_rejects_mismatched_http_routing_headers(
    tmp_path: Path,
) -> None:
    adapter = MCPTasksAdapter(
        FileTaskStore(tmp_path / "tasks"),
        _OwnerPayloads(),
        enabled=True,
    )
    mismatched = MCPTaskRequestContext(
        principal_id="principal-a",
        organ_id="abyss-stack",
        contour_id="read",
        protocol_version="2026-07-28",
        client_capabilities={"extensions": {TASKS_EXTENSION_ID: {}}},
        transport="streamable_http",
        headers={"Mcp-Method": "tasks/get", "Mcp-Name": "wrong"},
    )
    with pytest.raises(MCPTasksAdapterError) as error:
        adapter.create_task_result(
            mismatched,
            tool_name="diagnostic_snapshot",
            arguments={},
            owner_run_ref="owner://abyss-stack/run/header-mismatch",
            idempotency_key="header-mismatch",
            ttl_seconds=60,
            poll_interval_ms=250,
            now=NOW,
        )
    assert error.value.code == -32020
    assert error.value.http_status == 400


def test_mcp_tasks_adapter_bounds_polling_and_input_payloads(tmp_path: Path) -> None:
    store = FileTaskStore(tmp_path / "tasks")
    payloads = _OwnerPayloads()
    adapter = MCPTasksAdapter(
        store,
        payloads,
        enabled=True,
        maximum_input_response_bytes=64,
    )
    created = adapter.create_task_result(
        _tasks_context("tools/call", "bounded_task"),
        tool_name="bounded_task",
        arguments={},
        owner_run_ref="owner://abyss-stack/run/bounded-task",
        idempotency_key="bounded-task",
        ttl_seconds=60,
        poll_interval_ms=500,
        now=NOW,
    )
    assert created is not None
    task_id = created["taskId"]
    adapter.get_task(
        _tasks_context("tasks/get", task_id),
        task_id=task_id,
        now=NOW + timedelta(seconds=1),
    )
    with pytest.raises(MCPTasksAdapterError) as rate_limited:
        adapter.get_task(
            _tasks_context("tasks/get", task_id),
            task_id=task_id,
            now=NOW + timedelta(seconds=1, milliseconds=100),
        )
    assert rate_limited.value.code == -32029
    assert rate_limited.value.http_status == 429

    input_ref = "owner://abyss-stack/task-input/bounded"
    payloads.inputs[input_ref] = {
        "method": "elicitation/create",
        "params": {"mode": "form", "message": "bounded", "requestedSchema": {}},
    }
    store.require_input(
        task_id,
        principal_id="principal-a",
        organ_id="abyss-stack",
        contour_id="read",
        expected_revision=1,
        request=TaskInputRequest(
            request_key="bounded-input",
            prompt_ref=input_ref,
            input_schema_ref="owner://abyss-stack/schema/bounded-input",
            input_schema_digest=digest("bounded-input"),
            requested_at=NOW + timedelta(seconds=2),
            expires_at=NOW + timedelta(seconds=30),
        ),
        now=NOW + timedelta(seconds=2),
    )
    with pytest.raises(MCPTasksAdapterError) as oversized:
        adapter.update_task(
            _tasks_context("tasks/update", task_id),
            task_id=task_id,
            input_responses={"bounded-input": {"content": "x" * 100}},
            now=NOW + timedelta(seconds=3),
        )
    assert oversized.value.code == -32602


def _keeper_spec(package_digest: str) -> AdmissionKeeperSpec:
    stages = (
        KeeperStageSpec(
            stage="owner_source",
            owner="aoa-kag",
            validator_ref="owner://aoa-kag/validator/source",
            validator_revision="v1",
            validator_schema_digest=digest("source-schema"),
            subject_digest=digest("source"),
            maximum_age_seconds=600,
            cost_weight=5,
        ),
        KeeperStageSpec(
            stage="package",
            owner="abyss-stack",
            validator_ref="owner://abyss-stack/validator/package",
            validator_revision="v1",
            validator_schema_digest=digest("package-schema"),
            subject_digest=package_digest,
            dependency_stages=("owner_source",),
            maximum_age_seconds=600,
            cost_weight=10,
        ),
        KeeperStageSpec(
            stage="central_proof",
            owner="aoa-evals",
            validator_ref="owner://aoa-evals/validator/proof",
            validator_revision="v1",
            validator_schema_digest=digest("proof-schema"),
            subject_digest=digest("proof"),
            dependency_stages=("package",),
            maximum_age_seconds=600,
            cost_weight=100,
            automatic_execution_allowed=False,
        ),
    )
    return materialize_keeper_spec(
        AdmissionKeeperSpec(
            spec_id="sha256:" + "0" * 64,
            organ_id="aoa-kag",
            contour_id="read",
            transaction_ref="owner://aoa-sdk/admission/kag-read-one",
            registry_anchor_digest=digest("registry"),
            target_record_digest=digest("target"),
            authored_at=NOW,
            expires_at=NOW + timedelta(hours=1),
            stages=stages,
        )
    )


def _node(spec: AdmissionKeeperSpec, stage: str, dependencies=()):
    stage_spec = next(item for item in spec.stages if item.stage == stage)
    return materialize_evidence_node(
        AdmissionEvidenceNodeStatement(
            spec_id=spec.spec_id,
            organ_id=spec.organ_id,
            contour_id=spec.contour_id,
            stage=stage,
            stage_spec_digest=canonical_digest(stage_spec),
            dependency_node_ids=tuple(item.node_id for item in dependencies),
            owner=stage_spec.owner,
            subject_digest=stage_spec.subject_digest,
            receipt=QualifiedEvidenceRef(
                owner=stage_spec.owner,
                evidence_ref=f"owner://{stage_spec.owner}/receipt/{stage}",
                revision="v1",
                observed_at=NOW + timedelta(seconds=10),
                expires_at=NOW + timedelta(minutes=30),
            ),
            observed_at=NOW + timedelta(seconds=10),
            expires_at=NOW + timedelta(minutes=30),
            outcome="passed",
        ),
        spec,
        dependencies,
    )


def test_keeper_reuses_unchanged_nodes_and_invalidates_only_dependents() -> None:
    spec = _keeper_spec(digest("package-one"))
    source = _node(spec, "owner_source")
    package = _node(spec, "package", (source,))
    nodes = (source, package)

    unchanged = plan_keeper_refresh(
        spec,
        nodes=nodes,
        planned_at=NOW + timedelta(minutes=1),
        renewal_margin_seconds=60,
    )
    assert [item.action for item in unchanged.steps] == ["reuse", "reuse", "blocked"]
    assert unchanged.planned_refresh_cost == 0
    assert unchanged.full_refresh_cost == 115

    changed = _keeper_spec(digest("package-two"))
    incremental = plan_keeper_refresh(
        changed,
        nodes=nodes,
        planned_at=NOW + timedelta(minutes=1),
        renewal_margin_seconds=60,
    )
    assert [item.action for item in incremental.steps] == [
        "reuse",
        "refresh",
        "blocked",
    ]
    assert incremental.planned_refresh_cost == 10
    state = build_keeper_state(
        changed,
        nodes=nodes,
        updated_at=NOW + timedelta(minutes=1),
        last_good_state_ref="owner://aoa-sdk/admission/last-good/kag-read",
        last_good_state_digest=digest("last-good"),
    )
    assert not state.admission_current
    assert state.next_safe_stage == "package"
    assert "last_good" in state.currentness


def test_expired_keeper_spec_returns_fail_closed_plan_and_state() -> None:
    spec = _keeper_spec(digest("package-one"))
    expired_at = spec.expires_at + timedelta(seconds=1)
    plan = plan_keeper_refresh(spec, planned_at=expired_at)
    assert all(item.action == "blocked" for item in plan.steps)
    assert all("keeper_spec_expired" in item.reason_codes for item in plan.steps)
    assert plan.planned_refresh_cost == 0
    state = build_keeper_state(spec, nodes=(), updated_at=expired_at)
    assert not state.admission_current
    assert "keeper_spec_expired" in state.blocker_codes
    assert "blocked" in state.currentness


def test_keeper_cycle_persists_immutable_plan_and_resumes_idempotently(
    tmp_path: Path,
) -> None:
    spec = _keeper_spec(digest("package-one"))
    source = _node(spec, "owner_source")
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    (inbox / "source.json").write_text(source.model_dump_json(), encoding="utf-8")
    store = KeeperEvidenceStore(tmp_path / "keeper")
    first = run_keeper_cycle(
        spec,
        store=store,
        inbox_paths=(inbox / "source.json",),
        generated_at=NOW + timedelta(seconds=1),
    )
    second = run_keeper_cycle(
        spec,
        store=store,
        inbox_paths=(inbox / "source.json",),
        generated_at=NOW + timedelta(seconds=2),
    )
    assert first.imported_node_ids == (source.node_id,)
    assert second.imported_node_ids == ()
    assert second.state.revision == first.state.revision + 1
    assert len(tuple((tmp_path / "keeper/nodes").glob("*.json"))) == 1
    assert len(tuple((tmp_path / "keeper/plans").glob("*.json"))) == 2


def test_keeper_store_rejects_symlink_roots_and_internal_directories(
    tmp_path: Path,
) -> None:
    target = tmp_path / "keeper-target"
    target.mkdir()
    root_link = tmp_path / "keeper-root-link"
    root_link.symlink_to(target, target_is_directory=True)
    with pytest.raises(AdmissionKeeperError, match="non-symlink directory"):
        KeeperEvidenceStore(root_link)

    poisoned = tmp_path / "keeper-poisoned"
    poisoned.mkdir()
    external_nodes = tmp_path / "external-nodes"
    external_nodes.mkdir()
    (poisoned / "nodes").symlink_to(external_nodes, target_is_directory=True)
    with pytest.raises(AdmissionKeeperError, match="nodes root"):
        KeeperEvidenceStore(poisoned)


def test_keeper_cycle_serializes_concurrent_path_and_timer_triggers(
    tmp_path: Path,
) -> None:
    spec = _keeper_spec(digest("package-one"))
    source = _node(spec, "owner_source")
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    source_path = inbox / "source.json"
    source_path.write_text(source.model_dump_json(), encoding="utf-8")
    keeper_root = tmp_path / "keeper"

    def run(offset: int):
        return run_keeper_cycle(
            spec,
            store=KeeperEvidenceStore(keeper_root),
            inbox_paths=(source_path,),
            generated_at=NOW + timedelta(seconds=offset),
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        cycles = tuple(executor.map(run, (1, 2)))

    assert sorted(item.state.revision for item in cycles) == [1, 2]
    assert sorted(len(item.imported_node_ids) for item in cycles) == [0, 1]
    assert len(tuple((keeper_root / "nodes").glob("*.json"))) == 1
    assert len(tuple((keeper_root / "plans").glob("*.json"))) == 2
