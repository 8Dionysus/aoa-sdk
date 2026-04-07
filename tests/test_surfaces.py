from pathlib import Path

import pytest

from aoa_sdk import AoASDK
from aoa_sdk.models import SurfaceCloseoutHandoff, SurfaceDetectionReport


def _surface_item(report: SurfaceDetectionReport, surface_ref: str):
    return next(item for item in report.items if item.surface_ref == surface_ref)


def test_surface_detection_and_handoff_models_round_trip(
    workspace_root: Path,
    install_host_skills,
) -> None:
    install_host_skills(workspace_root, ["aoa-change-protocol"])
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    report = sdk.surfaces.detect(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="ingress",
        intent_text="plan verify a bounded change",
    )
    handoff = sdk.surfaces.build_closeout_handoff(
        report,
        session_ref="session:test-surface-round-trip",
    )

    round_tripped_report = SurfaceDetectionReport.model_validate_json(report.model_dump_json())
    round_tripped_handoff = SurfaceCloseoutHandoff.model_validate_json(handoff.model_dump_json())

    assert round_tripped_report.repo_root == str(workspace_root / "aoa-sdk")
    assert round_tripped_report.phase == "ingress"
    assert round_tripped_handoff.session_ref == "session:test-surface-round-trip"
    assert round_tripped_handoff.surface_detection_report_ref == "in-memory:surface-detection-report"


def test_surface_detect_maps_activate_now_to_activated_skill_item(
    workspace_root: Path,
    install_host_skills,
) -> None:
    install_host_skills(workspace_root, ["aoa-change-protocol"])
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    report = sdk.surfaces.detect(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="ingress",
        intent_text="plan verify a bounded change",
    )
    item = _surface_item(report, "aoa-skills:aoa-change-protocol")

    assert report.immediate_skill_dispatch == ["aoa-change-protocol"]
    assert item.object_kind == "skill"
    assert item.state == "activated"
    assert item.execution.lane == "skill-dispatch"
    assert item.execution.executable_now is True


def test_surface_detect_maps_router_only_skill_to_manual_equivalent(
    workspace_root: Path,
    install_host_skills,
) -> None:
    install_host_skills(workspace_root, ["aoa-approval-gate-check"])
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    report = sdk.surfaces.detect(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="ingress",
        intent_text="plan verify a bounded change",
    )
    item = _surface_item(report, "aoa-skills:aoa-change-protocol")

    assert report.immediate_skill_dispatch == []
    assert item.state == "manual-equivalent"
    assert item.execution.lane == "manual-fallback"
    assert item.execution.executable_now is False
    assert item.execution.manual_fallback_allowed is True


def test_surface_detect_maps_eval_and_memo_candidates_from_tokens(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    report = sdk.surfaces.detect(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="ingress",
        intent_text="verify prior provenance and recall the earlier proof",
    )

    eval_item = _surface_item(report, "aoa-evals.runtime_candidate_template_index.min")
    memo_item = _surface_item(report, "aoa-memo.memory_catalog.min")

    assert eval_item.object_kind == "eval"
    assert eval_item.state == "candidate-now"
    assert eval_item.execution.lane == "inspect-expand-use"
    assert memo_item.object_kind == "memo"
    assert memo_item.state == "candidate-now"
    assert memo_item.execution.lane == "inspect-expand-use"


def test_surface_detect_maps_playbook_candidate_from_recurring_tokens(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    report = sdk.surfaces.detect(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="ingress",
        intent_text="this recurring workflow needs a better handoff sequence",
    )
    item = _surface_item(report, "aoa-playbooks.playbook_registry.min")

    assert item.object_kind == "playbook"
    assert item.state == "candidate-later"
    assert item.execution.lane == "closeout-harvest"
    assert "aoa-automation-opportunity-scan" in item.closeout_family_candidates


def test_surface_detect_repeated_pattern_requires_runtime_or_closeout_signal(
    workspace_root: Path,
    install_host_skills,
    tmp_path: Path,
) -> None:
    install_host_skills(workspace_root, ["aoa-change-protocol"])
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    session_file = tmp_path / ".aoa" / "skill-runtime-session.json"

    ingress_without_session = sdk.surfaces.detect(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="ingress",
        intent_text="this pattern happens again",
        session_file=str(session_file),
    )

    sdk.skills.activate("aoa-change-protocol", session_file=str(session_file))
    ingress_with_session = sdk.surfaces.detect(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="ingress",
        intent_text="this pattern happens again",
        session_file=str(session_file),
    )

    assert "aoa-techniques.technique_promotion_readiness.min" not in {
        item.surface_ref for item in ingress_without_session.items
    }
    technique_item = _surface_item(
        ingress_with_session,
        "aoa-techniques.technique_promotion_readiness.min",
    )
    assert ingress_with_session.active_skill_names == ["aoa-change-protocol"]
    assert technique_item.state == "candidate-later"
    assert technique_item.execution.executable_now is False


def test_surface_detect_supports_in_flight_phase_without_writing_skill_session(
    workspace_root: Path,
    install_host_skills,
) -> None:
    install_host_skills(workspace_root, ["aoa-change-protocol"])
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    session_file = workspace_root / "aoa-sdk" / ".aoa" / "skill-runtime-session.json"

    report = sdk.surfaces.detect(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="in-flight",
        intent_text="plan verify a bounded change",
    )

    assert report.phase == "in-flight"
    assert report.immediate_skill_dispatch == ["aoa-change-protocol"]
    assert _surface_item(report, "aoa-skills:aoa-change-protocol").phase_detected == "in-flight"
    assert not session_file.exists()


def test_surface_handoff_requires_reviewed(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    report = sdk.surfaces.detect(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="ingress",
        intent_text="verify the route",
    )

    with pytest.raises(ValueError, match="reviewed=True"):
        sdk.surfaces.build_closeout_handoff(
            report,
            session_ref="session:test-surface-review-gate",
            reviewed=False,
        )


def test_surface_handoff_targets_are_deterministic(
    workspace_root: Path,
    install_host_skills,
) -> None:
    install_host_skills(workspace_root, ["aoa-approval-gate-check"])
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    report = sdk.surfaces.detect(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="pre-mutation",
        intent_text="verify recurring pattern workflow",
        mutation_surface="runtime",
    )
    handoff = sdk.surfaces.build_closeout_handoff(
        report,
        session_ref="session:test-surface-handoff-targets",
    )

    target_names = [target.skill_name for target in handoff.handoff_targets]

    assert "aoa-session-donor-harvest" in target_names
    assert "aoa-automation-opportunity-scan" in target_names
    assert "aoa-session-self-diagnose" in target_names
    assert "aoa-quest-harvest" in target_names
    assert all(item.state != "activated" for item in handoff.surviving_items)
    assert "aoa-session-route-forks" not in target_names


def test_surface_detect_does_not_write_skill_runtime_session(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    session_file = workspace_root / "aoa-sdk" / ".aoa" / "skill-runtime-session.json"

    report = sdk.surfaces.detect(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="ingress",
        intent_text="verify recurring handoff proof",
    )

    assert report.skill_report_included is True
    assert not session_file.exists()
