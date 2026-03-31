from __future__ import annotations

from pathlib import Path

from .compatibility import CompatibilityAPI
from .evals import EvalsAPI
from .routing.picker import RoutingAPI
from .skills.discovery import SkillsAPI
from .agents.phase_bindings import AgentsAPI
from .memo import MemoAPI
from .playbooks import PlaybooksAPI
from .workspace.discovery import Workspace

class AoASDK:
    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace
        self.compatibility = CompatibilityAPI(workspace)
        self.routing = RoutingAPI(workspace)
        self.skills = SkillsAPI(workspace)
        self.agents = AgentsAPI(workspace)
        self.playbooks = PlaybooksAPI(workspace)
        self.memo = MemoAPI(workspace)
        self.evals = EvalsAPI(workspace)

    @classmethod
    def from_workspace(cls, root: str | Path) -> "AoASDK":
        return cls(Workspace.discover(root))
