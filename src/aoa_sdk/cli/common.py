from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal, TypeAlias, cast

import typer

from ..loaders import load_json
from ..models import (
    CheckpointCaptureResult,
    SessionCheckpointNote,
    SkillDetectionReport,
    SurfaceCloseoutHandoff,
    SurfaceDetectionReport,
)
from ..workspace.discovery import Workspace
from ..workspace.roots import KNOWN_REPOS


OWNER_CHECKPOINT_HOOK_REPOS = tuple(repo for repo in KNOWN_REPOS if repo != "8Dionysus")
CheckpointManagedHookName: TypeAlias = Literal["post-commit", "pre-push", "pre-merge-commit"]
CHECKPOINT_MANAGED_HOOKS: tuple[CheckpointManagedHookName, ...] = (
    "post-commit",
    "pre-push",
    "pre-merge-commit",
)


def _workspace_payload(workspace: Workspace) -> dict[str, Any]:
    repos: dict[str, dict[str, str | None]] = {}
    for repo in KNOWN_REPOS:
        path = workspace.repo_roots.get(repo)
        origin = workspace.repo_origins.get(repo)
        repos[repo] = {
            "path": str(path) if path is not None else None,
            "origin": origin,
        }
    return {
        "root": str(workspace.root),
        "federation_root": str(workspace.federation_root),
        "federation_root_source": workspace.federation_root_source,
        "manifest": str(workspace.manifest_path) if workspace.manifest_path else None,
        "repos": repos,
    }

def _resolve_host_available_skills(
    *,
    host_skills: list[str],
    host_skill_manifest: str | None,
) -> tuple[list[str] | None, str]:
    if host_skills:
        return list(dict.fromkeys(skill_name for skill_name in host_skills if skill_name)), "host-skill-list"
    if host_skill_manifest is None:
        return None, "not-provided"

    manifest_path = Path(host_skill_manifest).expanduser().resolve()
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise typer.BadParameter(f"could not read host skill manifest: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise typer.BadParameter(f"host skill manifest is not valid JSON: {exc}") from exc

    if not isinstance(payload, dict):
        raise typer.BadParameter("host skill manifest must be a JSON object with a non-empty string list at 'skills'")
    skills = payload.get("skills")
    if not isinstance(skills, list) or not all(isinstance(item, str) and item for item in skills):
        raise typer.BadParameter("host skill manifest must be a JSON object with a non-empty string list at 'skills'")
    return list(dict.fromkeys(skills)), "host-manifest"

def _resolve_context_root(workspace: Workspace, repo_root: str) -> Path:
    resolved_repo_root = Path(repo_root).expanduser()
    if not resolved_repo_root.is_absolute():
        return (workspace.root / resolved_repo_root).resolve()
    return resolved_repo_root.resolve()

def _resolve_context_label(workspace: Workspace, repo_root: str) -> str:
    resolved_repo_root = _resolve_context_root(workspace, repo_root)
    return "workspace" if resolved_repo_root == workspace.federation_root else resolved_repo_root.name

def _resolve_skill_report_path(
    *,
    workspace: Workspace,
    repo_root: str,
    phase: str,
    mutation_surface: str = "none",
    report_output: str | None = None,
) -> Path:
    if report_output is not None:
        return Path(report_output).expanduser().resolve()

    label = _resolve_context_label(workspace, repo_root)
    suffix = phase
    if phase == "pre-mutation":
        suffix = f"{phase}-{mutation_surface}"
    return workspace.repo_path("aoa-sdk") / ".aoa" / "skill-dispatch" / f"{label}.{suffix}.latest.json"

def _write_skill_report(path: Path, report: SkillDetectionReport) -> dict[str, Any]:
    payload = {
        "report_path": str(path),
        "report": report.model_dump(mode="json"),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return payload

def _resolve_surface_report_path(
    *,
    workspace: Workspace,
    repo_root: str,
    phase: str,
    report_output: str | None = None,
) -> Path:
    if report_output is not None:
        return Path(report_output).expanduser().resolve()
    label = _resolve_context_label(workspace, repo_root)
    return workspace.repo_path("aoa-sdk") / ".aoa" / "surface-detection" / f"{label}.{phase}.latest.json"

def _resolve_surface_handoff_path(
    *,
    workspace: Workspace,
    repo_root: str,
    report_output: str | None = None,
) -> Path:
    if report_output is not None:
        return Path(report_output).expanduser().resolve()
    label = _resolve_context_label(workspace, repo_root)
    return workspace.repo_path("aoa-sdk") / ".aoa" / "surface-detection" / f"{label}.closeout-handoff.latest.json"

def _write_surface_report(path: Path, report: SurfaceDetectionReport) -> dict[str, Any]:
    payload = {
        "report_path": str(path),
        "report": report.model_dump(mode="json"),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return payload

def _merge_checkpoint_note(payload: dict[str, Any], note: SessionCheckpointNote | None) -> dict[str, Any]:
    if note is None:
        return payload
    merged = dict(payload)
    merged["checkpoint_note"] = note.model_dump(mode="json")
    return merged

def _merge_checkpoint_capture(payload: dict[str, Any], result: CheckpointCaptureResult | None) -> dict[str, Any]:
    if result is None:
        return payload
    merged = dict(payload)
    merged["checkpoint_capture"] = result.model_dump(mode="json", exclude={"note"})
    if result.note is not None:
        merged["checkpoint_note"] = result.note.model_dump(mode="json")
    return merged

def _write_surface_handoff(path: Path, report: SurfaceCloseoutHandoff) -> dict[str, Any]:
    payload = {
        "report_path": str(path),
        "report": report.model_dump(mode="json"),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return payload

def _load_surface_detection_report(path: str) -> SurfaceDetectionReport:
    payload = load_json(Path(path).expanduser().resolve())
    report_payload = payload.get("report", payload)
    return SurfaceDetectionReport.model_validate(report_payload)

def _resolve_checkpoint_hook_repos(
    *,
    workspace: Workspace,
    repo: str | None,
    all_owner: bool,
    allow_readonly: bool,
) -> list[str]:
    if (repo is None) == (not all_owner):
        raise typer.BadParameter("Pass exactly one of --repo or --all-owner.")
    if all_owner:
        return [name for name in OWNER_CHECKPOINT_HOOK_REPOS if workspace.has_repo(name)]
    assert repo is not None
    if repo not in KNOWN_REPOS:
        raise typer.BadParameter(f"Unknown repository {repo!r}.")
    if not workspace.has_repo(repo):
        raise typer.BadParameter(f"Repository {repo!r} is not available in this workspace.")
    return [repo]

def _resolve_checkpoint_managed_hooks(
    hook: str,
) -> list[CheckpointManagedHookName]:
    normalized = hook.strip().lower()
    if normalized == "all":
        return list(CHECKPOINT_MANAGED_HOOKS)
    if normalized not in CHECKPOINT_MANAGED_HOOKS:
        raise typer.BadParameter(
            "Managed checkpoint hook must be one of: post-commit, pre-push, pre-merge-commit, all."
        )
    return [cast(CheckpointManagedHookName, normalized)]

def _resolve_checkpoint_git_boundary(boundary: str) -> Literal["push", "merge"]:
    normalized = boundary.strip().lower()
    if normalized not in {"push", "merge"}:
        raise typer.BadParameter("Checkpoint git boundary must be one of: push, merge.")
    return cast(Literal["push", "merge"], normalized)
