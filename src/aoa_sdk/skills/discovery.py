from __future__ import annotations

from pathlib import Path

from ..models import (
    AgentSkillCatalog,
    CapabilityGraph,
    CapabilityNeighborhood,
    McpDependencyManifest,
    PortableExportMap,
    SkillEnvironmentReport,
    SkillPackProfile,
    SkillPackProfiles,
)
from ..workspace.discovery import Workspace
from .inspection import (
    inspect_skill_environment,
    load_agent_skill_catalog,
    load_capability_graph,
    load_capability_neighborhood,
    load_mcp_dependency_manifest,
    load_portable_export_map,
    load_skill_pack_profile,
    load_skill_pack_profiles,
)


class SkillsAPI:
    """Passive typed facade over owner-authored skill ecosystem surfaces."""

    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace

    def catalog(self) -> AgentSkillCatalog:
        return load_agent_skill_catalog(self.workspace)

    def profiles(self) -> SkillPackProfiles:
        return load_skill_pack_profiles(self.workspace)

    def profile(self, profile_name: str) -> SkillPackProfile:
        return load_skill_pack_profile(self.workspace, profile_name)

    def capability_graph(self) -> CapabilityGraph:
        return load_capability_graph(self.workspace)

    def capability(self, node_id: str) -> CapabilityNeighborhood:
        return load_capability_neighborhood(self.workspace, node_id)

    def portable_exports(self) -> PortableExportMap:
        return load_portable_export_map(self.workspace)

    def mcp_dependencies(self) -> McpDependencyManifest:
        return load_mcp_dependency_manifest(self.workspace)

    def inspect(
        self,
        *,
        repo_root: str | Path,
        user_skill_root: str | Path | None = None,
    ) -> SkillEnvironmentReport:
        return inspect_skill_environment(
            self.workspace,
            repo_root=repo_root,
            user_skill_root=user_skill_root,
        )
