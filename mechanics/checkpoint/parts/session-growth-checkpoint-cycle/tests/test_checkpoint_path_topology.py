from __future__ import annotations

from pathlib import Path

from aoa_sdk.checkpoints.topology import (
    checkpoint_current_root,
    checkpoint_paths_for_label,
    checkpoint_runtime_scope_key,
    post_commit_status_path,
)
from aoa_sdk.workspace.discovery import Workspace


def test_checkpoint_path_topology_names_runtime_scope(workspace_root: Path) -> None:
    workspace = Workspace.discover(workspace_root / "aoa-sdk")
    runtime_session_id = "thread:alpha/beta"

    paths = checkpoint_paths_for_label(
        workspace,
        "aoa-sdk",
        runtime_session_id=runtime_session_id,
    )

    current_root = workspace_root / "aoa-sdk" / ".aoa" / "session-growth" / "current"
    assert checkpoint_runtime_scope_key(runtime_session_id) == "thread-alpha-beta"
    assert checkpoint_current_root(workspace) == current_root
    assert paths.current_dir == current_root / "thread-alpha-beta" / "aoa-sdk"
    assert paths.jsonl == paths.current_dir / "checkpoint-note.jsonl"
    assert paths.note_json == paths.current_dir / "checkpoint-note.json"
    assert paths.surface_report == (
        workspace_root / "aoa-sdk" / ".aoa" / "surface-detection" / "aoa-sdk.checkpoint.latest.json"
    )
    assert post_commit_status_path(workspace, "aoa-sdk") == (
        workspace_root / "aoa-sdk" / ".aoa" / "session-growth" / "post-commit-status" / "aoa-sdk.latest.json"
    )
