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


def test_checkpoint_lineage_hint_example_validates_against_schema() -> None:
    validate_example(
        "schemas/checkpoint_lineage_hint.schema.json",
        "examples/checkpoint_lineage_hint.example.json",
    )


def test_closeout_candidate_lineage_map_example_validates_against_schema() -> None:
    validate_example(
        "schemas/closeout_candidate_lineage_map.schema.json",
        "examples/closeout_candidate_lineage_map.example.json",
    )


def test_sdk_lineage_examples_stay_on_first_wave_chain() -> None:
    checkpoint = load_json("examples/checkpoint_lineage_hint.example.json")
    closeout = load_json("examples/closeout_candidate_lineage_map.example.json")
    closeout_hint = closeout["candidate_lineage_map"][0]  # type: ignore[index]

    assert checkpoint["cluster_ref"] == "cluster:growth:aoa-sdk-checkpoint-auto-capture-verify-green"
    assert isinstance(closeout_hint, dict)
    assert closeout_hint["cluster_ref"] == checkpoint["cluster_ref"]
    assert checkpoint["owner_hypothesis"] == "aoa-skills"
    assert "candidate_ref" not in checkpoint
    assert "seed_ref" not in checkpoint
    assert "object_ref" not in checkpoint
