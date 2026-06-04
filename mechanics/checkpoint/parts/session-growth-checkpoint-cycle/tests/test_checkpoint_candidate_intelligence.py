from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from aoa_sdk import AoASDK
from aoa_sdk.cli.main import app


def _signature_by_action(report, action: str):  # type: ignore[no-untyped-def]
    return next(signature for signature in report.action_signatures if signature.action == action)


def _write_legacy_checkpoint_entry(note_dir: Path, *, observed_at: str) -> None:
    note_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "session_ref": "session:legacy-candidate-intelligence",
        "runtime_session_id": "runtime-legacy-candidate-intelligence",
        "runtime_session_created_at": "2026-04-10T13:55:00Z",
        "repo_root": str(note_dir.parents[3].resolve()),
        "repo_label": "aoa-sdk",
        "history_entry": {
            "checkpoint_kind": "manual",
            "observed_at": observed_at,
            "report_ref": str(note_dir / "legacy-report.json"),
            "intent_text": "legacy recurring workflow candidate",
            "checkpoint_should_capture": True,
            "blocked_by": [],
            "candidate_clusters": [
                {
                    "candidate_id": "candidate:route:aoa-playbooks-playbook-registry-min",
                    "candidate_kind": "route",
                    "owner_hint": "aoa-playbooks",
                    "display_name": "Recurring route candidate",
                    "source_surface_ref": "aoa-playbooks.playbook_registry.min",
                    "evidence_refs": [
                        "aoa-playbooks.playbook_registry.min",
                        "aoa-playbooks:legacy-review",
                    ],
                    "confidence": "medium",
                    "session_end_targets": ["harvest", "progression", "upgrade"],
                    "progression_axis_signals": [],
                    "next_owner_moves": [
                        "carry the candidate through reviewed session closeout before moving candidates or stats"
                    ],
                }
            ],
            "manual_review_requested": False,
        },
    }
    with (note_dir / "checkpoint-note.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=True) + "\n")


def test_checkpoint_surface_detection_emits_action_facets_and_signature_refs(
    workspace_root: Path,
) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    report = sdk.surfaces.detect(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="checkpoint",
        checkpoint_kind="commit",
        intent_text="recurring workflow needs better handoff proof and recall",
    )

    assert report.action_events
    assert report.action_signatures
    assert {signature.wrapper_family_hint for signature in report.action_signatures} >= {
        "eval",
        "memo",
        "owner_local",
        "playbook",
        "technique",
    }
    assert {
        event.facets.family
        for event in report.action_events
    } >= {
        "command_execution",
        "context_memory",
        "owner_routing",
        "verification",
    }
    assert all(event.facets.phase == "checkpoint" for event in report.action_events)
    assert all(event.action_signature_ref for event in report.action_events)
    assert all(cluster.action_signature_refs for cluster in report.candidate_clusters)


def test_checkpoint_candidate_intelligence_counts_repetition_after_deduping_events(
    workspace_root: Path,
) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    intent_text = "recurring workflow needs better handoff proof and recall"

    first = sdk.checkpoints.append(
        repo_root=str(workspace_root / "aoa-sdk"),
        checkpoint_kind="manual",
        intent_text=intent_text,
    )
    assert first.repetition_clusters
    assert {
        cluster.wrapper_readiness.draftability
        for cluster in first.repetition_clusters
    } == {"observe"}
    assert all(cluster.repeat_count == 1 for cluster in first.repetition_clusters)
    assert all(
        "no_single_event_promotion" in cluster.wrapper_readiness.stop_lines
        for cluster in first.repetition_clusters
    )

    second = sdk.checkpoints.append(
        repo_root=str(workspace_root / "aoa-sdk"),
        checkpoint_kind="manual",
        intent_text=intent_text,
    )

    assert all(cluster.repeat_count == 2 for cluster in second.repetition_clusters)
    assert {
        cluster.wrapper_readiness.draftability
        for cluster in second.repetition_clusters
    } == {"reviewable"}
    assert all(
        cluster.wrapper_readiness.draftability != "draftable"
        for cluster in second.repetition_clusters
    )
    assert len(second.action_events) < sum(
        len(entry.action_events) for entry in second.checkpoint_history
    )


def test_checkpoint_candidate_intelligence_backfills_legacy_candidate_clusters(
    workspace_root: Path,
) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    note_dir = workspace_root / "aoa-sdk" / ".aoa" / "session-growth" / "current" / "aoa-sdk"
    _write_legacy_checkpoint_entry(note_dir, observed_at="2026-04-10T14:00:00Z")
    _write_legacy_checkpoint_entry(note_dir, observed_at="2026-04-10T14:01:00Z")

    report = sdk.checkpoints.candidate_intelligence(
        repo_root=str(workspace_root / "aoa-sdk"),
        sample_limit=1,
    )

    signature = _signature_by_action(report, "repeat_manual_workflow")
    cluster = next(item for item in report.repetition_clusters if item.signature_id == signature.signature_id)
    assert signature.wrapper_family_hint == "playbook"
    assert signature.event_types == ["repeated_manual_workflow_candidate"]
    assert "route_signal:legacy_backfill" in signature.route_signals
    assert "single_event_cannot_promote" not in signature.negative_evidence
    assert cluster.repeat_count == 2
    assert cluster.wrapper_readiness.draftability == "reviewable"
    assert report.sample_audit[0].verdict == "unreviewed"


def test_checkpoint_candidate_intelligence_classifies_wrapper_lanes_and_gap_pressure(
    workspace_root: Path,
) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    eval_report = sdk.surfaces.detect(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="checkpoint",
        checkpoint_kind="manual",
        intent_text="verify regression proof invariant quality",
    )
    memo_report = sdk.surfaces.detect(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="checkpoint",
        checkpoint_kind="manual",
        intent_text="memory recall prior provenance",
    )
    owner_report = sdk.surfaces.detect(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="checkpoint",
        checkpoint_kind="manual",
        intent_text="agent role owner boundary",
    )
    risk_note = sdk.checkpoints.append(
        repo_root=str(workspace_root / "aoa-sdk"),
        checkpoint_kind="manual",
        intent_text="risk gate hidden automation requires confirmation",
    )
    gap_report = sdk.surfaces.detect(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="checkpoint",
        checkpoint_kind="manual",
        intent_text="нет существующего aoa для этой операции",
    )

    assert _signature_by_action(eval_report, "define_bounded_verification").wrapper_family_hint == "eval"
    assert _signature_by_action(memo_report, "retrieve_prior_context").wrapper_family_hint == "memo"
    assert _signature_by_action(owner_report, "clarify_owner_or_agent_role").wrapper_family_hint == "owner_local"
    assert risk_note.repetition_clusters[0].wrapper_readiness.draftability == "blocked"
    assert "automation_risk_requires_review" in risk_note.repetition_clusters[0].wrapper_readiness.blockers
    assert "risk_signal_requires_review" in risk_note.action_signatures[0].negative_evidence
    assert gap_report.action_signatures[0].family == "wrapper_gap"
    assert gap_report.action_signatures[0].wrapper_family_hint == "unknown"
    assert "wrapper_family_unknown" in gap_report.action_signatures[0].negative_evidence
    assert gap_report.wrapper_gap_candidates[0].nearest_existing_wrapper is None
    assert gap_report.wrapper_gap_candidates[0].draftability == "reviewable"


def test_checkpoint_candidate_intelligence_cli_writes_generated_navigation_index(
    workspace_root: Path,
) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    intent_text = "recurring workflow needs better handoff proof and recall"
    sdk.checkpoints.append(
        repo_root=str(workspace_root / "aoa-sdk"),
        checkpoint_kind="manual",
        intent_text=intent_text,
    )
    sdk.checkpoints.append(
        repo_root=str(workspace_root / "aoa-sdk"),
        checkpoint_kind="manual",
        intent_text=intent_text,
    )

    result = CliRunner().invoke(
        app,
        [
            "checkpoint",
            "candidate-intelligence",
            str(workspace_root / "aoa-sdk"),
            "--sample-limit",
            "2",
            "--write-index",
            "--root",
            str(workspace_root / "aoa-sdk"),
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    index_ref = Path(payload["generated_index_ref"])
    assert payload["report_type"] == "checkpoint_candidate_intelligence_report_v1"
    assert payload["source"] == "checkpoint_note"
    assert len(payload["sample_audit"]) == 2
    assert index_ref.exists()

    index = json.loads(index_ref.read_text(encoding="utf-8"))
    assert index["artifact_type"] == "checkpoint_candidate_intelligence_navigation_index_v1"
    assert "not reviewed memory" in index["boundary_note"]
    assert index["counts"]["repetition_clusters"] == len(payload["repetition_clusters"])
    assert index["counts"]["graph_anchors"] > 0
    assert index["counts"]["graph_edges"] > 0
    assert set(index["by_wrapper_family"]) >= {"eval", "memo", "owner_local", "playbook", "technique"}
    assert "repeated_manual_workflow_candidate" in index["by_event_type"]
    assert "route copied without owner review" in index["by_negative_evidence"]
