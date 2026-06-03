"""Checkpoint runtime-session reconciliation for sessions closed without closeout."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from ..models import CheckpointLifecycleEntry, CheckpointSessionReconcileResult
from ..workspace.discovery import Workspace
from .indexes import write_checkpoint_lifecycle_index
from .lifecycle import (
    archive_checkpoint_entry_without_closeout,
    audit_checkpoint_lifecycle,
    close_and_archive_checkpoint_entry,
)
from .timestamps import local_timestamp_parts


RECONCILE_ARCHIVE_STATES = {
    "closeout_executed",
    "session_closed_reviewed_no_closeout",
    "session_closed_collecting_no_closeout",
}

RECONCILE_BLOCKED_STATES = {
    "pending_review",
    "session_closed_pending_review",
}


def reconcile_closed_checkpoint_sessions(
    *,
    workspace: Workspace,
    repo_root: str | None = None,
    session_file: str | None = None,
    runtime_session_id: str | None = None,
    session_filter: str | None = None,
    since: str | None = None,
    until: str | None = None,
    dry_run: bool = True,
    write_index: bool = True,
) -> CheckpointSessionReconcileResult:
    executed_at, executed_at_local, executed_tz = local_timestamp_parts()
    audit = audit_checkpoint_lifecycle(
        workspace=workspace,
        repo_root=repo_root,
        session_file=session_file,
    )
    selected_entries: list[CheckpointLifecycleEntry] = []
    archived_entries: list[CheckpointLifecycleEntry] = []
    skipped_entries: list[CheckpointLifecycleEntry] = []
    required_actions: list[str] = []
    archive_refs: list[str] = []
    notes: list[str] = []

    for entry in audit.entries:
        if runtime_session_id is not None and not _matches_runtime(entry, runtime_session_id):
            continue
        if session_filter and not _matches_session_filter(entry, session_filter):
            continue
        if not _matches_time_filter(entry, since=since, until=until):
            continue
        selected_entries.append(entry)

        if entry.lifecycle_state in RECONCILE_BLOCKED_STATES:
            skipped_entries.append(entry)
            if entry.required_action:
                required_actions.append(entry.required_action)
            continue
        if entry.lifecycle_state not in RECONCILE_ARCHIVE_STATES:
            skipped_entries.append(entry)
            continue

        archived_entries.append(entry)
        if dry_run:
            continue
        archive_ref = _archive_entry(workspace=workspace, entry=entry)
        archive_refs.append(str(archive_ref))

    index_ref: str | None = None
    if write_index:
        post_report = (
            audit
            if dry_run
            else audit_checkpoint_lifecycle(
                workspace=workspace,
                repo_root=repo_root,
                session_file=session_file,
            )
        )
        index_ref = str(write_checkpoint_lifecycle_index(workspace=workspace, report=post_report))

    if dry_run:
        notes.append("dry-run only; no checkpoint files were moved")
    notes.append(
        "reconcile-sessions is bounded checkpoint preservation; it does not run reviewed closeout"
    )
    notes.append("aoa-session-memory archives were read as route evidence only and were not mutated")

    return CheckpointSessionReconcileResult(
        executed_at=executed_at,
        executed_at_local=executed_at_local,
        executed_tz=executed_tz,
        dry_run=dry_run,
        repo_root=audit.repo_root,
        repo_label=audit.repo_label,
        runtime_session_id=runtime_session_id,
        session_filter=session_filter,
        since=since,
        until=until,
        selected_count=len(selected_entries),
        archived_count=len(archived_entries),
        skipped_count=len(skipped_entries),
        required_action_count=len(_dedupe(required_actions)),
        archived_entries=archived_entries,
        skipped_entries=skipped_entries,
        required_actions=_dedupe(required_actions),
        archive_refs=archive_refs,
        generated_index_ref=index_ref,
        notes=notes,
    )


def _archive_entry(*, workspace: Workspace, entry: CheckpointLifecycleEntry) -> Path:
    if entry.lifecycle_state == "closeout_executed":
        return close_and_archive_checkpoint_entry(workspace=workspace, entry=entry)
    return archive_checkpoint_entry_without_closeout(workspace=workspace, entry=entry)


def _matches_runtime(entry: CheckpointLifecycleEntry, runtime_session_id: str) -> bool:
    return entry.runtime_session_id == runtime_session_id or entry.runtime_scope_key == runtime_session_id


def _matches_session_filter(entry: CheckpointLifecycleEntry, session_filter: str) -> bool:
    needle = session_filter.strip().lower()
    haystacks = [
        entry.runtime_session_id,
        entry.runtime_scope_key,
        entry.session_ref,
        entry.session_memory_session_id,
        entry.session_memory_archive_ref,
        entry.note_ref,
        entry.current_dir,
    ]
    return any(needle in value.lower() for value in haystacks if isinstance(value, str))


def _matches_time_filter(
    entry: CheckpointLifecycleEntry,
    *,
    since: str | None,
    until: str | None,
) -> bool:
    if since is None and until is None:
        return True
    observed = _entry_datetime(entry)
    if observed is None:
        return False
    if since is not None and observed < _parse_date_boundary(since, end=False):
        return False
    if until is not None and observed > _parse_date_boundary(until, end=True):
        return False
    return True


def _entry_datetime(entry: CheckpointLifecycleEntry) -> datetime | None:
    note_ref = Path(entry.note_ref) if entry.note_ref else Path(entry.current_dir) / "checkpoint-note.json"
    try:
        import json

        payload = json.loads(note_ref.read_text(encoding="utf-8"))
    except Exception:
        payload = {}
    for value in [
        payload.get("runtime_session_created_at") if isinstance(payload, dict) else None,
        _first_history_observed_at(payload),
    ]:
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


def _parse_date_boundary(value: str, *, end: bool) -> datetime:
    stripped = value.strip()
    if len(stripped) == 10:
        suffix = "T23:59:59.999999+00:00" if end else "T00:00:00+00:00"
        return datetime.fromisoformat(stripped + suffix).astimezone(UTC)
    return datetime.fromisoformat(stripped.replace("Z", "+00:00")).astimezone(UTC)


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))
