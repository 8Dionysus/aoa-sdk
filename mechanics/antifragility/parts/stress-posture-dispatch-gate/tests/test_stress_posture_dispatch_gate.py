from __future__ import annotations

import json
from pathlib import Path

from aoa_sdk import AoASDK
from aoa_sdk.a2a.rebase import EvidenceRef, QuestPassport, StressSignal, SummonIntent


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
    assert dispatch_decision["skill_activation_claimed"] is False
    assert dispatch_decision["runtime_enforcement_claimed"] is False


def test_stress_posture_dispatch_gate_narrows_task_dispatch_without_skill_runtime(
    workspace_root: Path,
) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    request = load_json(
        "mechanics/antifragility/parts/stress-posture-dispatch-gate/examples/stress-posture-dispatch-request.example.json",
    )
    expected = load_json(
        "mechanics/antifragility/parts/stress-posture-dispatch-gate/examples/stress-posture-dispatch-decision.example.json",
    )

    passport = QuestPassport(**request["passport"])
    intent = SummonIntent(**request["intent"])
    signals = [
        StressSignal(
            source_family=item["source_family"],
            posture=item["posture"],
            severity=item["severity"],
            evidence_refs=[EvidenceRef(**ref) for ref in item["evidence_refs"]],
            reentry_conditions=item["reentry_conditions"],
        )
        for item in request["stress_signals"]
    ]

    baseline = sdk.a2a.assess_summon(passport, intent)
    bundle = sdk.a2a.merge_stress_signals(signals)
    stressed = sdk.a2a.assess_summon(passport, intent, stress_bundle=bundle)

    assert baseline.allowed is True
    assert baseline.blocked_actions == []
    assert bundle.selected_posture == expected["stress_bundle"]["selected_posture"]
    assert bundle.blocked_actions == expected["stress_bundle"]["blocked_actions"]
    assert [ref.ref for ref in bundle.evidence_refs] == expected["stress_bundle"]["evidence_refs"]
    assert stressed.allowed is expected["task_dispatch"]["allowed"]
    assert stressed.lane == expected["task_dispatch"]["lane"]
    assert stressed.requested_posture == expected["task_dispatch"]["requested_posture"]
    assert stressed.reason_codes == expected["task_dispatch"]["reason_codes"]
    assert stressed.blocked_actions == expected["task_dispatch"]["blocked_actions"]
    assert not hasattr(sdk.skills, "dispatch")
