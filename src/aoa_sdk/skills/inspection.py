from __future__ import annotations

import hashlib
import os
from collections import defaultdict
from pathlib import Path
from typing import Literal

from ..compatibility import load_surface
from ..errors import InvalidSurface
from ..loaders.json_file import load_json
from ..models import (
    AgentSkillCatalog,
    CapabilityGraph,
    CapabilityNeighborhood,
    InstalledSkill,
    McpDependencyManifest,
    PortableExportMap,
    SkillEnvironmentReport,
    SkillHomePortManifest,
    SkillPackProfile,
    SkillPackProfiles,
    SkillRootInspection,
)
from ..workspace.discovery import Workspace


InstalledSkillStatus = Literal[
    "current",
    "drift",
    "missing",
    "unmanaged",
    "source-export",
    "legacy-unowned",
]


def load_agent_skill_catalog(workspace: Workspace) -> AgentSkillCatalog:
    payload = load_surface(workspace, "aoa-skills.agent_skill_catalog")
    return AgentSkillCatalog.model_validate(payload)


def load_skill_pack_profiles(workspace: Workspace) -> SkillPackProfiles:
    payload = load_surface(workspace, "aoa-skills.skill_pack_profiles.resolved")
    return SkillPackProfiles.model_validate(payload)


def load_skill_pack_profile(workspace: Workspace, profile_name: str) -> SkillPackProfile:
    profiles = load_skill_pack_profiles(workspace)
    profile = profiles.profiles.get(profile_name)
    if profile is None:
        available = ", ".join(sorted(profiles.profiles)) or "none"
        raise InvalidSurface(
            f"Unknown aoa-skills install profile {profile_name!r}; available profiles: {available}."
        )
    return profile


def load_capability_graph(workspace: Workspace) -> CapabilityGraph:
    payload = load_surface(workspace, "aoa-skills.capability_graph")
    return CapabilityGraph.model_validate(payload)


def load_capability_neighborhood(
    workspace: Workspace,
    node_id: str,
) -> CapabilityNeighborhood:
    graph = load_capability_graph(workspace)
    node = next((candidate for candidate in graph.nodes if candidate.id == node_id), None)
    if node is None:
        raise InvalidSurface(f"Capability node {node_id!r} is not present in the owner graph.")
    return CapabilityNeighborhood(
        node=node,
        incoming=[relation for relation in graph.relations if relation.target == node_id],
        outgoing=[relation for relation in graph.relations if relation.source == node_id],
    )


def load_portable_export_map(workspace: Workspace) -> PortableExportMap:
    payload = load_surface(workspace, "aoa-skills.portable_export_map")
    return PortableExportMap.model_validate(payload)


def load_mcp_dependency_manifest(workspace: Workspace) -> McpDependencyManifest:
    payload = load_surface(workspace, "aoa-skills.mcp_dependency_manifest")
    return McpDependencyManifest.model_validate(payload)


def resolve_user_skill_root(explicit_root: str | Path | None = None) -> Path:
    if explicit_root is not None:
        return Path(explicit_root).expanduser().resolve(strict=False)
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        return (Path(codex_home).expanduser() / "skills").resolve(strict=False)
    return (Path.home() / ".codex" / "skills").resolve(strict=False)


def inspect_skill_environment(
    workspace: Workspace,
    *,
    repo_root: str | Path,
    user_skill_root: str | Path | None = None,
) -> SkillEnvironmentReport:
    resolved_repo_root = _resolve_repo_root(workspace, repo_root)
    resolved_user_root = resolve_user_skill_root(user_skill_root)
    source_repo_root = workspace.repo_path("aoa-skills")
    source_export_root = source_repo_root / ".agents" / "skills"
    profiles = load_skill_pack_profiles(workspace)
    user_profile = profiles.profiles.get("user-default")

    roots: list[SkillRootInspection] = []
    roots.append(
        _inspect_source_export(
            source_export_root=source_export_root,
            owner_repo="aoa-skills",
        )
    )
    roots.append(
        _inspect_user_root(
            user_root=resolved_user_root,
            source_export_root=source_export_root,
            user_profile=user_profile,
        )
    )

    port_path = resolved_repo_root / "skills" / "port.manifest.json"
    repo_projection_root = resolved_repo_root / ".agents" / "skills"
    if port_path.is_file():
        port = SkillHomePortManifest.model_validate(load_json(port_path))
        roots.append(
            _inspect_repo_projection(
                repo_root=resolved_repo_root,
                port_path=port_path,
                port=port,
            )
        )
    elif _contains_skill_dirs(repo_projection_root):
        roots.append(
            _inspect_unowned_root(
                root=repo_projection_root,
                root_kind="repo-unowned",
                scope="repo",
                issue=(
                    "Repository projection contains skills but has no admitted "
                    "skills/port.manifest.json."
                ),
            )
        )

    workspace_legacy_root = workspace.federation_root / ".agents" / "skills"
    if workspace_legacy_root != repo_projection_root and _contains_skill_dirs(
        workspace_legacy_root
    ):
        roots.append(
            _inspect_unowned_root(
                root=workspace_legacy_root,
                root_kind="workspace-legacy",
                scope="workspace",
                issue=(
                    "Workspace-wide skill projection is legacy and is not an install or routing source."
                ),
            )
        )

    duplicate_names = _duplicate_names(roots)
    warnings: list[str] = []
    for root in roots:
        warnings.extend(root.issues)
        for entry in root.entries:
            if entry.status == "drift":
                warnings.append(f"{root.root_kind}:{entry.name} differs from its owner source.")
            elif entry.status == "missing":
                warnings.append(f"{root.root_kind}:{entry.name} is admitted but missing.")

    for name, locations in sorted(duplicate_names.items()):
        installed_locations = [
            item for item in locations if not item.startswith("source-export:")
        ]
        if len(installed_locations) > 1:
            warnings.append(
                f"Installed skill {name!r} appears in multiple scopes: "
                f"{', '.join(installed_locations)}."
            )

    return SkillEnvironmentReport(
        repo_root=str(resolved_repo_root),
        federation_root=str(workspace.federation_root),
        source_repo_root=str(source_repo_root),
        user_skill_root=str(resolved_user_root),
        roots=roots,
        duplicate_names=duplicate_names,
        warnings=list(dict.fromkeys(warnings)),
    )


def skill_tree_digest(path: Path) -> str:
    digest = hashlib.sha256()
    for entry in sorted(path.rglob("*")):
        relative = entry.relative_to(path).as_posix().encode("utf-8")
        digest.update(relative)
        if entry.is_symlink():
            digest.update(b"L")
            digest.update(os.readlink(entry).encode("utf-8"))
        elif entry.is_file():
            digest.update(b"F")
            digest.update(entry.read_bytes())
        elif entry.is_dir():
            digest.update(b"D")
    return digest.hexdigest()


def skill_trees_match(source_dir: Path, target_dir: Path) -> bool:
    if not source_dir.is_dir() or not target_dir.is_dir() or target_dir.is_symlink():
        return False
    return skill_tree_digest(source_dir) == skill_tree_digest(target_dir)


def _resolve_repo_root(workspace: Workspace, repo_root: str | Path) -> Path:
    raw = Path(repo_root).expanduser()
    if raw.is_absolute():
        resolved = raw.resolve(strict=False)
    elif str(repo_root) in workspace.repo_roots:
        resolved = workspace.repo_path(str(repo_root))
    else:
        resolved = (workspace.root / raw).resolve(strict=False)
    if not resolved.is_dir():
        raise InvalidSurface(f"Repository root is not a directory: {resolved}")
    return resolved


def _skill_dirs(root: Path) -> dict[str, Path]:
    if not root.is_dir():
        return {}
    result: dict[str, Path] = {}
    for candidate in sorted(root.iterdir(), key=lambda item: item.name):
        if (candidate / "SKILL.md").is_file():
            result[candidate.name] = candidate
    return result


def _contains_skill_dirs(root: Path) -> bool:
    return bool(_skill_dirs(root))


def _inspect_source_export(
    *,
    source_export_root: Path,
    owner_repo: str,
) -> SkillRootInspection:
    entries = [
        InstalledSkill(
            name=name,
            skill_dir=str(skill_dir),
            skill_file=str(skill_dir / "SKILL.md"),
            status="source-export",
            admitted=True,
        )
        for name, skill_dir in _skill_dirs(source_export_root).items()
    ]
    return SkillRootInspection(
        root_kind="source-export",
        scope="source",
        path=str(source_export_root),
        exists=source_export_root.is_dir(),
        authority="portable-export",
        owner_repo=owner_repo,
        admitted_names=[entry.name for entry in entries],
        entries=entries,
    )


def _inspect_user_root(
    *,
    user_root: Path,
    source_export_root: Path,
    user_profile: SkillPackProfile | None,
) -> SkillRootInspection:
    expected = {
        item.name: source_export_root / Path(item.source_path).parent.relative_to(
            Path(".agents/skills")
        )
        for item in (user_profile.skills if user_profile is not None else [])
    }
    entries: list[InstalledSkill] = []
    installed = _skill_dirs(user_root)
    for name, skill_dir in installed.items():
        source_dir = expected.get(name)
        status: InstalledSkillStatus = "unmanaged"
        admitted = source_dir is not None
        if source_dir is not None:
            status = "current" if skill_trees_match(source_dir, skill_dir) else "drift"
        entries.append(
            InstalledSkill(
                name=name,
                skill_dir=str(skill_dir),
                skill_file=str(skill_dir / "SKILL.md"),
                status=status,
                admitted=admitted,
                expected_source_dir=str(source_dir) if source_dir is not None else None,
            )
        )
    for name, source_dir in expected.items():
        if name not in installed:
            target_dir = user_root / name
            entries.append(
                InstalledSkill(
                    name=name,
                    skill_dir=str(target_dir),
                    skill_file=str(target_dir / "SKILL.md"),
                    status="missing",
                    admitted=True,
                    expected_source_dir=str(source_dir),
                )
            )
    return SkillRootInspection(
        root_kind="user",
        scope="user",
        path=str(user_root),
        exists=user_root.is_dir(),
        authority="host-projection",
        owner_repo="aoa-skills",
        admitted_names=sorted(expected),
        entries=sorted(entries, key=lambda item: item.name),
    )


def _inspect_repo_projection(
    *,
    repo_root: Path,
    port_path: Path,
    port: SkillHomePortManifest,
) -> SkillRootInspection:
    projection_root = repo_root / port.projection.root
    bundles = {bundle.name: repo_root / bundle.path for bundle in port.bundles}
    admitted = set(port.projection.skills)
    issues: list[str] = []
    missing_bundle_records = sorted(admitted - set(bundles))
    if missing_bundle_records:
        issues.append(
            "Projection admits skills without bundle records: "
            + ", ".join(missing_bundle_records)
            + "."
        )

    entries: list[InstalledSkill] = []
    installed = _skill_dirs(projection_root)
    for name, skill_dir in installed.items():
        source_dir = bundles.get(name)
        status: InstalledSkillStatus = "unmanaged"
        is_admitted = name in admitted and source_dir is not None
        if is_admitted and source_dir is not None:
            status = "current" if skill_trees_match(source_dir, skill_dir) else "drift"
        entries.append(
            InstalledSkill(
                name=name,
                skill_dir=str(skill_dir),
                skill_file=str(skill_dir / "SKILL.md"),
                status=status,
                admitted=is_admitted,
                expected_source_dir=str(source_dir) if source_dir is not None else None,
            )
        )
    for name in sorted(admitted):
        if name not in installed:
            target_dir = projection_root / name
            source_dir = bundles.get(name)
            entries.append(
                InstalledSkill(
                    name=name,
                    skill_dir=str(target_dir),
                    skill_file=str(target_dir / "SKILL.md"),
                    status="missing",
                    admitted=source_dir is not None,
                    expected_source_dir=str(source_dir) if source_dir is not None else None,
                )
            )
    return SkillRootInspection(
        root_kind="repo-projection",
        scope="repo",
        path=str(projection_root),
        exists=projection_root.is_dir(),
        authority="owner-projection",
        owner_repo=port.owner_repo,
        manifest_path=str(port_path),
        admitted_names=sorted(admitted),
        entries=sorted(entries, key=lambda item: item.name),
        issues=issues,
    )


def _inspect_unowned_root(
    *,
    root: Path,
    root_kind: Literal["repo-unowned", "workspace-legacy"],
    scope: Literal["repo", "workspace"],
    issue: str,
) -> SkillRootInspection:
    entries = [
        InstalledSkill(
            name=name,
            skill_dir=str(skill_dir),
            skill_file=str(skill_dir / "SKILL.md"),
            status="legacy-unowned",
        )
        for name, skill_dir in _skill_dirs(root).items()
    ]
    return SkillRootInspection(
        root_kind=root_kind,
        scope=scope,
        path=str(root),
        exists=root.is_dir(),
        authority="legacy-unowned",
        entries=entries,
        issues=[issue],
    )


def _duplicate_names(roots: list[SkillRootInspection]) -> dict[str, list[str]]:
    locations: defaultdict[str, list[str]] = defaultdict(list)
    for root in roots:
        for entry in root.entries:
            if entry.status == "missing":
                continue
            locations[entry.name].append(f"{root.root_kind}:{root.path}")
    return {
        name: values
        for name, values in sorted(locations.items())
        if len(values) > 1
    }
