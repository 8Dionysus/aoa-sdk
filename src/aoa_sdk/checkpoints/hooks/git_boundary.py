"""Git hook templates and dirty-boundary helpers for checkpoints."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any, Literal, NamedTuple

from ...errors import RepoNotFound, SurfaceNotFound
from ...workspace.discovery import Workspace


CheckpointHookName = Literal["post-commit", "pre-push", "pre-merge-commit"]
CheckpointHookInstallStatus = Literal["missing", "stale", "current"]

CHECKPOINT_HOOK_TEMPLATE_VERSIONS: dict[CheckpointHookName, str] = {
    "post-commit": "aoa-sdk-post-commit-hook-v2",
    "pre-push": "aoa-sdk-pre-push-hook-v1",
    "pre-merge-commit": "aoa-sdk-pre-merge-commit-hook-v1",
}
CHECKPOINT_HOOK_MARKERS: dict[CheckpointHookName, str] = {
    "post-commit": "# aoa-sdk checkpoint post-commit hook v2",
    "pre-push": "# aoa-sdk checkpoint pre-push hook v1",
    "pre-merge-commit": "# aoa-sdk checkpoint pre-merge-commit hook v1",
}
CHECKPOINT_HOOK_WORKSPACE_ROOT_PLACEHOLDERS = (
    "__AOA_CHECKPOINT_WORKSPACE_ROOT__",
    "<workspace-root>",
)
IGNORABLE_UNTRACKED_DIRS = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
IGNORABLE_UNTRACKED_SUFFIXES = (".pyc", ".pyo", ".pyd")


class CheckpointHookStatusParts(NamedTuple):
    repo_root: Path
    hook_path: Path
    template_path: Path
    template_version: str
    status: CheckpointHookInstallStatus


def checkpoint_hook_status_parts(
    workspace: Workspace,
    *,
    repo_name: str,
    hook_name: CheckpointHookName,
) -> CheckpointHookStatusParts:
    repo_root = workspace.repo_path(repo_name)
    hook_path = resolve_git_hook_path(repo_root, hook_name)
    template_path = hook_template_path(workspace, hook_name)
    rendered = render_checkpoint_hook(workspace, hook_name)
    status: CheckpointHookInstallStatus
    if not hook_path.exists():
        status = "missing"
    else:
        existing = hook_path.read_text(encoding="utf-8")
        status = "current" if existing == rendered and os.access(hook_path, os.X_OK) else "stale"
    return CheckpointHookStatusParts(
        repo_root=repo_root,
        hook_path=hook_path,
        template_path=template_path,
        template_version=CHECKPOINT_HOOK_TEMPLATE_VERSIONS[hook_name],
        status=status,
    )


def read_git_commit_metadata(repo_root: Path, commit_ref: str) -> dict[str, Any]:
    show_result = run_git(repo_root, "show", "-s", "--format=%H%x00%h%x00%s%x00%b", commit_ref)
    parts = show_result.stdout.split("\x00", 3)
    while len(parts) < 4:
        parts.append("")
    commit_sha, commit_short_sha, commit_subject, commit_body = [part.rstrip("\n") for part in parts[:4]]
    changed_result = run_git(
        repo_root,
        "show",
        "--pretty=format:",
        "--name-only",
        "--diff-filter=ACDMRTUXB",
        commit_ref,
    )
    changed_paths = [
        line.strip()
        for line in changed_result.stdout.splitlines()
        if line.strip()
    ]
    return {
        "commit_sha": commit_sha,
        "commit_short_sha": commit_short_sha,
        "commit_subject": commit_subject,
        "commit_body": commit_body,
        "changed_paths": _dedupe_strings(changed_paths),
    }


def render_checkpoint_hook(
    workspace: Workspace,
    hook_name: CheckpointHookName,
) -> str:
    template = hook_template_path(workspace, hook_name).read_text(encoding="utf-8")
    marker = CHECKPOINT_HOOK_MARKERS[hook_name]
    if marker not in template:
        raise ValueError(f"{hook_name} hook template is missing the aoa-sdk version marker")
    rendered = template
    for placeholder in CHECKPOINT_HOOK_WORKSPACE_ROOT_PLACEHOLDERS:
        rendered = rendered.replace(placeholder, str(workspace.federation_root))
    return rendered


def ensure_repo_not_dirty(repo_root: Path, *, repo_name: str) -> None:
    if not (repo_root / ".git").exists():
        return
    result = subprocess.run(
        ["git", "-C", str(repo_root), "status", "--porcelain"],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return
    meaningful_lines = [
        line
        for line in result.stdout.splitlines()
        if line.strip() and not _is_ignorable_untracked_status(line, repo_root=repo_root)
    ]
    if meaningful_lines:
        raise SurfaceNotFound(f"{repo_name} is dirty; keep the reviewed promotion on the local checkpoint note for now")


def hook_template_path(
    workspace: Workspace,
    hook_name: CheckpointHookName,
) -> Path:
    public_entry_root = _repo_path_if_available(workspace, "8Dionysus")
    if public_entry_root is not None:
        public_entry_candidate = public_entry_root / "config" / "git_hooks" / f"{hook_name}.sh"
        if public_entry_candidate.exists():
            return public_entry_candidate

    workspace_candidate: Path | None = None
    sdk_root = _repo_path_if_available(workspace, "aoa-sdk")
    if sdk_root is not None:
        workspace_candidate = (
            sdk_root
            / "mechanics"
            / "checkpoint"
            / "parts"
            / "session-growth-checkpoint-cycle"
            / "git-boundary-hook-templates"
            / hook_name
        )
        if workspace_candidate.exists():
            return workspace_candidate
    package_candidate = (
        Path(__file__).resolve().parents[4]
        / "mechanics"
        / "checkpoint"
        / "parts"
        / "session-growth-checkpoint-cycle"
        / "git-boundary-hook-templates"
        / hook_name
    )
    if package_candidate.exists():
        return package_candidate
    if workspace_candidate is not None:
        return workspace_candidate
    return package_candidate


def resolve_git_hook_path(
    repo_root: Path,
    hook_name: CheckpointHookName,
) -> Path:
    result = run_git(repo_root, "rev-parse", "--git-path", f"hooks/{hook_name}")
    raw_path = result.stdout.strip()
    hook_path = Path(raw_path)
    if hook_path.is_absolute():
        return hook_path
    return (repo_root / hook_path).resolve()


def run_git(repo_root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if check and result.returncode != 0:
        stderr = result.stderr.strip()
        stdout = result.stdout.strip()
        detail = stderr or stdout or f"git exited {result.returncode}"
        raise RuntimeError(f"git {' '.join(args)} failed for {repo_root}: {detail}")
    return result


def _repo_path_if_available(workspace: Workspace, repo_name: str) -> Path | None:
    try:
        return workspace.repo_path(repo_name)
    except RepoNotFound:
        return None


def _is_ignorable_untracked_status(line: str, *, repo_root: Path) -> bool:
    if not line.startswith("?? "):
        return False
    raw_path = line[3:].strip()
    candidate = repo_root / raw_path.rstrip("/\\")
    if candidate.is_dir():
        return _directory_contains_only_ignorable_cache(candidate)
    return _is_ignorable_cache_path(raw_path)


def _directory_contains_only_ignorable_cache(directory: Path) -> bool:
    for path in directory.rglob("*"):
        if path.is_dir():
            continue
        if not _is_ignorable_cache_path(str(path.relative_to(directory))):
            return False
    return True


def _is_ignorable_cache_path(raw_path: str) -> bool:
    normalized = raw_path.replace("\\", "/")
    parts = [part for part in normalized.split("/") if part]
    if any(part in IGNORABLE_UNTRACKED_DIRS for part in parts):
        return True
    return normalized.endswith(IGNORABLE_UNTRACKED_SUFFIXES)


def _dedupe_strings(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))
