from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
WAVE2_PREFIXES = (
    "certification_helper_",
    "sdk_deployment_",
    "sdk_rollback_",
    "sdk_watchtower_",
)


def wave2_pairs() -> list[tuple[Path, Path]]:
    pairs: list[tuple[Path, Path]] = []
    missing_pairs: list[str] = []
    for example_path in sorted((ROOT / "examples").glob("*.example.json")):
        stem = example_path.name.removesuffix(".example.json")
        if stem.endswith("_v1"):
            continue
        if not stem.startswith(WAVE2_PREFIXES):
            continue
        schema_path = ROOT / "schemas" / f"{stem}_v1.json"
        if not schema_path.exists():
            missing_pairs.append(f"{example_path.relative_to(ROOT)} -> {schema_path.relative_to(ROOT)}")
            continue
        pairs.append((schema_path, example_path))
    assert not missing_pairs, "missing wave2 schema pair(s): " + ", ".join(missing_pairs)
    return pairs


def test_experience_wave2_examples_match_schemas() -> None:
    pairs = wave2_pairs()
    assert pairs
    for schema_path, example_path in pairs:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        example = json.loads(example_path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        errors = sorted(Draft202012Validator(schema).iter_errors(example), key=lambda error: list(error.path))
        assert not errors, f"{example_path.name}: {errors[0].message if errors else ''}"
