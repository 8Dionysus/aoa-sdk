"""Checkpoint lifecycle audit and close/archive orchestration."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Literal

from ..models import (
    CheckpointLifecycleArchiveResult,
    CheckpointLifecycleAuditReport,
    CheckpointLifecycleEntry,
    SessionCheckpointLifecycleEvent,
)
from ..workspace.discovery import Workspace
from .ledger.notes import archive_current_checkpoint, build_checkpoint_note
from .indexes import write_checkpoint_lifecycle_index
from .render.markdown import render_checkpoint_note_markdown
from .runtime.sessions import probe_checkpoint_runtime_session
from .session_memory import (
    resolve_checkpoint_runtime_trace_ref,
    resolve_checkpoint_session_memory_for_runtime_session,
)
from .timestamps import local_timestamp_parts
from .topology.paths import (
    CheckpointPaths,
    checkpoint_current_root,
    checkpoint_runtime_scope_key,
)


LifecycleState = Literal[
    "active_current",
    "pending_review",
    "session_closed_pending_review",
    "session_closed_reviewed_no_closeout",
    "session_closed_collecting_no_closeout",
    "reviewed_awaiting_closeout",
    "closeout_built",
    "closeout_executed",
    "closed",
    "stale_current_scope",
]


def audit_checkpoint_lifecycle(
    *,
    workspace: Workspace,
    repo_root: str | None = None,
    session_file: str | None = None,
    write_index: bool = False,
) -> CheckpointLifecycleAuditReport:
    checked_at, checked_at_local, checked_tz = local_timestamp_parts()
    session_path, runtime_metadata = probe_checkpoint_runtime_session(
        workspace=workspace,
        session_file=session_file,
    )
    active_runtime_session_id = runtime_metadata["runtime_session_id"]
    repo_label = _resolve_context_label(workspace, repo_root) if repo_root is not None else None
    resolved_repo_root = (
        str(_resolve_context_root(workspace, repo_root)) if repo_root is not None else None
    )
    current_root = checkpoint_current_root(workspace)
    archive_root = workspace.repo_path("aoa-sdk") / ".aoa" / "session-growth" / "archive"
    current_dirs = _iter_checkpoint_current_dirs(current_root)
    if repo_label is not None:
        current_dirs = [
            current_dir
            for current_dir in current_dirs
            if _repo_label_from_current_dir(workspace, current_dir) == repo_label
        ]
    entries = [
        entry
        for entry in (
            _entry_from_current_dir(
                workspace=workspace,
                current_dir=current_dir,
                active_runtime_session_file_ref=str(session_path),
                active_runtime_session_id=(
                    active_runtime_session_id if isinstance(active_runtime_session_id, str) else None
                ),
            )
            for current_dir in current_dirs
        )
        if entry is not None
    ]
    lifecycle_counts = Counter(entry.lifecycle_state for entry in entries)
    pending_review_count = sum(
        1
        for entry in entries
        if entry.lifecycle_state in {"pending_review", "session_closed_pending_review"}
    )
    session_memory_ref_count = sum(1 for entry in entries if entry.session_memory_archive_ref)
    session_closed_without_closeout_count = sum(
        1
        for entry in entries
        if entry.lifecycle_state
        in {
            "session_closed_pending_review",
            "session_closed_reviewed_no_closeout",
            "session_closed_collecting_no_closeout",
        }
    )
    reviewed_not_closed_count = sum(
        1
        for entry in entries
        if entry.review_status == "reviewed" and entry.state not in {"closed", "promoted"}
    )
    notes: list[str] = []
    stale_count = sum(1 for entry in entries if not entry.active_runtime_scope)
    if stale_count:
        notes.append(
            f"{stale_count} checkpoint current entrie(s) are outside the active runtime scope"
        )
    if pending_review_count:
        notes.append(
            f"{pending_review_count} checkpoint entrie(s) still require agent review"
        )
    if any(entry.session_memory_archive_ref for entry in entries):
        notes.append(
            "session-memory refs are reported as route evidence only; lifecycle audit does not mutate .aoa"
        )
    recoverable_trace_count = sum(
        1 for entry in entries if entry.runtime_trace_status == "recoverable"
    )
    if recoverable_trace_count:
        notes.append(
            f"{recoverable_trace_count} checkpoint entrie(s) have recoverable raw trace refs from legacy post-commit reports"
        )
    report = CheckpointLifecycleAuditReport(
        checked_at=checked_at,
        checked_at_local=checked_at_local,
        checked_tz=checked_tz,
        repo_root=resolved_repo_root,
        repo_label=repo_label,
        session_file=str(session_path),
        active_runtime_session_id=(
            active_runtime_session_id if isinstance(active_runtime_session_id, str) else None
        ),
        current_scope_count=_current_scope_count(current_root),
        note_count=len(entries),
        archive_scope_count=_archive_scope_count(archive_root),
        closeout_context_count=sum(1 for entry in entries if entry.closeout_context_ref),
        closeout_execution_count=sum(1 for entry in entries if entry.closeout_execution_report_ref),
        session_memory_ref_count=session_memory_ref_count,
        session_closed_without_closeout_count=session_closed_without_closeout_count,
        pending_review_count=pending_review_count,
        reviewed_not_closed_count=reviewed_not_closed_count,
        closable_count=sum(1 for entry in entries if entry.closable),
        archiveable_count=sum(1 for entry in entries if entry.archiveable),
        lifecycle_counts={str(key): value for key, value in lifecycle_counts.items()},
        entries=entries,
        notes=notes,
    )
    if write_index:
        index_ref = write_checkpoint_lifecycle_index(workspace=workspace, report=report)
        report.generated_index_ref = str(index_ref)
    return report


def close_archive_checkpoint_lifecycle(
    *,
    workspace: Workspace,
    repo_root: str | None = None,
    session_file: str | None = None,
    runtime_session_id: str | None = None,
    dry_run: bool = True,
    include_stale: bool = False,
) -> CheckpointLifecycleArchiveResult:
    executed_at, executed_at_local, executed_tz = local_timestamp_parts()
    audit = audit_checkpoint_lifecycle(
        workspace=workspace,
        repo_root=repo_root,
        session_file=session_file,
    )
    archived_entries: list[CheckpointLifecycleEntry] = []
    skipped_entries: list[CheckpointLifecycleEntry] = []
    archive_refs: list[str] = []
    notes: list[str] = []

    for entry in audit.entries:
        if runtime_session_id is not None and not _matches_runtime(entry, runtime_session_id):
            continue
        if entry.lifecycle_state == "pending_review":
            skipped_entries.append(entry)
            continue
        if entry.closable:
            archived_entries.append(entry)
            if not dry_run:
                archive_ref = _close_and_archive_entry(workspace=workspace, entry=entry)
                archive_refs.append(str(archive_ref))
            continue
        if include_stale and entry.archiveable:
            archived_entries.append(entry)
            if not dry_run:
                archive_ref = _archive_entry_without_closing(workspace=workspace, entry=entry)
                archive_refs.append(str(archive_ref))
            continue
        skipped_entries.append(entry)

    if dry_run:
        notes.append("dry-run only; no checkpoint files were moved")
    if include_stale:
        notes.append(
            "include_stale archived nonpending stale current scopes without marking them closed"
        )
    notes.append("aoa-session-memory archives were not mutated")
    return CheckpointLifecycleArchiveResult(
        executed_at=executed_at,
        executed_at_local=executed_at_local,
        executed_tz=executed_tz,
        dry_run=dry_run,
        repo_root=audit.repo_root,
        repo_label=audit.repo_label,
        runtime_session_id=runtime_session_id,
        archived_count=len(archived_entries),
        skipped_count=len(skipped_entries),
        archived_entries=archived_entries,
        skipped_entries=skipped_entries,
        archive_refs=archive_refs,
        notes=notes,
    )


def _entry_from_current_dir(
    *,
    workspace: Workspace,
    current_dir: Path,
    active_runtime_session_file_ref: str | None,
    active_runtime_session_id: str | None,
) -> CheckpointLifecycleEntry | None:
    paths = _checkpoint_paths_from_current_dir(workspace, current_dir)
    if not paths.jsonl.exists():
        return None
    note = build_checkpoint_note(paths)
    note_ref = str(paths.note_json) if paths.note_json.exists() else None
    closeout_context_ref = str(paths.closeout_context) if paths.closeout_context.exists() else None
    closeout_execution_ref = (
        str(paths.closeout_execution_report)
        if paths.closeout_execution_report.exists()
        else None
    )
    post_commit_ref = str(paths.post_commit_report) if paths.post_commit_report.exists() else None
    active_runtime_scope = (
        active_runtime_session_id is not None
        and note.runtime_session_id == active_runtime_session_id
    )
    runtime_trace_ref = resolve_checkpoint_runtime_trace_ref(
        workspace=workspace,
        runtime_session_id=note.runtime_session_id,
        post_commit_report_ref=post_commit_ref,
        runtime_session_file_ref=active_runtime_session_file_ref,
    )
    runtime_trace_status: Literal["resolved", "recoverable", "missing"] = (
        "resolved"
        if runtime_trace_ref is not None
        and runtime_trace_ref.source == "aoa-sdk-skill-runtime-session"
        else "recoverable"
        if runtime_trace_ref is not None
        else "missing"
    )
    session_memory_ref, session_memory_freshness = (
        resolve_checkpoint_session_memory_for_runtime_session(
            workspace=workspace,
            runtime_session_id=note.runtime_session_id,
            post_commit_report_ref=post_commit_ref,
            runtime_session_file_ref=active_runtime_session_file_ref,
        )
        if not active_runtime_scope
        else (None, None)
    )
    session_memory_archive_ref = _dedupe_strings(
        [
            _session_memory_archive_ref(
                paths.closeout_execution_report,
                paths.closeout_context,
            ),
            session_memory_ref.archive_path if session_memory_ref is not None else None,
        ]
    )
    lifecycle_state, reason = _lifecycle_state(
        note_state=note.state,
        review_status=note.review_status,
        agent_review_status=note.agent_review_status,
        pending_refs=note.agent_review_pending_refs,
        active_runtime_scope=active_runtime_scope,
        has_session_memory_archive=bool(session_memory_archive_ref),
        has_closeout_context=closeout_context_ref is not None,
        has_closeout_execution=closeout_execution_ref is not None,
    )
    pending_refs = list(note.agent_review_pending_refs)
    closable = (
        lifecycle_state == "closeout_executed"
        and note.review_status == "reviewed"
        and not pending_refs
    ) or note.state in {"closed", "promoted"}
    archiveable = closable or (
        not active_runtime_scope
        and lifecycle_state not in {"pending_review", "session_closed_pending_review"}
    )
    evidence_refs = _dedupe_strings(
        [
            str(paths.jsonl),
            *(str(paths.note_json) if paths.note_json.exists() else None,),
            *(post_commit_ref,),
            *(closeout_context_ref,),
            *(closeout_execution_ref,),
            *(runtime_trace_ref.evidence_refs if runtime_trace_ref is not None else []),
            *(session_memory_ref.evidence_refs if session_memory_ref is not None else []),
            *note.evidence_refs,
        ]
    )
    raw_refs = _dedupe_strings(
        [
            runtime_trace_ref.codex_rollout_path if runtime_trace_ref is not None else None,
            session_memory_ref.raw_ref if session_memory_ref is not None else None,
            session_memory_ref.raw_blocks_index_ref if session_memory_ref is not None else None,
            session_memory_ref.source_trace_ref if session_memory_ref is not None else None,
        ]
    )
    next_route = _next_route(
        lifecycle_state=lifecycle_state,
        active_runtime_scope=active_runtime_scope,
        has_runtime_trace=runtime_trace_ref is not None,
        has_session_memory_archive=bool(session_memory_archive_ref),
        review_status=note.review_status,
    )
    required_action = _required_action(
        lifecycle_state=lifecycle_state,
        next_route=next_route,
        repo_label=paths.repo_label,
        pending_refs=pending_refs,
        runtime_session_id=note.runtime_session_id,
        runtime_trace_thread_id=(
            runtime_trace_ref.codex_thread_id if runtime_trace_ref is not None else None
        ),
        source_trace_ref=(
            runtime_trace_ref.codex_rollout_path if runtime_trace_ref is not None else None
        ),
    )
    return CheckpointLifecycleEntry(
        repo_label=paths.repo_label,
        runtime_session_id=note.runtime_session_id,
        runtime_scope_key=paths.runtime_scope_key,
        session_ref=note.session_ref,
        current_dir=str(paths.current_dir),
        note_ref=note_ref,
        post_commit_report_ref=post_commit_ref,
        closeout_context_ref=closeout_context_ref,
        closeout_execution_report_ref=closeout_execution_ref,
        runtime_trace_ref=(
            runtime_trace_ref.runtime_session_file_ref if runtime_trace_ref is not None else None
        ),
        runtime_trace_thread_id=(
            runtime_trace_ref.codex_thread_id if runtime_trace_ref is not None else None
        ),
        runtime_trace_status=runtime_trace_status,
        source_trace_ref=(
            runtime_trace_ref.codex_rollout_path if runtime_trace_ref is not None else None
        ),
        session_memory_archive_ref=session_memory_archive_ref[0] if session_memory_archive_ref else None,
        session_memory_session_id=(
            session_memory_ref.session_id if session_memory_ref is not None else None
        ),
        session_memory_status=(
            session_memory_freshness.status if session_memory_freshness is not None else None
        ),
        raw_refs=raw_refs,
        state=note.state,
        review_status=note.review_status,
        agent_review_status=note.agent_review_status,
        lifecycle_state=lifecycle_state,
        active_runtime_scope=active_runtime_scope,
        closable=closable,
        archiveable=archiveable,
        pending_refs=pending_refs,
        blocked_by=list(note.blocked_by),
        evidence_refs=evidence_refs,
        required_action=required_action,
        next_route=next_route,
        reason=reason,
    )


def _lifecycle_state(
    *,
    note_state: str,
    review_status: str,
    agent_review_status: str,
    pending_refs: list[str],
    active_runtime_scope: bool,
    has_session_memory_archive: bool,
    has_closeout_context: bool,
    has_closeout_execution: bool,
) -> tuple[LifecycleState, str]:
    if note_state in {"closed", "promoted"}:
        return "closed", "checkpoint note is already closed or promoted"
    pending_review = bool(pending_refs) or agent_review_status == "pending"
    if pending_review and has_session_memory_archive and not active_runtime_scope:
        return (
            "session_closed_pending_review",
            "aoa-session-memory archive exists, but pending agent review blocks reconcile/archive",
        )
    if pending_review:
        return "pending_review", "pending agent review blocks close/archive"
    if has_closeout_execution:
        return "closeout_executed", "reviewed closeout execution report exists"
    if has_session_memory_archive and not active_runtime_scope and review_status == "reviewed":
        return (
            "session_closed_reviewed_no_closeout",
            "aoa-session-memory archive exists, but reviewed closeout execution is missing",
        )
    if has_session_memory_archive and not active_runtime_scope:
        return (
            "session_closed_collecting_no_closeout",
            "aoa-session-memory archive exists, but checkpoint review or closeout did not complete",
        )
    if has_closeout_context:
        return "closeout_built", "reviewed closeout context exists but execution report is missing"
    if review_status == "reviewed":
        return "reviewed_awaiting_closeout", "checkpoint note is reviewed but no reviewed closeout execution exists"
    if active_runtime_scope:
        return "active_current", "checkpoint note belongs to the active runtime session"
    return "stale_current_scope", "checkpoint note is outside the active runtime session"


def _required_action(
    *,
    lifecycle_state: LifecycleState,
    next_route: str,
    repo_label: str,
    pending_refs: list[str],
    runtime_session_id: str | None,
    runtime_trace_thread_id: str | None,
    source_trace_ref: str | None,
) -> str | None:
    if lifecycle_state in {"pending_review", "session_closed_pending_review"}:
        refs_preview = ", ".join(pending_refs[:5]) if pending_refs else "pending checkpoint entry"
        if len(pending_refs) > 5:
            refs_preview += f" (+{len(pending_refs) - 5} more)"
        session_part = f" --runtime-session-id {runtime_session_id}" if runtime_session_id else ""
        return (
            f"review checkpoint note for {repo_label}{session_part} before reconcile/archive; "
            f"pending refs: {refs_preview}"
        )
    if next_route != "recover_session_memory_archive":
        return None
    if runtime_trace_thread_id and source_trace_ref:
        return (
            "recover aoa-session-memory archive for "
            f"{repo_label} from raw transcript {source_trace_ref} "
            f"with session id {runtime_trace_thread_id}; then rerun checkpoint backlog-audit"
        )
    if runtime_trace_thread_id:
        return (
            "recover aoa-session-memory archive for "
            f"{repo_label} by sweeping/importing Codex thread {runtime_trace_thread_id}; "
            "then rerun checkpoint backlog-audit"
        )
    return (
        f"recover aoa-session-memory archive for {repo_label}; "
        "then rerun checkpoint backlog-audit"
    )


def _close_and_archive_entry(*, workspace: Workspace, entry: CheckpointLifecycleEntry) -> Path:
    paths = _checkpoint_paths_from_entry(workspace, entry)
    note = build_checkpoint_note(paths)
    if note.agent_review_status == "pending" or note.agent_review_pending_refs:
        raise ValueError("pending checkpoint agent review blocks lifecycle close/archive")
    if not paths.closeout_execution_report.exists() and note.state not in {"closed", "promoted"}:
        raise ValueError("checkpoint close/archive requires reviewed closeout execution evidence")

    observed_at, observed_at_local, observed_tz = local_timestamp_parts()
    event = SessionCheckpointLifecycleEvent(
        event_id=f"lifecycle-close:{_safe_event_fragment(note.session_ref)}:{observed_at.strftime('%Y%m%dT%H%M%SZ')}",
        observed_at=observed_at,
        observed_at_local=observed_at_local,
        observed_tz=observed_tz,
        repo_root=str(_repo_root_for_label(workspace, paths.repo_label)),
        repo_label=paths.repo_label,
        session_ref=note.session_ref,
        runtime_session_id=note.runtime_session_id,
        closeout_context_ref=str(paths.closeout_context) if paths.closeout_context.exists() else None,
        closeout_execution_report_ref=(
            str(paths.closeout_execution_report)
            if paths.closeout_execution_report.exists()
            else None
        ),
        archive_reason="reviewed closeout execution exists; checkpoint scope can leave current",
        evidence_refs=_dedupe_strings(
            [
                str(paths.jsonl),
                *(str(paths.closeout_context) if paths.closeout_context.exists() else None,),
                *(
                    str(paths.closeout_execution_report)
                    if paths.closeout_execution_report.exists()
                    else None,
                ),
            ]
        ),
    )
    if not any(existing.event_type == event.event_type for existing in note.lifecycle_events):
        with paths.jsonl.open("a", encoding="utf-8") as handle:
            handle.write(
                json.dumps(
                    {
                        "session_ref": note.session_ref,
                        "runtime_session_id": note.runtime_session_id,
                        "runtime_session_created_at": (
                            note.runtime_session_created_at.isoformat().replace("+00:00", "Z")
                            if note.runtime_session_created_at is not None
                            else None
                        ),
                        "repo_root": str(_repo_root_for_label(workspace, paths.repo_label)),
                        "repo_label": paths.repo_label,
                        "lifecycle_event": event.model_dump(mode="json"),
                    },
                    ensure_ascii=True,
                )
                + "\n"
            )
    closed_note = build_checkpoint_note(paths)
    paths.note_json.write_text(closed_note.model_dump_json(indent=2) + "\n", encoding="utf-8")
    paths.note_md.write_text(
        render_checkpoint_note_markdown(closed_note, repo_label=paths.repo_label),
        encoding="utf-8",
    )
    archive_dir = archive_current_checkpoint(paths)
    _remove_empty_current_dirs(paths)
    return archive_dir


def close_and_archive_checkpoint_entry(
    *,
    workspace: Workspace,
    entry: CheckpointLifecycleEntry,
) -> Path:
    return _close_and_archive_entry(workspace=workspace, entry=entry)


def _archive_entry_without_closing(*, workspace: Workspace, entry: CheckpointLifecycleEntry) -> Path:
    paths = _checkpoint_paths_from_entry(workspace, entry)
    note = build_checkpoint_note(paths)
    if note.agent_review_status == "pending" or note.agent_review_pending_refs:
        raise ValueError("pending checkpoint agent review blocks stale archive")
    paths.note_json.write_text(note.model_dump_json(indent=2) + "\n", encoding="utf-8")
    paths.note_md.write_text(
        render_checkpoint_note_markdown(note, repo_label=paths.repo_label),
        encoding="utf-8",
    )
    archive_dir = archive_current_checkpoint(paths)
    _remove_empty_current_dirs(paths)
    return archive_dir


def archive_checkpoint_entry_without_closeout(
    *,
    workspace: Workspace,
    entry: CheckpointLifecycleEntry,
) -> Path:
    paths = _checkpoint_paths_from_entry(workspace, entry)
    note = build_checkpoint_note(paths)
    if note.agent_review_status == "pending" or note.agent_review_pending_refs:
        raise ValueError("pending checkpoint agent review blocks no-closeout reconcile/archive")
    if not entry.session_memory_archive_ref:
        raise ValueError("no-closeout reconcile/archive requires aoa-session-memory archive evidence")

    observed_at, observed_at_local, observed_tz = local_timestamp_parts()
    event = SessionCheckpointLifecycleEvent(
        event_type="checkpoint_session_archived_without_closeout_v1",
        event_id=(
            "session-archive-without-closeout:"
            f"{_safe_event_fragment(note.session_ref)}:"
            f"{observed_at.strftime('%Y%m%dT%H%M%SZ')}"
        ),
        observed_at=observed_at,
        observed_at_local=observed_at_local,
        observed_tz=observed_tz,
        repo_root=str(_repo_root_for_label(workspace, paths.repo_label)),
        repo_label=paths.repo_label,
        session_ref=note.session_ref,
        runtime_session_id=note.runtime_session_id,
        lifecycle_state="archived_without_closeout",
        closeout_context_ref=str(paths.closeout_context) if paths.closeout_context.exists() else None,
        closeout_execution_report_ref=None,
        session_memory_archive_ref=entry.session_memory_archive_ref,
        archive_reason=(
            "aoa-session-memory archive exists for a checkpoint runtime session "
            "that ended without reviewed checkpoint closeout execution"
        ),
        evidence_refs=_dedupe_strings(
            [
                str(paths.jsonl),
                *(str(paths.note_json) if paths.note_json.exists() else None,),
                *(str(paths.closeout_context) if paths.closeout_context.exists() else None,),
                entry.session_memory_archive_ref,
                *entry.evidence_refs,
            ]
        ),
    )
    if not any(existing.event_type == event.event_type for existing in note.lifecycle_events):
        with paths.jsonl.open("a", encoding="utf-8") as handle:
            handle.write(
                json.dumps(
                    {
                        "session_ref": note.session_ref,
                        "runtime_session_id": note.runtime_session_id,
                        "runtime_session_created_at": (
                            note.runtime_session_created_at.isoformat().replace("+00:00", "Z")
                            if note.runtime_session_created_at is not None
                            else None
                        ),
                        "repo_root": str(_repo_root_for_label(workspace, paths.repo_label)),
                        "repo_label": paths.repo_label,
                        "lifecycle_event": event.model_dump(mode="json"),
                    },
                    ensure_ascii=True,
                )
                + "\n"
            )
    reconciled_note = build_checkpoint_note(paths)
    paths.note_json.write_text(
        reconciled_note.model_dump_json(indent=2) + "\n",
        encoding="utf-8",
    )
    paths.note_md.write_text(
        render_checkpoint_note_markdown(reconciled_note, repo_label=paths.repo_label),
        encoding="utf-8",
    )
    archive_dir = archive_current_checkpoint(paths)
    _remove_empty_current_dirs(paths)
    return archive_dir


def _iter_checkpoint_current_dirs(current_root: Path) -> list[Path]:
    if not current_root.exists():
        return []
    return sorted(path.parent for path in current_root.rglob("checkpoint-note.jsonl"))


def _checkpoint_paths_from_current_dir(workspace: Workspace, current_dir: Path) -> CheckpointPaths:
    current_root = checkpoint_current_root(workspace)
    rel_parts = current_dir.relative_to(current_root).parts
    if len(rel_parts) == 1:
        runtime_scope_key = None
        repo_label = rel_parts[0]
        runtime_session_id = None
    else:
        runtime_scope_key = rel_parts[0]
        repo_label = rel_parts[1]
        runtime_session_id = runtime_scope_key
    sdk_root = workspace.repo_path("aoa-sdk")
    return CheckpointPaths(
        root=sdk_root,
        repo_label=repo_label,
        current_dir=current_dir,
        surface_report=sdk_root / ".aoa" / "surface-detection" / f"{repo_label}.checkpoint.latest.json",
        runtime_session_id=runtime_session_id,
        runtime_scope_key=runtime_scope_key,
    )


def _repo_label_from_current_dir(workspace: Workspace, current_dir: Path) -> str | None:
    current_root = checkpoint_current_root(workspace)
    try:
        rel_parts = current_dir.relative_to(current_root).parts
    except ValueError:
        return None
    if len(rel_parts) == 1:
        return rel_parts[0]
    if len(rel_parts) >= 2:
        return rel_parts[1]
    return None


def _checkpoint_paths_from_entry(workspace: Workspace, entry: CheckpointLifecycleEntry) -> CheckpointPaths:
    return _checkpoint_paths_from_current_dir(workspace, Path(entry.current_dir))


def _resolve_context_root(workspace: Workspace, repo_root: str) -> Path:
    resolved_repo_root = Path(repo_root).expanduser()
    if not resolved_repo_root.is_absolute():
        return (workspace.root / resolved_repo_root).resolve()
    return resolved_repo_root.resolve()


def _resolve_context_label(workspace: Workspace, repo_root: str) -> str:
    resolved_repo_root = _resolve_context_root(workspace, repo_root)
    return "workspace" if resolved_repo_root == workspace.federation_root else resolved_repo_root.name


def _repo_root_for_label(workspace: Workspace, repo_label: str) -> Path:
    if repo_label == "workspace":
        return workspace.federation_root
    return (workspace.root / repo_label).resolve()


def _matches_runtime(entry: CheckpointLifecycleEntry, runtime_session_id: str) -> bool:
    runtime_scope_key = checkpoint_runtime_scope_key(runtime_session_id)
    return entry.runtime_session_id == runtime_session_id or entry.runtime_scope_key == runtime_scope_key


def _current_scope_count(current_root: Path) -> int:
    if not current_root.exists():
        return 0
    return sum(1 for path in current_root.iterdir() if path.is_dir())


def _archive_scope_count(archive_root: Path) -> int:
    if not archive_root.exists():
        return 0
    return sum(1 for path in archive_root.iterdir() if path.is_dir())


def _session_memory_archive_ref(*paths: Path) -> str | None:
    for path in paths:
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        ref = payload.get("session_memory_ref") if isinstance(payload, dict) else None
        if not isinstance(ref, dict):
            continue
        archive_path = ref.get("archive_path")
        if isinstance(archive_path, str) and archive_path.strip():
            return archive_path
    return None


def _next_route(
    *,
    lifecycle_state: LifecycleState,
    active_runtime_scope: bool,
    has_runtime_trace: bool,
    has_session_memory_archive: bool,
    review_status: str,
) -> str:
    if lifecycle_state in {"pending_review", "session_closed_pending_review"}:
        return "review_checkpoint_note"
    if lifecycle_state == "active_current":
        return "continue_active_session"
    if lifecycle_state == "closeout_executed":
        return "close_archive"
    if lifecycle_state in {
        "session_closed_reviewed_no_closeout",
        "session_closed_collecting_no_closeout",
    }:
        return "reconcile_without_closeout"
    if lifecycle_state == "closeout_built":
        return "execute_reviewed_closeout_or_inspect"
    if lifecycle_state == "reviewed_awaiting_closeout":
        if active_runtime_scope:
            return "run_reviewed_closeout"
        if has_session_memory_archive:
            return "reconcile_without_closeout"
        if has_runtime_trace:
            return "recover_session_memory_archive"
        return "inspect_runtime_trace"
    if lifecycle_state == "stale_current_scope":
        if has_session_memory_archive:
            return "reconcile_without_closeout"
        if has_runtime_trace:
            return "recover_session_memory_archive"
        if review_status == "reviewed":
            return "inspect_runtime_trace"
        return "stale_archive_dry_run"
    if lifecycle_state == "closed":
        return "archive_closed_scope"
    return "inspect_checkpoint_scope"


def _remove_empty_current_dirs(paths: CheckpointPaths) -> None:
    for candidate in (paths.current_dir, paths.current_dir.parent):
        if candidate == checkpoint_current_root_from_paths(paths):
            continue
        try:
            candidate.rmdir()
        except OSError:
            continue


def checkpoint_current_root_from_paths(paths: CheckpointPaths) -> Path:
    return paths.root / ".aoa" / "session-growth" / "current"


def _safe_event_fragment(value: str) -> str:
    return "".join(ch if ch.isalnum() else "-" for ch in value)[:64].strip("-") or "checkpoint"


def _dedupe_strings(values: list[str | None]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))
