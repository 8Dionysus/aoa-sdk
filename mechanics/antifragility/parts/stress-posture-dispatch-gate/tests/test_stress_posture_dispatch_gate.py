from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[5]
PART_ROOT = Path(__file__).resolve().parents[1]


def load_json(relative_path: str) -> object:
    return json.loads((REPO_ROOT / relative_path).read_text(encoding="utf-8"))


def test_stress_posture_dispatch_examples_are_json_valid() -> None:
    for relative_path in [
        "mechanics/antifragility/parts/stress-posture-dispatch-gate/examples/stress-posture-dispatch-request.example.json",
        "mechanics/antifragility/parts/stress-posture-dispatch-gate/examples/stress-posture-dispatch-decision.example.json",
    ]:
        payload = load_json(relative_path)
        assert isinstance(payload, dict)


def test_stress_posture_dispatch_gate_keeps_narrowing_only_posture() -> None:
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    contract = (PART_ROOT / "CONTRACT.md").read_text(encoding="utf-8")
    control_plane = (PART_ROOT / "docs" / "stress-posture-dispatch-gate.md").read_text(encoding="utf-8")
    dispatch_decision = load_json(
        "mechanics/antifragility/parts/stress-posture-dispatch-gate/examples/stress-posture-dispatch-decision.example.json",
    )

    for fragment in [
        "mechanics/antifragility/parts/stress-posture-dispatch-gate/docs/stress-posture-dispatch-gate.md",
        "mechanics/antifragility/parts/stress-posture-dispatch-gate/examples/stress-posture-dispatch-request.example.json",
        "mechanics/antifragility/parts/stress-posture-dispatch-gate/examples/stress-posture-dispatch-decision.example.json",
    ]:
        assert fragment in readme

    assert "Stress posture may only narrow or block behavior." in control_plane
    assert "It may not:" in control_plane
    assert "They are not SDK-owned active route names" in contract
    assert "alternate-path vocabulary" in contract
    assert dispatch_decision["auto_activated_skill_ids"] == []
