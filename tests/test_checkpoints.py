from __future__ import annotations

from pathlib import Path

from aoa_sdk import AoASDK


def test_surface_detect_checkpoint_phase_emits_candidate_clusters(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    report = sdk.surfaces.detect(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="checkpoint",
        checkpoint_kind="commit",
        intent_text="recurring workflow needs better handoff proof and recall",
    )

    assert report.phase == "checkpoint"
    assert report.checkpoint_kind == "commit"
    assert report.checkpoint_should_capture is True
    assert report.candidate_clusters
    assert report.promotion_recommendation in {"local_note", "dionysus_note"}
    assert {cluster.candidate_kind for cluster in report.candidate_clusters} >= {"route", "proof", "recall"}


def test_checkpoint_status_becomes_reviewable_after_repeat(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    first = sdk.checkpoints.append(
        repo_root=str(workspace_root / "aoa-sdk"),
        checkpoint_kind="commit",
        intent_text="recurring workflow needs better handoff proof and recall",
    )
    second = sdk.checkpoints.append(
        repo_root=str(workspace_root / "aoa-sdk"),
        checkpoint_kind="verify_green",
        intent_text="recurring workflow needs better handoff proof and recall",
    )

    note_dir = workspace_root / "aoa-sdk" / ".aoa" / "session-growth" / "current" / "aoa-sdk"
    assert first.state == "collecting"
    assert second.state == "reviewable"
    assert (note_dir / "checkpoint-note.jsonl").exists()
    assert (note_dir / "checkpoint-note.json").exists()
    assert (note_dir / "checkpoint-note.md").exists()
    route_cluster = next(cluster for cluster in second.candidate_clusters if cluster.candidate_kind == "route")
    assert route_cluster.checkpoint_hits == 2
    assert route_cluster.review_status == "reviewable"
    assert route_cluster.session_end_targets == ["harvest", "upgrade"]
    assert second.carry_until_session_closeout is True
    assert second.session_end_recommendation == "harvest_and_upgrade"
    assert second.harvest_candidate_ids
    assert second.upgrade_candidate_ids
    assert second.stats_refresh_recommended is True


def test_capture_from_skill_phase_auto_appends_only_when_growth_signal_exists(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    capture = sdk.checkpoints.capture_from_skill_phase(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="pre-mutation",
        intent_text="recurring workflow needs better handoff proof and recall",
        mutation_surface="code",
    )

    note_dir = workspace_root / "aoa-sdk" / ".aoa" / "session-growth" / "current" / "aoa-sdk"
    assert capture.mode == "auto"
    assert capture.appended is True
    assert capture.reason == "checkpoint_signal"
    assert capture.checkpoint_kind == "commit"
    assert capture.note is not None
    assert (note_dir / "checkpoint-note.json").exists()


def test_capture_from_skill_phase_reports_no_signal_without_writing_note(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    capture = sdk.checkpoints.capture_from_skill_phase(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="ingress",
        intent_text="plan a cross-repo change",
        mutation_surface="none",
    )

    note_dir = workspace_root / "aoa-sdk" / ".aoa" / "session-growth" / "current" / "aoa-sdk"
    assert capture.mode == "auto"
    assert capture.appended is False
    assert capture.reason == "no_checkpoint_signal"
    assert capture.note is None
    assert not note_dir.exists()


def test_surface_detect_checkpoint_phase_emits_growth_cluster_for_explicit_commit_intent(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    report = sdk.surfaces.detect(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="checkpoint",
        checkpoint_kind="commit",
        intent_text="commit bounded patch",
        mutation_surface="code",
    )

    assert report.checkpoint_should_capture is True
    growth_cluster = next(cluster for cluster in report.candidate_clusters if cluster.candidate_kind == "growth")
    assert growth_cluster.owner_hint == "aoa-sdk"
    assert growth_cluster.source_surface_ref == "aoa-sdk:checkpoint_auto_capture.commit"
    assert "mutation_surface:code" in growth_cluster.evidence_refs


def test_capture_from_skill_phase_auto_appends_for_explicit_commit_intent(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    capture = sdk.checkpoints.capture_from_skill_phase(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="pre-mutation",
        intent_text="commit bounded patch",
        mutation_surface="code",
    )

    note_dir = workspace_root / "aoa-sdk" / ".aoa" / "session-growth" / "current" / "aoa-sdk"
    assert capture.mode == "auto"
    assert capture.appended is True
    assert capture.reason == "checkpoint_signal"
    assert capture.checkpoint_kind == "commit"
    assert capture.note is not None
    growth_cluster = next(cluster for cluster in capture.note.candidate_clusters if cluster.candidate_kind == "growth")
    assert growth_cluster.session_end_targets == ["harvest"]
    assert capture.note.harvest_candidate_ids == [growth_cluster.candidate_id]
    assert capture.note.upgrade_candidate_ids == []
    assert (note_dir / "checkpoint-note.json").exists()


def test_checkpoint_promote_writes_dionysus_snapshot_and_updates_note(workspace_root: Path) -> None:
    dionysus_root = workspace_root / "Dionysus"
    (dionysus_root / "reports" / "ecosystem-audits").mkdir(parents=True, exist_ok=True)
    (dionysus_root / "README.md").write_text("# Dionysus\n", encoding="utf-8")

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

    promotion = sdk.checkpoints.promote(
        repo_root=str(workspace_root / "aoa-sdk"),
        target="dionysus-note",
    )

    promoted_json = list((dionysus_root / "reports" / "ecosystem-audits").glob("*.aoa-sdk.checkpoint-note.json"))
    promoted_md = list((dionysus_root / "reports" / "ecosystem-audits").glob("*.aoa-sdk.checkpoint-note.md"))
    note = sdk.checkpoints.status(repo_root=str(workspace_root / "aoa-sdk"))

    assert promotion.target == "dionysus-note"
    assert promoted_json
    assert promoted_md
    assert note.state == "promoted"
    assert any("repo:Dionysus/reports/ecosystem-audits/" in ref for ref in promotion.output_refs)


def test_checkpoint_promote_harvest_handoff_closes_note(workspace_root: Path) -> None:
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

    promotion = sdk.checkpoints.promote(
        repo_root=str(workspace_root / "aoa-sdk"),
        target="harvest-handoff",
    )

    handoff_path = workspace_root / "aoa-sdk" / ".aoa" / "session-growth" / "current" / "aoa-sdk" / "harvest-handoff.json"
    note = sdk.checkpoints.status(repo_root=str(workspace_root / "aoa-sdk"))

    assert promotion.target == "harvest-handoff"
    assert handoff_path.exists()
    assert note.state == "closed"
    assert promotion.output_refs == [str(handoff_path)]


def test_surface_closeout_handoff_links_checkpoint_note(workspace_root: Path) -> None:
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
    report = sdk.surfaces.detect(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="closeout",
        intent_text="recurring workflow needs better handoff proof and recall",
    )

    handoff = sdk.surfaces.build_closeout_handoff(
        report,
        session_ref="session:test-checkpoint-closeout-handoff",
    )

    assert handoff.checkpoint_note_ref is not None
    assert handoff.surviving_checkpoint_clusters
    assert handoff.checkpoint_harvest_candidates
    assert handoff.checkpoint_upgrade_candidates
    assert handoff.stats_refresh_recommended is True
    assert any(target.skill_name == "aoa-session-donor-harvest" for target in handoff.handoff_targets)
    assert any(target.skill_name == "aoa-quest-harvest" for target in handoff.handoff_targets)
