from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest
from typer.testing import CliRunner

from aoa_sdk.contracts.organ_admission import (
    AdmissionDecisionStatement,
    AdmissionEvidenceStatement,
    AdmissionTarget,
    OrganAdmissionRequest,
    OwnerValidatorBinding,
    RegistryComparisonAnchor,
)
from aoa_sdk.contracts.organs import (
    CapabilityContract,
    OrganRecord,
    OrganRegistrySource,
)
from aoa_sdk.organs.admission import (
    ADMISSION_STAGES,
    OrganAdmissionError,
    advance_admission,
    audit_admission_baseline,
    authorize_registry_transition,
    build_admission_candidate,
    materialize_admission_decision,
    materialize_admission_evidence,
    start_admission,
    validate_admission_run,
)
from aoa_sdk.organs.registry import compile_registry, sha256_digest
from aoa_sdk.cli.main import app
from aoa_sdk.organs.api import OrgansAPI


NOW = datetime(2026, 8, 1, 12, 0, tzinfo=timezone.utc)
DIGEST_A = "sha256:" + ("a" * 64)
DIGEST_B = "sha256:" + ("b" * 64)
DIGEST_C = "sha256:" + ("c" * 64)
DIGEST_D = "sha256:" + ("d" * 64)

OWNERS = {
    "source_owner": "owner-source",
    "access_owner": "owner-access",
    "runtime_owner": "abyss-stack",
    "proof_owner": "aoa-evals",
    "acceptance_owner": "owner-acceptance",
}


def _capability() -> CapabilityContract:
    return CapabilityContract.model_validate(
        {
            "capability_id": "owner-read",
            "summary": "Read one owner-qualified result with exact provenance.",
            "policy_family": "read",
            "credential_class": "owner-read-credential",
            "primitives": [
                {
                    "primitive_id": "owner-inspect",
                    "kind": "tool",
                    "mcp_name": "owner_inspect",
                    "effect_class": "observe",
                    "policy_family": "read",
                    "input_schema_ref": "owner://schema/input",
                    "output_schema_ref": "owner://schema/output",
                    "idempotency": "read_only",
                    "maximum_blast_radius": "one read-only owner result",
                }
            ],
            "owner_payload_schema_ref": "owner://schema/payload",
        }
    )


def _qualified(receipt, *, owner: str | None = None) -> dict:
    return {
        "owner": owner or receipt.owner,
        "evidence_ref": receipt.evidence_ref,
        "revision": receipt.evidence_revision,
        "observed_at": receipt.observed_at,
        "expires_at": receipt.expires_at,
    }


def _declared_evidence() -> dict:
    return {
        "owner": "owner-source",
        "evidence_ref": "owner://decision/declared",
        "revision": "source-1",
        "observed_at": NOW,
        "expires_at": NOW + timedelta(hours=4),
    }


def _maturity_shadow() -> dict:
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
    return {
        name: (
            {
                "state": "asserted",
                "evidence": _declared_evidence(),
                "freshness_policy": "owner-review-v1",
            }
            if name == "declared"
            else {"state": "not_asserted"}
        )
        for name in names
    }


def _shadow_record() -> dict:
    return {
        "organ_id": "owner-organ",
        "display_name": "Owner Organ",
        "description": "Owner-bounded read access contour used for admission tests.",
        "owners": OWNERS,
        "registry_state": "shadow",
        "authority_ceiling": "read",
        "authentication_requirements": ["owner-bearer"],
        "credential_contours": {"read": "owner-read-credential"},
        "revisions": {"source": {"revision": "source-1", "digest": DIGEST_A}},
        "freshness_policy": {
            "policy_id": "owner-freshness",
            "max_age_seconds": 300,
            "cache_scope": "task",
        },
        "capabilities": [_capability().model_dump(mode="json")],
        "maturity": _maturity_shadow(),
        "rollback_route": "owner://rollback/read",
        "support_route": "owner://support/read",
        "handoff": {
            "input_ref_kind": "query-ref",
            "output_ref_kind": "owner-result-ref",
            "next_owner": "consumer",
            "stop_states": ["owner-review-required"],
        },
    }


def _projection():
    source = OrganRegistrySource.model_validate(
        {
            "registry_id": "private-registry",
            "workspace_owner": "os-abyss",
            "authored_at": NOW,
            "expires_at": NOW + timedelta(hours=4),
            "owner_decision_refs": ["owner://decision/registry"],
            "records": [_shadow_record()],
        }
    )
    return compile_registry(source)


def _validators() -> tuple[OwnerValidatorBinding, ...]:
    return tuple(
        OwnerValidatorBinding(
            owner=owner,
            validator_ref=f"owner://{owner}/validator/admission",
            validator_revision="validator-1",
            validator_schema_digest=DIGEST_D,
        )
        for owner in sorted({*OWNERS.values(), "consumer-owner", "os-operator"})
    )


def _request() -> tuple[OrganAdmissionRequest, object]:
    projection = _projection()
    entry = projection.entries[0]
    target = AdmissionTarget(
        organ_id="owner-organ",
        capability_id="owner-read",
        primitive_ids=("owner-inspect",),
        policy_family="read",
        credential_class="owner-read-credential",
    )
    request = OrganAdmissionRequest(
        request_id="owner-organ-read-admission",
        requested_by="owner-access",
        operator_owner="os-operator",
        consumer_owner="consumer-owner",
        owners=OWNERS,
        target=target,
        proposed_capability=_capability(),
        current_registry=RegistryComparisonAnchor(
            registry_id=projection.registry_id,
            registry_digest=projection.projection_digest,
            entry_digest=sha256_digest(entry.model_dump(mode="json")),
            entry_state=entry.registry_state,
            observed_at=projection.compiled_at,
            expires_at=projection.expires_at,
        ),
        owner_validator_bindings=_validators(),
        requested_at=NOW + timedelta(seconds=1),
        expires_at=NOW + timedelta(hours=3),
    )
    return request, projection


def test_admission_request_preserves_exact_mcp_binding() -> None:
    request, _ = _request()

    assert request.proposed_capability.primitives[0].mcp_name == "owner_inspect"
    assert request.model_dump(mode="json")["proposed_capability"]["primitives"][0][
        "mcp_name"
    ] == "owner_inspect"

    primitive = _capability().primitives[0]
    resource = primitive.__class__.model_validate(
        {
            **primitive.model_dump(mode="json"),
            "kind": "resource_template",
            "mcp_name": "owner://session/{session}/brief",
        }
    )
    assert resource.mcp_name == "owner://session/{session}/brief"


def _owner_for(request: OrganAdmissionRequest, stage: str) -> str:
    if stage in {"owner_source", "reviewed_revision"}:
        return request.owners.source_owner
    if stage in {"package", "observed_schema", "auth_contour"}:
        return request.owners.access_owner
    if stage in {
        "deploy_manifest",
        "deployed_bytes",
        "process_identity",
        "endpoint",
        "authenticated_canary",
    }:
        return request.owners.runtime_owner
    if stage == "consumer_registration":
        return request.consumer_owner
    if stage == "rollback_proof":
        return request.owners.proof_owner
    if stage == "central_proof":
        return request.owners.proof_owner
    return request.owners.acceptance_owner


def _subject(stage: str) -> tuple[str, str, str]:
    if stage == "owner_source":
        return "owner://source/tree", "source-1", DIGEST_A
    if stage == "package":
        return "package://owner/read", "package-1", DIGEST_B
    if stage == "deploy_manifest":
        return "deploy://owner/manifest", "deploy-1", DIGEST_B
    if stage == "deployed_bytes":
        return "deploy://owner/bytes", "deploy-1", DIGEST_C
    if stage == "endpoint":
        return "config://owner/endpoint", "endpoint-1", DIGEST_C
    if stage == "observed_schema":
        return "schema://owner/server", "schema-1", DIGEST_D
    if stage == "auth_contour":
        return "credential-class://owner/read", "owner-read-credential", DIGEST_A
    if stage == "consumer_registration":
        return "consumer://codex-main", "codex-main", DIGEST_B
    return f"owner://subject/{stage}", f"{stage}-1", DIGEST_A


def _receipt(
    run,
    stage: str,
    *,
    owner: str | None = None,
    outcome: str = "passed",
):
    selected_owner = owner or _owner_for(run.request, stage)
    validator = next(
        item
        for item in run.request.owner_validator_bindings
        if item.owner == selected_owner
    )
    subject_ref, subject_revision, subject_digest = _subject(stage)
    index = ADMISSION_STAGES.index(stage)
    statement = AdmissionEvidenceStatement(
        run_id=run.run_id,
        previous_snapshot_digest=run.snapshot_digest,
        stage=stage,
        issuer=selected_owner,
        owner=selected_owner,
        target=run.request.target,
        subject_ref=subject_ref,
        subject_revision=subject_revision,
        subject_digest=subject_digest,
        subject_schema_ref=f"owner://schema/{stage}",
        subject_schema_digest=DIGEST_D,
        evidence_ref=f"owner://evidence/{stage}",
        evidence_revision=f"evidence-{index}",
        evidence_digest=f"sha256:{index + 1:064x}",
        validator=validator,
        validation_receipt_ref=f"owner://validation/{stage}",
        validation_receipt_digest=f"sha256:{index + 20:064x}",
        observed_at=NOW + timedelta(seconds=index + 2),
        expires_at=NOW + timedelta(hours=2),
        outcome=outcome,
        reason_codes=("owner_gate_blocked",) if outcome != "passed" else (),
    )
    return materialize_admission_evidence(statement)


def _complete_run():
    request, projection = _request()
    run = start_admission(request, projection)
    for stage in ADMISSION_STAGES:
        run = advance_admission(run, _receipt(run, stage))
    return run, projection


def _admitted_record(run) -> OrganRecord:
    evidence = {item.stage: item for item in run.evidence}
    maturity_stages = {
        "declared": "owner_source",
        "owner_reviewed": "reviewed_revision",
        "packaged": "package",
        "exported": "deploy_manifest",
        "deployed": "deployed_bytes",
        "process_alive": "process_identity",
        "endpoint_ready": "endpoint",
        "consumer_registered": "consumer_registration",
        "schema_observed": "observed_schema",
        "call_succeeded": "authenticated_canary",
        "result_grounded": "owner_grounding_freshness",
        "freshness_satisfied": "owner_grounding_freshness",
        "owner_accepted": "owner_result_acceptance",
        "rollback_proven": "rollback_proof",
    }
    maturity = {
        axis: {
            "state": "asserted",
            "evidence": _qualified(evidence[stage]),
            "freshness_policy": "admission-evidence-expiry-v1",
        }
        for axis, stage in maturity_stages.items()
    }
    maturity["registry_indexed"] = {"state": "not_asserted"}
    maturity["cross_organ_proven"] = {"state": "not_asserted"}
    payload = _shadow_record()
    payload.update(
        {
            "registry_state": "admitted",
            "revisions": {
                "source": {"revision": "source-1", "digest": DIGEST_A},
                "package": {"revision": "package-1", "digest": DIGEST_B},
                "deploy": {"revision": "deploy-1", "digest": DIGEST_C},
                "consumer_schema": {
                    "revision": "consumer-schema-1",
                    "schema_digest": DIGEST_D,
                },
            },
            "freshness_state": "exact",
            "freshness_evidence": _qualified(
                evidence["owner_grounding_freshness"]
            ),
            "eval_status": "passed",
            "eval_evidence": _qualified(evidence["central_proof"]),
            "endpoint": {
                "adapter_id": "owner-direct",
                "transport": "streamable-http",
                "endpoint_ref": "config://owner/endpoint",
                "protocol_versions": ["2026-07-28"],
                "server_schema_digest": DIGEST_D,
            },
            "consumer_compatibility": [
                {
                    "consumer_id": "codex-main",
                    "support_state": "supported",
                    "protocol_versions": ["2026-07-28"],
                    "observed_schema_digest": DIGEST_D,
                    "evidence_ref": _qualified(
                        evidence["consumer_registration"]
                    ),
                }
            ],
            "maturity": maturity,
            "activation_preconditions": [
                _qualified(evidence["central_proof"]),
                _qualified(evidence["owner_result_acceptance"]),
            ],
        }
    )
    return OrganRecord.model_validate(payload)


def _decision(candidate, kind: str, issuer: str, offset: int):
    return materialize_admission_decision(
        AdmissionDecisionStatement(
            candidate_id=candidate.candidate_id,
            decision_kind=kind,
            issuer=issuer,
            decision="accepted",
            decision_ref=f"owner://decision/{kind}/{offset}",
            decision_artifact_digest=f"sha256:{offset:064x}",
            decided_at=candidate.created_at + timedelta(seconds=offset),
            expires_at=candidate.expires_at,
        )
    )


def test_complete_admission_is_deterministic_resumable_and_non_executing() -> None:
    run, projection = _complete_run()
    assert run.state == "ready_for_candidate"
    assert validate_admission_run(run.model_copy()) == run
    assert advance_admission(run, run.evidence[0]) == run

    candidate = build_admission_candidate(
        run,
        projection,
        evaluated_at=NOW + timedelta(minutes=1),
    )
    repeated = build_admission_candidate(
        run,
        projection,
        evaluated_at=NOW + timedelta(minutes=1),
    )
    assert repeated == candidate
    assert candidate.preview.action == "replace_capability"
    assert candidate.registry_update_authorized is False
    assert candidate.effect_activation_authorized is False
    assert candidate.preview.registry_mutation_performed is False

    owner = _decision(candidate, "owner", "owner-acceptance", 1)
    operator = _decision(candidate, "operator", "os-operator", 2)
    authorization = authorize_registry_transition(
        run,
        candidate,
        owner,
        operator,
        _admitted_record(run),
        projection,
        evaluated_at=candidate.created_at + timedelta(seconds=3),
    )
    assert authorization.registry_update_authorized is True
    assert authorization.registry_mutation_performed is False
    assert authorization.post_update_projection_verification_required is True
    assert authorization.effect_activation_authorized is False


def test_order_conflict_and_incomplete_candidate_fail_closed() -> None:
    request, projection = _request()
    run = start_admission(request, projection)
    with pytest.raises(OrganAdmissionError, match="out of order"):
        advance_admission(run, _receipt(run, "package"))
    with pytest.raises(OrganAdmissionError, match="incomplete"):
        build_admission_candidate(
            run,
            projection,
            evaluated_at=NOW + timedelta(minutes=1),
        )

    first = _receipt(run, "owner_source")
    advanced = advance_admission(run, first)
    conflicting = first.model_copy(update={"evidence_id": DIGEST_D})
    with pytest.raises(OrganAdmissionError, match="digest mismatch"):
        advance_admission(advanced, conflicting)


def test_blocked_stage_is_typed_terminal_state() -> None:
    request, projection = _request()
    run = start_admission(request, projection)
    blocked = advance_admission(
        run,
        _receipt(run, "owner_source", outcome="blocked"),
    )
    assert blocked.state == "blocked"
    assert blocked.next_stage is None
    assert blocked.stop_reason_codes == ("owner_gate_blocked",)
    with pytest.raises(OrganAdmissionError, match="incomplete"):
        build_admission_candidate(
            blocked,
            projection,
            evaluated_at=NOW + timedelta(minutes=1),
        )


def test_proof_and_acceptance_cannot_be_self_issued_or_wrong_owner() -> None:
    request, projection = _request()
    run = start_admission(request, projection)
    for stage in ADMISSION_STAGES[:12]:
        run = advance_admission(run, _receipt(run, stage))
    with pytest.raises(OrganAdmissionError, match="wrong owner"):
        advance_admission(
            run,
            _receipt(run, "central_proof", owner="owner-acceptance"),
        )


def test_consumer_receipt_cannot_be_issued_by_registry_operator() -> None:
    request, projection = _request()
    run = start_admission(request, projection)
    for stage in ADMISSION_STAGES[:9]:
        run = advance_admission(run, _receipt(run, stage))

    with pytest.raises(OrganAdmissionError, match="wrong owner"):
        advance_admission(
            run,
            _receipt(run, "consumer_registration", owner="os-operator"),
        )


def test_registry_drift_and_nonseparate_decisions_block_authorization() -> None:
    run, projection = _complete_run()
    candidate = build_admission_candidate(
        run,
        projection,
        evaluated_at=NOW + timedelta(minutes=1),
    )
    drifted = projection.model_copy(update={"projection_digest": DIGEST_D})
    with pytest.raises(OrganAdmissionError, match="registry digest drifted"):
        build_admission_candidate(
            run,
            drifted,
            evaluated_at=NOW + timedelta(minutes=1),
        )

    owner = _decision(candidate, "owner", "owner-acceptance", 1)
    copied = owner.model_copy(update={"decision_kind": "operator", "issuer": "os-operator"})
    with pytest.raises(OrganAdmissionError, match="digest mismatch"):
        authorize_registry_transition(
            run,
            candidate,
            owner,
            copied,
            _admitted_record(run),
            projection,
            evaluated_at=candidate.created_at + timedelta(seconds=3),
        )


def test_secret_like_evidence_is_rejected_before_chain_entry() -> None:
    request, projection = _request()
    run = start_admission(request, projection)
    receipt = _receipt(run, "owner_source")
    payload = receipt.model_dump(mode="json", exclude={"evidence_id"})
    payload["subject_ref"] = "sk-not-allowed"
    with pytest.raises(OrganAdmissionError, match="secret-like"):
        materialize_admission_evidence(
            AdmissionEvidenceStatement.model_validate(payload)
        )


def test_registry_indexed_is_projection_owned_not_circular_source_claim() -> None:
    projection = _projection()
    indexed = projection.entries[0].maturity.registry_indexed
    assert indexed.state == "asserted"
    assert indexed.evidence is not None
    assert indexed.evidence.owner == "aoa-sdk"
    assert indexed.freshness_policy == "registry-projection-expiry-v1"


def test_baseline_audit_distinguishes_current_from_expired_evidence() -> None:
    run, _ = _complete_run()
    admitted = _admitted_record(run)
    projection = compile_registry(
        OrganRegistrySource(
            registry_id="private-registry",
            workspace_owner="os-abyss",
            authored_at=NOW,
            expires_at=NOW + timedelta(hours=4),
            owner_decision_refs=("owner://decision/registry",),
            records=(admitted,),
        )
    )
    current = audit_admission_baseline(
        projection,
        organ_id="owner-organ",
        capability_id="owner-read",
        evaluated_at=NOW + timedelta(hours=1),
    )
    assert current.status == "current"
    assert current.admission_current is True

    expired = audit_admission_baseline(
        projection,
        organ_id="owner-organ",
        capability_id="owner-read",
        evaluated_at=NOW + timedelta(hours=2),
    )
    assert expired.status == "refresh_required"
    assert expired.admission_current is False
    assert "required_maturity_evidence_expired" in expired.reason_codes


def test_cli_validates_persisted_resumable_admission_run(tmp_path) -> None:
    run, _ = _complete_run()
    run_path = tmp_path / "admission-run.json"
    run_path.write_text(run.model_dump_json(indent=2), encoding="utf-8")
    result = CliRunner().invoke(
        app,
        ["organs", "admission-validate", str(run_path)],
    )
    assert result.exit_code == 0
    assert '"state": "ready_for_candidate"' in result.stdout
    assert '"registry_mutated_by_sdk": false' in result.stdout


def test_cli_writes_baseline_audit_without_mutating_registry(
    tmp_path,
    monkeypatch,
) -> None:
    audit = audit_admission_baseline(
        _projection(),
        organ_id="owner-organ",
        capability_id="owner-read",
        evaluated_at=NOW + timedelta(hours=1),
    )
    monkeypatch.setattr(
        OrgansAPI,
        "audit_admission_baseline",
        lambda self, organ_id, capability_id: audit,
    )
    output = tmp_path / "baseline-audit.json"
    result = CliRunner().invoke(
        app,
        [
            "organs",
            "admission-audit",
            "owner-organ",
            "owner-read",
            "--output",
            str(output),
        ],
    )
    assert result.exit_code == 0
    assert json.loads(output.read_text(encoding="utf-8")) == audit.model_dump(
        mode="json"
    )
    assert '"owner_tools_executed_by_sdk": false' in result.stdout
