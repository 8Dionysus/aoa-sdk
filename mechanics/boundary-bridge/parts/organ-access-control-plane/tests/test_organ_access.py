from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from pydantic import BaseModel, ConfigDict, ValidationError
from typer.testing import CliRunner

from aoa_sdk.contracts.organs import (
    ActivationRequest,
    CredentialContours,
    OrganRecord,
    OrganRegistrySource,
    OwnerResultCapture,
    OwnerResultReviewReceipt,
    OwnerResultReviewStatement,
    OrganResultEnvelope,
    OrganResultMetadata,
    PrimitiveContract,
)
from aoa_sdk.organs import OrganRegistryError, OrgansAPI, compile_registry
from aoa_sdk.organs import (
    OwnerResultReviewError,
    assert_owner_result_review,
    materialize_owner_result_review,
)
from aoa_sdk.organs.adapters import DirectConnectionDescriptor
from aoa_sdk.organs.registry import assert_projection_digest
from aoa_sdk.cli.main import app
from aoa_sdk.workspace.discovery import Workspace


DIGEST_A = "sha256:" + "a" * 64
DIGEST_B = "sha256:" + "b" * 64
DIGEST_C = "sha256:" + "c" * 64
NOW = datetime(2026, 7, 25, 12, 0, tzinfo=timezone.utc)


def _evidence(name: str = "review") -> dict:
    return {
        "owner": "owner-repo",
        "evidence_ref": f"evidence/{name}.json",
        "revision": "rev-1",
        "observed_at": NOW.isoformat(),
        "expires_at": (NOW + timedelta(days=2)).isoformat(),
    }


def _maturity(*, admitted: bool) -> dict:
    names = (
        "declared",
        "owner_reviewed",
        "packaged",
        "exported",
        "deployed",
        "process_alive",
        "endpoint_ready",
        "registry_indexed",
        "consumer_registered",
        "schema_observed",
        "call_succeeded",
        "result_grounded",
        "freshness_satisfied",
        "owner_accepted",
        "cross_organ_proven",
        "rollback_proven",
    )
    asserted = {"declared"}
    if admitted:
        asserted.update(set(names) - {"cross_organ_proven"})
    return {
        name: (
            {
                "state": "asserted",
                "evidence": _evidence(name),
                "freshness_policy": "owner-review-v1",
            }
            if name in asserted
            else {"state": "not_asserted"}
        )
        for name in names
    }


def _primitive(*, effect: bool = False) -> dict:
    if effect:
        return {
            "primitive_id": "publish-change",
            "kind": "tool",
            "effect_class": "external_change",
            "policy_family": "external_effect",
            "input_schema_ref": "schemas/publish-input.json",
            "output_schema_ref": "schemas/publish-result.json",
            "approval_required": True,
            "approval_owner": "os-operator",
            "idempotency": "idempotency_key_required",
            "rollback_route": "owner://rollback/publish",
            "maximum_blast_radius": "one exact external target",
        }
    return {
        "primitive_id": "inspect-knowledge",
        "kind": "tool",
        "effect_class": "observe",
        "policy_family": "read",
        "input_schema_ref": "schemas/inspect-input.json",
        "output_schema_ref": "schemas/inspect-result.json",
        "idempotency": "read_only",
        "maximum_blast_radius": "read-only owner result",
    }


def _record(
    organ_id: str,
    state: str,
    *,
    effect: bool = False,
) -> dict:
    admitted = state == "admitted"
    policy = "external_effect" if effect else "read"
    contour_prefix = organ_id.removeprefix("aoa-")
    credential = (
        f"{contour_prefix}-external-effect"
        if effect
        else f"{contour_prefix}-read"
    )
    revisions = {
        "source": {"revision": "source-1", "digest": DIGEST_A},
        "consumer_schema": {
            "revision": "consumer-1",
            "schema_digest": DIGEST_C,
        },
    }
    endpoint = None
    preconditions: list[dict] = []
    if admitted:
        revisions.update(
            {
                "package": {"revision": "pkg-1", "digest": DIGEST_B},
                "deploy": {"revision": "deploy-1", "digest": DIGEST_C},
            }
        )
        endpoint = {
            "adapter_id": "owner-direct",
            "transport": "streamable-http",
            "endpoint_ref": "config://organs/kag/endpoint",
            "protocol_versions": ["2025-11-25"],
            "server_schema_digest": DIGEST_B,
        }
        preconditions = [_evidence("precondition")]
    return {
        "organ_id": organ_id,
        "display_name": f"Organ {organ_id}",
        "description": "Owner-bounded knowledge access surface for tests.",
        "owners": {
            "source_owner": "aoa-kag",
            "access_owner": "aoa-kag",
            "runtime_owner": "abyss-stack",
            "proof_owner": "aoa-evals",
            "acceptance_owner": "aoa-kag",
        },
        "registry_state": state,
        "authority_ceiling": policy,
        "authentication_requirements": ["owner-bearer"],
        "credential_contours": {
            "read": f"{contour_prefix}-read",
            "external_effect": (
                f"{contour_prefix}-external-effect" if effect else None
            ),
        },
        "revisions": revisions,
        "freshness_policy": {
            "policy_id": "kag-freshness",
            "max_age_seconds": 300,
            "cache_scope": "task",
        },
        "freshness_state": "exact" if admitted else "unknown",
        "freshness_evidence": _evidence("freshness") if admitted else None,
        "eval_refs": ["eval://organ-access-integrity"],
        "eval_status": "passed" if admitted else "candidate",
        "eval_evidence": _evidence("eval") if admitted else None,
        "capabilities": [
            {
                "capability_id": "knowledge-publish" if effect else "knowledge-inspect",
                "summary": "Inspect or change owner-qualified knowledge safely.",
                "policy_family": policy,
                "credential_class": credential,
                "primitives": [_primitive(effect=effect)],
                "task_intent_terms": ["knowledge", "provenance"],
                "owner_payload_schema_ref": "schemas/kag-payload.json",
                "eval_refs": ["eval://organ-access-integrity"],
            }
        ],
        "endpoint": endpoint,
        "consumer_compatibility": (
            [
                {
                    "consumer_id": "codex-main",
                    "support_state": "supported",
                    "protocol_versions": ["2025-11-25"],
                    "observed_schema_digest": DIGEST_C,
                    "evidence_ref": _evidence("consumer"),
                }
            ]
            if admitted
            else []
        ),
        "maturity": _maturity(admitted=admitted),
        "activation_preconditions": preconditions,
        "rollback_route": "owner://rollback/kag",
        "support_route": "owner://support/kag",
        "handoff": {
            "input_ref_kind": "query-ref",
            "output_ref_kind": "evidence-ref",
            "next_owner": "consumer",
            "stop_states": ["owner-review-required"],
        },
    }


def _source(*records: dict) -> OrganRegistrySource:
    return OrganRegistrySource.model_validate(
        {
            "registry_id": "abyss-private",
            "workspace_owner": "os-abyss",
            "authored_at": NOW.isoformat(),
            "expires_at": (NOW + timedelta(days=1)).isoformat(),
            "owner_decision_refs": ["decision://AOA-SDK-D-0075"],
            "records": list(records),
        }
    )


def _api(tmp_path: Path, source: OrganRegistrySource) -> OrgansAPI:
    registry = tmp_path / "registry.json"
    registry.write_text(source.model_dump_json(indent=2), encoding="utf-8")
    workspace = Workspace(
        root=tmp_path,
        federation_root=tmp_path,
        federation_root_source="test",
        manifest_path=None,
        repo_roots={},
        repo_origins={},
        organ_registry_path=registry,
        organ_registry_source="test",
    )
    return OrgansAPI(workspace, clock=lambda: NOW)


def test_contracts_are_strict_and_effect_policy_is_enforced() -> None:
    with pytest.raises(ValidationError, match="extra"):
        OrganRegistrySource.model_validate(
            {
                **_source(_record("aoa-kag", "shadow")).model_dump(mode="json"),
                "unknown": True,
            }
        )
    bad = _primitive()
    bad["effect_class"] = "external_change"
    with pytest.raises(ValidationError, match="requires policy family"):
        PrimitiveContract.model_validate(bad)
    with pytest.raises(ValidationError, match="distinct"):
        CredentialContours(read="shared", candidate="shared")


def test_duplicate_ids_and_unsupported_admission_fail_closed() -> None:
    with pytest.raises(ValidationError, match="organ ids must be unique"):
        _source(_record("aoa-kag", "shadow"), _record("aoa-kag", "shadow"))
    admitted = _record("aoa-kag", "admitted")
    admitted["activation_preconditions"] = []
    with pytest.raises(ValidationError, match="activation preconditions"):
        OrganRecord.model_validate(admitted)
    admitted = _record("aoa-kag", "admitted")
    admitted["eval_status"] = "candidate"
    admitted["eval_evidence"] = None
    with pytest.raises(ValidationError, match="passed eval"):
        OrganRecord.model_validate(admitted)


def test_registry_rejects_shared_contours_and_secret_material() -> None:
    stats = _record("aoa-stats", "shadow")
    stats["credential_contours"]["read"] = "kag-read"
    stats["capabilities"][0]["credential_class"] = "kag-read"
    with pytest.raises(ValidationError, match="is shared"):
        _source(_record("aoa-kag", "shadow"), stats)

    source = _source(_record("aoa-kag", "shadow"))
    payload = source.model_dump(mode="json")
    payload["records"][0]["support_route"] = "sk-secret-like-value"
    with pytest.raises(OrganRegistryError, match="secret-like"):
        compile_registry(OrganRegistrySource.model_validate(payload))


def test_projection_is_deterministic_and_suspended_is_hidden(tmp_path: Path) -> None:
    source = _source(
        _record("aoa-stats", "suspended"),
        _record("aoa-kag", "shadow"),
    )
    first = compile_registry(source)
    second = compile_registry(source)
    assert first == second
    assert first.projection_digest == second.projection_digest
    assert_projection_digest(first)

    catalog = _api(tmp_path, source).catalog(maximum_policy="read")
    assert [entry.organ_id for entry in catalog.entries] == ["aoa-kag"]
    assert catalog.hidden_state_counts == {"suspended": 1}
    assert catalog.schema_bytes_loaded == 0
    assert "input_schema_ref" not in catalog.model_dump_json()


def test_long_lived_api_reloads_registry_revocations(tmp_path: Path) -> None:
    admitted = _source(_record("aoa-kag", "admitted"))
    api = _api(tmp_path, admitted)
    assert [entry.organ_id for entry in api.catalog().entries] == ["aoa-kag"]

    registry = tmp_path / "registry.json"
    suspended = _source(_record("aoa-kag", "suspended"))
    registry.write_text(suspended.model_dump_json(indent=2), encoding="utf-8")

    refreshed = api.catalog()
    assert refreshed.entries == ()
    assert refreshed.hidden_state_counts == {"suspended": 1}


def test_catalog_honors_byte_budget(tmp_path: Path) -> None:
    catalog = _api(
        tmp_path,
        _source(_record("aoa-kag", "shadow")),
    ).catalog(byte_budget=256)
    assert catalog.entries == ()
    assert catalog.truncated is True
    assert catalog.result_bytes == 2


def test_catalog_filters_task_allowlist_freshness_and_effect(tmp_path: Path) -> None:
    api = _api(tmp_path, _source(_record("aoa-kag", "shadow")))
    assert api.catalog(allowed_organ_ids=("aoa-stats",)).entries == ()
    assert api.catalog(freshness_states=("exact",)).entries == ()
    assert api.catalog(effect_classes=("external_change",)).entries == ()
    admitted = _api(tmp_path, _source(_record("aoa-kag", "admitted")))
    catalog = admitted.catalog(
        allowed_capability_ids=("knowledge-inspect",),
        freshness_states=("exact",),
        effect_classes=("observe",),
    )
    assert catalog.entries[0].capabilities[0].primitive_namespaces == (
        "aoa-kag.knowledge-inspect.inspect-knowledge",
    )


def test_workspace_registry_path_is_explicit_not_scanned(tmp_path: Path) -> None:
    manifest_dir = tmp_path / ".aoa"
    manifest_dir.mkdir()
    (manifest_dir / "workspace.toml").write_text(
        'schema_version = 1\n[organ_access]\nregistry_source = "../private.json"\n',
        encoding="utf-8",
    )
    workspace = Workspace.discover(tmp_path)
    assert workspace.organ_registry_path == (tmp_path / "private.json").resolve()
    assert workspace.organ_registry_source == (
        "manifest:organ_access.registry_source"
    )


def test_activation_is_content_addressed_candidate_only(tmp_path: Path) -> None:
    api = _api(tmp_path, _source(_record("aoa-kag", "admitted")))
    request = ActivationRequest(
        request_id="request-1",
        organ_id="aoa-kag",
        capability_id="knowledge-inspect",
        primitive_id="inspect-knowledge",
        consumer_id="codex-main",
        requested_policy_family="read",
        authorized_policy_families=("read",),
        credential_class="kag-read",
        observed_server_schema_digest=DIGEST_B,
        observed_consumer_schema_digest=DIGEST_C,
        requested_at=NOW,
        expires_at=NOW + timedelta(hours=1),
        precondition_evidence=(_evidence("precondition"),),
    )
    first = api.compile_activation(request, evaluated_at=NOW)
    second = api.compile_activation(request, evaluated_at=NOW)
    assert first == second
    assert first.execution_authorized is False
    assert first.plan_kind == "candidate_only"


def test_activation_uses_selected_consumer_schema_and_protocol(tmp_path: Path) -> None:
    record = _record("aoa-kag", "admitted")
    record["consumer_compatibility"][0]["observed_schema_digest"] = DIGEST_A
    api = _api(tmp_path, _source(record))
    request = ActivationRequest(
        request_id="request-consumer-drift",
        organ_id="aoa-kag",
        capability_id="knowledge-inspect",
        primitive_id="inspect-knowledge",
        consumer_id="codex-main",
        requested_policy_family="read",
        authorized_policy_families=("read",),
        credential_class="kag-read",
        observed_server_schema_digest=DIGEST_B,
        observed_consumer_schema_digest=DIGEST_C,
        requested_at=NOW,
        expires_at=NOW + timedelta(hours=1),
        precondition_evidence=(_evidence("precondition"),),
    )
    with pytest.raises(OrganRegistryError, match="selected consumer schema"):
        api.compile_activation(request, evaluated_at=NOW)

    record = _record("aoa-kag", "admitted")
    record["consumer_compatibility"][0]["protocol_versions"] = ["2099-01-01"]
    api = _api(tmp_path, _source(record))
    with pytest.raises(OrganRegistryError, match="no compatible endpoint protocol"):
        api.compile_activation(request, evaluated_at=NOW)


def test_activation_evidence_is_current_and_caps_plan_lifetime(
    tmp_path: Path,
) -> None:
    record = _record("aoa-kag", "admitted")
    evidence = _evidence("precondition")
    evidence["expires_at"] = (NOW + timedelta(minutes=20)).isoformat()
    record["activation_preconditions"] = [evidence]
    api = _api(tmp_path, _source(record))
    request = ActivationRequest(
        request_id="request-bounded-evidence",
        organ_id="aoa-kag",
        capability_id="knowledge-inspect",
        primitive_id="inspect-knowledge",
        consumer_id="codex-main",
        requested_policy_family="read",
        authorized_policy_families=("read",),
        credential_class="kag-read",
        observed_server_schema_digest=DIGEST_B,
        observed_consumer_schema_digest=DIGEST_C,
        requested_at=NOW,
        expires_at=NOW + timedelta(hours=1),
        precondition_evidence=(evidence,),
    )
    plan = api.compile_activation(
        request,
        evaluated_at=NOW + timedelta(minutes=10),
    )
    assert plan.expires_at == NOW + timedelta(minutes=20)
    with pytest.raises(OrganRegistryError, match="expired at plan compilation"):
        api.compile_activation(
            request,
            evaluated_at=NOW + timedelta(minutes=21),
        )


def test_shadow_and_schema_drift_block_activation(tmp_path: Path) -> None:
    shadow_api = _api(tmp_path, _source(_record("aoa-kag", "shadow")))
    request_payload = {
        "request_id": "request-1",
        "organ_id": "aoa-kag",
        "capability_id": "knowledge-inspect",
        "primitive_id": "inspect-knowledge",
        "consumer_id": "codex-main",
        "requested_policy_family": "read",
        "authorized_policy_families": ["read"],
        "credential_class": "kag-read",
        "observed_server_schema_digest": DIGEST_B,
        "observed_consumer_schema_digest": DIGEST_C,
        "requested_at": NOW,
        "expires_at": NOW + timedelta(hours=1),
        "precondition_evidence": [],
    }
    with pytest.raises(OrganRegistryError, match="not admitted"):
        shadow_api.compile_activation(ActivationRequest.model_validate(request_payload))

    admitted_api = _api(
        tmp_path,
        _source(_record("aoa-kag", "admitted")),
    )
    request_payload["observed_server_schema_digest"] = DIGEST_A
    request_payload["precondition_evidence"] = [_evidence("precondition")]
    with pytest.raises(OrganRegistryError, match="schema digest drift"):
        admitted_api.compile_activation(
            ActivationRequest.model_validate(request_payload)
        )


def test_expired_request_and_wrong_approval_owner_are_denied(
    tmp_path: Path,
) -> None:
    read_api = _api(tmp_path, _source(_record("aoa-kag", "admitted")))
    expired = ActivationRequest(
        request_id="request-expired",
        organ_id="aoa-kag",
        capability_id="knowledge-inspect",
        primitive_id="inspect-knowledge",
        consumer_id="codex-main",
        requested_policy_family="read",
        authorized_policy_families=("read",),
        credential_class="kag-read",
        observed_server_schema_digest=DIGEST_B,
        observed_consumer_schema_digest=DIGEST_C,
        requested_at=NOW,
        expires_at=NOW + timedelta(minutes=1),
        precondition_evidence=(_evidence("precondition"),),
    )
    with pytest.raises(OrganRegistryError, match="request is expired"):
        read_api.compile_activation(
            expired,
            evaluated_at=NOW + timedelta(minutes=2),
        )

    effect_api = _api(
        tmp_path,
        _source(_record("aoa-kag", "admitted", effect=True)),
    )
    wrong_approval = ActivationRequest(
        request_id="request-effect",
        organ_id="aoa-kag",
        capability_id="knowledge-publish",
        primitive_id="publish-change",
        consumer_id="codex-main",
        requested_policy_family="external_effect",
        authorized_policy_families=("external_effect",),
        credential_class="kag-external-effect",
        observed_server_schema_digest=DIGEST_B,
        observed_consumer_schema_digest=DIGEST_C,
        requested_at=NOW,
        expires_at=NOW + timedelta(hours=1),
        precondition_evidence=(_evidence("precondition"),),
        approval_ref=_evidence("approval"),
        exact_effect_target="https://example.invalid/exact/record",
    )
    with pytest.raises(OrganRegistryError, match="approval owner"):
        effect_api.compile_activation(wrong_approval, evaluated_at=NOW)


def test_external_effect_needs_exact_target_and_approval() -> None:
    payload = {
        "request_id": "request-1",
        "organ_id": "aoa-kag",
        "capability_id": "knowledge-publish",
        "primitive_id": "publish-change",
        "consumer_id": "codex-main",
        "requested_policy_family": "external_effect",
        "authorized_policy_families": ["external_effect"],
        "credential_class": "kag-external-effect",
        "observed_server_schema_digest": DIGEST_B,
        "observed_consumer_schema_digest": DIGEST_C,
        "requested_at": NOW,
        "expires_at": NOW + timedelta(hours=1),
        "precondition_evidence": [],
    }
    with pytest.raises(ValidationError, match="approval"):
        ActivationRequest.model_validate(payload)
    payload["approval_ref"] = _evidence("approval")
    with pytest.raises(ValidationError, match="exact target"):
        ActivationRequest.model_validate(payload)


def test_direct_connection_descriptor_cannot_claim_execution_authority() -> None:
    payload = {
        "adapter_id": "owner-direct",
        "endpoint": {
            "adapter_id": "owner-direct",
            "transport": "streamable-http",
            "endpoint_ref": "config://organs/kag/endpoint",
            "protocol_versions": ["2025-11-25"],
        },
        "credential_class": "kag-read",
        "execution_authorized": True,
    }
    with pytest.raises(ValidationError, match="False"):
        DirectConnectionDescriptor.model_validate(payload)


class OwnerPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    answer: str


def test_result_envelope_keeps_owner_payload_typed() -> None:
    metadata = OrganResultMetadata(
        organ_id="aoa-kag",
        capability_id="knowledge-inspect",
        primitive_id="inspect-knowledge",
        owners={
            "source_owner": "aoa-kag",
            "access_owner": "aoa-kag",
            "runtime_owner": "abyss-stack",
            "proof_owner": "aoa-evals",
            "acceptance_owner": "aoa-kag",
        },
        authority_ceiling="read",
        source_revision="source-1",
        deployed_revision="deploy-1",
        package_identity={"revision": "pkg-1", "digest": DIGEST_A},
        server_schema_digest=DIGEST_B,
        consumer_observed_digest=DIGEST_C,
        provider_watermark="owner-watermark-1",
        observed_at=NOW,
        freshness_state="exact",
        freshness_policy={
            "policy_id": "kag-freshness",
            "max_age_seconds": 300,
            "cache_scope": "task",
        },
        cache_scope="task",
        evidence_refs=(),
        effect_class="observe",
        applied_state="not_applied",
        trace_id="trace-1",
    )
    envelope = OrganResultEnvelope[OwnerPayload](
        metadata=metadata,
        owner_payload_schema_ref="schemas/kag-payload.json",
        owner_payload=OwnerPayload(answer="grounded"),
    )
    restored = OrganResultEnvelope[OwnerPayload].model_validate_json(
        envelope.model_dump_json()
    )
    assert restored.owner_payload.answer == "grounded"
    raw = json.loads(restored.model_dump_json())
    raw["metadata"]["applied_state"] = "applied"
    with pytest.raises(ValidationError, match="cannot claim"):
        OrganResultEnvelope[OwnerPayload].model_validate(raw)


def _owner_result_capture() -> OwnerResultCapture:
    return OwnerResultCapture(
        capture_owner="abyss-stack",
        capture_receipt_ref="records/aoa-kag/receipt.json",
        capture_receipt_id=DIGEST_A,
        result_artifact_ref="results/aoa-kag/result.json",
        result_artifact_id=DIGEST_B,
        organ_id="aoa-kag",
        capability_id="knowledge-inspect",
        primitive_id="inspect-knowledge",
        result_digest=DIGEST_C,
        result_schema_identity="aoa_kag_discover_result_v1",
        server_schema_digest=DIGEST_A,
        primitive_schema_digest=DIGEST_B,
        observed_at=NOW,
        expires_at=NOW + timedelta(minutes=10),
    )


def _owner_result_review() -> OwnerResultReviewStatement:
    return OwnerResultReviewStatement(
        review_owner="aoa-kag",
        organ_id="aoa-kag",
        capability_id="knowledge-inspect",
        primitive_id="inspect-knowledge",
        owners={
            "source_owner": "aoa-kag",
            "access_owner": "aoa-kag",
            "runtime_owner": "abyss-stack",
            "proof_owner": "aoa-evals",
            "acceptance_owner": "aoa-kag",
        },
        capture=_owner_result_capture(),
        source_revision={"revision": "source-1", "digest": DIGEST_A},
        owner_payload_schema_ref="schemas/kag-payload.json",
        owner_payload_schema_digest=DIGEST_B,
        reviewed_at=NOW + timedelta(seconds=2),
        expires_at=NOW + timedelta(minutes=5),
        grounding_state="grounded",
        freshness_state="exact",
        freshness_policy={
            "policy_id": "kag-freshness",
            "max_age_seconds": 300,
            "cache_scope": "task",
        },
        provider_watermark="owner-watermark-1",
        grounding_evidence=(
            {
                **_evidence("owner-grounding"),
                "owner": "aoa-kag",
            },
        ),
    )


def test_owner_result_review_is_owner_bounded_and_content_addressed() -> None:
    receipt = materialize_owner_result_review(_owner_result_review())
    assert assert_owner_result_review(receipt) is receipt
    assert receipt.review_owner == receipt.owners.source_owner
    assert receipt.capture.capture_owner == receipt.owners.runtime_owner
    assert receipt.owner_accepted is False
    assert receipt.central_proof_asserted is False
    assert receipt.admission_asserted is False

    tampered = receipt.model_copy(update={"review_id": DIGEST_C})
    with pytest.raises(OwnerResultReviewError, match="digest mismatch"):
        assert_owner_result_review(tampered)


def test_owner_result_review_rejects_authority_and_freshness_overreach() -> None:
    payload = _owner_result_review().model_dump(mode="json")
    payload["review_owner"] = "abyss-stack"
    with pytest.raises(ValidationError, match="source or acceptance owner"):
        OwnerResultReviewStatement.model_validate(payload)

    payload = _owner_result_review().model_dump(mode="json")
    payload["capture"]["capture_owner"] = "aoa-sdk"
    with pytest.raises(ValidationError, match="runtime owner"):
        OwnerResultReviewStatement.model_validate(payload)

    payload = _owner_result_review().model_dump(mode="json")
    payload["expires_at"] = (NOW + timedelta(minutes=11)).isoformat()
    with pytest.raises(ValidationError, match="outlive"):
        OwnerResultReviewStatement.model_validate(payload)

    payload = _owner_result_review().model_dump(mode="json")
    payload["grounding_state"] = "blocked"
    payload["freshness_state"] = "blocked"
    payload["provider_watermark"] = None
    payload["reason_codes"] = []
    with pytest.raises(ValidationError, match="reason codes"):
        OwnerResultReviewStatement.model_validate(payload)

    receipt_payload = materialize_owner_result_review(
        _owner_result_review()
    ).model_dump(mode="json")
    receipt_payload["owner_accepted"] = True
    with pytest.raises(ValidationError, match="False"):
        OwnerResultReviewReceipt.model_validate(receipt_payload)


def test_cli_exposes_progressive_non_executing_surface() -> None:
    runner = CliRunner()
    part_root = Path(__file__).resolve().parents[1]
    fixture = part_root / "examples" / "organ_registry.wave1-shadow.example.json"
    validated = runner.invoke(app, ["organs", "validate", str(fixture)])
    assert validated.exit_code == 0
    assert '"execution_authorized": false' in validated.stdout

    catalog = runner.invoke(
        app,
        [
            "organs",
            "catalog",
            "--registry",
            str(fixture),
            "--query",
            "knowledge",
        ],
    )
    assert catalog.exit_code == 0
    assert '"schema_bytes_loaded": 0' in catalog.stdout
    assert "input_schema_ref" not in catalog.stdout


def test_generated_schemas_declare_dialect_and_stable_identity() -> None:
    schema_root = Path(__file__).resolve().parents[5] / "schemas" / "organ-access"
    for path in sorted(schema_root.glob("*.schema.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert payload["$id"] == f"urn:aoa-sdk:organ-access:{path.name}"
