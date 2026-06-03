"""Filesystem path topology for checkpoint session-growth state."""

from __future__ import annotations

import re
from pathlib import Path

from ...workspace.discovery import Workspace


class CheckpointPaths:
    def __init__(
        self,
        *,
        root: Path,
        repo_label: str,
        current_dir: Path,
        surface_report: Path,
        runtime_session_id: str | None,
        runtime_scope_key: str | None,
    ) -> None:
        self.root = root
        self.repo_label = repo_label
        self.current_dir = current_dir
        self.runtime_session_id = runtime_session_id
        self.runtime_scope_key = runtime_scope_key
        self.jsonl = current_dir / "checkpoint-note.jsonl"
        self.note_json = current_dir / "checkpoint-note.json"
        self.note_md = current_dir / "checkpoint-note.md"
        self.harvest_handoff = current_dir / "harvest-handoff.json"
        self.closeout_context = current_dir / "closeout-context.json"
        self.closeout_execution_report = current_dir / "closeout-execution-report.json"
        self.closeout_artifacts = current_dir / "reviewed-closeout"
        self.post_commit_report = current_dir / "post-commit-report.json"
        self.surface_report = surface_report


def checkpoint_current_root(workspace: Workspace) -> Path:
    return workspace.repo_path("aoa-sdk") / ".aoa" / "session-growth" / "current"


def checkpoint_post_commit_status_root(workspace: Workspace) -> Path:
    return workspace.repo_path("aoa-sdk") / ".aoa" / "session-growth" / "post-commit-status"


def checkpoint_runtime_scope_key(runtime_session_id: str | None) -> str | None:
    if runtime_session_id is None:
        return None
    return _safe_path_name(runtime_session_id)


def checkpoint_paths_for_label(
    workspace: Workspace,
    repo_label: str,
    *,
    runtime_session_id: str | None = None,
) -> CheckpointPaths:
    sdk_root = workspace.repo_path("aoa-sdk")
    current_root = checkpoint_current_root(workspace)
    runtime_scope_key = checkpoint_runtime_scope_key(runtime_session_id)
    current_dir = (
        current_root / runtime_scope_key / repo_label
        if runtime_scope_key is not None
        else current_root / repo_label
    )
    surface_report = sdk_root / ".aoa" / "surface-detection" / f"{repo_label}.checkpoint.latest.json"
    return CheckpointPaths(
        root=sdk_root,
        repo_label=repo_label,
        current_dir=current_dir,
        surface_report=surface_report,
        runtime_session_id=runtime_session_id,
        runtime_scope_key=runtime_scope_key,
    )


def post_commit_status_path(workspace: Workspace, repo_label: str) -> Path:
    return checkpoint_post_commit_status_root(workspace) / f"{repo_label}.latest.json"


def _safe_path_name(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip())
    normalized = normalized.strip("-._")
    return normalized or "session"
