from __future__ import annotations

from builtins import list as builtin_list

from ..compatibility import load_surface
from ..errors import RecordNotFound
from ..models import TechniquePromotionReadinessEntry
from ..workspace.discovery import Workspace


class TechniquesAPI:
    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace

    def promotion_readiness(
        self,
        technique_id_or_name: str | None = None,
    ) -> builtin_list[TechniquePromotionReadinessEntry] | TechniquePromotionReadinessEntry:
        entries = self._promotion_readiness_entries()
        if technique_id_or_name is None:
            return entries
        needle = technique_id_or_name.casefold()
        for entry in entries:
            if needle in {entry.technique_id.casefold(), entry.technique_name.casefold()}:
                return entry
        raise RecordNotFound(f"No technique promotion readiness entry for: {technique_id_or_name}")

    def _promotion_readiness_entries(self) -> builtin_list[TechniquePromotionReadinessEntry]:
        data = load_surface(self.workspace, "aoa-techniques.technique_promotion_readiness.min")
        return [TechniquePromotionReadinessEntry.model_validate(item) for item in data.get("techniques", [])]
