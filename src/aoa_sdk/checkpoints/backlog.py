"""Checkpoint backlog audit for no-closeout and stale current scopes."""

from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from ..models import (
    CheckpointBacklogAuditReport,
    CheckpointBacklogEntry,
    CheckpointLifecycleEntry,
)
from ..workspace.discovery import Workspace
from .backlog_indexes import write_checkpoint_backlog_index
from .lifecycle import audit_checkpoint_lifecycle
from .timestamps import local_timestamp_parts


BACKLOG_STOP_LINES = (
    "no_raw_or_session_evidence_deletion",
    "no_aoa_session_memory_mutation",
    "no_closeout_execution",
    "no_candidate_promotion",
    "no_owner_verdict",
    "no_rag_or_graphrag_authority",
    "no_hidden_automation",
)


def audit_checkpoint_backlog(
    *,
    workspace: Workspace,
    repo_root: str | None = None,
    session_file: str | None = None,
    write_index: bool = False,
) -> CheckpointBacklogAuditReport:
    checked_at, checked_at_local, checked_tz = local_timestamp_parts()
    lifecycle_report = audit_checkpoint_lifecycle(
        workspace=workspace,
        repo_root=repo_root,
        session_file=session_file,
        write_index=False,
    )
    entries = [
        _backlog_entry(entry, checked_at=checked_at)
        for entry in lifecycle_report.entries
        if entry.lifecycle_state != "closed"
    ]
    counts = _counts(entries)
    notes = [
        "backlog-audit is read-only; no checkpoint files were moved",
        "runtime trace refs are evidence coordinates, not proof that aoa-session-memory archived the session",
        "session-memory archives may enable no-closeout reconcile only when an archive ref is present",
    ]
    if counts.get("runtime_trace_gaps", 0):
        notes.append(
            "runtime trace gaps should route to aoa-session-memory freshness/sweep/import checks before reconcile"
        )
    if counts.get("runtime_trace_recoverable", 0):
        notes.append(
            "recoverable runtime traces come from legacy post-commit report/raw transcript coordinates, not live SDK runtime session files"
        )
    report = CheckpointBacklogAuditReport(
        checked_at=checked_at,
        checked_at_local=checked_at_local,
        checked_tz=checked_tz,
        repo_root=lifecycle_report.repo_root,
        repo_label=lifecycle_report.repo_label,
        active_runtime_session_id=lifecycle_report.active_runtime_session_id,
        counts=counts,
        entries=entries,
        stop_lines=list(BACKLOG_STOP_LINES),
        notes=notes,
    )
    if write_index:
        index_path = write_checkpoint_backlog_index(workspace=workspace, report=report)
        report = report.model_copy(update={"generated_index_ref": str(index_path)})
    return report


def _backlog_entry(
    lifecycle_entry: CheckpointLifecycleEntry,
    *,
    checked_at: datetime,
) -> CheckpointBacklogEntry:
    return CheckpointBacklogEntry(
        repo_label=lifecycle_entry.repo_label,
        runtime_session_id=lifecycle_entry.runtime_session_id,
        lifecycle_state=lifecycle_entry.lifecycle_state,
        review_status=lifecycle_entry.review_status,
        agent_review_status=lifecycle_entry.agent_review_status,
        active_runtime_scope=lifecycle_entry.active_runtime_scope,
        age_days=_age_days(lifecycle_entry.note_ref, checked_at=checked_at),
        note_ref=lifecycle_entry.note_ref,
        current_dir=lifecycle_entry.current_dir,
        post_commit_report_ref=lifecycle_entry.post_commit_report_ref,
        runtime_trace_status=lifecycle_entry.runtime_trace_status,
        runtime_trace_thread_id=lifecycle_entry.runtime_trace_thread_id,
        runtime_trace_ref=lifecycle_entry.runtime_trace_ref,
        source_trace_ref=lifecycle_entry.source_trace_ref,
        session_memory_status=lifecycle_entry.session_memory_status,
        session_memory_session_id=lifecycle_entry.session_memory_session_id,
        session_memory_archive_ref=lifecycle_entry.session_memory_archive_ref,
        raw_refs=list(lifecycle_entry.raw_refs),
        why_open=lifecycle_entry.reason,
        next_route=lifecycle_entry.next_route or "inspect_checkpoint_scope",
        required_action=lifecycle_entry.required_action,
        evidence_refs=list(lifecycle_entry.evidence_refs),
    )


def _counts(entries: list[CheckpointBacklogEntry]) -> dict[str, int]:
    lifecycle_counts = Counter(entry.lifecycle_state for entry in entries)
    next_route_counts = Counter(entry.next_route for entry in entries)
    counts = {
        "entries": len(entries),
        "active_current": sum(1 for entry in entries if entry.active_runtime_scope),
        "pending_review": sum(
            1
            for entry in entries
            if entry.lifecycle_state in {"pending_review", "session_closed_pending_review"}
        ),
        "reviewed_not_closed": sum(
            1
            for entry in entries
            if entry.review_status == "reviewed" and entry.lifecycle_state != "closed"
        ),
        "session_memory_refs": sum(1 for entry in entries if entry.session_memory_archive_ref),
        "runtime_trace_resolved": sum(
            1 for entry in entries if entry.runtime_trace_status == "resolved"
        ),
        "runtime_trace_recoverable": sum(
            1 for entry in entries if entry.runtime_trace_status == "recoverable"
        ),
        "runtime_trace_missing": sum(1 for entry in entries if entry.runtime_trace_status == "missing"),
        "runtime_trace_gaps": sum(
            1
            for entry in entries
            if _is_runtime_trace_gap(entry)
        ),
        "reconcile_ready": sum(
            1 for entry in entries if entry.next_route == "reconcile_without_closeout"
        ),
        "closeout_gaps": sum(
            1
            for entry in entries
            if entry.next_route
            in {"run_reviewed_closeout", "recover_session_memory_archive", "inspect_runtime_trace"}
        ),
    }
    counts.update({f"lifecycle:{key}": value for key, value in sorted(lifecycle_counts.items())})
    counts.update({f"next_route:{key}": value for key, value in sorted(next_route_counts.items())})
    return counts


def _is_runtime_trace_gap(entry: CheckpointBacklogEntry) -> bool:
    return (
        not entry.active_runtime_scope
        and entry.runtime_trace_status in {"resolved", "recoverable"}
        and not entry.session_memory_archive_ref
    )


def _age_days(note_ref: str | None, *, checked_at: datetime) -> int | None:
    if not note_ref:
        return None
    observed = _note_observed_at(Path(note_ref))
    if observed is None:
        return None
    return max((checked_at.astimezone(UTC) - observed).days, 0)


def _note_observed_at(path: Path) -> datetime | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    candidates = [
        payload.get("runtime_session_created_at") if isinstance(payload, dict) else None,
        _first_history_observed_at(payload),
    ]
    for value in candidates:
        if not isinstance(value, str) or not value.strip():
            continue
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
        except ValueError:
            continue
    return None


def _first_history_observed_at(payload: object) -> str | None:
    if not isinstance(payload, dict):
        return None
    history = payload.get("checkpoint_history")
    if not isinstance(history, list) or not history:
        return None
    first = history[0]
    if not isinstance(first, dict):
        return None
    value = first.get("observed_at")
    return value if isinstance(value, str) else None
