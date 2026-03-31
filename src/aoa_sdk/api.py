from __future__ import annotations

from pathlib import Path

from .routing.picker import RoutingAPI
from .skills.discovery import SkillsAPI
from .agents.phase_bindings import AgentsAPI
from .workspace.discovery import Workspace

class AoASDK:
    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace
        self.routing = RoutingAPI(workspace)
        self.skills = SkillsAPI(workspace)
        self.agents = AgentsAPI(workspace)

    @classmethod
    def from_workspace(cls, root: str | Path) -> "AoASDK":
        return cls(Workspace.discover(root))
