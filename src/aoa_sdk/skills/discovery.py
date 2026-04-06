from __future__ import annotations

import re
from typing import Literal

from ..compatibility import load_surface
from ..loaders import extract_records
from ..models import (
    ProjectRiskGuardRingGovernanceEntry,
    ProjectRiskGuardRingGovernanceSurface,
    ProjectRiskGuardRingSurface,
    ProjectCoreOuterRingReadinessEntry,
    ProjectCoreOuterRingReadinessSurface,
    ProjectCoreOuterRingSurface,
    SkillActivationRequest,
    SkillCard,
    SkillDisclosure,
    SkillSession,
)
from ..workspace.discovery import Workspace
from .activation import activate_skill
from .disclosure import disclose_skill
from .session import compact_session, deactivate_session_skill, ensure_session, load_session, save_session

def load_skill_cards(workspace: Workspace) -> list[SkillCard]:
    data = load_surface(workspace, "aoa-skills.runtime_discovery_index")
    records = extract_records(data, preferred_keys=("skills",))
    return [SkillCard.model_validate(item) for item in records]


def rank_skill_cards(cards: list[SkillCard], query: str) -> list[SkillCard]:
    if not query.strip():
        return sorted(cards, key=lambda card: card.name)

    query_text = query.casefold()
    tokens = re.findall(r"[a-z0-9_-]+", query_text)

    def score(card: SkillCard) -> tuple[int, str]:
        total = 0
        fields = [
            card.name.casefold(),
            card.display_name.casefold(),
            card.description.casefold(),
            card.short_description.casefold(),
        ]
        if query_text in card.name.casefold():
            total += 40
        if query_text in card.display_name.casefold():
            total += 30
        if query_text in card.description.casefold():
            total += 20

        for token in tokens:
            for field in fields:
                if token in field:
                    total += 10
            for keyword in card.keywords:
                if token in keyword.casefold():
                    total += 8

        return total, card.name

    ranked = sorted(cards, key=score, reverse=True)
    return [card for card in ranked if score(card)[0] > 0]


class SkillsAPI:
    def __init__(self, workspace) -> None:
        self.workspace = workspace

    def discover(
        self,
        *,
        query: str = "",
        trust_posture: str | None = None,
        invocation_mode: str | None = None,
        mutation_surface: str | None = None,
        allow_implicit_invocation: bool | None = None,
        limit: int | None = None,
    ) -> list[SkillCard]:
        cards = load_skill_cards(self.workspace)

        if trust_posture is not None:
            cards = [card for card in cards if card.trust_posture == trust_posture]
        if invocation_mode is not None:
            cards = [card for card in cards if card.invocation_mode == invocation_mode]
        if mutation_surface is not None:
            cards = [card for card in cards if card.mutation_surface == mutation_surface]
        if allow_implicit_invocation is not None:
            cards = [
                card
                for card in cards
                if card.allow_implicit_invocation == allow_implicit_invocation
            ]

        ranked = rank_skill_cards(cards, query)
        if limit is not None:
            return ranked[:limit]
        return ranked

    def disclose(self, skill_name: str) -> SkillDisclosure:
        return disclose_skill(self.workspace, skill_name)

    def activate(
        self,
        skill_name: str,
        *,
        session_file: str | None = None,
        explicit_handle: str | None = None,
        include_frontmatter: bool = False,
        wrap_mode: Literal["structured", "markdown", "raw"] = "structured",
    ) -> dict:
        request = SkillActivationRequest(
            skill_name=skill_name,
            session_file=session_file,
            explicit_handle=explicit_handle,
            include_frontmatter=include_frontmatter,
            wrap_mode=wrap_mode,
        )
        return activate_skill(self.workspace, request)

    def session_status(self, session_file: str | None = None) -> SkillSession:
        return load_session(self.workspace, session_file)

    def deactivate(self, skill_name: str, session_file: str) -> SkillSession:
        path, session = ensure_session(self.workspace, session_file)
        updated = deactivate_session_skill(session, skill_name)
        save_session(path, updated)
        return updated

    def compact(self, session_file: str) -> dict:
        return compact_session(load_session(self.workspace, session_file))

    def project_core_outer_ring(self) -> ProjectCoreOuterRingSurface:
        data = load_surface(self.workspace, "aoa-skills.project_core_outer_ring.min")
        return ProjectCoreOuterRingSurface.model_validate(data)

    def project_core_outer_ring_readiness(self) -> list[ProjectCoreOuterRingReadinessEntry]:
        data = load_surface(self.workspace, "aoa-skills.project_core_outer_ring_readiness.min")
        readiness = ProjectCoreOuterRingReadinessSurface.model_validate(data)
        return readiness.skills

    def project_risk_guard_ring(self) -> ProjectRiskGuardRingSurface:
        data = load_surface(self.workspace, "aoa-skills.project_risk_guard_ring.min")
        return ProjectRiskGuardRingSurface.model_validate(data)

    def project_risk_guard_ring_governance(self) -> list[ProjectRiskGuardRingGovernanceEntry]:
        data = load_surface(self.workspace, "aoa-skills.project_risk_guard_ring_governance.min")
        governance = ProjectRiskGuardRingGovernanceSurface.model_validate(data)
        return governance.skills
