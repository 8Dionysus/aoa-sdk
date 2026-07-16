"""Read-only host runtime-session lookup for checkpoint state."""

from __future__ import annotations

import json
import os
import sqlite3
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, cast

from ...errors import InvalidSurface
from ...loaders import load_json
from ...models import CheckpointRuntimeSessionRef
from ...workspace.discovery import Workspace


AFTER_COMMIT_SESSION_PROBE_ATTEMPTS = 3
AFTER_COMMIT_SESSION_PROBE_DELAY_SECONDS = 0.05
RUNTIME_SESSION_FILE_ENV = "AOA_RUNTIME_SESSION_FILE"
RUNTIME_SESSION_ID_ENV = "AOA_SESSION_ID"
RUNTIME_SESSION_CREATED_AT_ENV = "AOA_SESSION_CREATED_AT"
CODEX_THREAD_ID_ENV = "CODEX_THREAD_ID"
CODEX_ROLLOUT_PATH_ENV = "CODEX_ROLLOUT_PATH"

CheckpointRuntimeSessionMetadata = dict[str, str | datetime | None]


def resolve_checkpoint_runtime_session_identity(
    *,
    workspace: Workspace,
    runtime_session_file: str | None,
) -> tuple[str | None, datetime | None]:
    _, runtime_session = resolve_checkpoint_runtime_session(
        workspace=workspace,
        runtime_session_file=runtime_session_file,
    )
    if runtime_session is None:
        return None, None
    return runtime_session.session_id, runtime_session.created_at


def resolve_checkpoint_runtime_session(
    *,
    workspace: Workspace,
    runtime_session_file: str | None,
) -> tuple[Path | None, CheckpointRuntimeSessionRef | None]:
    """Resolve an external runtime identity without creating or changing state."""

    metadata_path = resolve_runtime_session_file(workspace, runtime_session_file)
    host_ref = _runtime_session_from_host_environment()
    if metadata_path is None:
        return None, host_ref
    if not metadata_path.is_file():
        raise InvalidSurface(f"runtime session metadata file does not exist: {metadata_path}")

    metadata_ref = _runtime_session_from_metadata_file(metadata_path)
    _validate_host_metadata_alignment(host_ref=host_ref, metadata_ref=metadata_ref)
    return metadata_path, metadata_ref


def load_checkpoint_runtime_session(
    *,
    workspace: Workspace,
    runtime_session_file: str | None,
) -> CheckpointRuntimeSessionMetadata:
    try:
        _, runtime_session = resolve_checkpoint_runtime_session(
            workspace=workspace,
            runtime_session_file=runtime_session_file,
        )
    except InvalidSurface:
        return _empty_metadata()
    return _metadata_from_session(runtime_session)


def probe_checkpoint_runtime_session(
    *,
    workspace: Workspace,
    runtime_session_file: str | None,
) -> tuple[Path | None, CheckpointRuntimeSessionMetadata]:
    metadata_path = resolve_runtime_session_file(workspace, runtime_session_file)
    try:
        metadata_path, runtime_session = resolve_checkpoint_runtime_session(
            workspace=workspace,
            runtime_session_file=runtime_session_file,
        )
    except InvalidSurface:
        return metadata_path, _empty_metadata()
    return metadata_path, _metadata_from_session(runtime_session)


def peek_checkpoint_runtime_session(
    *,
    workspace: Workspace,
    runtime_session_file: str | None,
) -> CheckpointRuntimeSessionMetadata:
    _, metadata = probe_checkpoint_runtime_session(workspace=workspace, runtime_session_file=runtime_session_file)
    return metadata


def probe_existing_checkpoint_runtime_session(
    *,
    workspace: Workspace,
    runtime_session_file: str | None,
) -> tuple[Path | None, CheckpointRuntimeSessionRef | None]:
    metadata_path = resolve_runtime_session_file(workspace, runtime_session_file)
    try:
        return resolve_checkpoint_runtime_session(
            workspace=workspace,
            runtime_session_file=runtime_session_file,
        )
    except InvalidSurface:
        return metadata_path, None


def probe_active_runtime_session_for_after_commit(
    workspace: Workspace,
    runtime_session_file: str | None,
) -> tuple[Path | None, CheckpointRuntimeSessionRef | None, str | None]:
    metadata_path = resolve_runtime_session_file(workspace, runtime_session_file)
    if metadata_path is None:
        try:
            _, runtime_session = resolve_checkpoint_runtime_session(
                workspace=workspace,
                runtime_session_file=None,
            )
            return None, runtime_session, None
        except InvalidSurface as exc:
            return None, None, str(exc)

    if not metadata_path.exists():
        return metadata_path, None, f"runtime session metadata file does not exist: {metadata_path}"

    last_error: InvalidSurface | None = None
    for attempt in range(AFTER_COMMIT_SESSION_PROBE_ATTEMPTS):
        try:
            _, runtime_session = resolve_checkpoint_runtime_session(
                workspace=workspace,
                runtime_session_file=str(metadata_path),
            )
            return metadata_path, runtime_session, None
        except InvalidSurface as exc:
            last_error = exc
            if attempt + 1 < AFTER_COMMIT_SESSION_PROBE_ATTEMPTS:
                time.sleep(AFTER_COMMIT_SESSION_PROBE_DELAY_SECONDS)

    return (
        metadata_path,
        None,
        f"runtime session metadata exists but could not be read: {last_error}",
    )


def resolve_runtime_session_file(
    workspace: Workspace,
    runtime_session_file: str | Path | None,
) -> Path | None:
    candidate = runtime_session_file
    if candidate is None:
        candidate = os.environ.get(RUNTIME_SESSION_FILE_ENV)
    if not isinstance(candidate, (str, Path)) or not str(candidate).strip():
        return None
    path = Path(candidate).expanduser()
    if path.is_absolute():
        return path.resolve(strict=False)
    return (workspace.root / path).resolve(strict=False)


def _runtime_session_from_metadata_file(path: Path) -> CheckpointRuntimeSessionRef:
    try:
        payload = load_json(path)
    except (OSError, json.JSONDecodeError) as exc:
        raise InvalidSurface(f"runtime session metadata is not valid JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise InvalidSurface(f"runtime session metadata must be a JSON object: {path}")

    session_id = _string_value(payload, "session_id") or _string_value(
        payload, "codex_thread_id"
    )
    if session_id is None:
        raise InvalidSurface(
            "runtime session metadata requires session_id or codex_thread_id: " f"{path}"
        )
    source: Literal["explicit-metadata", "legacy-skill-session"] = (
        "legacy-skill-session"
        if any(key in payload for key in ("active_skills", "activation_log", "profile"))
        else "explicit-metadata"
    )
    return CheckpointRuntimeSessionRef(
        source=source,
        session_id=session_id,
        created_at=_datetime_value(payload.get("created_at")),
        codex_thread_id=_string_value(payload, "codex_thread_id"),
        codex_rollout_path=_normalized_path_value(payload, "codex_rollout_path"),
        codex_thread_title=_string_value(payload, "codex_thread_title"),
        codex_first_user_message=_string_value(payload, "codex_first_user_message"),
        codex_thread_updated_at=_datetime_value(payload.get("codex_thread_updated_at")),
        metadata_file_ref=str(path),
        evidence_refs=[str(path)],
    )


def _runtime_session_from_host_environment() -> CheckpointRuntimeSessionRef | None:
    explicit_session_id = _normalized_env(RUNTIME_SESSION_ID_ENV)
    thread_id = _normalized_env(CODEX_THREAD_ID_ENV)
    session_id = explicit_session_id or thread_id
    if session_id is None:
        return None

    context = _codex_thread_context(thread_id)
    rollout_path = _normalized_env(CODEX_ROLLOUT_PATH_ENV) or cast(
        str | None, context.get("codex_rollout_path")
    )
    evidence_refs: list[str] = []
    if explicit_session_id is not None:
        evidence_refs.append(f"env:{RUNTIME_SESSION_ID_ENV}")
    if thread_id is not None:
        evidence_refs.append(f"env:{CODEX_THREAD_ID_ENV}")
    if _normalized_env(CODEX_ROLLOUT_PATH_ENV) is not None:
        evidence_refs.append(f"env:{CODEX_ROLLOUT_PATH_ENV}")
    state_db_ref = context.get("state_db_ref")
    if isinstance(state_db_ref, str):
        evidence_refs.append(state_db_ref)
    return CheckpointRuntimeSessionRef(
        source="host-environment",
        session_id=session_id,
        created_at=_datetime_value(_normalized_env(RUNTIME_SESSION_CREATED_AT_ENV)),
        codex_thread_id=thread_id,
        codex_rollout_path=rollout_path,
        codex_thread_title=cast(str | None, context.get("codex_thread_title")),
        codex_first_user_message=cast(str | None, context.get("codex_first_user_message")),
        codex_thread_updated_at=cast(datetime | None, context.get("codex_thread_updated_at")),
        evidence_refs=evidence_refs,
    )


def _codex_thread_context(thread_id: str | None) -> dict[str, str | datetime]:
    if thread_id is None:
        return {}
    state_db = Path.home() / ".codex" / "state_5.sqlite"
    if not state_db.is_file():
        return {}
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(f"file:{state_db}?mode=ro", uri=True)
        row = connection.execute(
            "select rollout_path, title, first_user_message, updated_at from threads where id = ?",
            (thread_id,),
        ).fetchone()
    except sqlite3.Error:
        return {}
    finally:
        if connection is not None:
            connection.close()
    if row is None:
        return {}

    rollout_path, title, first_user_message, updated_at = row
    context: dict[str, str | datetime] = {"state_db_ref": str(state_db)}
    if isinstance(rollout_path, str) and rollout_path.strip():
        context["codex_rollout_path"] = str(
            Path(rollout_path).expanduser().resolve(strict=False)
        )
    if isinstance(title, str) and title.strip():
        context["codex_thread_title"] = title.strip()
    if isinstance(first_user_message, str) and first_user_message.strip():
        context["codex_first_user_message"] = first_user_message.strip()
    normalized_updated_at = _datetime_value(updated_at)
    if normalized_updated_at is not None:
        context["codex_thread_updated_at"] = normalized_updated_at
    return context


def _validate_host_metadata_alignment(
    *,
    host_ref: CheckpointRuntimeSessionRef | None,
    metadata_ref: CheckpointRuntimeSessionRef,
) -> None:
    if host_ref is None:
        return
    if (
        host_ref.codex_thread_id is not None
        and metadata_ref.codex_thread_id is not None
        and host_ref.codex_thread_id != metadata_ref.codex_thread_id
    ):
        raise InvalidSurface(
            "runtime session metadata belongs to a different Codex thread: "
            f"{metadata_ref.metadata_file_ref}"
        )
    explicit_session_id = _normalized_env(RUNTIME_SESSION_ID_ENV)
    if explicit_session_id is not None and metadata_ref.session_id != explicit_session_id:
        raise InvalidSurface(
            "runtime session metadata session_id conflicts with AOA_SESSION_ID: "
            f"{metadata_ref.metadata_file_ref}"
        )


def _metadata_from_session(
    runtime_session: CheckpointRuntimeSessionRef | None,
) -> CheckpointRuntimeSessionMetadata:
    if runtime_session is None:
        return _empty_metadata()
    return {
        "runtime_session_id": runtime_session.session_id,
        "runtime_session_created_at": (
            runtime_session.created_at.astimezone(UTC)
            if runtime_session.created_at is not None
            else None
        ),
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


def _normalized_env(name: str) -> str | None:
    value = os.environ.get(name)
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()


def _string_value(payload: dict[str, Any], key: str) -> str | None:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()


def _normalized_path_value(payload: dict[str, Any], key: str) -> str | None:
    value = _string_value(payload, key)
    if value is None:
        return None
    return str(Path(value).expanduser().resolve(strict=False))


def _datetime_value(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, (int, float)):
        timestamp_value = value / 1000 if value > 1_000_000_000_000 else value
        try:
            parsed = datetime.fromtimestamp(timestamp_value, UTC)
        except (OverflowError, OSError, ValueError):
            return None
    elif isinstance(value, str) and value.strip():
        iso_value = value.strip().replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(iso_value)
        except ValueError:
            return None
    else:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)
