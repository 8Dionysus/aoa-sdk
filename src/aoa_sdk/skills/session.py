from __future__ import annotations

import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from ..compatibility import load_surface
from ..models import ActiveSkillRecord, SkillDisclosure, SkillSession
from ..loaders import load_json, write_json
from ..workspace.discovery import Workspace
from .disclosure import build_allowlist_paths

DEFAULT_MUST_KEEP_SECTIONS = ("Intent", "Trigger boundary", "Procedure", "Verification")


def load_session_contract(workspace: Workspace) -> dict[str, Any]:
    return load_surface(workspace, "aoa-skills.runtime_session_contract")


def _nearest_existing_dir(path: Path) -> Path:
    current = path
    while not current.exists() and current.parent != current:
        current = current.parent
    return current if current.exists() else path.parent


def _is_parent_writable(path: Path) -> bool:
    if path.exists():
        return path.is_file() and os.access(path, os.W_OK)
    existing = _nearest_existing_dir(path.parent)
    return existing.is_dir() and os.access(existing, os.W_OK | os.X_OK)


def _safe_storage_name(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip())
    normalized = normalized.strip("-._")
    return normalized or "session"


def _thread_scoped_session_path(candidate: Path, thread_id: str) -> Path:
    suffix = candidate.suffix or ".json"
    return candidate.parent / "skill-runtime-sessions" / f"{_safe_storage_name(thread_id)}{suffix}"


def _default_session_path(
    workspace: Workspace,
    hint: str,
    *,
    thread_context: dict[str, Any] | None = None,
) -> Path:
    relative_hint = Path(hint)
    candidates: list[Path] = []
    if workspace.has_repo("aoa-sdk"):
        candidates.append(workspace.repo_path("aoa-sdk") / relative_hint)
    candidates.append(workspace.root / relative_hint)
    thread_id = (
        thread_context.get("codex_thread_id")
        if isinstance(thread_context, dict)
        else None
    )
    if isinstance(thread_id, str) and thread_id.strip():
        candidates = [_thread_scoped_session_path(candidate, thread_id.strip()) for candidate in candidates]

    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve(strict=False)
        if resolved in seen:
            continue
        seen.add(resolved)
        if _is_parent_writable(candidate):
            return candidate
    return candidates[0]


def resolve_session_file(workspace: Workspace, session_file: str | Path | None) -> Path:
    if session_file is None:
        hint = load_session_contract(workspace).get("session_file_hint", ".aoa/skill-runtime-session.json")
        return _default_session_path(
            workspace,
            hint,
            thread_context=resolve_codex_thread_context(),
        )

    path = Path(session_file)
    if path.is_absolute():
        return path
    return workspace.root / path


def load_session(workspace: Workspace, session_file: str | Path | None) -> SkillSession:
    path = resolve_session_file(workspace, session_file)
    return SkillSession.model_validate(load_json(path))


def probe_session(workspace: Workspace, session_file: str | Path | None) -> tuple[Path, SkillSession | None]:
    path = resolve_session_file(workspace, session_file)
    if not path.exists():
        return path, None
    return path, SkillSession.model_validate(load_json(path))


def resolve_codex_thread_context() -> dict[str, Any]:
    thread_id = os.environ.get("CODEX_THREAD_ID")
    if not isinstance(thread_id, str) or not thread_id.strip():
        return {}
    resolved_thread_id = thread_id.strip()
    context: dict[str, Any] = {"codex_thread_id": resolved_thread_id}
    state_db = Path.home() / ".codex" / "state_5.sqlite"
    if not state_db.exists():
        return context
    try:
        conn = sqlite3.connect(state_db)
        row = conn.execute(
            "select rollout_path, title, first_user_message, updated_at from threads where id = ?",
            (resolved_thread_id,),
        ).fetchone()
    except sqlite3.Error:
        return context
    finally:
        try:
            conn.close()
        except Exception:
            pass
    if row is None:
        return context
    rollout_path_value, title, first_user_message, updated_at = row
    if isinstance(rollout_path_value, str) and rollout_path_value.strip():
        rollout_path = Path(rollout_path_value).expanduser().resolve(strict=False)
        context["codex_rollout_path"] = str(rollout_path)
    if isinstance(title, str) and title.strip():
        context["codex_thread_title"] = title
    if isinstance(first_user_message, str) and first_user_message.strip():
        context["codex_first_user_message"] = first_user_message
    if isinstance(updated_at, int | float):
        normalized_updated_at = updated_at / 1000 if updated_at > 1_000_000_000_000 else updated_at
        context["codex_thread_updated_at"] = datetime.fromtimestamp(normalized_updated_at, timezone.utc)
    return context


def _new_skill_session(
    contract: dict[str, Any],
    *,
    now: datetime,
    thread_context: dict[str, Any] | None = None,
) -> SkillSession:
    return SkillSession(
        schema_version=contract.get("schema_version", 1),
        profile=contract.get("profile", "aoa-sdk"),
        session_id=str(uuid4()),
        created_at=now,
        updated_at=now,
        active_skills=[],
        activation_log=[],
        **(thread_context or {}),
    )


def _should_rotate_for_codex_thread(session: SkillSession, thread_context: dict[str, Any]) -> bool:
    current_thread_id = thread_context.get("codex_thread_id")
    if not isinstance(current_thread_id, str) or not current_thread_id:
        return False
    return session.codex_thread_id != current_thread_id


def _apply_codex_thread_context(session: SkillSession, thread_context: dict[str, Any]) -> bool:
    changed = False
    for field in (
        "codex_thread_id",
        "codex_rollout_path",
        "codex_thread_title",
        "codex_first_user_message",
        "codex_thread_updated_at",
    ):
        value = thread_context.get(field)
        if value is None or getattr(session, field) == value:
            continue
        setattr(session, field, value)
        changed = True
    return changed


def ensure_session(workspace: Workspace, session_file: str | Path | None) -> tuple[Path, SkillSession]:
    path = resolve_session_file(workspace, session_file)
    contract = load_session_contract(workspace)
    thread_context = resolve_codex_thread_context()
    if path.exists():
        session = load_session(workspace, path)
        if _should_rotate_for_codex_thread(session, thread_context):
            session = _new_skill_session(
                contract,
                now=datetime.now(timezone.utc),
                thread_context=thread_context,
            )
            save_session(path, session)
            return path, session
        if _apply_codex_thread_context(session, thread_context):
            save_session(path, session)
        return path, session

    session = _new_skill_session(
        contract,
        now=datetime.now(timezone.utc),
        thread_context=thread_context,
    )
    return path, session


def save_session(path: Path, session: SkillSession) -> None:
    write_json(path, session.model_dump(mode="json"))


def activate_session_skill(
    session: SkillSession,
    *,
    disclosure: SkillDisclosure,
    activated_at: datetime,
    explicit_handle: str | None,
    wrap_mode: str,
) -> SkillSession:
    must_keep = [
        heading
        for heading in DEFAULT_MUST_KEEP_SECTIONS
        if heading in disclosure.headings_available
    ]
    allowlist_paths = build_allowlist_paths(disclosure)
    compact_summary = disclosure.short_description or disclosure.description
    rehydration_hint = disclosure.path

    existing = next((record for record in session.active_skills if record.name == disclosure.name), None)
    if existing is None:
        session.active_skills.append(
            ActiveSkillRecord(
                name=disclosure.name,
                activated_at=activated_at,
                activation_count=1,
                protected_from_compaction=True,
                allowlist_paths=allowlist_paths,
                compact_summary=compact_summary,
                must_keep=must_keep,
                rehydration_hint=rehydration_hint,
            )
        )
    else:
        existing.activated_at = activated_at
        existing.activation_count += 1
        existing.allowlist_paths = sorted(set(existing.allowlist_paths) | set(allowlist_paths))
        existing.must_keep = sorted(set(existing.must_keep) | set(must_keep))
        existing.protected_from_compaction = True
        existing.compact_summary = compact_summary
        existing.rehydration_hint = rehydration_hint

    session.updated_at = activated_at
    session.activation_log.append(
        {
            "name": disclosure.name,
            "activated_at": activated_at.isoformat(),
            "explicit_handle": explicit_handle,
            "wrap_mode": wrap_mode,
        }
    )
    return session


def deactivate_session_skill(session: SkillSession, skill_name: str) -> SkillSession:
    session.active_skills = [record for record in session.active_skills if record.name != skill_name]
    session.updated_at = datetime.now(timezone.utc)
    return session


def compact_session(session: SkillSession) -> dict[str, Any]:
    return {
        "session_id": session.session_id,
        "active_skill_packets": [
            {
                "name": record.name,
                "compact_summary": record.compact_summary,
                "must_keep": record.must_keep,
                "allowlist_paths": record.allowlist_paths,
                "rehydration_hint": record.rehydration_hint,
            }
            for record in session.active_skills
        ],
        "reactivation_instructions": [
            f"Activate {record.name} from {record.rehydration_hint}"
            for record in session.active_skills
        ],
    }
