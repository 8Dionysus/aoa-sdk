from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator


PART_ROOT = Path(__file__).resolve().parents[1]


def test_capture_pipeline_helper_example_validates_against_schema() -> None:
    schema = json.loads((PART_ROOT / "schemas/capture-pipeline-helper.schema.json").read_text(encoding="utf-8"))
    example = json.loads((PART_ROOT / "examples/capture-pipeline-helper.example.json").read_text(encoding="utf-8"))

    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(example)


def test_capture_pipeline_helper_doc_names_the_seed_zips_and_boundary() -> None:
    doc = (PART_ROOT / "docs/capture-pipeline-helper.md").read_text(encoding="utf-8")

    assert "aoa-experience-mechanic-seed-v0_1.zip" in doc
    assert "aoa-experience-runtime-capture-seed-v0_2.zip" in doc
    assert "aoa-experience-pilot-integration-seed-v0_3.zip" in doc
    assert "worker services" in doc
    assert "runtime activation" in doc
    assert "pilot record shape" in doc
