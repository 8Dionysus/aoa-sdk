from __future__ import annotations

import hashlib
import os
import shutil
from pathlib import Path
from typing import Literal

from ..errors import InvalidSurface, SurfaceNotFound
from ..loaders.json_file import load_json
from ..models import (
    ProjectFoundationProfileSurface,
    WorkspaceBootstrapAgentsFile,
    WorkspaceBootstrapInstallStep,
    WorkspaceBootstrapReport,
)
from .roots import WORKSPACE_OPTIONAL_REPOS, WORKSPACE_REQUIRED_REPOS


ROOT_AGENTS_TEMPLATE = """# AGENTS.md — {workspace_name} workspace

## Purpose

`{workspace_root}` is the editable federation workspace root.
Treat it as the sibling-parent directory for the public AoA / ToS repositories, not as the source of truth for any one layer.

## Read first

1. `{workspace_root}/8Dionysus/README.md`
2. `{workspace_root}/8Dionysus/GLOSSARY.md`
3. the target repository's own `README.md` and `AGENTS.md`

## Session start

For every new session started from `{workspace_root}`, before substantial work:

1. choose the primary `repo_root`
2. run one ingress pass

```bash
aoa skills enter <repo_root> --root {workspace_root} --intent-text "<short task summary>" --json
```

If the task is truly cross-repo and no single owner repo is primary yet, use `{workspace_root}` as `repo_root`.

## Mutation gate

Before risky, mutating, infra, runtime, repo-config, or public-share actions, run:

```bash
aoa skills guard <repo_root> --root {workspace_root} --intent-text "<planned change>" --mutation-surface <code|repo-config|infra|runtime|public-share> --json
```

Do not silently skip `must_confirm` or `blocked_actions`.

## Workspace posture

- `{workspace_root}/.agents/skills` is the shared project-foundation install.
- `{workspace_root}/8Dionysus` is the public profile and route map.
- `{workspace_root}/Dionysus` is the seed garden and staging surface.
- source repositories live as sibling checkouts under `{workspace_root}`.
- `abyss-stack` may still use an external preferred source checkout; respect `aoa-sdk` workspace discovery and overrides.

## Workflow

`INGRESS -> READ -> DIFF -> VERIFY -> REPORT`
"""


def bootstrap_workspace(
    workspace_root: str | Path,
    *,
    mode: Literal["symlink", "copy"] = "symlink",
    execute: bool = False,
    overwrite: bool = False,
    write_agents: bool = True,
    overwrite_agents: bool = False,
    strict_layout: bool = True,
) -> WorkspaceBootstrapReport:
    root = Path(workspace_root).expanduser().resolve()
    foundation = _load_foundation_profile(root)

    missing_required = [repo for repo in WORKSPACE_REQUIRED_REPOS if not _repo_present(root / repo)]
    optional_present = [repo for repo in WORKSPACE_OPTIONAL_REPOS if _repo_present(root / repo)]
    optional_missing = [repo for repo in WORKSPACE_OPTIONAL_REPOS if repo not in optional_present]

    install_root = root / ".agents" / "skills"
    source_root = root / "aoa-skills" / ".agents" / "skills"

    warnings: list[str] = []
    blockers: list[str] = []
    if strict_layout and missing_required:
        blockers.append("workspace root is missing one or more required sibling repositories.")
    if optional_missing:
        warnings.append("optional ecosystem repos are missing and stayed outside bootstrap scope.")

    install_steps: list[WorkspaceBootstrapInstallStep] = []
    for skill_name in foundation.skills:
        source_dir = source_root / skill_name
        target_dir = install_root / skill_name
        action = _plan_install_action(source_dir=source_dir, target_dir=target_dir, mode=mode, overwrite=overwrite)
        install_steps.append(
            WorkspaceBootstrapInstallStep(
                skill_name=skill_name,
                source_dir=str(source_dir),
                target_dir=str(target_dir),
                action=action,
            )
        )
        if action in {"missing-source", "conflict"}:
            blockers.append(f"{skill_name}: {action}")

    agents_file = _plan_agents_file(
        workspace_root=root,
        write_agents=write_agents,
        overwrite_agents=overwrite_agents,
    )

    ready = not blockers
    executed = False
    verified: bool | None = None

    if execute and ready:
        install_root.mkdir(parents=True, exist_ok=True)
        for step in install_steps:
            _apply_install_step(
                source_dir=Path(step.source_dir),
                target_dir=Path(step.target_dir),
                action=step.action,
                mode=mode,
            )
        if agents_file is not None and agents_file.action in {"write", "overwrite"}:
            Path(agents_file.path).write_text(_render_root_agents(root), encoding="utf-8")
        verified = _verify_install(
            foundation=foundation,
            install_root=install_root,
            source_root=source_root,
            mode=mode,
        )
        executed = True

    return WorkspaceBootstrapReport(
        workspace_root=str(root),
        foundation_id=foundation.foundation_id,
        canonical_install_profile=foundation.canonical_install_profile,
        mode=mode,
        strict_layout=strict_layout,
        execute_requested=execute,
        overwrite=overwrite,
        ready=ready,
        executed=executed,
        verified=verified,
        required_repos=list(WORKSPACE_REQUIRED_REPOS),
        missing_required_repos=missing_required,
        optional_repos_present=optional_present,
        optional_repos_missing=optional_missing,
        install_root=str(install_root),
        install_steps=install_steps,
        agents_file=agents_file,
        warnings=warnings,
        blockers=list(dict.fromkeys(blockers)),
    )


def _load_foundation_profile(workspace_root: Path) -> ProjectFoundationProfileSurface:
    profile_path = workspace_root / "aoa-skills" / "generated" / "project_foundation_profile.min.json"
    try:
        payload = load_json(profile_path)
    except SurfaceNotFound as exc:
        raise InvalidSurface(
            f"workspace bootstrap needs {profile_path} to exist; bootstrap assumes an already assembled sibling workspace."
        ) from exc
    return ProjectFoundationProfileSurface.model_validate(payload)


def _repo_present(path: Path) -> bool:
    return path.is_dir()


def _path_present(path: Path) -> bool:
    return path.exists() or path.is_symlink()


def _plan_install_action(
    *,
    source_dir: Path,
    target_dir: Path,
    mode: Literal["symlink", "copy"],
    overwrite: bool,
) -> Literal["create", "replace", "unchanged", "conflict", "missing-source"]:
    if not source_dir.is_dir():
        return "missing-source"
    if not _path_present(target_dir):
        return "create"
    if _target_matches_source(source_dir=source_dir, target_dir=target_dir, mode=mode):
        return "unchanged"
    return "replace" if overwrite else "conflict"


def _plan_agents_file(
    *,
    workspace_root: Path,
    write_agents: bool,
    overwrite_agents: bool,
) -> WorkspaceBootstrapAgentsFile | None:
    if not write_agents:
        return None

    path = workspace_root / "AGENTS.md"
    rendered = _render_root_agents(workspace_root)
    if not path.exists():
        return WorkspaceBootstrapAgentsFile(path=str(path), action="write")
    if path.read_text(encoding="utf-8") == rendered:
        return WorkspaceBootstrapAgentsFile(path=str(path), action="unchanged")
    if overwrite_agents:
        return WorkspaceBootstrapAgentsFile(path=str(path), action="overwrite")
    return WorkspaceBootstrapAgentsFile(path=str(path), action="preserve-existing")


def _render_root_agents(workspace_root: Path) -> str:
    return ROOT_AGENTS_TEMPLATE.format(
        workspace_name=workspace_root.name,
        workspace_root=str(workspace_root),
    )


def _apply_install_step(
    *,
    source_dir: Path,
    target_dir: Path,
    action: Literal["create", "replace", "unchanged", "conflict", "missing-source"],
    mode: Literal["symlink", "copy"],
) -> None:
    if action == "unchanged":
        return
    if action in {"conflict", "missing-source"}:
        raise ValueError(f"cannot apply install step with action={action}")
    if action == "replace":
        _remove_path(target_dir)
    target_dir.parent.mkdir(parents=True, exist_ok=True)
    if mode == "symlink":
        target_dir.symlink_to(source_dir, target_is_directory=True)
        return
    shutil.copytree(source_dir, target_dir)


def _remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
        return
    if path.is_dir():
        shutil.rmtree(path)


def _target_matches_source(
    *,
    source_dir: Path,
    target_dir: Path,
    mode: Literal["symlink", "copy"],
) -> bool:
    if mode == "symlink":
        return target_dir.is_symlink() and target_dir.resolve() == source_dir.resolve()
    if not target_dir.is_dir():
        return False
    return _dir_digest(source_dir) == _dir_digest(target_dir)


def _dir_digest(path: Path) -> str:
    digest = hashlib.sha256()
    for entry in sorted(path.rglob("*")):
        relative = entry.relative_to(path).as_posix().encode("utf-8")
        digest.update(relative)
        if entry.is_file():
            digest.update(b"F")
            digest.update(entry.read_bytes())
        elif entry.is_symlink():
            digest.update(b"L")
            digest.update(os.readlink(entry).encode("utf-8"))
        elif entry.is_dir():
            digest.update(b"D")
    return digest.hexdigest()


def _verify_install(
    *,
    foundation: ProjectFoundationProfileSurface,
    install_root: Path,
    source_root: Path,
    mode: Literal["symlink", "copy"],
) -> bool:
    for skill_name in foundation.skills:
        source_dir = source_root / skill_name
        target_dir = install_root / skill_name
        if not _path_present(target_dir):
            return False
        if not _target_matches_source(source_dir=source_dir, target_dir=target_dir, mode=mode):
            return False
    return True
