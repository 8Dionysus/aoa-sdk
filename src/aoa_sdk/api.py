from __future__ import annotations

from pathlib import Path

from .a2a import A2AAPI
from .compatibility import CompatibilityAPI
from .closeout import CloseoutAPI
from .checkpoints import CheckpointsAPI
from .codex import CodexAPI
from .evals import EvalsAPI
from .agents.phase_bindings import AgentsAPI
from .governed_runs import GovernedRunsAPI
from .kag import KagAPI
from .memo import MemoAPI
from .playbooks import PlaybooksAPI
from .recurrence import RecurrenceAPI
from .release import ReleaseAPI
from .rpg import RpgAPI
from .routing.picker import RoutingAPI
from .skills.discovery import SkillsAPI
from .stats import StatsAPI
from .surfaces import SurfacesAPI
from .techniques import TechniquesAPI
from .workspace.discovery import Workspace


class AoASDK:
    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace
        self.a2a = A2AAPI(workspace)
        self.compatibility = CompatibilityAPI(workspace)
        self.checkpoints = CheckpointsAPI(workspace)
        self.codex = CodexAPI(workspace)
        self.routing = RoutingAPI(workspace)
        self.skills = SkillsAPI(workspace)
        self.surfaces = SurfacesAPI(workspace)
        self.agents = AgentsAPI(workspace)
        self.playbooks = PlaybooksAPI(workspace)
        self.recurrence = RecurrenceAPI(workspace)
        self.memo = MemoAPI(workspace)
        self.techniques = TechniquesAPI(workspace)
        self.evals = EvalsAPI(workspace)
        self.stats = StatsAPI(workspace)
        self.kag = KagAPI(workspace)
        self.rpg = RpgAPI(workspace)
        self.governed_runs = GovernedRunsAPI(workspace)
        self.closeout = CloseoutAPI(workspace)
        self.release = ReleaseAPI(workspace)

    @classmethod
    def from_workspace(cls, root: str | Path) -> "AoASDK":
        return cls(Workspace.discover(root))
