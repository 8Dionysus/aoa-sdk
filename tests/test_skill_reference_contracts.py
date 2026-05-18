from __future__ import annotations

from pathlib import Path

from aoa_sdk.models import CheckpointCloseoutExecutionReport


ROOT = Path(__file__).resolve().parents[1]


def _yaml_list(path: Path, section: str) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    values: list[str] = []
    in_section = False
    for line in lines:
        if line == f"{section}:":
            in_section = True
            continue
        if in_section and line and not line.startswith(" "):
            break
        if in_section and line.startswith("  - "):
            values.append(line.removeprefix("  - ").strip())
    return values


def test_checkpoint_closeout_reference_required_payload_matches_emitter() -> None:
    path = (
        ROOT
        / ".agents/skills/aoa-checkpoint-closeout-bridge/references/"
        / "checkpoint-closeout-execution-report-schema.yaml"
    )
    required = set(_yaml_list(path, "required_payload_fields"))

    assert required <= set(CheckpointCloseoutExecutionReport.model_fields)
    assert "stage_results" not in required


def test_quest_harvest_reference_required_payload_matches_current_emitters() -> None:
    path = (
        ROOT
        / ".agents/skills/aoa-quest-harvest/references/"
        / "quest-promotion-receipt-schema.yaml"
    )
    required = set(_yaml_list(path, "required_payload_fields"))

    current_emitted_payload = {
        "promotion_verdict",
        "owner_repo",
        "next_surface",
        "nearest_wrong_target",
        "repeat_shape",
        "bounded_unit_ref",
        "candidate_refs",
        "additional_candidate_refs",
        "accepted_candidate_count",
        "multi_candidate_followup_required",
        "authority_contract",
    }
    assert required <= current_emitted_payload
    assert "repeat_evidence_posture" not in required
