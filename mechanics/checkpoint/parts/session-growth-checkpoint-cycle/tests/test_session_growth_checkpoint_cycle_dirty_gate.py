from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from aoa_sdk import AoASDK
from aoa_sdk.errors import SurfaceNotFound


def _init_clean_git_repo(repo_root: Path) -> None:
    repo_root.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-b", "main", str(repo_root)], check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(repo_root), "config", "user.name", "Codex"], check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "-C", str(repo_root), "config", "user.email", "codex@example.invalid"],
        check=True,
        capture_output=True,
        text=True,
    )
    (repo_root / "README.md").write_text("# Dionysus\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo_root), "add", "README.md"], check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(repo_root), "commit", "-m", "init"], check=True, capture_output=True, text=True)


def _prepare_reviewable_checkpoint_note(workspace_root: Path) -> AoASDK:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    sdk.checkpoints.append(
        repo_root=str(workspace_root / "aoa-sdk"),
        checkpoint_kind="commit",
        intent_text="recurring workflow needs better handoff proof and recall",
    )
    sdk.checkpoints.append(
        repo_root=str(workspace_root / "aoa-sdk"),
        checkpoint_kind="verify_green",
        intent_text="recurring workflow needs better handoff proof and recall",
    )
    return sdk


def test_checkpoint_promote_to_dionysus_ignores_ephemeral_cache_noise(workspace_root: Path) -> None:
    dionysus_root = workspace_root / "Dionysus"
    _init_clean_git_repo(dionysus_root)
    (dionysus_root / "scripts" / "__pycache__").mkdir(parents=True, exist_ok=True)
    (dionysus_root / "scripts" / "__pycache__" / "validate_seed_surfaces.cpython-314.pyc").write_bytes(b"cache")
    (dionysus_root / "tests" / "__pycache__").mkdir(parents=True, exist_ok=True)
    (dionysus_root / "tests" / "__pycache__" / "test_validate_seed_surfaces.cpython-314.pyc").write_bytes(b"cache")

    sdk = _prepare_reviewable_checkpoint_note(workspace_root)

    promotion = sdk.checkpoints.promote(
        repo_root=str(workspace_root / "aoa-sdk"),
        target="dionysus-note",
    )

    promoted_json = list((dionysus_root / "reports" / "ecosystem-audits").glob("*.aoa-sdk.checkpoint-note.json"))
    assert promotion.target == "dionysus-note"
    assert promoted_json


def test_checkpoint_promote_to_dionysus_blocks_meaningful_dirty_state(workspace_root: Path) -> None:
    dionysus_root = workspace_root / "Dionysus"
    _init_clean_git_repo(dionysus_root)
    (dionysus_root / "scratch-note.md").write_text("meaningful local tail\n", encoding="utf-8")

    sdk = _prepare_reviewable_checkpoint_note(workspace_root)

    with pytest.raises(SurfaceNotFound, match="Dionysus is dirty"):
        sdk.checkpoints.promote(
            repo_root=str(workspace_root / "aoa-sdk"),
            target="dionysus-note",
        )
