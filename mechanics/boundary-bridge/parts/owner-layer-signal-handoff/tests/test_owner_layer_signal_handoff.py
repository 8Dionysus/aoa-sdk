from pathlib import Path
import json

import pytest

from aoa_sdk import AoASDK
from aoa_sdk.models import (
    SurfaceCloseoutHandoff,
    SurfaceDetectionReport,
)


def _surface_item(report: SurfaceDetectionReport, surface_ref: str):
    return next(item for item in report.items if item.surface_ref == surface_ref)


def _install_stats_regrounding_fixture(workspace_root: Path) -> None:
    stats_root = workspace_root / "aoa-stats"
    generated = stats_root / "generated"
    generated.mkdir(parents=True, exist_ok=True)
    (stats_root / "README.md").write_text("# aoa-stats\n", encoding="utf-8")
    (generated / "summary_surface_catalog.min.json").write_text(
        json.dumps(
            {
                "schema_version": "aoa_stats_summary_surface_catalog_v2",
                "schema_ref": "schemas/summary-surface-catalog.schema.json",
                "owner_repo": "aoa-stats",
                "surface_kind": "runtime_surface",
                "authority_ref": "docs/ARCHITECTURE.md",
                "generated_from": {"receipt_input_paths": [], "total_receipts": 1, "latest_observed_at": "2026-04-05T10:00:00Z"},
                "validation_refs": [],
                "surfaces": [
                    {
                        "name": "surface_detection_summary",
                        "surface_ref": "generated/surface_detection_summary.min.json",
                        "schema_ref": "schemas/surface-detection-summary.schema.json",
                        "primary_question": "What enrichment-layer surface-detection signals are accumulating without turning stats into routing authority?",
                        "derivation_rule": "aggregate advisory surface_detection_context payloads",
                        "input_posture": "receipt_backed_live",
                        "owner_truth_inputs": ["aoa-skills core skill application receipts"],
                        "authority_ceiling": "Weaker than owner-local route decisions and weaker than aoa-sdk or aoa-routing dispatch surfaces.",
                        "consumer_risk": "high",
                        "live_state_capable": True,
                    }
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (generated / "source_coverage_summary.min.json").write_text(
        json.dumps(
            {
                "schema_version": "aoa_stats_source_coverage_summary_v1",
                "generated_from": {"receipt_input_paths": [], "total_receipts": 1, "latest_observed_at": "2026-04-05T10:00:00Z"},
                "source_mode": "registry_backed_receipt_feed",
                "input_registry_ref": "config/live_receipt_sources.json",
                "expected_owner_repos": ["aoa-skills", "aoa-evals"],
                "missing_owner_repos": ["aoa-evals"],
                "unexpected_owner_repos": [],
                "active_receipt_total": 1,
                "observed_owner_repo_count": 1,
                "expected_owner_repo_count": 2,
                "owner_repo_counts": {"aoa-skills": 1},
                "event_kind_counts": {"core_skill_application_receipt": 1},
                "owners": [],
                "thin_signal_flags": ["missing_owner_repos"],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def test_surface_detection_and_handoff_models_round_trip(
    workspace_root: Path,
) -> None:
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


def test_surface_detect_keeps_explicit_skill_request_non_executable(
    workspace_root: Path,
) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    report = sdk.surfaces.detect(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="ingress",
        intent_text="inspect the skill layer",
    )
    item = _surface_item(report, "aoa-skills:layer-request")

    assert item.object_kind == "skill"
    assert item.state == "candidate-now"
    assert item.execution.lane == "inspect-expand-use"
    assert item.execution.executable_now is False
    assert item.execution.existing_surface == "aoa-skills.agent_skill_catalog"
    report_payload = report.model_dump()
    assert "immediate_skill_dispatch" not in report_payload
    assert "active_skill_names" not in report_payload
    assert "skill_report_included" not in report_payload


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
    assert item.closeout_capability_candidates == [
        "workflow.operations.checkpoint-closeout"
    ]


def test_surface_detect_repeated_pattern_requires_closeout_or_checkpoint_phase(
    workspace_root: Path,
) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    ingress = sdk.surfaces.detect(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="ingress",
        intent_text="this pattern happens again",
    )
    closeout = sdk.surfaces.detect(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="closeout",
        intent_text="this pattern happens again",
    )

    assert "aoa-techniques.technique_promotion_readiness.min" not in {
        item.surface_ref for item in ingress.items
    }
    technique_item = _surface_item(
        closeout,
        "aoa-techniques.technique_promotion_readiness.min",
    )
    assert technique_item.state == "candidate-later"
    assert technique_item.execution.executable_now is False


def test_surface_detect_supports_in_flight_phase_without_execution_state(
    workspace_root: Path,
) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    session_file = workspace_root / "aoa-sdk" / ".aoa" / "skill-runtime-session.json"

    report = sdk.surfaces.detect(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="in-flight",
        intent_text="inspect the skill layer",
    )

    assert report.phase == "in-flight"
    assert _surface_item(report, "aoa-skills:layer-request").phase_detected == "in-flight"
    assert all(item.execution.executable_now is False for item in report.items)
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
) -> None:
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

    target_refs = [target.target_ref for target in handoff.handoff_targets]

    assert target_refs == [
        "skill.aoa-session-harvest",
        "aoa-playbooks:generated/playbook_registry.min.json",
        "aoa-techniques:generated/technique_promotion_readiness.min.json",
    ]
    assert all(item.execution.executable_now is False for item in handoff.surviving_items)


def test_surface_handoff_does_not_promote_explicit_playbook_request_only(
    workspace_root: Path,
) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    report = sdk.surfaces.detect(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="closeout",
        intent_text="playbook layer inspection only",
    )
    handoff = sdk.surfaces.build_closeout_handoff(
        report,
        session_ref="session:test-surface-explicit-playbook",
    )

    target_refs = [target.target_ref for target in handoff.handoff_targets]

    assert "skill.aoa-session-harvest" in target_refs
    assert "aoa-playbooks:generated/playbook_registry.min.json" not in target_refs


def test_surface_detect_orders_explicit_layer_hints_stably(
    workspace_root: Path,
) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    report = sdk.surfaces.detect(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="ingress",
        intent_text="skill technique playbook eval memo",
    )

    explicit_items = [
        item.surface_ref
        for item in report.items
        if "explicit-request" in item.signals
    ]

    assert explicit_items == [
        "aoa-evals.runtime_candidate_template_index.min",
        "aoa-memo.memory_catalog.min",
        "aoa-playbooks.playbook_registry.min",
        "aoa-skills:layer-request",
        "aoa-techniques.technique_promotion_readiness.min",
    ]


def test_surface_detect_does_not_read_or_write_skill_runtime_session(
    workspace_root: Path,
) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    session_file = workspace_root / "aoa-sdk" / ".aoa" / "skill-runtime-session.json"

    report = sdk.surfaces.detect(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="ingress",
        intent_text="verify recurring handoff proof",
    )

    assert all(item.execution.executable_now is False for item in report.items)
    assert "skill-runtime-session" not in " ".join(report.source_inputs)
    assert not session_file.exists()


def test_surface_handoff_ignores_non_open_checkpoint_notes(
    workspace_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CODEX_THREAD_ID", "thread-owner-layer-handoff")
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    sdk.checkpoints.append(
        repo_root=str(workspace_root / "aoa-sdk"),
        checkpoint_kind="commit",
        intent_text="recurring workflow needs better handoff proof and recall",
    )
    sdk.checkpoints.append(
        repo_root=str(workspace_root / "aoa-sdk"),
        checkpoint_kind="verify_green",
        intent_text="recurring workflow needs better handoff proof and recall",
    )
    sdk.checkpoints.promote(
        repo_root=str(workspace_root / "aoa-sdk"),
        target="harvest-handoff",
    )

    report = sdk.surfaces.detect(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="closeout",
        intent_text="opaque token only",
    )
    handoff = sdk.surfaces.build_closeout_handoff(
        report,
        session_ref="session:test-surface-closed-checkpoint",
    )

    assert handoff.checkpoint_note_ref is not None
    assert handoff.surviving_checkpoint_clusters == []
    assert handoff.checkpoint_harvest_candidates == []
    assert handoff.checkpoint_progression_candidates == []
    assert handoff.checkpoint_upgrade_candidates == []
    assert handoff.checkpoint_progression_axes == []
    assert handoff.stats_refresh_recommended is False


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


def test_surface_detect_raises_stats_regrounding_hints_for_stats_intent(workspace_root: Path) -> None:
    _install_stats_regrounding_fixture(workspace_root)
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    report = sdk.surfaces.detect(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="pre-mutation",
        mutation_surface="code",
        intent_text="use stats surface_detection_summary before mutation",
    )

    assert report.regrounding_required is True
    assert [hint.surface_name for hint in report.regrounding_hints] == [
        "surface_detection_summary"
    ]
    assert report.regrounding_hints[0].decision == "reground_required"
    assert "coverage_missing_owner_repos" in report.regrounding_reason_codes


def test_surface_detect_skips_malformed_stats_for_non_stats_intent(workspace_root: Path) -> None:
    _install_stats_regrounding_fixture(workspace_root)
    coverage_path = (
        workspace_root
        / "aoa-stats"
        / "generated"
        / "source_coverage_summary.min.json"
    )
    coverage_path.write_text("{not-json", encoding="utf-8")
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    report = sdk.surfaces.detect(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="ingress",
        intent_text="plan verify a bounded change",
    )

    assert report.regrounding_hints == []
    assert report.regrounding_required is False


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
                    {
                        "shortlist_id": "explicit-request.source_route.primary",
                        "signal": "explicit-request",
                        "owner_repo": "Dionysus",
                        "object_kind": "source_route",
                        "target_surface": "Dionysus.source_route_anchor",
                        "inspect_surface": "Dionysus.source_route_anchor",
                        "hint_reason": "source-route requests should inspect the Dionysus route anchor first",
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
    object_kinds = {
        hint.object_kind
        for item in report.items
        for hint in item.shortlist_hints
    }
    assert object_kinds >= {
        "runtime_surface",
        "seed",
        "source_route",
        "orientation_surface",
    }


def test_surface_detect_does_not_promote_session_receipts_into_owner_truth(
    workspace_root: Path,
) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    receipt_path = (
        workspace_root
        / "aoa-skills"
        / ".aoa"
        / "live_receipts"
        / "core-skill-applications.jsonl"
    )
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(
        json.dumps(
            {
                "event_kind": "core_skill_application_receipt",
                "session_ref": "session:legacy-runtime-evidence",
                "payload": {
                    "skill_name": "aoa-automation-opportunity-scan",
                    "activation_truth": "activated",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = sdk.surfaces.detect(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="ingress",
        intent_text="inspect the skill layer",
    )
    item = _surface_item(report, "aoa-skills:layer-request")

    assert item.state == "candidate-now"
    assert item.execution.executable_now is False
    assert item.evidence_refs == []
    assert not any("receipt" in source for source in report.source_inputs)
