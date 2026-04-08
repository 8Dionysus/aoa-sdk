from pathlib import Path
import json

import pytest

from aoa_sdk import AoASDK
from aoa_sdk.models import (
    SurfaceCloseoutHandoff,
    SurfaceDetectionReport,
    SurfaceOpportunityExecutionHint,
    SurfaceOpportunityItem,
)


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


def test_surface_detect_consumes_owner_layer_shortlist_without_changing_truth(
    workspace_root: Path,
) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    shortlist_path = workspace_root / "aoa-routing" / "generated" / "owner_layer_shortlist.min.json"
    shortlist_path.parent.mkdir(parents=True, exist_ok=True)
    shortlist_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "hints": [
                    {
                        "shortlist_id": "scenario.playbooks.primary",
                        "signal": "scenario-recurring",
                        "owner_repo": "aoa-playbooks",
                        "object_kind": "playbook",
                        "target_surface": "aoa-playbooks.playbook_registry.min",
                        "inspect_surface": "aoa-playbooks.playbook_registry.min",
                        "hint_reason": "recurring route should inspect playbook registry first",
                        "confidence": "high",
                        "ambiguity": "clear",
                    },
                    {
                        "shortlist_id": "scenario.techniques.adjacent",
                        "signal": "scenario-recurring",
                        "owner_repo": "aoa-techniques",
                        "object_kind": "technique",
                        "target_surface": "aoa-techniques.technique_promotion_readiness.min",
                        "inspect_surface": "aoa-techniques.technique_promotion_readiness.min",
                        "hint_reason": "recurring route may still be repeated bounded discipline",
                        "confidence": "medium",
                        "ambiguity": "ambiguous",
                    },
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    report = sdk.surfaces.detect(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="ingress",
        intent_text="this recurring workflow needs a better handoff sequence",
    )
    item = _surface_item(report, "aoa-playbooks.playbook_registry.min")

    assert report.shortlist_included is True
    assert item.state == "candidate-later"
    assert item.execution.executable_now is False
    assert {hint.owner_repo for hint in item.shortlist_hints} == {
        "aoa-playbooks",
        "aoa-techniques",
    }
    assert item.owner_layer_ambiguity_note is not None
    assert {
        ref.ref for ref in item.family_entry_refs if ref.role == "family-entry"
    } >= {
        "aoa-playbooks.playbook_registry.min",
        "aoa-techniques.technique_promotion_readiness.min",
    }


def test_surface_detect_accepts_runtime_seed_and_profile_shortlist_hints(
    workspace_root: Path,
) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    shortlist_path = workspace_root / "aoa-routing" / "generated" / "owner_layer_shortlist.min.json"
    shortlist_path.parent.mkdir(parents=True, exist_ok=True)
    shortlist_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "hints": [
                    {
                        "shortlist_id": "explicit-request.sdk.primary",
                        "signal": "explicit-request",
                        "owner_repo": "aoa-sdk",
                        "object_kind": "runtime_surface",
                        "target_surface": "aoa-sdk.workspace_control_plane.min",
                        "inspect_surface": "aoa-sdk.workspace_control_plane.min",
                        "hint_reason": "control plane route should stay capsule-first",
                        "confidence": "high",
                        "ambiguity": "clear",
                    },
                    {
                        "shortlist_id": "explicit-request.stats.primary",
                        "signal": "explicit-request",
                        "owner_repo": "aoa-stats",
                        "object_kind": "runtime_surface",
                        "target_surface": "aoa-stats.summary_surface_catalog.min",
                        "inspect_surface": "aoa-stats.summary_surface_catalog.min",
                        "hint_reason": "stats route should stay owner-owned",
                        "confidence": "high",
                        "ambiguity": "clear",
                    },
                    {
                        "shortlist_id": "explicit-request.seed.primary",
                        "signal": "explicit-request",
                        "owner_repo": "Dionysus",
                        "object_kind": "seed",
                        "target_surface": "Dionysus.seed_route_map.min",
                        "inspect_surface": "Dionysus.seed_route_map.min",
                        "hint_reason": "seed route should stay capsule-first",
                        "confidence": "high",
                        "ambiguity": "clear",
                    },
                    {
                        "shortlist_id": "explicit-request.runtime.primary",
                        "signal": "explicit-request",
                        "owner_repo": "abyss-stack",
                        "object_kind": "runtime_surface",
                        "target_surface": "abyss-stack.diagnostic_surface_catalog.min",
                        "inspect_surface": "abyss-stack.diagnostic_surface_catalog.min",
                        "hint_reason": "runtime route should stay source-owned",
                        "confidence": "high",
                        "ambiguity": "clear",
                    },
                    {
                        "shortlist_id": "explicit-request.profile.primary",
                        "signal": "explicit-request",
                        "owner_repo": "8Dionysus",
                        "object_kind": "orientation_surface",
                        "target_surface": "8Dionysus.public_route_map.min",
                        "inspect_surface": "8Dionysus.public_route_map.min",
                        "hint_reason": "profile route should stay orientation-only",
                        "confidence": "high",
                        "ambiguity": "clear",
                    },
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    report = sdk.surfaces.detect(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="ingress",
        intent_text="skill control plane seed runtime profile route drift",
    )

    assert report.shortlist_included is True
    owner_repos = {
        hint.owner_repo
        for item in report.items
        for hint in item.shortlist_hints
    }
    assert owner_repos >= {
        "aoa-sdk",
        "aoa-stats",
        "Dionysus",
        "abyss-stack",
        "8Dionysus",
    }


def test_surface_detect_enriches_skill_items_from_core_receipt_context(
    workspace_root: Path,
) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    core_skill_log_path = workspace_root / "aoa-skills" / ".aoa" / "live_receipts" / "core-skill-applications.jsonl"
    core_skill_log_path.parent.mkdir(parents=True, exist_ok=True)
    core_skill_log_path.write_text(
        json.dumps(
            {
                "event_kind": "core_skill_application_receipt",
                "event_id": "evt-core-surface-0001",
                "observed_at": "2026-04-06T20:25:00Z",
                "run_ref": "run-core-surface-001",
                "session_ref": "session:test-surface-context",
                "actor_ref": "aoa-skills:automation-opportunity-scan",
                "object_ref": {
                    "repo": "aoa-skills",
                    "kind": "skill",
                    "id": "aoa-automation-opportunity-scan",
                    "version": "main",
                },
                "evidence_refs": [
                    {"kind": "receipt", "ref": "repo:aoa-skills/tmp/AUTOMATION_CANDIDATE_RECEIPT.json"}
                ],
                "payload": {
                    "kernel_id": "project-core-session-growth-v1",
                    "skill_name": "aoa-automation-opportunity-scan",
                    "application_stage": "finish",
                    "detail_event_kind": "automation_candidate_receipt",
                    "detail_receipt_ref": "repo:aoa-skills/tmp/AUTOMATION_CANDIDATE_RECEIPT.json",
                    "surface_detection_context": {
                        "activation_truth": "activated",
                        "adjacent_owner_repos": ["aoa-playbooks", "aoa-techniques"],
                        "owner_layer_ambiguity": True,
                        "surface_detection_report_ref": "repo:aoa-sdk/.aoa/surface-detection/aoa-sdk.closeout.latest.json",
                        "surface_closeout_handoff_ref": "repo:aoa-sdk/.aoa/surface-detection/aoa-sdk.closeout-handoff.latest.json",
                        "family_entry_refs": [
                            "aoa-playbooks.playbook_registry.min",
                            "aoa-techniques.technique_promotion_readiness.min"
                        ]
                    }
                }
            }
        )
        + "\n",
        encoding="utf-8",
    )

    from aoa_sdk.surfaces import registry as surfaces_registry

    item = SurfaceOpportunityItem(
        surface_ref="aoa-skills:aoa-automation-opportunity-scan",
        display_name="AoA Automation Opportunity Scan",
        object_kind="skill",
        owner_repo="aoa-skills",
        state="manual-equivalent",
        phase_detected="closeout",
        reason="router-only closeout helper",
        signals=["risk-gate", "closeout-chain"],
        confidence="medium",
        execution=SurfaceOpportunityExecutionHint(
            lane="manual-fallback",
            executable_now=False,
            requires_confirmation=True,
            existing_command="aoa skills detect",
            existing_surface=None,
            manual_fallback_allowed=True,
            manual_fallback_note="keep truth visible",
            host_availability_status="router-only",
        ),
        related_skill_names=[],
        closeout_family_candidates=["aoa-session-donor-harvest"],
        promotion_hint=None,
    )
    contexts = surfaces_registry._load_core_skill_receipt_contexts(sdk.workspace)
    item = surfaces_registry._enrich_item_with_skill_receipt_context(
        item,
        skill_receipt_contexts=contexts,
    )

    assert item.state == "manual-equivalent"
    assert any(ref.role == "runtime-receipt" for ref in item.evidence_refs)
    assert any(ref.role == "skill-report" for ref in item.evidence_refs)
    assert any(ref.role == "closeout-handoff" for ref in item.evidence_refs)
    assert {
        ref.ref for ref in item.family_entry_refs if ref.role == "family-entry"
    } >= {
        "aoa-playbooks.playbook_registry.min",
        "aoa-techniques.technique_promotion_readiness.min",
    }
    assert item.owner_layer_ambiguity_note is not None
