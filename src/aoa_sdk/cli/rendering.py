from __future__ import annotations

from datetime import datetime

import typer

from ..models import (
    CheckpointAfterCommitReport,
    CheckpointCloseoutContext,
    CheckpointCloseoutExecutionReport,
    CheckpointCaptureResult,
    CheckpointGitBoundaryCheck,
    CheckpointHookInstallResult,
    CheckpointHookStatus,
    CheckpointLifecycleArchiveResult,
    CheckpointLifecycleAuditReport,
    CheckpointSessionReconcileResult,
    KernelNextStepBrief,
    OwnerFollowThroughBrief,
    SessionCheckpointNote,
    SessionCheckpointPromotion,
    SurfaceCloseoutHandoff,
    SurfaceDetectionReport,
    SurfaceOpportunityItem,
    SkillDetectionReport,
    SkillDispatchItem,
    WorkflowFollowThroughBrief,
)
from ..release.api import ReleaseAuditResult, ReleasePublishResult


def _print_kernel_next_brief(brief: KernelNextStepBrief | None, *, indent: str = "") -> None:
    if brief is None:
        return
    typer.echo(f"{indent}kernel_next:")
    typer.echo(f"{indent}  action: {brief.suggested_action}")
    if brief.suggested_skill_name is not None:
        typer.echo(f"{indent}  skill: {brief.suggested_skill_name}")
    if brief.suggested_owner_repo is not None:
        typer.echo(f"{indent}  owner_repo: {brief.suggested_owner_repo}")
    if brief.missing_kernel_skill_names:
        typer.echo(f"{indent}  missing: {', '.join(brief.missing_kernel_skill_names)}")
    typer.echo(f"{indent}  reason: {brief.reason}")

def _print_owner_follow_through(
    briefs: list[OwnerFollowThroughBrief],
    *,
    handoff_path: str | None = None,
    indent: str = "",
) -> None:
    if not briefs:
        return
    typer.echo(f"{indent}owner_follow_through:")
    if handoff_path is not None:
        typer.echo(f"{indent}  handoff: {handoff_path}")
    for item in briefs:
        unit_label = item.unit_name or item.unit_ref
        typer.echo(
            f"{indent}  - [{item.suggested_action}] {unit_label} -> {item.owner_repo}:{item.next_surface}"
        )
        typer.echo(f"{indent}    reason: {item.reason}")

def _print_workflow_follow_through(
    briefs: list[WorkflowFollowThroughBrief],
    *,
    indent: str = "",
) -> None:
    if not briefs:
        return
    typer.echo(f"{indent}workflow_follow_through:")
    for item in briefs:
        typer.echo(f"{indent}  - [{item.suggested_action}] {item.skill_name}")
        typer.echo(f"{indent}    reason: {item.reason}")

def _print_skill_items(label: str, items: list[SkillDispatchItem]) -> None:
    typer.echo(f"{label}:")
    if not items:
        typer.echo("  - none")
        return
    for item in items:
        family = item.collision_family or "none"
        availability = item.host_availability.status
        typer.echo(f"  - {item.skill_name} [{item.layer} / {family} / {availability}]")
        typer.echo(f"    reason: {item.reason}")
        host_line = f"{item.host_availability.status} via {item.host_availability.source}"
        if item.host_availability.manual_equivalence_allowed:
            host_line += "; manual equivalence allowed"
        typer.echo(f"    host: {host_line}")

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

def _print_skill_detection_report(report: SkillDetectionReport) -> None:
    typer.echo(f"phase: {report.phase}")
    typer.echo(f"repo_root: {report.repo_root}")
    typer.echo(f"foundation_id: {report.foundation_id}")
    _print_skill_items("activate_now", report.activate_now)
    _print_skill_items("must_confirm", report.must_confirm)
    _print_skill_items("suggest_next", report.suggest_next)
    typer.echo(f"host_inventory_provided: {'yes' if report.host_inventory_provided else 'no'}")
    typer.echo(f"actionability_gaps: {', '.join(report.actionability_gaps) if report.actionability_gaps else 'none'}")
    typer.echo(f"blocked_actions: {', '.join(report.blocked_actions) if report.blocked_actions else 'none'}")
    _print_kernel_next_brief(report.closeout_chain)
    typer.echo("reasoning:")
    for line in report.reasoning:
        typer.echo(f"  - {line}")

def _print_surface_detection_report(report: SurfaceDetectionReport) -> None:
    typer.echo(f"phase: {report.phase}")
    typer.echo(f"repo_root: {report.repo_root}")
    typer.echo(f"workspace_root: {report.workspace_root}")
    typer.echo(f"skill_report_path: {report.skill_report_path or 'none'}")
    typer.echo(f"skill_report_included: {'yes' if report.skill_report_included else 'no'}")
    typer.echo(f"shortlist_included: {'yes' if report.shortlist_included else 'no'}")
    typer.echo(f"active_skill_names: {', '.join(report.active_skill_names) if report.active_skill_names else 'none'}")
    typer.echo(
        "immediate_skill_dispatch: "
        f"{', '.join(report.immediate_skill_dispatch) if report.immediate_skill_dispatch else 'none'}"
    )
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
    typer.echo(f"actionability_gaps: {', '.join(report.actionability_gaps) if report.actionability_gaps else 'none'}")

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
            typer.echo(f"  - {item.skill_name}")
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
            if entry.auto_observation.applied_skill_names:
                typer.echo(
                    "    auto_skills: "
                    + ", ".join(entry.auto_observation.applied_skill_names)
                )

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
    if result.session_end_skill_targets:
        typer.echo("session_end_skill_targets:")
        for target in result.session_end_skill_targets:
            typer.echo(f"  - {target.skill_name} [{target.phase}]")
            typer.echo(f"    why: {target.why}")
            typer.echo(
                "    candidate_ids: "
                f"{', '.join(target.candidate_ids) if target.candidate_ids else 'none'}"
            )
    else:
        typer.echo("session_end_skill_targets: none")
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
    typer.echo(f"  closeout_execution_count: {report.closeout_execution_count}")
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
                f"archiveable={'yes' if entry.archiveable else 'no'}{pending}"
            )
            if entry.session_memory_archive_ref:
                typer.echo(f"      session_memory: {entry.session_memory_archive_ref}")
            if entry.required_action:
                typer.echo(f"      required_action: {entry.required_action}")
        if len(report.entries) > 20:
            typer.echo(f"    - ... {len(report.entries) - 20} more")
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
    typer.echo(f"orchestrator_skill_name: {context.orchestrator_skill_name}")
    typer.echo(f"execution_mode: {context.execution_mode}")
    typer.echo(f"mechanical_bridge_only: {'yes' if context.mechanical_bridge_only else 'no'}")
    typer.echo(
        "agent_skill_application_required: "
        f"{'yes' if context.agent_skill_application_required else 'no'}"
    )
    typer.echo(f"authority_contract: {context.authority_contract}")
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
    typer.echo("ordered_skill_plan:")
    if not context.ordered_skill_plan:
        typer.echo("  - none")
    else:
        for target in context.ordered_skill_plan:
            typer.echo(f"  - {target.skill_name}")
            typer.echo(
                "    candidate_ids: "
                f"{', '.join(target.candidate_ids) if target.candidate_ids else 'none'}"
            )
            typer.echo(f"    why: {target.why}")
    typer.echo(f"notes: {', '.join(context.notes) if context.notes else 'none'}")

def _print_closeout_execution_report(report: CheckpointCloseoutExecutionReport) -> None:
    typer.echo(f"session_ref: {report.session_ref}")
    typer.echo(f"orchestrator_skill_name: {report.orchestrator_skill_name}")
    typer.echo(f"execution_mode: {report.execution_mode}")
    typer.echo(f"mechanical_bridge_only: {'yes' if report.mechanical_bridge_only else 'no'}")
    typer.echo(
        "agent_skill_application_required: "
        f"{'yes' if report.agent_skill_application_required else 'no'}"
    )
    typer.echo(f"authority_contract: {report.authority_contract}")
    typer.echo(
        "executed_at_canonical_utc: "
        + _format_dual_timestamp(
            utc_value=report.executed_at,
            local_value=report.executed_at_local,
            tz_name=report.executed_tz,
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
    _print_owner_follow_through(
        report.owner_follow_through_briefs,
        handoff_path=report.owner_handoff_path,
    )
    _print_workflow_follow_through(report.workflow_follow_through_briefs)
    typer.echo("executed_skills:")
    if not report.executed_skills:
        typer.echo("  - none")
    else:
        for item in report.executed_skills:
            typer.echo(f"  - {item.skill_name}")
            typer.echo(f"    execution_mode: {item.execution_mode}")
            typer.echo(
                "    agent_skill_application_required: "
                f"{'yes' if item.agent_skill_application_required else 'no'}"
            )
            typer.echo(f"    reason: {item.reason}")
            typer.echo(
                "    artifact_refs: "
                f"{', '.join(item.artifact_refs) if item.artifact_refs else 'none'}"
            )
            typer.echo(
                "    receipt_refs: "
                f"{', '.join(item.receipt_refs) if item.receipt_refs else 'none'}"
            )
    typer.echo("skipped_skills:")
    if not report.skipped_skills:
        typer.echo("  - none")
    else:
        for item in report.skipped_skills:
            typer.echo(f"  - {item.skill_name}: {item.reason}")
    typer.echo(
        "produced_artifact_refs: "
        f"{', '.join(report.produced_artifact_refs) if report.produced_artifact_refs else 'none'}"
    )
    typer.echo(
        "produced_receipt_refs: "
        f"{', '.join(report.produced_receipt_refs) if report.produced_receipt_refs else 'none'}"
    )
    typer.echo(f"final_stop_reason: {report.final_stop_reason}")
