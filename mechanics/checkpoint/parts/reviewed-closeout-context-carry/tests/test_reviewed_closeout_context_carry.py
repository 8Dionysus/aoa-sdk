from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator


PART_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[5]


def load_json(relative_path: str) -> dict[str, object]:
    return json.loads((PART_ROOT / relative_path).read_text(encoding="utf-8"))


def validate_example(schema_path: str, example_path: str) -> None:
    schema = load_json(schema_path)
    example = load_json(example_path)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(example), key=lambda error: list(error.absolute_path))
    assert errors == []


def test_checkpoint_lineage_hint_example_validates_against_schema() -> None:
    validate_example(
        "schemas/checkpoint_lineage_hint.schema.json",
        "examples/checkpoint_lineage_hint.example.json",
    )


def test_reviewed_closeout_context_carry_routes_from_readme() -> None:
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    for fragment in [
        "mechanics/checkpoint/parts/reviewed-closeout-context-carry/docs/candidate-lineage-carry.md",
        "mechanics/checkpoint/parts/reviewed-closeout-context-carry/schemas/closeout_owner_followthrough_map.schema.json",
        "mechanics/checkpoint/parts/reviewed-closeout-context-carry/examples/closeout_owner_followthrough_map.example.json",
        "mechanics/checkpoint/parts/reviewed-closeout-context-carry/docs/next-kernel-followthrough-decision.md",
    ]:
        assert fragment in readme


def test_closeout_candidate_lineage_map_example_validates_against_schema() -> None:
    validate_example(
        "schemas/closeout_candidate_lineage_map.schema.json",
        "examples/closeout_candidate_lineage_map.example.json",
    )


def test_closeout_candidate_lineage_map_schema_allows_empty_reviewed_maps() -> None:
    schema = load_json("schemas/closeout_candidate_lineage_map.schema.json")
    Draft202012Validator(schema).validate(
        {
            "schema_version": "aoa_closeout_candidate_lineage_map_v1",
            "session_ref": "session:no-candidates",
            "reviewed": True,
            "candidate_lineage_map": [],
        }
    )


def test_closeout_owner_followthrough_map_example_validates_against_schema() -> None:
    validate_example(
        "schemas/closeout_owner_followthrough_map.schema.json",
        "examples/closeout_owner_followthrough_map.example.json",
    )


def test_closeout_continuity_window_example_validates_against_schema() -> None:
    validate_example(
        "schemas/closeout_continuity_window.schema.json",
        "examples/closeout_continuity_window.example.json",
    )


def test_closeout_followthrough_decision_example_validates_against_schema() -> None:
    validate_example(
        "schemas/closeout_followthrough_decision.schema.json",
        "examples/closeout_followthrough_decision.example.json",
    )


def test_sdk_lineage_examples_stay_on_first_wave_chain() -> None:
    checkpoint = load_json("examples/checkpoint_lineage_hint.example.json")
    closeout = load_json("examples/closeout_candidate_lineage_map.example.json")
    followthrough = load_json("examples/closeout_owner_followthrough_map.example.json")
    closeout_hint = closeout["candidate_lineage_map"][0]  # type: ignore[index]
    followthrough_hint = followthrough["owner_followthrough_map"][0]  # type: ignore[index]

    assert checkpoint["cluster_ref"] == "cluster:growth:aoa-sdk-checkpoint-auto-capture-verify-green"
    assert isinstance(closeout_hint, dict)
    assert isinstance(followthrough_hint, dict)
    assert closeout_hint["cluster_ref"] == checkpoint["cluster_ref"]
    assert followthrough_hint["cluster_ref"] == checkpoint["cluster_ref"]
    assert checkpoint["owner_hypothesis"] == "aoa-skills"
    assert "candidate_ref" not in checkpoint
    assert "seed_ref" not in checkpoint
    assert "object_ref" not in checkpoint
    assert "candidate_ref" not in followthrough_hint
    assert "seed_ref" not in followthrough_hint
    assert "object_ref" not in followthrough_hint
    assert followthrough_hint["recommended_owner_status_surface"] == "aoa-skills:reviewed_owner_landing_bundle"
    assert followthrough_hint["requested_next_decision_class"] == "land_direct"


def test_closeout_followthrough_decision_example_stays_reviewed_only() -> None:
    decision = load_json("examples/closeout_followthrough_decision.example.json")

    assert decision["cluster_ref"] == "cluster:route:aoa-playbooks-playbook-registry-min"
    assert decision["recommended_next_skill"] == "aoa-automation-opportunity-scan"
    assert "candidate_ref" not in decision
    also_considered = decision["also_considered"]  # type: ignore[index]
    assert isinstance(also_considered, list)
    assert decision["recommended_next_skill"] not in also_considered
    assert decision["approval_posture"] == "review_required"


def test_closeout_continuity_window_example_stays_hint_only() -> None:
    continuity = load_json("examples/closeout_continuity_window.example.json")

    assert continuity["continuity_ref_hint"] == "continuity:aoa-playbooks:self-agency-continuity-cycle"
    assert continuity["continuity_status_hint"] == "reanchor_needed"
    assert continuity["reanchor_need"] is True
    assert "continuity_ref" not in continuity
    assert "revision_window_ref" not in continuity
    assert "reanchor_ref" not in continuity
