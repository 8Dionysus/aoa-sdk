from __future__ import annotations

from ..errors import RecordNotFound
from ..workspace.discovery import Workspace
from .models import (
    AgentBuildSnapshot,
    AgentBuildSnapshotCollection,
    AgentSheetCard,
    DualVocabularyOverlay,
    FrontendProjectionBundle,
    FrontendProjectionBundleCollection,
    QuestBoardCard,
    QuestRunResult,
    QuestRunResultCollection,
    ReputationLedger,
    ReputationLedgerCollection,
    ReputationPanel,
)
from .surfaces import RpgCompatibilityAPI, load_rpg_surface


class RpgAPI:
    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace
        self.compatibility = RpgCompatibilityAPI(workspace)

    def vocabulary(self) -> DualVocabularyOverlay:
        data = load_rpg_surface(self.workspace, "Agents-of-Abyss.dual_vocabulary_overlay")
        return DualVocabularyOverlay.model_validate(data)

    def label_for(self, canonical_key: str, default: str | None = None) -> str | None:
        label = self.vocabulary().label_for(canonical_key)
        return label if label is not None else default

    def builds(
        self,
        *,
        agent_id: str | None = None,
        class_archetype: str | None = None,
        rank: str | None = None,
    ) -> list[AgentBuildSnapshot]:
        data = load_rpg_surface(self.workspace, "abyss-stack.rpg_build_snapshots")
        collection = AgentBuildSnapshotCollection.model_validate(data)
        items = collection.builds
        if agent_id is not None:
            items = [item for item in items if item.agent_id.casefold() == agent_id.casefold()]
        if class_archetype is not None:
            items = [item for item in items if item.class_archetype.casefold() == class_archetype.casefold()]
        if rank is not None:
            items = [item for item in items if item.rank == rank]
        return sorted(items, key=lambda item: item.captured_at, reverse=True)

    def build(self, snapshot_id: str) -> AgentBuildSnapshot:
        for item in self.builds():
            if item.snapshot_id.casefold() == snapshot_id.casefold():
                return item
        raise RecordNotFound(f"Unknown build snapshot: {snapshot_id}")

    def latest_build(self, agent_id: str) -> AgentBuildSnapshot:
        matches = self.builds(agent_id=agent_id)
        if matches:
            return matches[0]
        raise RecordNotFound(f"No build snapshot for agent: {agent_id}")

    def ledgers(
        self,
        *,
        subject_ref: str | None = None,
        subject_kind: str | None = None,
    ) -> list[ReputationLedger]:
        data = load_rpg_surface(self.workspace, "abyss-stack.rpg_reputation_ledgers")
        collection = ReputationLedgerCollection.model_validate(data)
        items = collection.ledgers
        if subject_ref is not None:
            items = [item for item in items if item.subject_ref.casefold() == subject_ref.casefold()]
        if subject_kind is not None:
            items = [item for item in items if item.subject_kind == subject_kind]
        return sorted(items, key=lambda item: item.generated_at, reverse=True)

    def ledger(self, subject_ref: str) -> ReputationLedger:
        matches = self.ledgers(subject_ref=subject_ref)
        if matches:
            return matches[0]
        raise RecordNotFound(f"No reputation ledger for subject: {subject_ref}")

    def runs(
        self,
        *,
        quest_ref: str | None = None,
        agent_id: str | None = None,
        status: str | None = None,
    ) -> list[QuestRunResult]:
        data = load_rpg_surface(self.workspace, "abyss-stack.rpg_quest_run_results")
        collection = QuestRunResultCollection.model_validate(data)
        items = collection.runs
        if quest_ref is not None:
            items = [item for item in items if item.quest_ref.casefold() == quest_ref.casefold()]
        if agent_id is not None:
            items = [
                item
                for item in items
                if any(member.casefold() == agent_id.casefold() for member in item.execution.party)
            ]
        if status is not None:
            items = [item for item in items if item.outcome.run_status == status]
        return sorted(items, key=lambda item: item.finished_at, reverse=True)

    def run(self, run_id: str) -> QuestRunResult:
        for item in self.runs():
            if item.run_id.casefold() == run_id.casefold():
                return item
        raise RecordNotFound(f"Unknown quest run result: {run_id}")

    def bundles(self) -> list[FrontendProjectionBundle]:
        data = load_rpg_surface(self.workspace, "abyss-stack.rpg_frontend_projection_bundles")
        collection = FrontendProjectionBundleCollection.model_validate(data)
        return sorted(collection.bundles, key=lambda item: item.generated_at, reverse=True)

    def bundle(self, bundle_id: str) -> FrontendProjectionBundle:
        for item in self.bundles():
            if item.bundle_id.casefold() == bundle_id.casefold():
                return item
        raise RecordNotFound(f"Unknown frontend projection bundle: {bundle_id}")

    def latest_bundle(self) -> FrontendProjectionBundle:
        bundles = self.bundles()
        if bundles:
            return bundles[0]
        raise RecordNotFound("No frontend projection bundle is available")

    def agent_sheet(self, agent_id: str, *, bundle_id: str | None = None) -> AgentSheetCard:
        bundle = self.bundle(bundle_id) if bundle_id is not None else self.latest_bundle()
        for card in bundle.views.agent_sheet_cards:
            if card.agent_id.casefold() == agent_id.casefold():
                return card
        raise RecordNotFound(f"No agent sheet card for agent: {agent_id}")

    def quest_board(
        self,
        *,
        state: str | None = None,
        band: str | None = None,
        bundle_id: str | None = None,
    ) -> list[QuestBoardCard]:
        bundle = self.bundle(bundle_id) if bundle_id is not None else self.latest_bundle()
        cards = bundle.views.quest_board_cards
        if state is not None:
            cards = [card for card in cards if card.state == state]
        if band is not None:
            cards = [card for card in cards if card.band == band]
        return cards

    def reputation_panel(self, subject_ref: str, *, bundle_id: str | None = None) -> ReputationPanel:
        bundle = self.bundle(bundle_id) if bundle_id is not None else self.latest_bundle()
        for panel in bundle.views.reputation_panels:
            if panel.subject_ref.casefold() == subject_ref.casefold():
                return panel
        raise RecordNotFound(f"No reputation panel for subject: {subject_ref}")
