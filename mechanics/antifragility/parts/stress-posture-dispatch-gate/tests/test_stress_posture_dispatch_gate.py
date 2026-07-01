from __future__ import annotations

import json
from pathlib import Path

from aoa_sdk import AoASDK


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
    package_readme = (REPO_ROOT / "mechanics" / "antifragility" / "README.md").read_text(encoding="utf-8")
    part_readme = (PART_ROOT / "README.md").read_text(encoding="utf-8")
    contract = (PART_ROOT / "CONTRACT.md").read_text(encoding="utf-8")
    control_plane = (PART_ROOT / "docs" / "stress-posture-dispatch-gate.md").read_text(encoding="utf-8")
    dispatch_decision = load_json(
        "mechanics/antifragility/parts/stress-posture-dispatch-gate/examples/stress-posture-dispatch-decision.example.json",
    )

    assert "mechanics/antifragility/README.md" in readme
    assert "mechanics/antifragility/parts/stress-posture-dispatch-gate/" in package_readme
    assert "docs/stress-posture-dispatch-gate.md" in part_readme
    assert "examples/stress-posture-dispatch-request.example.json" in part_readme
    assert "examples/stress-posture-dispatch-decision.example.json" in part_readme

    assert "Stress posture may only narrow or block behavior." in control_plane
    assert "It may not:" in control_plane
    assert "They are not SDK-owned active route names" in contract
    assert "alternate-path vocabulary" in contract
    assert dispatch_decision["auto_activated_skill_ids"] == []


def test_stress_posture_dispatch_gate_blocks_live_auto_activation(
    workspace_root: Path,
    install_host_skills,
) -> None:
    install_host_skills(workspace_root, ["aoa-change-protocol"])
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    request = load_json(
        "mechanics/antifragility/parts/stress-posture-dispatch-gate/examples/stress-posture-dispatch-request.example.json",
    )
    session_file = workspace_root / "aoa-sdk" / ".aoa" / "stress-posture-session.json"

    report = sdk.skills.dispatch(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="pre-mutation",
        intent_text="plan verify a bounded change",
        mutation_surface="repo-config",
        session_file=str(session_file),
        stress_context=request["stress_context"],
    )

    assert report.activate_now == []
    must_confirm_names = [item.skill_name for item in report.must_confirm]
    assert "aoa-change-protocol" in must_confirm_names
    assert {"aoa-approval-gate-check", "aoa-dry-run-first"}.issubset(must_confirm_names)
    assert "stress_posture_requires_human_review" in report.blocked_actions
    assert "stress posture active: human_review_first" in report.reasoning
    assert not session_file.exists()
