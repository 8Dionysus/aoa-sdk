"""Runtime-session lookup for checkpoint state."""

from __future__ import annotations

import time
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from ...errors import InvalidSurface
from ...models import SkillSession
from ...skills.session import ensure_session, load_session, probe_session, resolve_session_file, save_session
from ...workspace.discovery import Workspace


AFTER_COMMIT_SESSION_PROBE_ATTEMPTS = 3
AFTER_COMMIT_SESSION_PROBE_DELAY_SECONDS = 0.05

CheckpointRuntimeSessionMetadata = dict[str, str | datetime | None]


def ensure_checkpoint_runtime_session(
    *,
    workspace: Workspace,
    session_file: str | None,
) -> tuple[str | None, datetime | None]:
    metadata = load_checkpoint_runtime_session(workspace=workspace, session_file=session_file)
    return (
        cast(str | None, metadata["runtime_session_id"]),
        cast(datetime | None, metadata["runtime_session_created_at"]),
    )


def load_checkpoint_runtime_session(
    *,
    workspace: Workspace,
    session_file: str | None,
) -> CheckpointRuntimeSessionMetadata:
    try:
        session_path, runtime_session = ensure_session(workspace, session_file)
        if not session_path.exists():
            session_path.parent.mkdir(parents=True, exist_ok=True)
            save_session(session_path, runtime_session)
        return _metadata_from_session(runtime_session)
    except Exception:
        return _empty_metadata()


def probe_checkpoint_runtime_session(
    *,
    workspace: Workspace,
    session_file: str | None,
) -> tuple[Path, CheckpointRuntimeSessionMetadata]:
    session_path = resolve_session_file(workspace, session_file)
    try:
        session_path, runtime_session = probe_session(workspace, session_file)
        if runtime_session is None:
            return session_path, _empty_metadata()
        return session_path, _metadata_from_session(runtime_session)
    except Exception:
        return session_path, _empty_metadata()


def peek_checkpoint_runtime_session(
    *,
    workspace: Workspace,
    session_file: str | None,
) -> CheckpointRuntimeSessionMetadata:
    _, metadata = probe_checkpoint_runtime_session(workspace=workspace, session_file=session_file)
    return metadata


def probe_existing_checkpoint_runtime_session(
    *,
    workspace: Workspace,
    session_file: str | None,
) -> tuple[Path, SkillSession | None]:
    session_path = resolve_session_file(workspace, session_file)
    try:
        return probe_session(workspace, session_file)
    except Exception:
        return session_path, None


def probe_active_runtime_session_for_after_commit(
    workspace: Workspace,
    session_file: str | None,
) -> tuple[Path, SkillSession | None, str | None]:
    session_path = resolve_session_file(workspace, session_file)
    if not session_path.exists():
        return session_path, None, None

    last_error: InvalidSurface | None = None
    for attempt in range(AFTER_COMMIT_SESSION_PROBE_ATTEMPTS):
        try:
            return session_path, load_session(workspace, str(session_path)), None
        except InvalidSurface as exc:
            last_error = exc
            if attempt + 1 < AFTER_COMMIT_SESSION_PROBE_ATTEMPTS:
                time.sleep(AFTER_COMMIT_SESSION_PROBE_DELAY_SECONDS)
                continue

    error_text = (
        f"active runtime session exists but could not be read: {last_error}"
        if last_error is not None
        else "active runtime session exists but could not be read"
    )
    return session_path, None, error_text


def _metadata_from_session(runtime_session: SkillSession) -> CheckpointRuntimeSessionMetadata:
    return {
        "runtime_session_id": runtime_session.session_id,
        "runtime_session_created_at": runtime_session.created_at.astimezone(UTC),
        "session_trace_ref": runtime_session.codex_rollout_path,
        "session_trace_thread_id": runtime_session.codex_thread_id,
    }


def _empty_metadata() -> CheckpointRuntimeSessionMetadata:
    return {
        "runtime_session_id": None,
        "runtime_session_created_at": None,
        "session_trace_ref": None,
        "session_trace_thread_id": None,
    }
