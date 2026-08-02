from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from aoa_sdk.cli.main import app
from aoa_sdk.contracts.control_plane import canonical_digest
from aoa_sdk.contracts.organ_orchestration import (
    CrossOrganOrchestrationRequest,
    CrossOrganOrchestrationRun,
    CrossOrganStageObservation,
    HostVisibleStageReceipt,
)
from aoa_sdk.organs.orchestration import (
    OrganOrchestrationError,
    advance_orchestration,
    start_orchestration,
    validate_orchestration_run,
)


PART_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_ROOT = PART_ROOT / "examples"
SCHEMA_ROOT = PART_ROOT / "schemas"


def _payload(name: str) -> dict:
    return json.loads((EXAMPLE_ROOT / name).read_text(encoding="utf-8"))


def _request() -> CrossOrganOrchestrationRequest:
    return CrossOrganOrchestrationRequest.model_validate(
        _payload("cross-organ.request.example.json")
    )


def _accepted() -> CrossOrganOrchestrationRun:
    return CrossOrganOrchestrationRun.model_validate(
        _payload("cross-organ.accepted-shape.example.json")
    )


def _observation_payload(stage_index: int) -> dict:
    return _accepted().stages[stage_index].observation.model_dump(mode="json")


def _rehash_receipt(observation_payload: dict) -> None:
    receipt_payload = observation_payload["receipt"]
    receipt_payload["receipt_digest"] = "sha256:" + ("0" * 64)
    receipt = HostVisibleStageReceipt.model_validate(receipt_payload)
    receipt_payload["receipt_digest"] = canonical_digest(
        receipt,
        exclude={"receipt_digest"},
    )


def test_generated_runs_are_deterministic_and_keep_authority_bounded() -> None:
    accepted = validate_orchestration_run(_accepted())
    assert accepted.state == "accepted"
    assert len(accepted.stages) == 5
    assert accepted.next_owner is None
    assert accepted.owner_tools_executed_by_sdk is False
    assert accepted.proof_computed_by_sdk is False
    assert accepted.durable_memory_written_by_sdk is False
    assert accepted.acceptance_inferred_by_sdk is False
    assert accepted.runtime_execution_authorized is False

    stopped = validate_orchestration_run(
        CrossOrganOrchestrationRun.model_validate(
            _payload("cross-organ.stale-stop.example.json")
        )
    )
    assert stopped.state == "stopped"
    assert stopped.stop_reason_codes == ("stale_owner_evidence",)
    assert len(stopped.stages) == 1
    assert stopped.next_stage_kind is None


def test_chain_can_only_advance_one_exact_receipted_stage_at_a_time() -> None:
    expected = _accepted()
    run = start_orchestration(_request())
    assert run == start_orchestration(_request())
    for sequence, expected_stage in enumerate(expected.stages):
        assert run.next_stage_kind == expected_stage.observation.stage_kind
        run = advance_orchestration(run, expected_stage.observation)
        assert run.stages[-1].sequence == sequence
        assert (
            run.stages[-1].previous_stage_digest
            == (
                None
                if sequence == 0
                else run.stages[sequence - 1].stage_digest
            )
        )
    assert run == expected


def test_receipt_or_snapshot_tampering_fails_closed() -> None:
    payload = _payload("cross-organ.accepted-shape.example.json")
    payload["stages"][2]["observation"]["receipt"]["receipt_digest"] = (
        "sha256:" + ("f" * 64)
    )
    tampered = CrossOrganOrchestrationRun.model_validate(payload)
    with pytest.raises(OrganOrchestrationError, match="receipt digest"):
        validate_orchestration_run(tampered)

    payload = _payload("cross-organ.accepted-shape.example.json")
    payload["snapshot_digest"] = "sha256:" + ("e" * 64)
    tampered = CrossOrganOrchestrationRun.model_validate(payload)
    with pytest.raises(OrganOrchestrationError, match="deterministic receipt chain"):
        validate_orchestration_run(tampered)


def test_acceptance_requires_explicit_owner_review_and_exact_owner_receipt() -> None:
    expected = _accepted()
    run = start_orchestration(_request())
    for stage in expected.stages[:4]:
        run = advance_orchestration(run, stage.observation)

    final_payload = expected.stages[-1].observation.model_dump(mode="json")
    final_payload["review_ref"] = None
    without_review = CrossOrganStageObservation.model_validate(final_payload)
    with pytest.raises(OrganOrchestrationError, match="explicit review"):
        advance_orchestration(run, without_review)

    final_payload = expected.stages[-1].observation.model_dump(mode="json")
    final_payload["receipt"]["owner_receipt_refs"] = []
    receipt = final_payload["receipt"]
    receipt["receipt_digest"] = "sha256:" + ("0" * 64)
    receipt_model = HostVisibleStageReceipt.model_validate(receipt)
    receipt["receipt_digest"] = canonical_digest(
        receipt_model,
        exclude={"receipt_digest"},
    )
    without_owner_receipt = CrossOrganStageObservation.model_validate(
        final_payload
    )
    with pytest.raises(OrganOrchestrationError, match="owner decision receipt"):
        advance_orchestration(run, without_owner_receipt)


def test_stale_evidence_and_model_confidence_cannot_proceed() -> None:
    first = _accepted().stages[0].observation.model_dump(mode="json")
    first["freshness_state"] = "stale_readable"
    with pytest.raises(ValidationError, match="must stop or deny"):
        CrossOrganStageObservation.model_validate(first)

    final = _accepted().stages[-1].observation.model_dump(mode="json")
    final["model_confidence_is_acceptance_authority"] = True
    with pytest.raises(ValidationError, match="False"):
        CrossOrganStageObservation.model_validate(final)


def test_malformed_memo_candidate_and_schema_drift_fail_closed() -> None:
    first = _accepted().stages[0].observation
    run = advance_orchestration(start_orchestration(_request()), first)

    malformed_payload = _observation_payload(1)
    malformed_payload["output_ref"]["ref_kind"] = "eval_request"
    malformed = CrossOrganStageObservation.model_validate(malformed_payload)
    with pytest.raises(OrganOrchestrationError, match="output kind"):
        advance_orchestration(run, malformed)

    drift_payload = _observation_payload(1)
    drift_digest = "sha256:" + ("9" * 64)
    drift_payload["output_schema_identity"]["schema_digest"] = drift_digest
    drift_payload["output_ref"]["schema_identity"]["schema_digest"] = drift_digest
    drifted = CrossOrganStageObservation.model_validate(drift_payload)
    with pytest.raises(OrganOrchestrationError, match="schema identity drifted"):
        advance_orchestration(run, drifted)


def test_wrong_owner_and_expired_receipt_fail_closed() -> None:
    run = advance_orchestration(
        start_orchestration(_request()),
        _accepted().stages[0].observation,
    )

    wrong_owner_payload = _observation_payload(1)
    wrong_owner_payload["stage_owner"] = "not-aoa-memo"
    wrong_owner_payload["output_ref"]["owner"] = "not-aoa-memo"
    wrong_owner_payload["output_ref"]["schema_identity"]["owner"] = (
        "not-aoa-memo"
    )
    wrong_owner_payload["output_schema_identity"]["owner"] = "not-aoa-memo"
    wrong_owner = CrossOrganStageObservation.model_validate(wrong_owner_payload)
    with pytest.raises(OrganOrchestrationError, match="wrong owner"):
        advance_orchestration(run, wrong_owner)

    expired_receipt_payload = _observation_payload(1)
    expired_receipt_payload["expires_at"] = "2026-07-26T12:20:00Z"
    expired_receipt_payload["receipt"]["issued_at"] = "2026-07-26T12:20:00Z"
    _rehash_receipt(expired_receipt_payload)
    expired_receipt = CrossOrganStageObservation.model_validate(
        expired_receipt_payload
    )
    with pytest.raises(OrganOrchestrationError, match="after stage expiry"):
        advance_orchestration(run, expired_receipt)


def test_eval_rejection_stops_before_owner_acceptance() -> None:
    expected = _accepted()
    run = start_orchestration(_request())
    for stage in expected.stages[:3]:
        run = advance_orchestration(run, stage.observation)

    rejected_payload = _observation_payload(3)
    rejected_payload["next_owner"] = None
    rejected_payload["transition_state"] = "denied"
    rejected_payload["stop_reason_codes"] = ["eval_rejected"]
    rejected_payload["receipt"]["outcome"] = "denied"
    _rehash_receipt(rejected_payload)
    rejected = CrossOrganStageObservation.model_validate(rejected_payload)

    stopped = advance_orchestration(run, rejected)
    assert stopped.state == "denied"
    assert stopped.next_stage_kind is None
    assert stopped.next_owner is None
    assert stopped.stop_reason_codes == ("eval_rejected",)
    with pytest.raises(OrganOrchestrationError, match="terminal orchestration state"):
        advance_orchestration(stopped, expected.stages[4].observation)


def test_exact_replay_is_idempotent_and_advanced_snapshot_replay_is_denied() -> None:
    request = _request()
    initial = start_orchestration(request)
    first = _accepted().stages[0].observation

    advanced = advance_orchestration(initial, first)
    assert advance_orchestration(start_orchestration(request), first) == advanced
    with pytest.raises(OrganOrchestrationError, match="out of order"):
        advance_orchestration(advanced, first)


def test_serialized_restart_resumes_from_the_exact_snapshot() -> None:
    expected = _accepted()
    after_first = advance_orchestration(
        start_orchestration(_request()),
        expected.stages[0].observation,
    )
    restored = CrossOrganOrchestrationRun.model_validate_json(
        after_first.model_dump_json()
    )

    assert validate_orchestration_run(restored) == after_first
    assert advance_orchestration(restored, expected.stages[1].observation) == (
        advance_orchestration(after_first, expected.stages[1].observation)
    )


def test_cli_starts_advances_and_validates_without_owner_execution(
    tmp_path: Path,
) -> None:
    runner = CliRunner()
    request_path = EXAMPLE_ROOT / "cross-organ.request.example.json"
    initial_path = tmp_path / "initial.json"
    started = runner.invoke(
        app,
        [
            "organs",
            "orchestration-start",
            str(request_path),
            "--root",
            str(PART_ROOT),
            "--output",
            str(initial_path),
        ],
    )
    assert started.exit_code == 0, started.stdout
    assert '"owner_tools_executed_by_sdk": false' in started.stdout

    accepted = _accepted()
    observation_path = tmp_path / "observation.json"
    observation_path.write_text(
        accepted.stages[0].observation.model_dump_json(indent=2),
        encoding="utf-8",
    )
    advanced_path = tmp_path / "advanced.json"
    advanced = runner.invoke(
        app,
        [
            "organs",
            "orchestration-advance",
            str(initial_path),
            str(observation_path),
            "--root",
            str(PART_ROOT),
            "--output",
            str(advanced_path),
        ],
    )
    assert advanced.exit_code == 0, advanced.stdout

    validated = runner.invoke(
        app,
        [
            "organs",
            "orchestration-validate",
            str(advanced_path),
            "--root",
            str(PART_ROOT),
        ],
    )
    assert validated.exit_code == 0, validated.stdout
    assert '"stage_count": 1' in validated.stdout
    assert '"proof_computed_by_sdk": false' in validated.stdout


def test_generated_schemas_declare_dialect_and_part_local_identity() -> None:
    paths = sorted(SCHEMA_ROOT.glob("*.schema.json"))
    assert len(paths) == 8
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert payload["$id"] == (
            "urn:aoa-sdk:cross-organ-orchestration:" + path.name
        )


def test_examples_pin_exact_consumed_owner_schema_versions() -> None:
    request = _payload("cross-organ.request.example.json")
    by_stage = {
        contract["stage_kind"]: contract["output_schema"]
        for contract in request["stage_contracts"]
    }

    assert by_stage["eval_request"]["schema_version"] == "eval_need_v1"
    assert (
        by_stage["owner_acceptance"]["schema_version"]
        == "aoa_memo_reviewed_intake_landing_receipt_v1"
    )
