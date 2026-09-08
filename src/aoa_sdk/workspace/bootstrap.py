from __future__ import annotations

import shutil
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Literal

from ..errors import InvalidSurface
from ..models import (
    OSSkillProfileBootstrapReport,
    SkillProfileBootstrapReport,
    SkillProfileBootstrapStep,
)
from ..skills.inspection import (
    load_skill_pack_profile,
    resolve_user_skill_root,
    skill_trees_match,
)
from .discovery import Workspace


OS_PROFILE_NAME = "os-user-default"
LEGACY_PROFILE_NAMES = {"user-default"}


def bootstrap_workspace(
    discovery_root: str | Path,
    *,
    profile_name: str = OS_PROFILE_NAME,
    user_skill_root: str | Path | None = None,
    execute: bool = False,
    overwrite: bool = False,
    check: bool | None = None,
    replace_unmanaged: bool = False,
    prune_managed: bool = False,
    allow_dirty_source: bool = False,
    source_roots: Mapping[str, str | Path] | None = None,
    os_root: str | Path | None = None,
) -> SkillProfileBootstrapReport | OSSkillProfileBootstrapReport:
    """Dispatch an explicit portable profile or the owner OS profile.

    ``os-user-default`` is a transport to the current aoa-skills owner
    installer.  Portable v2 profile names continue through the SDK's existing
    copy planner.  The former implicit ``user-default`` name is retained only
    as a migration diagnostic so callers do not silently receive a different
    owner policy.
    """

    resolved_discovery_root = Path(discovery_root).expanduser().resolve(strict=False)
    if profile_name != OS_PROFILE_NAME:
        _reject_os_profile_options(
            profile_name,
            check=check,
            replace_unmanaged=replace_unmanaged,
            prune_managed=prune_managed,
            allow_dirty_source=allow_dirty_source,
            source_roots=source_roots,
            os_root=os_root,
        )
    workspace = Workspace.discover(resolved_discovery_root)
    if profile_name == OS_PROFILE_NAME:
        from .os_profile import bootstrap_os_profile

        return bootstrap_os_profile(
            resolved_discovery_root,
            profile_name=profile_name,
            user_skill_root=user_skill_root,
            execute=execute,
            check=check,
            overwrite=overwrite,
            replace_unmanaged=replace_unmanaged,
            prune_managed=prune_managed,
            allow_dirty_source=allow_dirty_source,
            source_roots=source_roots,
            os_root=os_root,
            workspace=workspace,
        )
    if profile_name in LEGACY_PROFILE_NAMES:
        try:
            load_skill_pack_profile(workspace, profile_name)
        except InvalidSurface as exc:
            return _legacy_profile_migration_report(
                workspace,
                resolved_discovery_root=resolved_discovery_root,
                profile_name=profile_name,
                user_skill_root=user_skill_root,
                execute=execute,
                overwrite=overwrite,
                detail=str(exc),
            )
        report = _bootstrap_portable_workspace(
            workspace,
            resolved_discovery_root=resolved_discovery_root,
            profile_name=profile_name,
            user_skill_root=user_skill_root,
            execute=execute,
            overwrite=overwrite,
        )
        report.warnings.append(
            "Profile 'user-default' is legacy portable vocabulary; migrate to "
            "'os-user-default' for owner-managed installation. No profile alias "
            "was applied."
        )
        return report
    return _bootstrap_portable_workspace(
        workspace,
        resolved_discovery_root=resolved_discovery_root,
        profile_name=profile_name,
        user_skill_root=user_skill_root,
        execute=execute,
        overwrite=overwrite,
    )


def _reject_os_profile_options(
    profile_name: str,
    *,
    check: bool | None,
    replace_unmanaged: bool,
    prune_managed: bool,
    allow_dirty_source: bool,
    source_roots: Mapping[str, str | Path] | None,
    os_root: str | Path | None,
) -> None:
    """Fail closed when OS-installer controls accompany a portable profile."""

    supplied: list[str] = []
    if check:
        supplied.append("--check")
    if replace_unmanaged:
        supplied.append("--replace-unmanaged")
    if prune_managed:
        supplied.append("--prune-managed")
    if allow_dirty_source:
        supplied.append("--allow-dirty-source")
    if source_roots:
        supplied.append("--source-root")
    if os_root is not None:
        supplied.append("--os-root")
    if supplied:
        options = ", ".join(supplied)
        raise ValueError(
            f"{options} only apply to OS profile {OS_PROFILE_NAME!r}; "
            f"portable profile {profile_name!r} requires no OS-installer options"
        )


def _bootstrap_portable_workspace(
    workspace: Workspace,
    *,
    resolved_discovery_root: Path,
    profile_name: str,
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


def _legacy_profile_migration_report(
    workspace: Workspace,
    *,
    resolved_discovery_root: Path,
    profile_name: str,
    user_skill_root: str | Path | None,
    execute: bool,
    overwrite: bool,
    detail: str,
) -> SkillProfileBootstrapReport:
    install_root = resolve_user_skill_root(user_skill_root)
    source_repo_root = workspace.repo_roots.get("aoa-skills")
    source_root = str(source_repo_root) if source_repo_root is not None else ""
    return SkillProfileBootstrapReport(
        discovery_root=str(resolved_discovery_root),
        source_repo_root=source_root,
        profile_name=profile_name,
        profile_scope="user",
        install_mode="copy",
        install_root=str(install_root),
        target_scope_root=str(install_root),
        execute_requested=execute,
        overwrite=overwrite,
        ready=False,
        executed=False,
        verified=None,
        blockers=[
            "Profile 'user-default' is legacy portable vocabulary. Use "
            "'os-user-default' to invoke the aoa-skills owner installer; no "
            f"profile alias was applied. Profile lookup failed: {detail}"
        ],
    )


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
