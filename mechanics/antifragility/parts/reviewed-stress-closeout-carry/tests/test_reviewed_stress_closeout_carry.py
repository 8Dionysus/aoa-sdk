from __future__ import annotations

import json
from pathlib import Path


PART_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[5]


def test_reviewed_stress_closeout_manifest_is_json_valid() -> None:
    payload = json.loads(
        (PART_ROOT / "examples" / "reviewed-stress-closeout-manifest.example.json").read_text(
            encoding="utf-8",
        ),
    )

    assert payload["reviewed"] is True
    assert payload["allow_empty"] is False
    assert "stress_bundle" in payload


def test_reviewed_stress_closeout_carry_stays_below_owner_authority() -> None:
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    package_readme = (REPO_ROOT / "mechanics" / "antifragility" / "README.md").read_text(encoding="utf-8")
    part_readme = (PART_ROOT / "README.md").read_text(encoding="utf-8")
    contract = (PART_ROOT / "CONTRACT.md").read_text(encoding="utf-8")
    doc = (PART_ROOT / "docs" / "reviewed-stress-closeout-carry.md").read_text(encoding="utf-8")

    assert "mechanics/antifragility/README.md" in readme
    assert "mechanics/antifragility/parts/reviewed-stress-closeout-carry/" in package_readme
    assert "docs/reviewed-stress-closeout-carry.md" in part_readme
    assert "examples/reviewed-stress-closeout-manifest.example.json" in part_readme

    assert "auto-trigger runtime repair" in doc
    assert "treat routing hints as source truth" in doc
    assert "They are not SDK-owned active route names" in contract
    assert "alternate-path vocabulary" in contract
