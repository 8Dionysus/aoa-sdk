from __future__ import annotations

from builtins import list as builtin_list

from ..compatibility import load_surface
from ..errors import RecordNotFound
from ..models import (
    PlaybookActivationSurface,
    PlaybookAutomationSeed,
    PlaybookCard,
    PlaybookCompositionManifest,
    PlaybookFederationSurface,
    PlaybookFailure,
    PlaybookHandoffContract,
    PlaybookReviewIntake,
    PlaybookReviewPacketContract,
    PlaybookReviewStatus,
    PlaybookSubagentRecipe,
)
from ..workspace.discovery import Workspace


def _match_playbook_name_or_id(
    value: str,
    *,
    card: PlaybookCard | None = None,
    contract: PlaybookHandoffContract | None = None,
    activation: PlaybookActivationSurface | None = None,
    federation: PlaybookFederationSurface | None = None,
    review_status: PlaybookReviewStatus | None = None,
) -> bool:
    needle = value.casefold()
    if card is not None:
        return needle in {card.id.casefold(), card.name.casefold()}
    if contract is not None:
        return needle in {contract.playbook_id.casefold(), contract.name.casefold()}
    if activation is not None:
        return needle in {activation.playbook_id.casefold(), activation.name.casefold()}
    if federation is not None:
        return needle in {federation.playbook_id.casefold(), federation.name.casefold()}
    if review_status is not None:
        return needle in {review_status.playbook_id.casefold(), review_status.playbook_name.casefold()}
    return False


class PlaybooksAPI:
    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace

    def list(
        self,
        *,
        status: str | None = None,
        scenario: str | None = None,
    ) -> builtin_list[PlaybookCard]:
        cards = self._registry()
        if status is not None:
            cards = [card for card in cards if card.status == status]
        if scenario is not None:
            cards = [card for card in cards if card.scenario == scenario]
        return cards

    def get(self, playbook_id_or_name: str) -> PlaybookCard:
        for card in self._registry():
            if _match_playbook_name_or_id(playbook_id_or_name, card=card):
                return card
        raise RecordNotFound(f"Unknown playbook: {playbook_id_or_name}")

    def activation_surface(self, playbook_id_or_name: str) -> PlaybookActivationSurface:
        for surface in self._activation_surfaces():
            if _match_playbook_name_or_id(playbook_id_or_name, activation=surface):
                return surface
        raise RecordNotFound(f"No activation surface for playbook: {playbook_id_or_name}")

    def federation_surface(self, playbook_id_or_name: str) -> PlaybookFederationSurface:
        for surface in self._federation_surfaces():
            if _match_playbook_name_or_id(playbook_id_or_name, federation=surface):
                return surface
        raise RecordNotFound(f"No federation surface for playbook: {playbook_id_or_name}")

    def handoff_contracts(
        self,
        playbook_id_or_name: str | None = None,
    ) -> builtin_list[PlaybookHandoffContract] | PlaybookHandoffContract:
        contracts = self._handoff_contracts()
        if playbook_id_or_name is None:
            return contracts
        for contract in contracts:
            if _match_playbook_name_or_id(playbook_id_or_name, contract=contract):
                return contract
        raise RecordNotFound(f"No handoff contract for playbook: {playbook_id_or_name}")

    def failure_catalog(
        self,
        *,
        code: str | None = None,
        playbook: str | None = None,
    ) -> builtin_list[PlaybookFailure] | PlaybookFailure:
        failures = self._failure_catalog()
        if playbook is not None:
            failures = [item for item in failures if playbook in item.used_by_playbooks]
        if code is None:
            return failures
        for failure in failures:
            if failure.code.casefold() == code.casefold():
                return failure
        raise RecordNotFound(f"Unknown playbook failure code: {code}")

    def subagent_recipe(
        self,
        *,
        name: str | None = None,
        playbook: str | None = None,
    ) -> builtin_list[PlaybookSubagentRecipe] | PlaybookSubagentRecipe:
        recipes = self._subagent_recipes()
        if playbook is not None:
            recipes = [recipe for recipe in recipes if recipe.playbook == playbook]
        if name is None:
            return recipes
        for recipe in recipes:
            if recipe.name.casefold() == name.casefold():
                return recipe
        raise RecordNotFound(f"Unknown playbook subagent recipe: {name}")

    def automation_seeds(
        self,
        playbook_id_or_name: str | None = None,
    ) -> builtin_list[PlaybookAutomationSeed]:
        seeds = self._automation_seeds()
        if playbook_id_or_name is None:
            return seeds

        filtered = [
            seed
            for seed in seeds
            if playbook_id_or_name.casefold() in {seed.playbook.casefold(), seed.name.casefold()}
        ]
        if filtered:
            return filtered
        raise RecordNotFound(f"No automation seeds for playbook: {playbook_id_or_name}")

    def composition_manifest(self) -> PlaybookCompositionManifest:
        data = load_surface(self.workspace, "aoa-playbooks.playbook_composition_manifest")
        return PlaybookCompositionManifest.model_validate(data)

    def review_status(self, playbook_id_or_name: str) -> PlaybookReviewStatus:
        for entry in self._review_status_entries():
            if _match_playbook_name_or_id(playbook_id_or_name, review_status=entry):
                return entry
        raise RecordNotFound(f"No review status for playbook: {playbook_id_or_name}")

    def review_packet_contract(self, playbook_id_or_name: str) -> PlaybookReviewPacketContract:
        for entry in self._review_packet_contracts():
            if playbook_id_or_name.casefold() in {entry.playbook_id.casefold(), entry.playbook_name.casefold()}:
                return entry
        raise RecordNotFound(f"No review packet contract for playbook: {playbook_id_or_name}")

    def review_intake(self, playbook_id_or_name: str) -> PlaybookReviewIntake:
        for entry in self._review_intake_entries():
            if playbook_id_or_name.casefold() in {entry.playbook_id.casefold(), entry.playbook_name.casefold()}:
                return entry
        raise RecordNotFound(f"No review intake for playbook: {playbook_id_or_name}")

    def _registry(self) -> builtin_list[PlaybookCard]:
        data = load_surface(self.workspace, "aoa-playbooks.playbook_registry.min")
        return [PlaybookCard.model_validate(item) for item in data.get("playbooks", [])]

    def _activation_surfaces(self) -> builtin_list[PlaybookActivationSurface]:
        data = load_surface(self.workspace, "aoa-playbooks.playbook_activation_surfaces.min")
        return [PlaybookActivationSurface.model_validate(item) for item in data]

    def _federation_surfaces(self) -> builtin_list[PlaybookFederationSurface]:
        data = load_surface(self.workspace, "aoa-playbooks.playbook_federation_surfaces.min")
        return [PlaybookFederationSurface.model_validate(item) for item in data]

    def _handoff_contracts(self) -> builtin_list[PlaybookHandoffContract]:
        data = load_surface(self.workspace, "aoa-playbooks.playbook_handoff_contracts")
        return [PlaybookHandoffContract.model_validate(item) for item in data.get("playbooks", [])]

    def _failure_catalog(self) -> builtin_list[PlaybookFailure]:
        data = load_surface(self.workspace, "aoa-playbooks.playbook_failure_catalog")
        return [PlaybookFailure.model_validate(item) for item in data.get("failures", [])]

    def _subagent_recipes(self) -> builtin_list[PlaybookSubagentRecipe]:
        data = load_surface(self.workspace, "aoa-playbooks.playbook_subagent_recipes")
        return [PlaybookSubagentRecipe.model_validate(item) for item in data.get("recipes", [])]

    def _automation_seeds(self) -> builtin_list[PlaybookAutomationSeed]:
        data = load_surface(self.workspace, "aoa-playbooks.playbook_automation_seeds")
        return [PlaybookAutomationSeed.model_validate(item) for item in data.get("seeds", [])]

    def _review_status_entries(self) -> builtin_list[PlaybookReviewStatus]:
        data = load_surface(self.workspace, "aoa-playbooks.playbook_review_status.min")
        return [PlaybookReviewStatus.model_validate(item) for item in data.get("playbooks", [])]

    def _review_packet_contracts(self) -> builtin_list[PlaybookReviewPacketContract]:
        data = load_surface(self.workspace, "aoa-playbooks.playbook_review_packet_contracts.min")
        return [PlaybookReviewPacketContract.model_validate(item) for item in data.get("playbooks", [])]

    def _review_intake_entries(self) -> builtin_list[PlaybookReviewIntake]:
        data = load_surface(self.workspace, "aoa-playbooks.playbook_review_intake.min")
        return [PlaybookReviewIntake.model_validate(item) for item in data.get("playbooks", [])]
