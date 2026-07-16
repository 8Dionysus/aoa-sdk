from __future__ import annotations

from datetime import datetime

import typer

from ..models import (
    CheckpointAfterCommitReport,
    CheckpointCloseoutContext,
    CheckpointCloseoutMaterializationReport,
    CheckpointCaptureResult,
    CheckpointBacklogAuditReport,
    CheckpointGitBoundaryCheck,
    CheckpointHookInstallResult,
    CheckpointHookStatus,
    CandidateIntelligenceReport,
    CarrierIntelligenceReport,
    CheckpointLifecycleArchiveResult,
    CheckpointLifecycleAuditReport,
    CheckpointSessionReconcileResult,
    SessionCheckpointNote,
    SessionCheckpointPromotion,
    SurfaceCloseoutHandoff,
    SurfaceDetectionReport,
    SurfaceOpportunityItem,
)
from ..release.api import ReleaseAuditResult, ReleasePublishResult


def _print_surface_items(label: str, items: list[SurfaceOpportunityItem]) -> None:
    typer.echo(f"{label}:")
    if not items:
        typer.echo("  - none")
        return
    for item in items:
        typer.echo(
            f"  - {item.display_name} [{item.object_kind} / {item.owner_repo} / {item.state} / {item.execution.lane}]"
        )
        typer.echo(f"    ref: {item.surface_ref}")
        typer.echo(f"    reason: {item.reason}")
        if item.owner_layer_ambiguity_note:
            typer.echo(f"    ambiguity: {item.owner_layer_ambiguity_note}")
        if item.shortlist_hints:
            typer.echo(
                "    shortlist: "
                + ", ".join(
                    f"{hint.owner_repo} ({hint.confidence}/{hint.ambiguity})"
                    for hint in item.shortlist_hints
                )
            )

def _print_surface_detection_report(report: SurfaceDetectionReport) -> None:
    typer.echo(f"phase: {report.phase}")
    typer.echo(f"repo_root: {report.repo_root}")
    typer.echo(f"workspace_root: {report.workspace_root}")
    typer.echo(f"source_inputs: {', '.join(report.source_inputs) if report.source_inputs else 'none'}")
    typer.echo(f"shortlist_included: {'yes' if report.shortlist_included else 'no'}")
    typer.echo(f"regrounding_required: {'yes' if report.regrounding_required else 'no'}")
    if report.regrounding_hints:
        typer.echo("regrounding_hints:")
        for hint in report.regrounding_hints:
            typer.echo(f"  - {hint.surface_name}: {hint.decision}")
            typer.echo(
                "    reason_codes: "
                f"{', '.join(hint.reason_codes) if hint.reason_codes else 'none'}"
            )
            if hint.owner_truth_inputs:
                typer.echo(f"    owner_truth_inputs: {', '.join(hint.owner_truth_inputs)}")
    else:
        typer.echo("regrounding_hints: none")
    if report.phase == "checkpoint":
        typer.echo(f"checkpoint_kind: {report.checkpoint_kind or 'none'}")
        typer.echo(f"checkpoint_should_capture: {'yes' if report.checkpoint_should_capture else 'no'}")
        typer.echo(f"promotion_recommendation: {report.promotion_recommendation}")
        typer.echo(f"blocked_by: {', '.join(report.blocked_by) if report.blocked_by else 'none'}")
        typer.echo("candidate_clusters:")
        if not report.candidate_clusters:
            typer.echo("  - none")
        else:
            for cluster in report.candidate_clusters:
                typer.echo(
                    f"  - {cluster.display_name} [{cluster.candidate_kind} / {cluster.owner_hint} / {cluster.confidence}]"
                )
                typer.echo(f"    candidate_id: {cluster.candidate_id}")
                if cluster.blocked_by:
                    typer.echo(f"    blocked_by: {', '.join(cluster.blocked_by)}")
    _print_surface_items("items", report.items)
    typer.echo(f"closeout_followups: {', '.join(report.closeout_followups) if report.closeout_followups else 'none'}")
    typer.echo(f"owner_layer_notes: {', '.join(report.owner_layer_notes) if report.owner_layer_notes else 'none'}")
    typer.echo(f"inspection_gaps: {', '.join(report.inspection_gaps) if report.inspection_gaps else 'none'}")

def _print_surface_handoff(report: SurfaceCloseoutHandoff) -> None:
    typer.echo(f"session_ref: {report.session_ref}")
    typer.echo(f"reviewed: {'yes' if report.reviewed else 'no'}")
    typer.echo(f"surface_detection_report_ref: {report.surface_detection_report_ref}")
    typer.echo(f"checkpoint_note_ref: {report.checkpoint_note_ref or 'none'}")
    typer.echo(f"stats_refresh_recommended: {'yes' if report.stats_refresh_recommended else 'no'}")
    _print_surface_items("surviving_items", report.surviving_items)
    typer.echo("surviving_checkpoint_clusters:")
    if not report.surviving_checkpoint_clusters:
        typer.echo("  - none")
    else:
        for cluster in report.surviving_checkpoint_clusters:
            typer.echo(
                f"  - {cluster.display_name} [{cluster.candidate_kind} / {cluster.owner_hint} / {cluster.review_status}]"
            )
            typer.echo(
                "    session_end_targets: "
                f"{', '.join(cluster.session_end_targets) if cluster.session_end_targets else 'none'}"
            )
    typer.echo("checkpoint_harvest_candidates:")
    if not report.checkpoint_harvest_candidates:
        typer.echo("  - none")
    else:
        for cluster in report.checkpoint_harvest_candidates:
            typer.echo(f"  - {cluster.display_name} [{cluster.candidate_id}]")
    typer.echo("checkpoint_progression_candidates:")
    if not report.checkpoint_progression_candidates:
        typer.echo("  - none")
    else:
        for cluster in report.checkpoint_progression_candidates:
            typer.echo(f"  - {cluster.display_name} [{cluster.candidate_id}]")
    typer.echo("checkpoint_progression_axes:")
    if not report.checkpoint_progression_axes:
        typer.echo("  - none")
    else:
        for signal in report.checkpoint_progression_axes:
            typer.echo(f"  - {signal.axis} -> {signal.movement}")
            typer.echo(
                "    candidate_ids: "
                f"{', '.join(signal.candidate_ids) if signal.candidate_ids else 'none'}"
            )
    typer.echo("checkpoint_upgrade_candidates:")
    if not report.checkpoint_upgrade_candidates:
        typer.echo("  - none")
    else:
        for cluster in report.checkpoint_upgrade_candidates:
            typer.echo(f"  - {cluster.display_name} [{cluster.candidate_id}]")
    typer.echo("handoff_targets:")
    if not report.handoff_targets:
        typer.echo("  - none")
    else:
        for item in report.handoff_targets:
            typer.echo(f"  - {item.target_ref} [{item.target_kind}; {item.owner_repo}]")
            typer.echo(f"    why: {item.why}")
            typer.echo(f"    triggered_by: {', '.join(item.triggered_by) if item.triggered_by else 'none'}")
    typer.echo(f"notes: {', '.join(report.notes) if report.notes else 'none'}")

def _print_release_audit(result: ReleaseAuditResult) -> None:
    typer.echo(f"workspace_root: {result.workspace_root}")
    typer.echo(f"phase: {result.phase}")
    typer.echo(f"strict: {'yes' if result.strict else 'no'}")
    typer.echo(f"passed: {'yes' if result.passed else 'no'}")
    for report in result.repo_reports:
        typer.echo(f"{report.repo}: {'pass' if report.passed else 'fail'}")
        if report.latest_tag:
            typer.echo(f"  latest_tag: {report.latest_tag}")
        if report.expected_version:
            typer.echo(f"  expected_version: {report.expected_version}")
        if report.commits_since_tag is not None:
            typer.echo(f"  commits_since_tag: {report.commits_since_tag}")
        if report.hours_since_release is not None:
            typer.echo(f"  hours_since_release: {report.hours_since_release:.2f}")
        if report.due is not None:
            typer.echo(f"  due: {'yes' if report.due else 'no'}")
        if report.blocked_reason:
            typer.echo(f"  blocked_reason: {report.blocked_reason}")
        for check in report.checks:
            typer.echo(f"  - {check.name}: {'ok' if check.passed else 'fail'} ({check.detail})")

def _print_release_publish(result: ReleasePublishResult) -> None:
    typer.echo(f"workspace_root: {result.workspace_root}")
    typer.echo(f"dry_run: {'yes' if result.dry_run else 'no'}")
    typer.echo(f"passed: {'yes' if result.passed else 'no'}")
    for report in result.repo_reports:
        typer.echo(f"{report.repo}: {'pass' if report.passed else 'fail'}")
        typer.echo(f"  tag: {report.tag}")
        typer.echo(f"  version: {report.version}")
        if report.release_url:
            typer.echo(f"  release_url: {report.release_url}")
        typer.echo(f"  postpublish_passed: {'yes' if report.postpublish_passed else 'no'}")
        for action in report.actions:
            typer.echo(f"  - {action}")

def _print_checkpoint_note(note: SessionCheckpointNote) -> None:
    typer.echo(f"session_ref: {note.session_ref}")
    typer.echo(f"state: {note.state}")
    typer.echo(f"review_status: {note.review_status}")
    typer.echo(f"promotion_recommendation: {note.promotion_recommendation}")
    typer.echo(f"carry_until_session_closeout: {'yes' if note.carry_until_session_closeout else 'no'}")
    typer.echo(f"session_end_recommendation: {note.session_end_recommendation}")
    typer.echo(f"agent_review_status: {note.agent_review_status}")
    if note.agent_review_pending_refs:
        typer.echo(f"agent_review_pending_refs: {', '.join(note.agent_review_pending_refs)}")
    typer.echo(
        "harvest_candidate_ids: "
        f"{', '.join(note.harvest_candidate_ids) if note.harvest_candidate_ids else 'none'}"
    )
    typer.echo(
        "progression_candidate_ids: "
        f"{', '.join(note.progression_candidate_ids) if note.progression_candidate_ids else 'none'}"
    )
    typer.echo(
        "upgrade_candidate_ids: "
        f"{', '.join(note.upgrade_candidate_ids) if note.upgrade_candidate_ids else 'none'}"
    )
    typer.echo("progression_axis_signals:")
    if not note.progression_axis_signals:
        typer.echo("  - none")
    else:
        for signal in note.progression_axis_signals:
            typer.echo(f"  - {signal.axis} -> {signal.movement}")
            typer.echo(f"    why: {signal.why}")
            typer.echo(
                "    candidate_ids: "
                f"{', '.join(signal.candidate_ids) if signal.candidate_ids else 'none'}"
            )
    typer.echo(f"stats_refresh_recommended: {'yes' if note.stats_refresh_recommended else 'no'}")
    typer.echo(f"repo_scope: {', '.join(note.repo_scope) if note.repo_scope else 'none'}")
    typer.echo(f"blocked_by: {', '.join(note.blocked_by) if note.blocked_by else 'none'}")
    typer.echo(
        "action_signatures: "
        f"{len(note.action_signatures)} signature(s), "
        f"{len(note.repetition_clusters)} repetition cluster(s), "
        f"{len(note.wrapper_gap_candidates)} wrapper gap(s)"
    )
    typer.echo("candidate_clusters:")
    if not note.candidate_clusters:
        typer.echo("  - none")
    else:
        for cluster in note.candidate_clusters:
            typer.echo(
                f"  - {cluster.display_name} [{cluster.candidate_kind} / {cluster.owner_hint} / hits={cluster.checkpoint_hits} / {cluster.review_status}]"
            )
            typer.echo(f"    candidate_id: {cluster.candidate_id}")
            typer.echo(
                "    session_end_targets: "
                f"{', '.join(cluster.session_end_targets) if cluster.session_end_targets else 'none'}"
            )
            if cluster.blocked_by:
                typer.echo(f"    blocked_by: {', '.join(cluster.blocked_by)}")
    typer.echo("checkpoint_history:")
    if not note.checkpoint_history:
        typer.echo("  - none")
        return
    for entry in note.checkpoint_history:
        typer.echo(
            "  - "
            + f"{entry.checkpoint_kind} @ {entry.commit_short_sha or entry.commit_sha or entry.intent_text or 'checkpoint'}"
        )
        typer.echo(f"    agent_review: {entry.agent_review_status}")
        if entry.auto_observation is not None:
            typer.echo(f"    auto_summary: {entry.auto_observation.summary}")
            if entry.auto_observation.related_capability_refs:
                typer.echo(
                    "    related_capability_refs: "
                    + ", ".join(entry.auto_observation.related_capability_refs)
                )


def _print_candidate_intelligence_report(report: CandidateIntelligenceReport) -> None:
    typer.echo(f"repo_label: {report.repo_label}")
    typer.echo(f"source: {report.source}")
    typer.echo(f"boundary: {report.boundary_note}")
    if report.generated_index_ref:
        typer.echo(f"generated_index_ref: {report.generated_index_ref}")
    typer.echo(f"action_events: {len(report.action_events)}")
    typer.echo(f"action_signatures: {len(report.action_signatures)}")
    typer.echo(f"repetition_clusters: {len(report.repetition_clusters)}")
    typer.echo(f"wrapper_gap_candidates: {len(report.wrapper_gap_candidates)}")
    typer.echo("signatures:")
    if not report.action_signatures:
        typer.echo("  - none")
    else:
        for signature in report.action_signatures:
            typer.echo(
                f"  - {signature.signature_id} [{signature.wrapper_family_hint} / {signature.confidence}]"
            )
            typer.echo(f"    action: {signature.family}.{signature.action} -> {signature.object}")
            typer.echo(
                "    owner_pressure: "
                f"{', '.join(signature.owner_pressure) if signature.owner_pressure else 'none'}"
            )
    typer.echo("repetition_clusters:")
    if not report.repetition_clusters:
        typer.echo("  - none")
    else:
        for cluster in report.repetition_clusters:
            typer.echo(
                f"  - {cluster.cluster_id} repeat={cluster.repeat_count} "
                f"draftability={cluster.wrapper_readiness.draftability} "
                f"fit={cluster.existing_wrapper_fit.fit_status}"
            )
            typer.echo(
                f"    wrapper: {cluster.wrapper_readiness.proposed_wrapper_family}; "
                f"automation_risk={cluster.automation_risk}; owner_clarity={cluster.owner_clarity}"
            )
            if cluster.wrapper_gap is not None:
                typer.echo(f"    wrapper_gap: {cluster.wrapper_gap.candidate_id}")
    typer.echo("wrapper_gap_candidates:")
    if not report.wrapper_gap_candidates:
        typer.echo("  - none")
    else:
        for gap in report.wrapper_gap_candidates:
            typer.echo(
                f"  - {gap.candidate_id} [{gap.proposed_wrapper_family} / {gap.draftability}]"
            )
            typer.echo(f"    novelty_reason: {gap.novelty_reason}")
    typer.echo("sample_audit:")
    if not report.sample_audit:
        typer.echo("  - none")
    else:
        for sample in report.sample_audit:
            typer.echo(f"  - {sample.sample_id} -> {sample.target_ref} [{sample.verdict}]")
            typer.echo(f"    reason: {sample.reason}")


def _print_carrier_intelligence_report(report: CarrierIntelligenceReport) -> None:
    typer.echo(f"repo_label: {report.repo_label}")
    typer.echo(f"source: {report.source}")
    typer.echo(f"boundary: {report.boundary_note}")
    if report.generated_index_ref:
        typer.echo(f"generated_index_ref: {report.generated_index_ref}")
    typer.echo(f"carrier_candidates: {len(report.carrier_candidates)}")
    typer.echo("carriers:")
    if not report.carrier_candidates:
        typer.echo("  - none")
    else:
        for candidate in report.carrier_candidates:
            typer.echo(
                f"  - {candidate.candidate_id} "
                f"[{candidate.carrier_kind} / {candidate.owner_scope}]"
            )
            typer.echo(
                f"    source: {candidate.source_wrapper_family}; "
                f"risk={candidate.execution_risk}; posture={candidate.execution_posture}; "
                f"installability={candidate.installability}"
            )
            typer.echo(
                f"    readiness: {candidate.carrier_readiness.draftability}; "
                f"fit={candidate.existing_carrier_fit.fit_status}"
            )
            if candidate.carrier_readiness.blockers:
                typer.echo(
                    "    blockers: "
                    + ", ".join(candidate.carrier_readiness.blockers)
                )
    typer.echo("sample_audit:")
    if not report.sample_audit:
        typer.echo("  - none")
    else:
        for sample in report.sample_audit:
            typer.echo(f"  - {sample.sample_id} -> {sample.target_ref} [{sample.verdict}]")
            typer.echo(f"    reason: {sample.reason}")


def _format_dual_timestamp(
    *,
    utc_value: object,
    local_value: str | None,
    tz_name: str | None,
) -> str:
    if isinstance(utc_value, datetime):
        parsed_utc = utc_value
        canonical = utc_value.isoformat().replace("+00:00", "Z")
    else:
        canonical = str(utc_value)
        try:
            normalized = canonical[:-1] + "+00:00" if canonical.endswith("Z") else canonical
            parsed_utc = datetime.fromisoformat(normalized)
        except ValueError:
            parsed_utc = None
    if not local_value and parsed_utc is not None:
        local_now = parsed_utc.astimezone()
        local_value = local_now.isoformat()
        tz_name = tz_name or local_now.tzname() or local_now.strftime("%z")
    if not local_value:
        return canonical
    suffix = f" {tz_name}" if tz_name else ""
    return f"{canonical} (local {local_value}{suffix})"

def _print_checkpoint_capture(result: CheckpointCaptureResult | None) -> None:
    if result is None:
        return
    if result.appended:
        typer.echo(
            f"checkpoint_capture: appended ({result.mode}, kind={result.checkpoint_kind}, reason={result.reason})"
        )
    elif not result.attempted:
        typer.echo("checkpoint_capture: disabled")
    else:
        typer.echo(
            f"checkpoint_capture: skipped ({result.mode}, kind={result.checkpoint_kind or 'none'}, reason={result.reason})"
        )
    if result.captured_at is not None:
        typer.echo(
            "checkpoint_capture_at_canonical_utc: "
            + _format_dual_timestamp(
                utc_value=result.captured_at,
                local_value=result.captured_at_local,
                tz_name=result.captured_tz,
            )
        )
    if result.note_ref:
        typer.echo(f"checkpoint_note_ref: {result.note_ref}")
    typer.echo(
        "checkpoint_candidate_ids:"
        f" harvest={', '.join(result.harvest_candidate_ids) if result.harvest_candidate_ids else 'none'};"
        f" progression={', '.join(result.progression_candidate_ids) if result.progression_candidate_ids else 'none'};"
        f" upgrade={', '.join(result.upgrade_candidate_ids) if result.upgrade_candidate_ids else 'none'}"
    )
    if result.progression_axis_signals:
        typer.echo("progression_axis_signals:")
        for signal in result.progression_axis_signals:
            typer.echo(f"  - {signal.axis} -> {signal.movement}")
            typer.echo(
                "    candidate_ids: "
                f"{', '.join(signal.candidate_ids) if signal.candidate_ids else 'none'}"
            )
    if result.session_end_capability_candidates:
        typer.echo("session_end_capability_candidates:")
        for target in result.session_end_capability_candidates:
            typer.echo(
                f"  - {target.target_ref} "
                f"[{target.target_kind} / {target.lifecycle_posture} / {target.use_posture}]"
            )
            typer.echo(f"    why: {target.why}")
            typer.echo(
                "    candidate_ids: "
                f"{', '.join(target.candidate_ids) if target.candidate_ids else 'none'}"
            )
    else:
        typer.echo("session_end_capability_candidates: none")
    typer.echo(f"stats_refresh_recommended: {'yes' if result.stats_refresh_recommended else 'no'}")
    if result.session_end_next_honest_move:
        typer.echo(f"session_end_next_honest_move: {result.session_end_next_honest_move}")

def _print_checkpoint_after_commit_report(report: CheckpointAfterCommitReport) -> None:
    commit_label = report.commit_short_sha or report.commit_ref
    if report.status == "captured":
        typer.echo(
            f"post_commit_checkpoint: captured kind={report.checkpoint_kind} commit={commit_label} agent_review={report.agent_review_status} note={report.note_ref} report={report.report_path}"
        )
        if report.agent_review_command is not None:
            typer.echo(f"post_commit_checkpoint_review: required command={report.agent_review_command}")
        return
    if report.status == "recorded_closed_session_followthrough":
        typer.echo(
            f"post_commit_checkpoint: recorded_closed_session_followthrough kind={report.checkpoint_kind} commit={commit_label} note={report.note_ref} report={report.report_path}"
        )
        return
    if report.status == "recorded_reviewed_closeout_followthrough":
        typer.echo(
            f"post_commit_checkpoint: recorded_reviewed_closeout_followthrough kind={report.checkpoint_kind} commit={commit_label} note={report.note_ref} report={report.report_path}"
        )
        return
    if report.status == "skipped_no_active_session":
        typer.echo(
            f"post_commit_checkpoint: skipped_no_active_session kind={report.checkpoint_kind} commit={commit_label} report={report.report_path}"
        )
        return
    if report.status == "skipped_closed_session":
        typer.echo(
            f"post_commit_checkpoint: skipped_closed_session kind={report.checkpoint_kind} commit={commit_label} report={report.report_path} error={report.error_text or 'closed_session'}"
        )
        return
    typer.echo(
        f"post_commit_checkpoint: failed kind={report.checkpoint_kind} commit={commit_label} report={report.report_path} error={report.error_text or 'unknown'}"
    )

def _print_checkpoint_hook_status(status: CheckpointHookStatus) -> None:
    typer.echo(f"{status.repo} [{status.hook_name}]: {status.status}")
    typer.echo(f"  hook_path: {status.hook_path}")
    typer.echo(f"  template_path: {status.template_path}")
    typer.echo(f"  template_version: {status.template_version}")

def _print_checkpoint_hook_install(result: CheckpointHookInstallResult) -> None:
    typer.echo(f"{result.repo} [{result.hook_name}]: {result.action} (was {result.status_before})")
    typer.echo(f"  hook_path: {result.hook_path}")
    typer.echo(f"  template_version: {result.template_version}")

def _print_checkpoint_git_boundary(report: CheckpointGitBoundaryCheck) -> None:
    if report.status == "blocked_pending_review":
        pending_preview = ", ".join(report.pending_refs[:5]) or "none"
        blocking_preview = ", ".join(report.blocking_repo_labels[:5])
        blocking_suffix = f" blocking={blocking_preview}" if blocking_preview else ""
        typer.echo(
            "checkpoint_git_boundary: "
            f"blocked boundary={report.boundary} repo={report.repo_label}{blocking_suffix} pending={pending_preview}",
            err=True,
        )
        if report.required_action is not None:
            typer.echo(report.required_action, err=True)
        return
    if report.status == "blocked_unresolved_checkpoint":
        pending_preview = ", ".join(report.pending_refs[:5]) or "none"
        report_suffix = (
            f" report={report.post_commit_status_ref}"
            if report.post_commit_status_ref is not None
            else ""
        )
        typer.echo(
            "checkpoint_git_boundary: "
            f"blocked_unresolved_checkpoint boundary={report.boundary} "
            f"repo={report.repo_label} pending={pending_preview}{report_suffix}",
            err=True,
        )
        if report.required_action is not None:
            typer.echo(report.required_action, err=True)
        return
    typer.echo(
        "checkpoint_git_boundary: "
        f"{report.status} boundary={report.boundary} repo={report.repo_label} "
        f"session={report.runtime_session_id or 'none'}"
    )

def _print_checkpoint_promotion(promotion: SessionCheckpointPromotion) -> None:
    typer.echo(f"session_ref: {promotion.session_ref}")
    typer.echo(f"target: {promotion.target}")
    typer.echo(
        "promoted_at_canonical_utc: "
        + _format_dual_timestamp(
            utc_value=promotion.promoted_at,
            local_value=promotion.promoted_at_local,
            tz_name=promotion.promoted_tz,
        )
    )
    typer.echo(f"resulting_state: {promotion.resulting_state}")
    typer.echo(f"source_note_ref: {promotion.source_note_ref}")
    typer.echo(f"output_refs: {', '.join(promotion.output_refs) if promotion.output_refs else 'none'}")


def _print_checkpoint_lifecycle_audit(report: CheckpointLifecycleAuditReport) -> None:
    typer.echo("checkpoint_lifecycle_audit:")
    typer.echo(
        "  checked_at_canonical_utc: "
        + _format_dual_timestamp(
            utc_value=report.checked_at,
            local_value=report.checked_at_local,
            tz_name=report.checked_tz,
        )
    )
    typer.echo(f"  repo_label: {report.repo_label or 'all'}")
    typer.echo(f"  active_runtime_session_id: {report.active_runtime_session_id or 'none'}")
    typer.echo(f"  current_scope_count: {report.current_scope_count}")
    typer.echo(f"  note_count: {report.note_count}")
    typer.echo(f"  archive_scope_count: {report.archive_scope_count}")
    typer.echo(f"  pending_review_count: {report.pending_review_count}")
    typer.echo(f"  reviewed_not_closed_count: {report.reviewed_not_closed_count}")
    typer.echo(
        f"  closeout_materialization_count: {report.closeout_materialization_count}"
    )
    typer.echo(f"  session_memory_ref_count: {report.session_memory_ref_count}")
    typer.echo(
        f"  session_closed_without_closeout_count: {report.session_closed_without_closeout_count}"
    )
    typer.echo(f"  closable_count: {report.closable_count}")
    typer.echo(f"  archiveable_count: {report.archiveable_count}")
    typer.echo(f"  generated_index_ref: {report.generated_index_ref or 'none'}")
    typer.echo("  lifecycle_counts:")
    if not report.lifecycle_counts:
        typer.echo("    - none")
    else:
        for key, value in sorted(report.lifecycle_counts.items()):
            typer.echo(f"    - {key}: {value}")
    typer.echo("  entries:")
    if not report.entries:
        typer.echo("    - none")
    else:
        for entry in report.entries[:20]:
            pending = f" pending={','.join(entry.pending_refs[:3])}" if entry.pending_refs else ""
            active = "active" if entry.active_runtime_scope else "stale"
            typer.echo(
                "    - "
                f"{entry.repo_label} session={entry.runtime_session_id or 'none'} "
                f"state={entry.lifecycle_state}/{entry.state or 'unknown'} "
                f"{active} closable={'yes' if entry.closable else 'no'} "
                f"archiveable={'yes' if entry.archiveable else 'no'} "
                f"next={entry.next_route or 'inspect'}{pending}"
            )
            if entry.runtime_trace_ref:
                typer.echo(f"      runtime_trace: {entry.runtime_trace_ref}")
            if entry.session_memory_archive_ref:
                typer.echo(f"      session_memory: {entry.session_memory_archive_ref}")
            if entry.required_action:
                typer.echo(f"      required_action: {entry.required_action}")
        if len(report.entries) > 20:
            typer.echo(f"    - ... {len(report.entries) - 20} more")
    typer.echo(f"  notes: {', '.join(report.notes) if report.notes else 'none'}")


def _print_checkpoint_backlog_audit(report: CheckpointBacklogAuditReport) -> None:
    typer.echo("checkpoint_backlog_audit:")
    typer.echo(
        "  checked_at_canonical_utc: "
        + _format_dual_timestamp(
            utc_value=report.checked_at,
            local_value=report.checked_at_local,
            tz_name=report.checked_tz,
        )
    )
    typer.echo(f"  repo_label: {report.repo_label or 'all'}")
    typer.echo(f"  active_runtime_session_id: {report.active_runtime_session_id or 'none'}")
    typer.echo(f"  generated_index_ref: {report.generated_index_ref or 'none'}")
    typer.echo("  counts:")
    if not report.counts:
        typer.echo("    - none")
    else:
        for key, value in sorted(report.counts.items()):
            typer.echo(f"    - {key}: {value}")
    typer.echo("  evidence_table:")
    if not report.entries:
        typer.echo("    - none")
    else:
        for entry in report.entries[:30]:
            typer.echo(
                "    - "
                f"id={(entry.runtime_session_id or 'none')[:12]} "
                f"state={entry.lifecycle_state} "
                f"age_days={entry.age_days if entry.age_days is not None else 'unknown'} "
                f"trace={entry.runtime_trace_status or 'not_checked'} "
                f"session_memory={entry.session_memory_status or 'not_checked'} "
                f"next={entry.next_route}"
            )
            typer.echo(f"      path: {entry.note_ref or entry.current_dir}")
            typer.echo(f"      why: {entry.why_open}")
            if entry.runtime_trace_ref:
                typer.echo(f"      runtime_trace: {entry.runtime_trace_ref}")
            if entry.session_memory_archive_ref:
                typer.echo(f"      session_memory_archive: {entry.session_memory_archive_ref}")
            if entry.raw_refs:
                typer.echo(f"      raw_refs: {', '.join(entry.raw_refs[:4])}")
            if entry.required_action:
                typer.echo(f"      required_action: {entry.required_action}")
        if len(report.entries) > 30:
            typer.echo(f"    - ... {len(report.entries) - 30} more")
    typer.echo(f"  stop_lines: {', '.join(report.stop_lines) if report.stop_lines else 'none'}")
    typer.echo(f"  notes: {', '.join(report.notes) if report.notes else 'none'}")


def _print_checkpoint_session_reconcile_result(report: CheckpointSessionReconcileResult) -> None:
    typer.echo("checkpoint_session_reconcile:")
    typer.echo(
        "  executed_at_canonical_utc: "
        + _format_dual_timestamp(
            utc_value=report.executed_at,
            local_value=report.executed_at_local,
            tz_name=report.executed_tz,
        )
    )
    typer.echo(f"  dry_run: {'yes' if report.dry_run else 'no'}")
    typer.echo(f"  repo_label: {report.repo_label or 'all'}")
    typer.echo(f"  runtime_session_id: {report.runtime_session_id or 'all'}")
    typer.echo(f"  session_filter: {report.session_filter or 'none'}")
    typer.echo(f"  selected_count: {report.selected_count}")
    typer.echo(f"  archived_count: {report.archived_count}")
    typer.echo(f"  skipped_count: {report.skipped_count}")
    typer.echo(f"  required_action_count: {report.required_action_count}")
    typer.echo(f"  generated_index_ref: {report.generated_index_ref or 'none'}")
    typer.echo(f"  archive_refs: {', '.join(report.archive_refs) if report.archive_refs else 'none'}")
    typer.echo("  archived_entries:")
    if not report.archived_entries:
        typer.echo("    - none")
    else:
        for entry in report.archived_entries[:20]:
            typer.echo(
                "    - "
                f"{entry.repo_label} session={entry.runtime_session_id or 'none'} "
                f"state={entry.lifecycle_state} "
                f"session_memory={entry.session_memory_archive_ref or 'none'}"
            )
        if len(report.archived_entries) > 20:
            typer.echo(f"    - ... {len(report.archived_entries) - 20} more")
    typer.echo("  required_actions:")
    if not report.required_actions:
        typer.echo("    - none")
    else:
        for action in report.required_actions[:20]:
            typer.echo(f"    - {action}")
        if len(report.required_actions) > 20:
            typer.echo(f"    - ... {len(report.required_actions) - 20} more")
    typer.echo(f"  notes: {', '.join(report.notes) if report.notes else 'none'}")


def _print_checkpoint_lifecycle_archive_result(report: CheckpointLifecycleArchiveResult) -> None:
    typer.echo("checkpoint_lifecycle_archive:")
    typer.echo(
        "  executed_at_canonical_utc: "
        + _format_dual_timestamp(
            utc_value=report.executed_at,
            local_value=report.executed_at_local,
            tz_name=report.executed_tz,
        )
    )
    typer.echo(f"  dry_run: {'yes' if report.dry_run else 'no'}")
    typer.echo(f"  repo_label: {report.repo_label or 'all'}")
    typer.echo(f"  runtime_session_id: {report.runtime_session_id or 'all'}")
    typer.echo(f"  archived_count: {report.archived_count}")
    typer.echo(f"  skipped_count: {report.skipped_count}")
    typer.echo(f"  archive_refs: {', '.join(report.archive_refs) if report.archive_refs else 'none'}")
    typer.echo("  archived_entries:")
    if not report.archived_entries:
        typer.echo("    - none")
    else:
        for entry in report.archived_entries[:20]:
            typer.echo(
                "    - "
                f"{entry.repo_label} session={entry.runtime_session_id or 'none'} "
                f"state={entry.lifecycle_state} dir={entry.current_dir}"
            )
        if len(report.archived_entries) > 20:
            typer.echo(f"    - ... {len(report.archived_entries) - 20} more")
    typer.echo(f"  notes: {', '.join(report.notes) if report.notes else 'none'}")


def _print_closeout_context(context: CheckpointCloseoutContext) -> None:
    typer.echo(f"session_ref: {context.session_ref}")
    typer.echo(f"materialization_mode: {context.materialization_mode}")
    typer.echo(f"capability_execution_claimed: {'yes' if context.capability_execution_claimed else 'no'}")
    typer.echo(f"authority_contract: {context.authority_contract}")
    typer.echo(f"related_workflow_ref: {context.related_workflow_ref}")
    typer.echo(
        "built_at_canonical_utc: "
        + _format_dual_timestamp(
            utc_value=context.built_at,
            local_value=context.built_at_local,
            tz_name=context.built_tz,
        )
    )
    typer.echo(f"repo_root: {context.repo_root}")
    typer.echo(f"reviewed_artifact_ref: {context.reviewed_artifact_ref}")
    typer.echo(f"runtime_session_id: {context.runtime_session_id or 'none'}")
    typer.echo(f"session_trace_ref: {context.session_trace_ref or 'none'}")
    typer.echo(f"session_trace_thread_id: {context.session_trace_thread_id or 'none'}")
    if context.session_memory_ref is None:
        typer.echo(f"session_memory_ref: none [{context.session_memory_freshness.status}]")
    else:
        typer.echo(
            "session_memory_ref: "
            f"{context.session_memory_ref.session_id} "
            f"[{context.session_memory_freshness.status}] "
            f"{context.session_memory_ref.archive_path}"
        )
    typer.echo(f"checkpoint_note_ref: {context.checkpoint_note_ref or 'none'}")
    typer.echo(
        "checkpoint_note_refs: "
        f"{', '.join(context.checkpoint_note_refs) if context.checkpoint_note_refs else 'none'}"
    )
    typer.echo(f"surface_handoff_ref: {context.surface_handoff_ref or 'none'}")
    typer.echo(f"receipt_refs: {', '.join(context.receipt_refs) if context.receipt_refs else 'none'}")
    typer.echo(f"repo_scope: {', '.join(context.repo_scope) if context.repo_scope else 'none'}")
    typer.echo(
        "candidate_map: "
        f"harvest={len(context.candidate_map.harvest_candidate_ids)}, "
        f"progression={len(context.candidate_map.progression_candidate_ids)}, "
        f"upgrade={len(context.candidate_map.upgrade_candidate_ids)}"
    )
    typer.echo(
        "checkpoint_review_carry: "
        f"reviews={len(context.checkpoint_review_carry.review_refs)}, "
        f"questions={len(context.checkpoint_review_carry.closeout_questions)}, "
        f"findings={len(context.checkpoint_review_carry.findings)}"
    )
    typer.echo("capability_candidates:")
    if not context.capability_candidates:
        typer.echo("  - none")
    else:
        for target in context.capability_candidates:
            typer.echo(
                f"  - {target.target_ref} "
                f"[{target.target_kind} / {target.lifecycle_posture} / {target.use_posture}]"
            )
            typer.echo(
                "    candidate_ids: "
                f"{', '.join(target.candidate_ids) if target.candidate_ids else 'none'}"
            )
            typer.echo(f"    why: {target.why}")
    typer.echo(f"notes: {', '.join(context.notes) if context.notes else 'none'}")

def _print_closeout_materialization_report(
    report: CheckpointCloseoutMaterializationReport,
) -> None:
    typer.echo(f"session_ref: {report.session_ref}")
    typer.echo(f"materialization_mode: {report.materialization_mode}")
    typer.echo(f"capability_execution_claimed: {'yes' if report.capability_execution_claimed else 'no'}")
    typer.echo(f"authority_contract: {report.authority_contract}")
    typer.echo(f"related_workflow_ref: {report.related_workflow_ref}")
    typer.echo(
        "materialized_at_canonical_utc: "
        + _format_dual_timestamp(
            utc_value=report.materialized_at,
            local_value=report.materialized_at_local,
            tz_name=report.materialized_tz,
        )
    )
    typer.echo(f"context_ref: {report.context_ref}")
    typer.echo(f"reviewed_artifact_ref: {report.reviewed_artifact_ref}")
    typer.echo(f"runtime_session_id: {report.runtime_session_id or 'none'}")
    typer.echo(f"session_trace_ref: {report.session_trace_ref or 'none'}")
    typer.echo(f"session_trace_thread_id: {report.session_trace_thread_id or 'none'}")
    if report.session_memory_ref is None:
        typer.echo(f"session_memory_ref: none [{report.session_memory_freshness.status}]")
    else:
        typer.echo(
            "session_memory_ref: "
            f"{report.session_memory_ref.session_id} "
            f"[{report.session_memory_freshness.status}] "
            f"{report.session_memory_ref.archive_path}"
        )
    typer.echo(f"checkpoint_note_ref: {report.checkpoint_note_ref or 'none'}")
    typer.echo(
        "checkpoint_note_refs: "
        f"{', '.join(report.checkpoint_note_refs) if report.checkpoint_note_refs else 'none'}"
    )
    typer.echo(f"surface_handoff_ref: {report.surface_handoff_ref or 'none'}")
    typer.echo(f"owner_handoff_path: {report.owner_handoff_path or 'none'}")
    if report.owner_handoff is not None:
        typer.echo("owner_handoff_items:")
        for handoff_item in report.owner_handoff.items:
            typer.echo(
                f"  - {handoff_item.candidate_ref} -> "
                f"{handoff_item.owner_ref}:{handoff_item.proposed_surface} "
                f"[{handoff_item.decision_posture}]"
            )
    typer.echo("materialization_stages:")
    if not report.stages:
        typer.echo("  - none")
    else:
        for stage in report.stages:
            typer.echo(f"  - {stage.stage_id} [{stage.status}]")
            typer.echo(f"    reason: {stage.reason}")
            typer.echo(
                "    artifact_refs: "
                f"{', '.join(stage.artifact_refs) if stage.artifact_refs else 'none'}"
            )
            typer.echo(
                "    receipt_refs: "
                f"{', '.join(stage.receipt_refs) if stage.receipt_refs else 'none'}"
            )
    typer.echo(
        "produced_artifact_refs: "
        f"{', '.join(report.produced_artifact_refs) if report.produced_artifact_refs else 'none'}"
    )
    typer.echo(
        "produced_receipt_refs: "
        f"{', '.join(report.produced_receipt_refs) if report.produced_receipt_refs else 'none'}"
    )
    typer.echo(f"final_stop_reason: {report.final_stop_reason}")
