from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]


def test_wave1_helper_example_validates_against_schema() -> None:
    schema = json.loads((ROOT / "schemas/agon-experience-capture-pipeline-helper.schema.json").read_text(encoding="utf-8"))
    example = json.loads((ROOT / "examples/agon_experience_capture_pipeline_helper.example.json").read_text(encoding="utf-8"))

    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(example)


def test_wave1_helper_doc_names_the_seed_zips_and_boundary() -> None:
    doc = (ROOT / "docs/AGON_WAVE1_EXPERIENCE_CAPTURE_PIPELINE.md").read_text(encoding="utf-8")

    assert "aoa-experience-mechanic-seed-v0_1.zip" in doc
    assert "aoa-experience-runtime-capture-seed-v0_2.zip" in doc
    assert "aoa-experience-pilot-integration-seed-v0_3.zip" in doc
    assert "worker services" in doc
    assert "runtime activation" in doc
    assert "pilot record shape" in doc
