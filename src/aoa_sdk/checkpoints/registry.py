from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, cast

from ..errors import SurfaceNotFound
from ..loaders import write_json
from ..models import (
    CheckpointAfterCommitReport,
    CheckpointCloseoutContext,
    CheckpointCloseoutExecutionReport,
    CheckpointCaptureResult,
    CheckpointGitBoundaryCheck,
    CheckpointHookInstallResult,
    CheckpointHookStatus,
    CheckpointBacklogAuditReport,
    CheckpointLifecycleArchiveResult,
    CheckpointLifecycleAuditReport,
    CheckpointSessionReconcileResult,
    CarrierIntelligenceReport,
    CandidateIntelligenceReport,
    CloseoutContextCandidateMap,
    CloseoutExecutionStep,
    SessionCheckpointAutoObservation,
    SessionCheckpointAgentReview,
    SessionCheckpointHistoryEntry,
    SessionCheckpointNote,
    SessionCheckpointPromotion,
    SurfaceDetectionReport,
)
from ..skills.discovery import SkillsAPI
from ..surfaces import SurfacesAPI
from ..workspace.discovery import Workspace
from ..workspace.roots import KNOWN_REPOS
from .closeout.context import (
    _closeout_candidate_clusters,
    _collect_candidate_lineage_hints,
    _collect_receipt_paths,
    _derive_closeout_skill_plan,
    _load_context_checkpoint_notes,
    _load_context_surface_handoff,
    _load_receipt_payloads,
    _load_reviewed_surface_handoff,
    _resolve_closeout_session_ref,
    _surface_handoff_path,
    _validate_repo_root_closeout_scope,
)
from .closeout.evidence import (
    _merge_closeout_evidence,
    _read_reviewed_artifact,
    _read_session_trace,
)
from .closeout.execution import (
    _build_donor_harvest_outputs,
    _build_progression_lift_outputs,
    _build_quest_harvest_outputs,
)
from .closeout.followthrough import (
    _build_closeout_followthrough_decision,
    _build_owner_followthrough_map,
)
from .closeout.owner_handoff import (
    _has_reviewed_closeout_owner_handoff_for_repo,
    _write_checkpoint_owner_handoff,
)
from .hooks.git_boundary import (
    CheckpointHookName,
    checkpoint_hook_status_parts,
    read_git_commit_metadata,
    render_checkpoint_hook,
)
from .kinds import infer_auto_checkpoint_kind as _infer_auto_checkpoint_kind
from .candidate_indexes import (
    write_checkpoint_candidate_intelligence_index as _write_checkpoint_candidate_intelligence_index,
)
from .candidate_intelligence import (
    build_candidate_intelligence_from_note as _build_candidate_intelligence_from_note,
)
from .carrier_indexes import (
    write_checkpoint_carrier_candidate_intelligence_index as _write_checkpoint_carrier_candidate_intelligence_index,
)
from .carrier_intelligence import (
    build_carrier_intelligence_from_candidate_report as _build_carrier_intelligence_from_candidate_report,
)
from .backlog import audit_checkpoint_backlog as _audit_checkpoint_backlog
from .lifecycle import (
    audit_checkpoint_lifecycle as _audit_checkpoint_lifecycle,
    close_archive_checkpoint_lifecycle as _close_archive_checkpoint_lifecycle,
)
from .ledger.notes import (
    archive_current_checkpoint as _archive_current_checkpoint,
    build_checkpoint_note as _build_checkpoint_note,
    default_session_ref as _default_session_ref,
    derive_session_end_next_honest_move as _derive_session_end_next_honest_move,
    derive_session_end_skill_targets as _derive_session_end_skill_targets,
    load_checkpoint_note as _load_checkpoint_note,
    load_runtime_checkpoint_note as _load_runtime_checkpoint_note,
    load_runtime_checkpoint_notes_for_closeout as _load_runtime_checkpoint_notes_for_closeout,
    load_runtime_scoped_checkpoint_notes as _load_runtime_scoped_checkpoint_notes,
    merge_progression_axis_signals as _merge_progression_axis_signals,
    peek_runtime_checkpoint_note as _peek_runtime_checkpoint_note,
    should_hide_current_checkpoint_note as _should_hide_current_checkpoint_note,
    should_rotate_checkpoint_note as _should_rotate_checkpoint_note,
)
from .naming import safe_checkpoint_name as _safe_name
from .promotion.targets import promote_to_dionysus, write_harvest_handoff
from .reconcile import reconcile_closed_checkpoint_sessions as _reconcile_closed_checkpoint_sessions
from .render.markdown import render_checkpoint_note_markdown as _render_checkpoint_note_markdown
from .review.after_commit import (
    after_commit_intent as _after_commit_intent,
    after_commit_mutation_surface as _after_commit_mutation_surface,
    agent_review_command as _agent_review_command,
    build_after_commit_auto_observation as _build_after_commit_auto_observation,
    mark_after_commit_report_reviewed as _mark_after_commit_report_reviewed,
    resolve_after_commit_checkpoint_kind as _resolve_after_commit_checkpoint_kind,
    write_after_commit_report as _write_after_commit_report,
)
from .review.agent_review import (
    auto_review_candidate_notes as _auto_review_candidate_notes,
    auto_review_closeout_questions as _auto_review_closeout_questions,
    auto_review_findings as _auto_review_findings,
    auto_review_mechanic_hints as _auto_review_mechanic_hints,
    auto_review_next_owner_moves as _auto_review_next_owner_moves,
    auto_review_stats_hints as _auto_review_stats_hints,
    auto_review_summary as _auto_review_summary,
    closeout_pending_agent_review_refs as _closeout_pending_agent_review_refs,
    collect_closeout_review_carry as _collect_closeout_review_carry,
    history_auto_review_evidence_refs as _history_auto_review_evidence_refs,
    matching_auto_observation as _matching_auto_observation,
    matching_checkpoint_history_entry as _matching_checkpoint_history_entry,
    merge_auto_review_items as _merge_auto_review_items,
)
from .review.skipped_recovery import (
    recover_skipped_after_commit_for_review as _recover_skipped_after_commit_for_review,
    skipped_after_commit_pending_ref as _skipped_after_commit_pending_ref,
    skipped_after_commit_required_action as _skipped_after_commit_required_action,
    unresolved_skipped_post_commit_status_for_boundary as _unresolved_skipped_post_commit_status_for_boundary,
)
from .runtime.sessions import (
    ensure_checkpoint_runtime_session,
    load_checkpoint_runtime_session,
    peek_checkpoint_runtime_session,
    probe_active_runtime_session_for_after_commit,
    probe_checkpoint_runtime_session,
    probe_existing_checkpoint_runtime_session,
)
from .session_memory import (
    resolve_checkpoint_session_memory as _resolve_checkpoint_session_memory,
    session_memory_evidence_from_ref as _session_memory_evidence_from_ref,
)
from .timestamps import (
    local_timestamp_parts as _local_timestamp_parts,
)
from .topology.paths import (
    CheckpointPaths,
    checkpoint_paths_for_label,
    post_commit_status_path,
)


CHECKPOINT_KINDS = (
    "manual",
    "commit",
    "verify_green",
    "pr_opened",
    "pr_merged",
    "pause",
    "owner_followthrough",
)
POST_COMMIT_CHECKPOINT_KINDS = ("auto", "commit", "owner_followthrough")
OWNER_MUTABLE_REPOS = tuple(repo for repo in KNOWN_REPOS if repo != "8Dionysus")
PROMOTION_TARGETS = ("dionysus-note", "harvest-handoff")


class CheckpointsAPI:
    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace
        self._surfaces = SurfacesAPI(workspace)

    def append(
        self,
        *,
        repo_root: str,
        checkpoint_kind: Literal[
            "manual",
            "commit",
            "verify_green",
            "pr_opened",
            "pr_merged",
            "pause",
            "owner_followthrough",
        ],
        intent_text: str = "",
        mutation_surface: Literal["none", "code", "repo-config", "infra", "runtime", "public-share"] = "none",
        session_file: str | None = None,
        skill_report_path: str | None = None,
        surface_report: SurfaceDetectionReport | None = None,
        surface_report_path: str | None = None,
        manual_review_requested: bool = False,
        commit_sha: str | None = None,
        commit_short_sha: str | None = None,
        agent_review_status: Literal["not_required", "pending", "reviewed"] = "not_required",
        agent_review_ref: str | None = None,
        auto_observation: SessionCheckpointAutoObservation | None = None,
        observed_at: datetime | None = None,
        observed_at_local: str | None = None,
        observed_tz: str | None = None,
    ) -> SessionCheckpointNote:
        runtime_session_id, runtime_session_created_at = ensure_checkpoint_runtime_session(
            workspace=self.workspace,
            session_file=session_file,
        )
        paths = _resolve_runtime_checkpoint_paths(
            self.workspace,
            repo_root=repo_root,
            runtime_session_id=runtime_session_id,
            migrate_legacy=True,
        )
        existing_note = _load_checkpoint_note(paths.note_json) if paths.note_json.exists() else None
        if paths.note_json.exists():
            if existing_note is not None and _should_rotate_checkpoint_note(
                existing_note,
                runtime_session_id=runtime_session_id,
            ):
                _archive_current_checkpoint(paths)
                existing_note = None

        report = surface_report or self._surfaces.detect(
            repo_root=repo_root,
            phase="checkpoint",
            intent_text=intent_text,
            mutation_surface=mutation_surface,
            session_file=session_file,
            skill_report_path=skill_report_path,
            checkpoint_kind=checkpoint_kind,
        )
        if report.phase != "checkpoint":
            raise ValueError("checkpoint append requires a checkpoint-phase surface report")
        if report.checkpoint_kind != checkpoint_kind:
            raise ValueError(
                "checkpoint append requires surface_report.checkpoint_kind to match checkpoint_kind"
            )
        report_path = (
            Path(surface_report_path).expanduser().resolve()
            if surface_report_path is not None
            else paths.surface_report
        )
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(
                {
                    "report_path": str(report_path),
                    "report": report.model_dump(mode="json"),
                },
                indent=2,
                ensure_ascii=True,
            )
            + "\n",
            encoding="utf-8",
        )
        if observed_at is None:
            observed_at, observed_at_local, observed_tz = _local_timestamp_parts()
        payload = {
            "session_ref": _default_session_ref(
                paths,
                existing_note=existing_note,
                runtime_session_id=runtime_session_id,
            ),
            "runtime_session_id": runtime_session_id,
            "runtime_session_created_at": (
                runtime_session_created_at.isoformat().replace("+00:00", "Z")
                if runtime_session_created_at is not None
                else None
            ),
            "repo_root": str(_resolve_context_root(self.workspace, repo_root)),
            "repo_label": paths.repo_label,
            "history_entry": SessionCheckpointHistoryEntry(
                checkpoint_kind=checkpoint_kind,
                observed_at=observed_at,
                observed_at_local=observed_at_local,
                observed_tz=observed_tz,
                report_ref=str(report_path),
                intent_text=intent_text,
                checkpoint_should_capture=report.checkpoint_should_capture,
                blocked_by=list(report.blocked_by),
                candidate_clusters=list(report.candidate_clusters),
                action_events=list(report.action_events),
                action_signatures=list(report.action_signatures),
                wrapper_gap_candidates=list(report.wrapper_gap_candidates),
                manual_review_requested=manual_review_requested,
                commit_sha=commit_sha,
                commit_short_sha=commit_short_sha,
                agent_review_status=agent_review_status,
                agent_review_ref=agent_review_ref,
                auto_observation=auto_observation,
            ).model_dump(mode="json"),
        }
        paths.jsonl.parent.mkdir(parents=True, exist_ok=True)
        with paths.jsonl.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=True) + "\n")
        return self.status(repo_root=repo_root, session_file=session_file)

    def capture_from_skill_phase(
        self,
        *,
        repo_root: str,
        phase: Literal["ingress", "pre-mutation"],
        intent_text: str = "",
        mutation_surface: Literal["none", "code", "repo-config", "infra", "runtime", "public-share"] = "none",
        session_file: str | None = None,
        skill_report_path: str | None = None,
        checkpoint_kind: Literal[
            "manual",
            "commit",
            "verify_green",
            "pr_opened",
            "pr_merged",
            "pause",
            "owner_followthrough",
        ] | None = None,
        manual_review_requested: bool = False,
        auto_capture: bool = True,
    ) -> CheckpointCaptureResult:
        if checkpoint_kind is not None:
            captured_at, captured_at_local, captured_tz = _local_timestamp_parts()
            note = self.append(
                repo_root=repo_root,
                checkpoint_kind=checkpoint_kind,
                intent_text=intent_text,
                mutation_surface=mutation_surface,
                session_file=session_file,
                skill_report_path=skill_report_path,
                manual_review_requested=manual_review_requested,
            )
            session_end_targets = _derive_session_end_skill_targets(note)
            return CheckpointCaptureResult(
                mode="explicit",
                attempted=True,
                appended=True,
                checkpoint_kind=checkpoint_kind,
                captured_at=captured_at,
                captured_at_local=captured_at_local,
                captured_tz=captured_tz,
                reason="explicit_request",
                note_ref=_checkpoint_note_ref_for_capture(
                    self.workspace,
                    repo_root,
                    runtime_session_id=note.runtime_session_id,
                ),
                session_end_skill_targets=session_end_targets,
                session_end_next_honest_move=_derive_session_end_next_honest_move(
                    note=note,
                    session_end_targets=session_end_targets,
                ),
                harvest_candidate_ids=list(note.harvest_candidate_ids),
                progression_candidate_ids=list(note.progression_candidate_ids),
                upgrade_candidate_ids=list(note.upgrade_candidate_ids),
                progression_axis_signals=list(note.progression_axis_signals),
                stats_refresh_recommended=note.stats_refresh_recommended,
                note=note,
            )

        if not auto_capture:
            return _checkpoint_capture_result_without_append(
                self,
                repo_root=repo_root,
                session_file=session_file,
                reason="auto_disabled",
                attempted=False,
                checkpoint_kind=None,
                read_only=True,
            )

        if phase == "ingress" and mutation_surface == "none":
            return _checkpoint_capture_result_without_append(
                self,
                repo_root=repo_root,
                session_file=session_file,
                reason="no_checkpoint_signal",
                attempted=True,
                checkpoint_kind=None,
                read_only=True,
            )

        inferred_kind = _infer_auto_checkpoint_kind(intent_text=intent_text)
        report = self._surfaces.detect(
            repo_root=repo_root,
            phase="checkpoint",
            intent_text=intent_text,
            mutation_surface=mutation_surface,
            session_file=session_file,
            skill_report_path=skill_report_path,
            checkpoint_kind=inferred_kind,
        )
        if not report.checkpoint_should_capture:
            return _checkpoint_capture_result_without_append(
                self,
                repo_root=repo_root,
                session_file=session_file,
                reason="no_checkpoint_signal",
                attempted=True,
                checkpoint_kind=inferred_kind,
                read_only=False,
            )

        note = self.append(
            repo_root=repo_root,
            checkpoint_kind=inferred_kind,
            intent_text=intent_text,
            mutation_surface=mutation_surface,
            session_file=session_file,
            skill_report_path=skill_report_path,
            surface_report=report,
            manual_review_requested=manual_review_requested,
        )
        session_end_targets = _derive_session_end_skill_targets(note)
        captured_at, captured_at_local, captured_tz = _local_timestamp_parts()
        return CheckpointCaptureResult(
            mode="auto",
            attempted=True,
            appended=True,
            checkpoint_kind=inferred_kind,
            captured_at=captured_at,
            captured_at_local=captured_at_local,
            captured_tz=captured_tz,
            reason="checkpoint_signal",
            note_ref=_checkpoint_note_ref_for_capture(
                self.workspace,
                repo_root,
                runtime_session_id=note.runtime_session_id,
            ),
            session_end_skill_targets=session_end_targets,
            session_end_next_honest_move=_derive_session_end_next_honest_move(
                note=note,
                session_end_targets=session_end_targets,
            ),
            harvest_candidate_ids=list(note.harvest_candidate_ids),
            progression_candidate_ids=list(note.progression_candidate_ids),
            upgrade_candidate_ids=list(note.upgrade_candidate_ids),
            progression_axis_signals=list(note.progression_axis_signals),
            stats_refresh_recommended=note.stats_refresh_recommended,
            note=note,
        )

    def after_commit(
        self,
        *,
        repo_root: str,
        commit_ref: str = "HEAD",
        session_file: str | None = None,
        checkpoint_kind: Literal["auto", "commit", "owner_followthrough"] = "auto",
    ) -> CheckpointAfterCommitReport:
        if checkpoint_kind not in POST_COMMIT_CHECKPOINT_KINDS:
            raise ValueError(
                "post-commit checkpoint kind must be auto, commit, or owner_followthrough"
            )
        repo_root_path = _resolve_context_root(self.workspace, repo_root)
        repo_label = _resolve_context_label(self.workspace, repo_root)
        session_path: Path | None = None
        runtime_session_id: str | None = None
        runtime_session_created_at: datetime | None = None
        skill_report_path: str | None = None
        surface_report_path: str | None = None
        note_ref: str | None = None
        commit_metadata: dict[str, Any] = {
            "commit_sha": None,
            "commit_short_sha": None,
            "commit_subject": None,
            "commit_body": None,
            "changed_paths": [],
        }

        try:
            commit_metadata = read_git_commit_metadata(repo_root_path, commit_ref)
            session_path, runtime_session, session_probe_error = (
                probe_active_runtime_session_for_after_commit(
                    self.workspace,
                    session_file,
                )
            )
            captured_at, captured_at_local, captured_tz = _local_timestamp_parts()
            if runtime_session is None:
                if session_probe_error is not None:
                    raise RuntimeError(session_probe_error)
                resolved_checkpoint_kind = _resolve_after_commit_checkpoint_kind(
                    checkpoint_kind=checkpoint_kind,
                    commit_subject=commit_metadata["commit_subject"],
                    commit_body=commit_metadata["commit_body"],
                    existing_note=None,
                )
                mutation_surface = _after_commit_mutation_surface(resolved_checkpoint_kind)
                report_path = post_commit_status_path(self.workspace, repo_label)
                report = CheckpointAfterCommitReport(
                    status="skipped_no_active_session",
                    repo_root=str(repo_root_path),
                    repo_label=repo_label,
                    report_path=str(report_path),
                    commit_ref=commit_ref,
                    commit_sha=commit_metadata["commit_sha"],
                    commit_short_sha=commit_metadata["commit_short_sha"],
                    commit_subject=commit_metadata["commit_subject"],
                    commit_body=commit_metadata["commit_body"],
                    changed_paths=list(commit_metadata["changed_paths"]),
                    checkpoint_kind=resolved_checkpoint_kind,
                    mutation_surface=mutation_surface,
                    captured_at=captured_at,
                    captured_at_local=captured_at_local,
                    captured_tz=captured_tz,
                    session_file=str(session_path),
                )
                _write_after_commit_report(report_path, report)
                return report

            runtime_session_id = runtime_session.session_id
            runtime_session_created_at = runtime_session.created_at.astimezone(UTC)
            paths = _resolve_runtime_checkpoint_paths(
                self.workspace,
                repo_root=repo_root,
                runtime_session_id=runtime_session_id,
                migrate_legacy=True,
            )
            report_path = paths.post_commit_report
            session_file_ref = str(session_path)
            existing_note = _load_checkpoint_note(paths.note_json) if paths.note_json.exists() else None
            resolved_checkpoint_kind = _resolve_after_commit_checkpoint_kind(
                checkpoint_kind=checkpoint_kind,
                commit_subject=commit_metadata["commit_subject"],
                commit_body=commit_metadata["commit_body"],
                existing_note=existing_note,
            )
            mutation_surface = _after_commit_mutation_surface(resolved_checkpoint_kind)
            intent_text = _after_commit_intent(
                commit_short_sha=commit_metadata["commit_short_sha"],
                commit_subject=commit_metadata["commit_subject"],
                checkpoint_kind=resolved_checkpoint_kind,
            )

            if existing_note is not None and existing_note.state in {"closed", "promoted"}:
                is_followthrough = resolved_checkpoint_kind == "owner_followthrough"
                report = CheckpointAfterCommitReport(
                    status=(
                        "recorded_closed_session_followthrough"
                        if is_followthrough
                        else "skipped_closed_session"
                    ),
                    repo_root=str(repo_root_path),
                    repo_label=repo_label,
                    report_path=str(report_path),
                    commit_ref=commit_ref,
                    commit_sha=commit_metadata["commit_sha"],
                    commit_short_sha=commit_metadata["commit_short_sha"],
                    commit_subject=commit_metadata["commit_subject"],
                    commit_body=commit_metadata["commit_body"],
                    changed_paths=list(commit_metadata["changed_paths"]),
                    checkpoint_kind=resolved_checkpoint_kind,
                    mutation_surface=mutation_surface,
                    manual_review_requested=False,
                    captured_at=captured_at,
                    captured_at_local=captured_at_local,
                    captured_tz=captured_tz,
                    session_file=session_file_ref,
                    runtime_session_id=runtime_session_id,
                    runtime_session_created_at=runtime_session_created_at,
                    note_ref=_checkpoint_note_ref_for_capture(
                        self.workspace,
                        repo_root,
                        runtime_session_id=runtime_session_id,
                    ),
                    error_text=(
                        f"checkpoint note is {existing_note.state}; "
                        "owner follow-through was recorded without mutating the closed note"
                        if is_followthrough
                        else f"checkpoint note is {existing_note.state}; start a new runtime session or use owner_followthrough"
                    ),
                )
                _write_after_commit_report(report_path, report)
                return report

            if (
                existing_note is not None
                and resolved_checkpoint_kind == "owner_followthrough"
                and existing_note.review_status == "reviewed"
                and _has_reviewed_closeout_owner_handoff_for_repo(
                    self.workspace,
                    session_ref=existing_note.session_ref,
                    repo_label=repo_label,
                )
            ):
                report = CheckpointAfterCommitReport(
                    status="recorded_reviewed_closeout_followthrough",
                    repo_root=str(repo_root_path),
                    repo_label=repo_label,
                    report_path=str(report_path),
                    commit_ref=commit_ref,
                    commit_sha=commit_metadata["commit_sha"],
                    commit_short_sha=commit_metadata["commit_short_sha"],
                    commit_subject=commit_metadata["commit_subject"],
                    commit_body=commit_metadata["commit_body"],
                    changed_paths=list(commit_metadata["changed_paths"]),
                    checkpoint_kind=resolved_checkpoint_kind,
                    mutation_surface=mutation_surface,
                    manual_review_requested=False,
                    captured_at=captured_at,
                    captured_at_local=captured_at_local,
                    captured_tz=captured_tz,
                    session_file=session_file_ref,
                    runtime_session_id=runtime_session_id,
                    runtime_session_created_at=runtime_session_created_at,
                    note_ref=_checkpoint_note_ref_for_capture(
                        self.workspace,
                        repo_root,
                        runtime_session_id=runtime_session_id,
                    ),
                    error_text=(
                        "checkpoint note is reviewed and reviewed closeout already emitted "
                        f"a matching owner handoff for {repo_label}; owner follow-through "
                        "was recorded without mutating the reviewed note"
                    ),
                )
                _write_after_commit_report(report_path, report)
                return report

            skill_report = SkillsAPI(self.workspace).dispatch(
                repo_root=repo_root,
                phase="checkpoint",
                intent_text=intent_text,
                mutation_surface=mutation_surface,
                session_file=session_file_ref,
            )
            skill_report_path = str(_checkpoint_skill_report_path(self.workspace, repo_root))
            _write_skill_detection_report(
                Path(skill_report_path),
                skill_report.model_dump(mode="json"),
            )

            surface_report = self._surfaces.detect(
                repo_root=repo_root,
                phase="checkpoint",
                intent_text=intent_text,
                mutation_surface=mutation_surface,
                session_file=session_file_ref,
                skill_report_path=skill_report_path,
                checkpoint_kind=resolved_checkpoint_kind,
            )
            surface_report_path = str(paths.surface_report)
            observed_at, observed_at_local, observed_tz = _local_timestamp_parts()
            note = self.append(
                repo_root=repo_root,
                checkpoint_kind=resolved_checkpoint_kind,
                intent_text=intent_text,
                mutation_surface=mutation_surface,
                session_file=session_file_ref,
                skill_report_path=skill_report_path,
                surface_report=surface_report,
                surface_report_path=surface_report_path,
                manual_review_requested=True,
                commit_sha=commit_metadata["commit_sha"],
                commit_short_sha=commit_metadata["commit_short_sha"],
                agent_review_status="pending",
                auto_observation=_build_after_commit_auto_observation(
                    repo_root_path=repo_root_path,
                    repo_label=repo_label,
                    commit_ref=commit_ref,
                    commit_metadata=commit_metadata,
                    checkpoint_kind=resolved_checkpoint_kind,
                    mutation_surface=mutation_surface,
                    skill_report=skill_report,
                    surface_report=surface_report,
                    observed_at=observed_at,
                    observed_at_local=observed_at_local,
                    observed_tz=observed_tz,
                    skill_report_path=skill_report_path,
                    surface_report_path=surface_report_path,
                ),
                observed_at=observed_at,
                observed_at_local=observed_at_local,
                observed_tz=observed_tz,
            )
            note_ref = _checkpoint_note_ref_for_capture(
                self.workspace,
                repo_root,
                runtime_session_id=note.runtime_session_id,
            )
            report = CheckpointAfterCommitReport(
                status="captured",
                repo_root=str(repo_root_path),
                repo_label=repo_label,
                report_path=str(report_path),
                commit_ref=commit_ref,
                commit_sha=commit_metadata["commit_sha"],
                commit_short_sha=commit_metadata["commit_short_sha"],
                commit_subject=commit_metadata["commit_subject"],
                commit_body=commit_metadata["commit_body"],
                changed_paths=list(commit_metadata["changed_paths"]),
                checkpoint_kind=resolved_checkpoint_kind,
                mutation_surface=mutation_surface,
                captured_at=captured_at,
                captured_at_local=captured_at_local,
                captured_tz=captured_tz,
                session_file=session_file_ref,
                runtime_session_id=runtime_session_id,
                runtime_session_created_at=runtime_session_created_at,
                skill_report_path=skill_report_path,
                surface_report_path=surface_report_path,
                note_ref=note_ref,
                agent_review_required=True,
                agent_review_status="pending",
                agent_review_command=_agent_review_command(
                    repo_root=str(repo_root_path),
                    commit_ref=commit_metadata["commit_sha"] or commit_ref,
                    workspace_root=str(self.workspace.federation_root),
                ),
            )
            _write_after_commit_report(report_path, report)
            return report
        except Exception as exc:
            captured_at, captured_at_local, captured_tz = _local_timestamp_parts()
            failed_checkpoint_kind = _resolve_after_commit_checkpoint_kind(
                checkpoint_kind=checkpoint_kind,
                commit_subject=commit_metadata["commit_subject"],
                commit_body=commit_metadata["commit_body"],
                existing_note=None,
            )
            report_path = (
                _resolve_runtime_checkpoint_paths(
                    self.workspace,
                    repo_root=repo_root,
                    runtime_session_id=runtime_session_id,
                    migrate_legacy=True,
                ).post_commit_report
                if runtime_session_id is not None
                else post_commit_status_path(self.workspace, repo_label)
            )
            report = CheckpointAfterCommitReport(
                status="failed",
                repo_root=str(repo_root_path),
                repo_label=repo_label,
                report_path=str(report_path),
                commit_ref=commit_ref,
                commit_sha=commit_metadata["commit_sha"],
                commit_short_sha=commit_metadata["commit_short_sha"],
                commit_subject=commit_metadata["commit_subject"],
                commit_body=commit_metadata["commit_body"],
                changed_paths=list(commit_metadata["changed_paths"]),
                checkpoint_kind=failed_checkpoint_kind,
                mutation_surface=_after_commit_mutation_surface(failed_checkpoint_kind),
                captured_at=captured_at,
                captured_at_local=captured_at_local,
                captured_tz=captured_tz,
                session_file=(
                    str(session_path)
                    if session_path is not None
                    else str(session_file)
                    if session_file is not None
                    else None
                ),
                runtime_session_id=runtime_session_id,
                runtime_session_created_at=runtime_session_created_at,
                skill_report_path=skill_report_path,
                surface_report_path=surface_report_path,
                note_ref=note_ref,
                error_text=str(exc),
            )
            _write_after_commit_report(report_path, report)
            if runtime_session_id is not None:
                _write_after_commit_report(post_commit_status_path(self.workspace, repo_label), report)
            return report

    def review_note(
        self,
        *,
        repo_root: str,
        commit_ref: str = "HEAD",
        summary: str | None = None,
        auto_fill: bool = False,
        findings: list[str] | None = None,
        candidate_notes: list[str] | None = None,
        stats_hints: list[str] | None = None,
        mechanic_hints: list[str] | None = None,
        closeout_questions: list[str] | None = None,
        evidence_refs: list[str] | None = None,
        next_owner_moves: list[str] | None = None,
        applied_skill_names: list[str] | None = None,
        session_file: str | None = None,
    ) -> SessionCheckpointNote:
        repo_root_path = _resolve_context_root(self.workspace, repo_root)
        repo_label = _resolve_context_label(self.workspace, repo_root)
        commit_metadata = read_git_commit_metadata(repo_root_path, commit_ref)
        session_path, runtime_session = probe_existing_checkpoint_runtime_session(
            workspace=self.workspace,
            session_file=session_file,
        )
        if runtime_session is None and auto_fill:
            recovered_session = _recover_skipped_after_commit_for_review(
                workspace=self.workspace,
                repo_root=repo_root,
                repo_label=repo_label,
                commit_ref=commit_ref,
                commit_metadata=commit_metadata,
                session_path=session_path,
                capture_after_commit=self.after_commit,
            )
            if recovered_session is not None:
                session_path, runtime_session = recovered_session
        if runtime_session is None:
            raise SurfaceNotFound("checkpoint agent review requires an existing active runtime session")

        paths = _resolve_runtime_checkpoint_paths(
            self.workspace,
            repo_root=repo_root,
            runtime_session_id=runtime_session.session_id,
            migrate_legacy=True,
        )
        if not paths.jsonl.exists():
            raise SurfaceNotFound(f"no checkpoint note exists yet for {paths.repo_label}")

        current_note = self.status(repo_root=repo_root, session_file=str(session_path))
        auto_observation = _matching_auto_observation(
            note=current_note,
            commit_ref=commit_ref,
            commit_sha=cast(str | None, commit_metadata.get("commit_sha")),
            commit_short_sha=cast(str | None, commit_metadata.get("commit_short_sha")),
        )
        history_entry = _matching_checkpoint_history_entry(
            note=current_note,
            commit_ref=commit_ref,
            commit_sha=cast(str | None, commit_metadata.get("commit_sha")),
            commit_short_sha=cast(str | None, commit_metadata.get("commit_short_sha")),
        )
        resolved_summary = summary.strip() if isinstance(summary, str) and summary.strip() else None
        if auto_fill:
            if auto_observation is None and history_entry is None:
                raise SurfaceNotFound(
                    "checkpoint auto review requires matching checkpoint history for the commit"
                )
            if resolved_summary is None:
                resolved_summary = _auto_review_summary(
                    auto_observation=auto_observation,
                    history_entry=history_entry,
                    commit_ref=commit_ref,
                    commit_subject=cast(str | None, commit_metadata.get("commit_subject")),
                    commit_short_sha=cast(str | None, commit_metadata.get("commit_short_sha")),
                )
        elif resolved_summary is None:
            raise ValueError("checkpoint agent review requires a non-empty summary")

        reviewed_at, reviewed_at_local, reviewed_tz = _local_timestamp_parts()
        review_id = (
            "agent-review:"
            f"{_safe_name(commit_metadata['commit_short_sha'] or commit_ref)}:"
            f"{reviewed_at.strftime('%Y%m%dT%H%M%SZ')}"
        )
        review_evidence_refs = _dedupe_strings(
            [
                *(evidence_refs or []),
                str(paths.post_commit_report),
                str(paths.note_json),
                str(paths.surface_report),
                _checkpoint_skill_report_path(self.workspace, repo_root).as_posix(),
                *(auto_observation.evidence_refs if auto_observation is not None else []),
                *(
                    _history_auto_review_evidence_refs(history_entry)
                    if auto_fill and history_entry is not None
                    else []
                ),
                *(
                    [f"auto-observation:{auto_observation.observation_id}"]
                    if auto_observation is not None
                    else []
                ),
            ]
        )
        review = SessionCheckpointAgentReview(
            review_id=review_id,
            auto_observation_ref=(
                auto_observation.observation_id if auto_observation is not None else None
            ),
            reviewed_at=reviewed_at,
            reviewed_at_local=reviewed_at_local,
            reviewed_tz=reviewed_tz,
            repo_root=str(repo_root_path),
            repo_label=repo_label,
            commit_ref=commit_ref,
            commit_sha=commit_metadata["commit_sha"],
            commit_short_sha=commit_metadata["commit_short_sha"],
            commit_subject=commit_metadata["commit_subject"],
            summary=cast(str, resolved_summary),
            applied_skill_names=_dedupe_strings(
                [
                    *(applied_skill_names or []),
                    *(auto_observation.applied_skill_names if auto_observation is not None else []),
                ]
            ),
            findings=_merge_auto_review_items(
                explicit_items=findings,
                auto_items=_auto_review_findings(
                    auto_observation=auto_observation,
                    history_entry=history_entry,
                    auto_fill=auto_fill,
                ),
            ),
            candidate_notes=_merge_auto_review_items(
                explicit_items=candidate_notes,
                auto_items=_auto_review_candidate_notes(
                    auto_observation=auto_observation,
                    history_entry=history_entry,
                    auto_fill=auto_fill,
                ),
            ),
            stats_hints=_merge_auto_review_items(
                explicit_items=stats_hints,
                auto_items=_auto_review_stats_hints(
                    auto_observation=auto_observation,
                    history_entry=history_entry,
                    auto_fill=auto_fill,
                ),
            ),
            mechanic_hints=_merge_auto_review_items(
                explicit_items=mechanic_hints,
                auto_items=_auto_review_mechanic_hints(
                    auto_observation=auto_observation,
                    history_entry=history_entry,
                    auto_fill=auto_fill,
                ),
            ),
            closeout_questions=_merge_auto_review_items(
                explicit_items=closeout_questions,
                auto_items=_auto_review_closeout_questions(
                    auto_observation=auto_observation,
                    history_entry=history_entry,
                    auto_fill=auto_fill,
                ),
            ),
            evidence_refs=review_evidence_refs,
            next_owner_moves=_merge_auto_review_items(
                explicit_items=next_owner_moves,
                auto_items=_auto_review_next_owner_moves(
                    auto_observation=auto_observation,
                    history_entry=history_entry,
                    auto_fill=auto_fill,
                ),
            ),
        )
        payload = {
            "session_ref": self.peek_status(repo_root=repo_root, session_file=str(session_path)).session_ref,
            "runtime_session_id": runtime_session.session_id,
            "runtime_session_created_at": runtime_session.created_at.astimezone(UTC).isoformat().replace("+00:00", "Z"),
            "repo_root": str(repo_root_path),
            "repo_label": repo_label,
            "agent_review": review.model_dump(mode="json"),
        }
        paths.jsonl.parent.mkdir(parents=True, exist_ok=True)
        with paths.jsonl.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=True) + "\n")

        note = self.status(repo_root=repo_root, session_file=str(session_path))
        _mark_after_commit_report_reviewed(paths.post_commit_report, review=review)
        _mark_after_commit_report_reviewed(post_commit_status_path(self.workspace, repo_label), review=review)
        return note

    def hook_status(
        self,
        *,
        repo_name: str,
        hook_name: CheckpointHookName,
    ) -> CheckpointHookStatus:
        hook_status = checkpoint_hook_status_parts(
            self.workspace,
            repo_name=repo_name,
            hook_name=hook_name,
        )
        return CheckpointHookStatus(
            repo=repo_name,
            hook_name=hook_name,
            repo_root=str(hook_status.repo_root),
            hook_path=str(hook_status.hook_path),
            template_path=str(hook_status.template_path),
            template_version=hook_status.template_version,
            status=hook_status.status,
        )

    def install_hook(
        self,
        *,
        repo_name: str,
        hook_name: CheckpointHookName,
        overwrite: bool = False,
    ) -> CheckpointHookInstallResult:
        status = self.hook_status(repo_name=repo_name, hook_name=hook_name)
        hook_path = Path(status.hook_path)
        action: Literal["installed", "updated", "unchanged"]
        if status.status == "missing":
            hook_path.parent.mkdir(parents=True, exist_ok=True)
            hook_path.write_text(render_checkpoint_hook(self.workspace, hook_name), encoding="utf-8")
            hook_path.chmod(0o755)
            action = "installed"
        elif status.status == "stale" and overwrite:
            hook_path.write_text(render_checkpoint_hook(self.workspace, hook_name), encoding="utf-8")
            hook_path.chmod(0o755)
            action = "updated"
        else:
            action = "unchanged"
        return CheckpointHookInstallResult(
            repo=repo_name,
            hook_name=hook_name,
            repo_root=status.repo_root,
            hook_path=status.hook_path,
            template_path=status.template_path,
            template_version=status.template_version,
            status_before=status.status,
            action=action,
        )

    def git_boundary_check(
        self,
        *,
        repo_root: str,
        boundary: Literal["push", "merge"],
        session_file: str | None = None,
    ) -> CheckpointGitBoundaryCheck:
        repo_root_path = _resolve_context_root(self.workspace, repo_root)
        repo_label = _resolve_context_label(self.workspace, repo_root)
        session_path, runtime_metadata = probe_checkpoint_runtime_session(
            workspace=self.workspace,
            session_file=session_file,
        )
        runtime_session_id = cast(str | None, runtime_metadata["runtime_session_id"])
        if runtime_session_id is None:
            unresolved_skipped_status = _unresolved_skipped_post_commit_status_for_boundary(
                self.workspace,
                repo_root_path=repo_root_path,
                repo_label=repo_label,
            )
            if unresolved_skipped_status is not None:
                status_path, skipped_report = unresolved_skipped_status
                pending_ref = _skipped_after_commit_pending_ref(skipped_report)
                return CheckpointGitBoundaryCheck(
                    repo_root=str(repo_root_path),
                    repo_label=repo_label,
                    boundary=boundary,
                    status="blocked_unresolved_checkpoint",
                    post_commit_status_ref=str(status_path),
                    pending_refs=[pending_ref],
                    blocking_repo_labels=[repo_label],
                    required_action=_skipped_after_commit_required_action(
                        repo_root_path=repo_root_path,
                        workspace_root=self.workspace.federation_root,
                        boundary=boundary,
                        report=skipped_report,
                    ),
                )
            return CheckpointGitBoundaryCheck(
                repo_root=str(repo_root_path),
                repo_label=repo_label,
                boundary=boundary,
                status="clear_no_active_session",
            )

        primary_note = _peek_runtime_checkpoint_note(
            self,
            repo_root=repo_root,
            session_file=str(session_path),
        )
        if primary_note is not None:
            session_records = _load_runtime_checkpoint_notes_for_closeout(
                self,
                repo_root=repo_root,
                resolved_session_ref=primary_note.session_ref,
                primary_note=primary_note,
            )
        else:
            session_records = _load_runtime_scoped_checkpoint_notes(
                self,
                runtime_session_id=runtime_session_id,
            )
        if not session_records:
            return CheckpointGitBoundaryCheck(
                repo_root=str(repo_root_path),
                repo_label=repo_label,
                boundary=boundary,
                status="clear_no_note",
                runtime_session_id=runtime_session_id,
            )

        preferred_note_ref: str | None = None
        pending_refs: list[str] = []
        blocking_repo_labels: list[str] = []
        blocking_note_refs: list[str] = []
        for paths, note in session_records:
            note_ref = str(paths.note_json)
            if preferred_note_ref is None or paths.repo_label == repo_label:
                preferred_note_ref = note_ref
            note_pending_refs = _dedupe_strings(note.agent_review_pending_refs)
            if not note_pending_refs:
                continue
            pending_refs.extend(note_pending_refs)
            blocking_repo_labels.append(paths.repo_label)
            blocking_note_refs.append(note_ref)

        pending_refs = _dedupe_strings(pending_refs)
        blocking_repo_labels = _dedupe_strings(blocking_repo_labels)
        if pending_refs:
            refs_preview = ", ".join(pending_refs[:5])
            if len(pending_refs) > 5:
                refs_preview += f" (+{len(pending_refs) - 5} more)"
            blocking_preview = ", ".join(blocking_repo_labels[:5])
            if len(blocking_repo_labels) > 5:
                blocking_preview += f" (+{len(blocking_repo_labels) - 5} more)"
            return CheckpointGitBoundaryCheck(
                repo_root=str(repo_root_path),
                repo_label=repo_label,
                boundary=boundary,
                status="blocked_pending_review",
                runtime_session_id=runtime_session_id,
                note_ref=blocking_note_refs[0] if blocking_note_refs else preferred_note_ref,
                pending_refs=pending_refs,
                blocking_repo_labels=blocking_repo_labels,
                required_action=(
                    "pending checkpoint agent review blocks "
                    f"{boundary}; blocking repos: {blocking_preview}; "
                    f"run `aoa checkpoint review-note --auto` for: {refs_preview}"
                ),
            )
        return CheckpointGitBoundaryCheck(
            repo_root=str(repo_root_path),
            repo_label=repo_label,
            boundary=boundary,
            status="clear",
            runtime_session_id=runtime_session_id,
            note_ref=preferred_note_ref,
        )

    def lifecycle_audit(
        self,
        *,
        repo_root: str | None = None,
        session_file: str | None = None,
        write_index: bool = False,
    ) -> CheckpointLifecycleAuditReport:
        return _audit_checkpoint_lifecycle(
            workspace=self.workspace,
            repo_root=repo_root,
            session_file=session_file,
            write_index=write_index,
        )

    def close_archive(
        self,
        *,
        repo_root: str | None = None,
        session_file: str | None = None,
        runtime_session_id: str | None = None,
        dry_run: bool = True,
        include_stale: bool = False,
    ) -> CheckpointLifecycleArchiveResult:
        return _close_archive_checkpoint_lifecycle(
            workspace=self.workspace,
            repo_root=repo_root,
            session_file=session_file,
            runtime_session_id=runtime_session_id,
            dry_run=dry_run,
            include_stale=include_stale,
        )

    def reconcile_sessions(
        self,
        *,
        repo_root: str | None = None,
        session_file: str | None = None,
        runtime_session_id: str | None = None,
        session_filter: str | None = None,
        since: str | None = None,
        until: str | None = None,
        dry_run: bool = True,
        write_index: bool = True,
    ) -> CheckpointSessionReconcileResult:
        return _reconcile_closed_checkpoint_sessions(
            workspace=self.workspace,
            repo_root=repo_root,
            session_file=session_file,
            runtime_session_id=runtime_session_id,
            session_filter=session_filter,
            since=since,
            until=until,
            dry_run=dry_run,
            write_index=write_index,
        )

    def backlog_audit(
        self,
        *,
        repo_root: str | None = None,
        session_file: str | None = None,
        write_index: bool = False,
    ) -> CheckpointBacklogAuditReport:
        return _audit_checkpoint_backlog(
            workspace=self.workspace,
            repo_root=repo_root,
            session_file=session_file,
            write_index=write_index,
        )

    def candidate_intelligence(
        self,
        *,
        repo_root: str,
        session_file: str | None = None,
        sample_limit: int = 0,
        write_index: bool = False,
    ) -> CandidateIntelligenceReport:
        note = self.status(repo_root=repo_root, session_file=session_file)
        report = _build_candidate_intelligence_from_note(
            workspace=self.workspace,
            repo_root=repo_root,
            action_events=list(note.action_events),
            action_signatures=list(note.action_signatures),
            candidate_clusters=list(note.candidate_clusters),
            runtime_session_ids=[note.runtime_session_id] if note.runtime_session_id else [],
            sample_limit=sample_limit,
        )
        if write_index:
            index_path = _write_checkpoint_candidate_intelligence_index(
                workspace=self.workspace,
                report=report,
            )
            report = report.model_copy(update={"generated_index_ref": str(index_path)})
        return report

    def carrier_intelligence(
        self,
        *,
        repo_root: str,
        session_file: str | None = None,
        sample_limit: int = 0,
        write_index: bool = False,
    ) -> CarrierIntelligenceReport:
        candidate_report = self.candidate_intelligence(
            repo_root=repo_root,
            session_file=session_file,
            sample_limit=0,
            write_index=False,
        )
        report = _build_carrier_intelligence_from_candidate_report(
            candidate_report=candidate_report,
            sample_limit=sample_limit,
        )
        if write_index:
            index_path = _write_checkpoint_carrier_candidate_intelligence_index(
                workspace=self.workspace,
                report=report,
            )
            report = report.model_copy(update={"generated_index_ref": str(index_path)})
        return report

    def status(self, *, repo_root: str, session_file: str | None = None) -> SessionCheckpointNote:
        runtime_session_metadata = peek_checkpoint_runtime_session(
            workspace=self.workspace,
            session_file=session_file,
        )
        runtime_session_id = cast(str | None, runtime_session_metadata["runtime_session_id"])
        if runtime_session_id is None and session_file is not None:
            runtime_session_id, _ = ensure_checkpoint_runtime_session(
                workspace=self.workspace,
                session_file=session_file,
            )
        paths = _resolve_runtime_checkpoint_paths(
            self.workspace,
            repo_root=repo_root,
            runtime_session_id=runtime_session_id,
            migrate_legacy=True,
        )
        if not paths.jsonl.exists():
            raise SurfaceNotFound(f"no checkpoint note exists yet for {paths.repo_label}")

        note = _build_checkpoint_note(paths)
        if _should_hide_current_checkpoint_note(note, runtime_session_id=runtime_session_id):
            _archive_current_checkpoint(paths)
            raise SurfaceNotFound(f"no active checkpoint note exists yet for {paths.repo_label}")
        paths.note_json.parent.mkdir(parents=True, exist_ok=True)
        paths.note_json.write_text(note.model_dump_json(indent=2) + "\n", encoding="utf-8")
        paths.note_md.write_text(_render_checkpoint_note_markdown(note, repo_label=paths.repo_label), encoding="utf-8")
        return note

    def peek_status(self, *, repo_root: str, session_file: str | None = None) -> SessionCheckpointNote:
        runtime_session_metadata = peek_checkpoint_runtime_session(
            workspace=self.workspace,
            session_file=session_file,
        )
        runtime_session_id = cast(str | None, runtime_session_metadata["runtime_session_id"])
        paths = _resolve_runtime_checkpoint_paths(
            self.workspace,
            repo_root=repo_root,
            runtime_session_id=runtime_session_id,
            migrate_legacy=False,
        )
        if not paths.jsonl.exists():
            raise SurfaceNotFound(f"no checkpoint note exists yet for {paths.repo_label}")

        note = _build_checkpoint_note(paths)
        if _should_hide_current_checkpoint_note(note, runtime_session_id=runtime_session_id):
            raise SurfaceNotFound(f"no active checkpoint note exists yet for {paths.repo_label}")
        return note

    def promote(
        self,
        *,
        repo_root: str,
        target: Literal["dionysus-note", "harvest-handoff"],
        session_file: str | None = None,
    ) -> SessionCheckpointPromotion:
        if target not in PROMOTION_TARGETS:
            raise ValueError(f"unsupported target {target!r}")

        note = self.status(repo_root=repo_root, session_file=session_file)
        paths = _resolve_runtime_checkpoint_paths(
            self.workspace,
            repo_root=repo_root,
            runtime_session_id=note.runtime_session_id,
            migrate_legacy=True,
        )
        if not note.candidate_clusters:
            raise SurfaceNotFound("cannot promote an empty checkpoint note")
        if note.agent_review_pending_refs:
            refs_preview = ", ".join(note.agent_review_pending_refs[:5])
            if len(note.agent_review_pending_refs) > 5:
                refs_preview += f" (+{len(note.agent_review_pending_refs) - 5} more)"
            raise ValueError(
                "pending checkpoint agent review blocks checkpoint promotion; "
                f"run `aoa checkpoint review-note --auto` for: {refs_preview}"
            )

        new_state: Literal["collecting", "reviewable", "promoted", "closed"]
        if target == "dionysus-note":
            output_refs = promote_to_dionysus(self.workspace, paths=paths, note=note)
            new_state = "promoted"
            note.review_status = "reviewed"
        else:
            output_refs = write_harvest_handoff(paths=paths, note=note)
            new_state = "closed"
            note.review_status = "reviewed"

        note.state = new_state  # type: ignore[assignment]
        note.evidence_refs = list(dict.fromkeys([*note.evidence_refs, *output_refs]))
        note.next_owner_moves = _dedupe_strings(
            [
                *note.next_owner_moves,
                "use the explicit session-harvest family after reviewed closeout",
            ]
        )
        paths.note_json.write_text(note.model_dump_json(indent=2) + "\n", encoding="utf-8")
        paths.note_md.write_text(_render_checkpoint_note_markdown(note, repo_label=paths.repo_label), encoding="utf-8")

        return SessionCheckpointPromotion(
            session_ref=note.session_ref,
            target=target,
            promoted_at=(promoted_parts := _local_timestamp_parts())[0],
            promoted_at_local=promoted_parts[1],
            promoted_tz=promoted_parts[2],
            source_note_ref=str(paths.note_json),
            output_refs=output_refs,
            resulting_state=new_state,
        )

    def build_closeout_context(
        self,
        *,
        repo_root: str,
        reviewed_artifact_path: str,
        session_ref: str | None = None,
        receipt_paths: list[str] | None = None,
        receipt_dirs: list[str] | None = None,
        surface_handoff_path: str | None = None,
        session_file: str | None = None,
    ) -> CheckpointCloseoutContext:
        reviewed_artifact = Path(reviewed_artifact_path).expanduser().resolve()
        if not reviewed_artifact.exists():
            raise FileNotFoundError(f"missing reviewed artifact: {reviewed_artifact}")

        runtime_session_metadata = load_checkpoint_runtime_session(
            workspace=self.workspace,
            session_file=session_file,
        )
        active_runtime_session_id = cast(str | None, runtime_session_metadata["runtime_session_id"])
        paths = _resolve_runtime_checkpoint_paths(
            self.workspace,
            repo_root=repo_root,
            runtime_session_id=active_runtime_session_id,
            migrate_legacy=True,
        )
        note = _load_runtime_checkpoint_note(self, repo_root=repo_root, session_file=session_file)
        handoff = _load_reviewed_surface_handoff(
            workspace=self.workspace,
            repo_root=repo_root,
            handoff_path=surface_handoff_path,
        )
        collected_receipt_paths = _collect_receipt_paths(
            receipt_paths=receipt_paths or [],
            receipt_dirs=receipt_dirs or [],
        )
        resolved_session_ref = _resolve_closeout_session_ref(
            explicit_session_ref=session_ref,
            checkpoint_note=note,
            surface_handoff=handoff,
            reviewed_artifact=reviewed_artifact,
            receipt_paths=collected_receipt_paths,
        )
        _validate_repo_root_closeout_scope(
            checkpoint_note=note,
            resolved_session_ref=resolved_session_ref,
        )
        note_records = _load_runtime_checkpoint_notes_for_closeout(
            self,
            repo_root=repo_root,
            resolved_session_ref=resolved_session_ref,
            primary_note=note,
        )
        aggregated_notes = [candidate_note for _, candidate_note in note_records]
        aggregated_note_refs = [str(candidate_paths.note_json) for candidate_paths, _ in note_records]
        pending_agent_review_refs = _closeout_pending_agent_review_refs(aggregated_notes)
        if pending_agent_review_refs:
            refs_preview = ", ".join(pending_agent_review_refs[:5])
            if len(pending_agent_review_refs) > 5:
                refs_preview += f" (+{len(pending_agent_review_refs) - 5} more)"
            raise ValueError(
                "pending checkpoint agent review blocks reviewed closeout; "
                f"run `aoa checkpoint review-note --auto` for: {refs_preview}"
            )
        runtime_session_id = next(
            (
                candidate_note.runtime_session_id
                for candidate_note in aggregated_notes
                if candidate_note.runtime_session_id is not None
            ),
            (
                note.runtime_session_id
                if note is not None and note.runtime_session_id is not None
                else cast(str | None, runtime_session_metadata["runtime_session_id"])
            ),
        )
        session_trace_ref = cast(str | None, runtime_session_metadata["session_trace_ref"])
        session_trace_thread_id = cast(str | None, runtime_session_metadata["session_trace_thread_id"])
        session_memory_ref, session_memory_freshness = _resolve_checkpoint_session_memory(
            workspace=self.workspace,
            session_trace_thread_id=session_trace_thread_id,
            session_trace_ref=session_trace_ref,
        )

        notes: list[str] = []
        note_ref: str | None = None
        if str(paths.note_json) in aggregated_note_refs:
            note_ref = str(paths.note_json)
        elif note is not None:
            notes.append(
                "ignored the local checkpoint note because its session_ref did not match the reviewed closeout session"
            )
        if len(aggregated_note_refs) > 1:
            notes.append(
                "aggregated runtime-session checkpoint notes across repo labels before building the reviewed closeout context"
            )

        handoff_ref: str | None = None
        if handoff is not None and handoff.session_ref == resolved_session_ref:
            handoff_ref = str(
                _surface_handoff_path(self.workspace, repo_root, override=surface_handoff_path)
            )
        elif handoff is not None:
            notes.append(
                "ignored the reviewed surface closeout handoff because its session_ref did not match the reviewed closeout session"
            )
            handoff = None

        checkpoint_review_carry = _collect_closeout_review_carry(aggregated_notes)
        shortlisted_clusters = _closeout_candidate_clusters(notes=aggregated_notes, handoff=handoff)
        repo_scope = _dedupe_strings(
            [
                paths.repo_label,
                *(scope for candidate_note in aggregated_notes for scope in candidate_note.repo_scope),
                *(cluster.owner_hint for cluster in shortlisted_clusters),
            ]
        )
        candidate_map = CloseoutContextCandidateMap(
            harvest_candidate_ids=_dedupe_strings(
                [
                    candidate_id
                    for candidate_note in aggregated_notes
                    for candidate_id in candidate_note.harvest_candidate_ids
                ]
            ),
            progression_candidate_ids=_dedupe_strings(
                [
                    candidate_id
                    for candidate_note in aggregated_notes
                    for candidate_id in candidate_note.progression_candidate_ids
                ]
            ),
            upgrade_candidate_ids=_dedupe_strings(
                [
                    candidate_id
                    for candidate_note in aggregated_notes
                    for candidate_id in candidate_note.upgrade_candidate_ids
                ]
            ),
        )
        candidate_lineage_map = _collect_candidate_lineage_hints(shortlisted_clusters)
        owner_followthrough_map = _build_owner_followthrough_map(candidate_lineage_map)
        ordered_skill_plan = _derive_closeout_skill_plan(notes=aggregated_notes, handoff=handoff)
        followthrough_decision = _build_closeout_followthrough_decision(
            session_ref=resolved_session_ref,
            reviewed_closeout_context_ref=str(paths.closeout_context),
            clusters=shortlisted_clusters,
            progression_axis_signals=_merge_progression_axis_signals(
                [
                    signal
                    for candidate_note in aggregated_notes
                    for signal in candidate_note.progression_axis_signals
                ]
            ),
        )
        if not aggregated_notes:
            notes.append("no matching local checkpoint note was available; the reviewed artifact becomes the primary execution source")
        if handoff is None:
            notes.append("no matching reviewed surface closeout handoff was available; closeout will reread the reviewed artifact without a reviewed surface shortlist")
        if session_trace_ref is None:
            notes.append("no live Codex rollout trace was available from the active runtime session; closeout will rely on the reviewed artifact plus checkpoint evidence only")
        else:
            notes.append("bound closeout evidence to the live Codex rollout trace referenced by the active runtime session")
        if session_memory_ref is None:
            notes.append("no aoa-session-memory archive ref was available for the active Codex thread; closeout will keep using reviewed artifact and checkpoint-local evidence")
        else:
            notes.append(
                "bound closeout evidence to the aoa-session-memory archive as route evidence, not reviewed truth"
            )
        for caution in session_memory_freshness.cautions:
            notes.append(f"session-memory freshness caution: {caution}")
        if not collected_receipt_paths:
            notes.append("no prior receipt refs were supplied; closeout execution will rely on the reviewed artifact and any local checkpoint evidence only")
        if checkpoint_review_carry.review_refs:
            notes.append(
                f"bound {len(checkpoint_review_carry.review_refs)} agent-authored checkpoint review(s) into the closeout context so the final reread can revisit semantic findings and questions"
            )
        notes.append(
            "checkpoint closeout bridge builds mechanical artifacts only; a Codex agent must still apply the listed skills by rereading session evidence before treating outputs as final analysis"
        )

        built_at, built_at_local, built_tz = _local_timestamp_parts()
        context = CheckpointCloseoutContext(
            session_ref=resolved_session_ref,
            built_at=built_at,
            built_at_local=built_at_local,
            built_tz=built_tz,
            repo_root=str(_resolve_context_root(self.workspace, repo_root)),
            reviewed_artifact_ref=str(reviewed_artifact),
            runtime_session_id=runtime_session_id,
            session_trace_ref=session_trace_ref,
            session_trace_thread_id=session_trace_thread_id,
            session_memory_ref=session_memory_ref,
            session_memory_freshness=session_memory_freshness,
            checkpoint_note_ref=note_ref,
            checkpoint_note_refs=aggregated_note_refs,
            surface_handoff_ref=handoff_ref,
            receipt_refs=[str(path) for path in collected_receipt_paths],
            repo_scope=repo_scope,
            candidate_map=candidate_map,
            checkpoint_review_carry=checkpoint_review_carry,
            candidate_lineage_map=candidate_lineage_map,
            owner_followthrough_map=owner_followthrough_map,
            followthrough_decision=followthrough_decision,
            progression_axis_signals=_merge_progression_axis_signals(
                [
                    signal
                    for candidate_note in aggregated_notes
                    for signal in candidate_note.progression_axis_signals
                ]
            ),
            ordered_skill_plan=ordered_skill_plan,
            notes=notes,
        )
        write_json(paths.closeout_context, context.model_dump(mode="json"))
        return context

    def execute_closeout_chain(
        self,
        *,
        repo_root: str,
        reviewed_artifact_path: str,
        session_ref: str | None = None,
        receipt_paths: list[str] | None = None,
        receipt_dirs: list[str] | None = None,
        surface_handoff_path: str | None = None,
        session_file: str | None = None,
    ) -> CheckpointCloseoutExecutionReport:
        context = self.build_closeout_context(
            repo_root=repo_root,
            reviewed_artifact_path=reviewed_artifact_path,
            session_ref=session_ref,
            receipt_paths=receipt_paths,
            receipt_dirs=receipt_dirs,
            surface_handoff_path=surface_handoff_path,
            session_file=session_file,
        )
        paths = _resolve_runtime_checkpoint_paths(
            self.workspace,
            repo_root=repo_root,
            runtime_session_id=context.runtime_session_id,
            migrate_legacy=False,
        )
        execution_dir = paths.closeout_artifacts / _safe_name(context.session_ref)
        execution_dir.mkdir(parents=True, exist_ok=True)

        reviewed_artifact_path_obj = Path(context.reviewed_artifact_ref)
        reviewed_artifact_evidence = _merge_closeout_evidence(
            primary=_merge_closeout_evidence(
                primary=_read_reviewed_artifact(reviewed_artifact_path_obj),
                secondary=(
                    _read_session_trace(Path(context.session_trace_ref).expanduser().resolve())
                    if context.session_trace_ref is not None
                    else None
                ),
            ),
            secondary=_session_memory_evidence_from_ref(context.session_memory_ref),
        )
        notes = _load_context_checkpoint_notes(context)
        handoff = _load_context_surface_handoff(context)
        receipt_payloads = _load_receipt_payloads(context.receipt_refs)
        shortlisted_clusters = _closeout_candidate_clusters(notes=notes, handoff=handoff)

        executed_steps: list[CloseoutExecutionStep] = []
        produced_artifact_refs: list[str] = []
        produced_receipt_refs: list[str] = []

        donor_outputs = _build_donor_harvest_outputs(
            context=context,
            reviewed_artifact=reviewed_artifact_path_obj,
            reviewed_artifact_evidence=reviewed_artifact_evidence,
            shortlisted_clusters=shortlisted_clusters,
            receipt_payloads=receipt_payloads,
            output_dir=execution_dir,
        )
        executed_steps.append(
            CloseoutExecutionStep(
                skill_name="aoa-session-donor-harvest",
                status="executed",
                reason="mechanical bridge artifact build for donor-harvest-shaped output; final donor harvest analysis still requires the Codex agent to apply the skill protocol against reviewed session evidence",
                artifact_refs=donor_outputs["artifact_refs"],
                receipt_refs=donor_outputs["receipt_refs"],
            )
        )
        produced_artifact_refs.extend(donor_outputs["artifact_refs"])
        produced_receipt_refs.extend(donor_outputs["receipt_refs"])

        progression_outputs = _build_progression_lift_outputs(
            context=context,
            reviewed_artifact=reviewed_artifact_path_obj,
            reviewed_artifact_evidence=reviewed_artifact_evidence,
            donor_packet=donor_outputs["packet"],
            shortlisted_clusters=shortlisted_clusters,
            receipt_payloads=receipt_payloads,
            output_dir=execution_dir,
        )
        executed_steps.append(
            CloseoutExecutionStep(
                skill_name="aoa-session-progression-lift",
                status="executed",
                reason="mechanical bridge artifact build for progression-lift-shaped output; final progression analysis still requires the Codex agent to apply the skill protocol against reviewed session evidence",
                artifact_refs=progression_outputs["artifact_refs"],
                receipt_refs=progression_outputs["receipt_refs"],
            )
        )
        produced_artifact_refs.extend(progression_outputs["artifact_refs"])
        produced_receipt_refs.extend(progression_outputs["receipt_refs"])

        quest_outputs = _build_quest_harvest_outputs(
            context=context,
            reviewed_artifact=reviewed_artifact_path_obj,
            reviewed_artifact_evidence=reviewed_artifact_evidence,
            donor_packet=donor_outputs["packet"],
            progression_packet=progression_outputs["packet"],
            shortlisted_clusters=shortlisted_clusters,
            receipt_payloads=receipt_payloads,
            output_dir=execution_dir,
        )
        executed_steps.append(
            CloseoutExecutionStep(
                skill_name="aoa-quest-harvest",
                status="executed",
                reason="mechanical bridge artifact build for quest-harvest-shaped output; final quest triage still requires the Codex agent to apply the skill protocol against reviewed session evidence",
                artifact_refs=quest_outputs["artifact_refs"],
                receipt_refs=quest_outputs["receipt_refs"],
            )
        )
        produced_artifact_refs.extend(quest_outputs["artifact_refs"])
        produced_receipt_refs.extend(quest_outputs["receipt_refs"])

        owner_handoff_path, owner_follow_through_briefs, workflow_follow_through_briefs = (
            _write_checkpoint_owner_handoff(
                workspace=self.workspace,
                closeout_context_ref=paths.closeout_context,
                context=context,
                donor_outputs=donor_outputs,
                quest_outputs=quest_outputs,
                reviewed_artifact=reviewed_artifact_path_obj,
            )
        )
        if owner_handoff_path is not None:
            produced_artifact_refs.append(str(owner_handoff_path))

        executed_at, executed_at_local, executed_tz = _local_timestamp_parts()
        report = CheckpointCloseoutExecutionReport(
            session_ref=context.session_ref,
            executed_at=executed_at,
            executed_at_local=executed_at_local,
            executed_tz=executed_tz,
            reviewed_artifact_ref=context.reviewed_artifact_ref,
            runtime_session_id=context.runtime_session_id,
            session_trace_ref=context.session_trace_ref,
            session_trace_thread_id=context.session_trace_thread_id,
            session_memory_ref=context.session_memory_ref,
            session_memory_freshness=context.session_memory_freshness,
            checkpoint_note_ref=context.checkpoint_note_ref,
            checkpoint_note_refs=list(context.checkpoint_note_refs),
            surface_handoff_ref=context.surface_handoff_ref,
            context_ref=str(paths.closeout_context),
            owner_handoff_path=str(owner_handoff_path) if owner_handoff_path is not None else None,
            owner_follow_through_briefs=owner_follow_through_briefs,
            workflow_follow_through_briefs=workflow_follow_through_briefs,
            executed_skills=executed_steps,
            skipped_skills=[],
            produced_artifact_refs=_dedupe_strings(produced_artifact_refs),
            produced_receipt_refs=_dedupe_strings(produced_receipt_refs),
            final_stop_reason=(
                "Mechanical checkpoint-closeout bridge artifacts were built; final session analysis requires agent-led skill application over reviewed evidence, and owner-local publication plus stats refresh remain downstream steps."
            ),
        )
        write_json(paths.closeout_execution_report, report.model_dump(mode="json"))
        return report


def _checkpoint_paths(
    workspace: Workspace,
    repo_root: str,
    *,
    runtime_session_id: str | None = None,
) -> CheckpointPaths:
    repo_label = _resolve_context_label(workspace, repo_root)
    return checkpoint_paths_for_label(workspace, repo_label, runtime_session_id=runtime_session_id)


def _resolve_runtime_checkpoint_paths(
    workspace: Workspace,
    *,
    repo_root: str,
    runtime_session_id: str | None,
    migrate_legacy: bool = False,
) -> CheckpointPaths:
    repo_label = _resolve_context_label(workspace, repo_root)
    return _resolve_runtime_checkpoint_paths_for_label(
        workspace,
        repo_label=repo_label,
        runtime_session_id=runtime_session_id,
        migrate_legacy=migrate_legacy,
    )


def _resolve_runtime_checkpoint_paths_for_label(
    workspace: Workspace,
    *,
    repo_label: str,
    runtime_session_id: str | None,
    migrate_legacy: bool = False,
) -> CheckpointPaths:
    scoped_paths = checkpoint_paths_for_label(
        workspace,
        repo_label,
        runtime_session_id=runtime_session_id,
    )
    if runtime_session_id is None:
        return scoped_paths

    legacy_paths = checkpoint_paths_for_label(workspace, repo_label, runtime_session_id=None)
    if scoped_paths.current_dir == legacy_paths.current_dir:
        return scoped_paths
    if scoped_paths.jsonl.exists():
        return scoped_paths
    legacy_note: SessionCheckpointNote | None = None
    if legacy_paths.jsonl.exists():
        legacy_note = _load_checkpoint_note(legacy_paths.note_json)
        if legacy_note is None:
            legacy_note = _build_checkpoint_note(legacy_paths)
        # Unscoped legacy ledgers stay quarantined once an active runtime session
        # exists, even if their payload happens to mention the same session id.
        if migrate_legacy and legacy_note.runtime_session_id is not None:
            _archive_current_checkpoint(legacy_paths)
        return scoped_paths
    if not legacy_paths.jsonl.exists():
        return scoped_paths

    return scoped_paths


def _checkpoint_note_ref_for_capture(
    workspace: Workspace,
    repo_root: str,
    *,
    runtime_session_id: str | None,
) -> str:
    return str(
        _resolve_runtime_checkpoint_paths(
            workspace,
            repo_root=repo_root,
            runtime_session_id=runtime_session_id,
            migrate_legacy=False,
        ).note_json
    )


def _checkpoint_skill_report_path(workspace: Workspace, repo_root: str) -> Path:
    repo_label = _resolve_context_label(workspace, repo_root)
    return workspace.repo_path("aoa-sdk") / ".aoa" / "skill-dispatch" / f"{repo_label}.checkpoint.latest.json"


def _write_skill_detection_report(path: Path, report: object) -> None:
    write_json(
        path,
        {
            "report_path": str(path),
            "report": report,
        },
    )


def _checkpoint_capture_result_without_append(
    api: CheckpointsAPI,
    *,
    repo_root: str,
    session_file: str | None,
    reason: Literal["no_checkpoint_signal", "auto_disabled"],
    attempted: bool,
    checkpoint_kind: Literal[
        "manual",
        "commit",
        "verify_green",
        "pr_opened",
        "pr_merged",
        "pause",
        "owner_followthrough",
    ] | None,
    read_only: bool,
) -> CheckpointCaptureResult:
    captured_at, captured_at_local, captured_tz = _local_timestamp_parts()
    current_note = (
        _peek_runtime_checkpoint_note(api, repo_root=repo_root, session_file=session_file)
        if read_only
        else _load_runtime_checkpoint_note(api, repo_root=repo_root, session_file=session_file)
    )
    session_end_targets = _derive_session_end_skill_targets(current_note)
    return CheckpointCaptureResult(
        mode="auto",
        attempted=attempted,
        appended=False,
        checkpoint_kind=checkpoint_kind,
        captured_at=captured_at,
        captured_at_local=captured_at_local,
        captured_tz=captured_tz,
        reason=reason,
        note_ref=(
            _checkpoint_note_ref_for_capture(
                api.workspace,
                repo_root,
                runtime_session_id=current_note.runtime_session_id,
            )
            if current_note is not None
            else None
        ),
        session_end_skill_targets=session_end_targets,
        session_end_next_honest_move=_derive_session_end_next_honest_move(
            note=current_note,
            session_end_targets=session_end_targets,
        ),
        harvest_candidate_ids=list(current_note.harvest_candidate_ids) if current_note is not None else [],
        progression_candidate_ids=list(current_note.progression_candidate_ids) if current_note is not None else [],
        upgrade_candidate_ids=list(current_note.upgrade_candidate_ids) if current_note is not None else [],
        progression_axis_signals=list(current_note.progression_axis_signals) if current_note is not None else [],
        stats_refresh_recommended=current_note.stats_refresh_recommended if current_note is not None else False,
        note=current_note,
    )


def _resolve_context_root(workspace: Workspace, repo_root: str) -> Path:
    resolved_repo_root = Path(repo_root).expanduser()
    if not resolved_repo_root.is_absolute():
        return (workspace.root / resolved_repo_root).resolve()
    return resolved_repo_root.resolve()


def _resolve_context_label(workspace: Workspace, repo_root: str) -> str:
    resolved_repo_root = _resolve_context_root(workspace, repo_root)
    return "workspace" if resolved_repo_root == workspace.federation_root else resolved_repo_root.name




def _dedupe_strings(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))
