from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_json(relative_path: str) -> object:
    return json.loads((REPO_ROOT / relative_path).read_text(encoding="utf-8"))


def test_antifragility_fixtures_are_json_valid() -> None:
    for relative_path in [
        "tests/fixtures/antifragility/stress_dispatch_input.example.json",
        "tests/fixtures/antifragility/stress_dispatch_result.example.json",
        "tests/fixtures/antifragility/stress_closeout_manifest.example.json",
    ]:
        payload = load_json(relative_path)
        assert isinstance(payload, dict)


def test_antifragility_docs_and_fixtures_keep_narrowing_only_posture() -> None:
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    control_plane = (REPO_ROOT / "docs" / "antifragility-control-plane.md").read_text(encoding="utf-8")
    closeout = (REPO_ROOT / "docs" / "antifragility-closeout-seam.md").read_text(encoding="utf-8")
    dispatch_result = load_json("tests/fixtures/antifragility/stress_dispatch_result.example.json")

    for fragment in [
        "docs/antifragility-control-plane.md",
        "docs/antifragility-closeout-seam.md",
        "tests/fixtures/antifragility/stress_dispatch_input.example.json",
        "tests/fixtures/antifragility/stress_dispatch_result.example.json",
        "tests/fixtures/antifragility/stress_closeout_manifest.example.json",
    ]:
        assert fragment in readme

    assert "Stress posture may only narrow or block behavior." in control_plane
    assert "It may not:" in control_plane
    assert "auto-trigger runtime repair" in closeout
    assert dispatch_result["auto_activated_skill_ids"] == []
