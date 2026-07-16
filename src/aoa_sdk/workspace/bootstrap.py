from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Literal

from ..models import SkillProfileBootstrapReport, SkillProfileBootstrapStep
from ..skills.inspection import (
    load_skill_pack_profile,
    resolve_user_skill_root,
    skill_trees_match,
)
from .discovery import Workspace


def bootstrap_workspace(
    discovery_root: str | Path,
    *,
    profile_name: str = "user-default",
    user_skill_root: str | Path | None = None,
    execute: bool = False,
    overwrite: bool = False,
) -> SkillProfileBootstrapReport:
    """Plan or apply one exact aoa-skills owner profile.

    The command discovers the owner repository from ``discovery_root``. User
    profiles install into the host-selected Codex skill root. Repository
    profiles remain owner-build inputs and are rejected here, because applying
    one outside its repository home-port builder would bypass admission.
    Workspace-wide skill projections and workspace guidance are never mutated.
    """

    resolved_discovery_root = Path(discovery_root).expanduser().resolve(strict=False)
    workspace = Workspace.discover(resolved_discovery_root)
    source_repo_root = workspace.repo_path("aoa-skills")
    profile = load_skill_pack_profile(workspace, profile_name)

    blockers: list[str] = []
    warnings: list[str] = []
    if profile.scope == "user":
        target_scope_root = resolve_user_skill_root(user_skill_root)
        install_root = target_scope_root
    else:
        target_scope_root = resolved_discovery_root
        profile_install_root = Path(profile.install_root)
        install_root = target_scope_root / profile_install_root
        blockers.append(
            "Repository-scoped profiles are not installed by workspace bootstrap; "
            "use the target repository's admitted skills/port.manifest.json and owner builder."
        )

    steps: list[SkillProfileBootstrapStep] = []
    if profile.scope == "user":
        for item in profile.skills:
            source_dir = source_repo_root / Path(item.source_path).parent
            target_dir = install_root / item.name
            action = _plan_copy_action(
                source_dir=source_dir,
                target_dir=target_dir,
                overwrite=overwrite,
            )
            steps.append(
                SkillProfileBootstrapStep(
                    skill_name=item.name,
                    source_dir=str(source_dir),
                    target_dir=str(target_dir),
                    action=action,
                )
            )
            if action in {"missing-source", "conflict"}:
                blockers.append(f"{item.name}: {action}")

    if profile.scope == "user" and not steps:
        warnings.append(f"Profile {profile_name!r} contains no skills.")

    legacy_workspace_root = workspace.federation_root / ".agents" / "skills"
    legacy_path: str | None = None
    if _contains_skills(legacy_workspace_root):
        legacy_path = str(legacy_workspace_root)
        warnings.append(
            "A legacy workspace-wide skill projection exists and was left untouched."
        )

    ready = not blockers
    executed = False
    verified: bool | None = None
    if execute and ready:
        install_root.mkdir(parents=True, exist_ok=True)
        for step in steps:
            _apply_copy_step(step)
        verified = all(
            skill_trees_match(Path(step.source_dir), Path(step.target_dir))
            for step in steps
        )
        executed = True

    return SkillProfileBootstrapReport(
        discovery_root=str(resolved_discovery_root),
        source_repo_root=str(source_repo_root),
        profile_name=profile_name,
        profile_scope=profile.scope,
        install_mode=profile.install_mode,
        install_root=str(install_root),
        target_scope_root=str(target_scope_root),
        execute_requested=execute,
        overwrite=overwrite,
        ready=ready,
        executed=executed,
        verified=verified,
        steps=steps,
        legacy_workspace_root=legacy_path,
        warnings=warnings,
        blockers=list(dict.fromkeys(blockers)),
    )


def _plan_copy_action(
    *,
    source_dir: Path,
    target_dir: Path,
    overwrite: bool,
) -> Literal["create", "replace", "unchanged", "conflict", "missing-source"]:
    if not source_dir.is_dir():
        return "missing-source"
    if not _path_present(target_dir):
        return "create"
    if skill_trees_match(source_dir, target_dir):
        return "unchanged"
    return "replace" if overwrite else "conflict"


def _apply_copy_step(step: SkillProfileBootstrapStep) -> None:
    if step.action == "unchanged":
        return
    if step.action in {"conflict", "missing-source"}:
        raise ValueError(f"cannot apply install step with action={step.action}")

    source_dir = Path(step.source_dir)
    target_dir = Path(step.target_dir)
    target_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        dir=target_dir.parent,
        prefix=f".{target_dir.name}.aoa-sdk-",
    ) as temporary_root:
        staged = Path(temporary_root) / target_dir.name
        shutil.copytree(source_dir, staged, symlinks=True)
        if step.action == "replace":
            _remove_path(target_dir)
        staged.replace(target_dir)


def _path_present(path: Path) -> bool:
    return path.exists() or path.is_symlink()


def _remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def _contains_skills(root: Path) -> bool:
    return root.is_dir() and any((candidate / "SKILL.md").is_file() for candidate in root.iterdir())
