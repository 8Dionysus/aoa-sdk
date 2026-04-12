from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_json(relative_path: str) -> dict[str, object]:
    return json.loads((REPO_ROOT / relative_path).read_text(encoding="utf-8"))


def validate_example(schema_path: str, example_path: str) -> None:
    schema = load_json(schema_path)
    example = load_json(example_path)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(example), key=lambda error: list(error.absolute_path))
    assert errors == []


def test_component_drift_hint_example_validates_against_schema() -> None:
    validate_example(
        "schemas/component_drift_hint_set.schema.json",
        "examples/component_drift_hints.example.json",
    )


def test_component_refresh_followthrough_example_validates_against_schema() -> None:
    validate_example(
        "schemas/component_refresh_followthrough_decision_set.schema.json",
        "examples/component_refresh_followthrough_decision.example.json",
    )


def test_component_refresh_examples_stay_coherent() -> None:
    hint_set = load_json("examples/component_drift_hints.example.json")
    decision_set = load_json("examples/component_refresh_followthrough_decision.example.json")

    hints = hint_set["hints"]  # type: ignore[index]
    decisions = decision_set["decisions"]  # type: ignore[index]
    assert isinstance(hints, list)
    assert isinstance(decisions, list)

    hints_by_ref: dict[str, dict[str, object]] = {}
    for hint in hints:
        assert isinstance(hint, dict)
        hints_by_ref[str(hint["hint_ref"])] = hint
        assert hint["review_required"] is True

    for decision in decisions:
        assert isinstance(decision, dict)
        evidence_refs = decision["evidence_refs"]  # type: ignore[index]
        assert isinstance(evidence_refs, list)
        assert len(evidence_refs) == 1
        hint = hints_by_ref[evidence_refs[0]]
        assert decision["component_ref"] == hint["component_ref"]
        assert decision["owner_repo"] == hint["owner_repo"]

    codex_plane = next(
        decision for decision in decisions if decision["component_ref"] == "component:codex-plane:shared-root"
    )
    assert codex_plane["decision_status"] == "chosen"
    assert codex_plane["route_class"] == "regenerate"

    subagents = next(
        decision
        for decision in decisions
        if decision["component_ref"] == "component:codex-subagents:projection"
    )
    assert subagents["decision_status"] == "deferred"
