from __future__ import annotations

from ..compatibility import load_surface
from ..errors import RecordNotFound
from ..models import (
    PlaybookActivationSurface,
    PlaybookCard,
    PlaybookCompositionManifest,
    PlaybookFederationSurface,
    PlaybookAutomationSeed,
    PlaybookFailure,
    PlaybookHandoffContract,
    PlaybookSubagentRecipe,
)
from ..workspace.discovery import Workspace


def _match_playbook_name_or_id(
    value: str,
    *,
    card: PlaybookCard | None = None,
    contract=None,
    activation=None,
    federation=None,
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
    return False


class PlaybooksAPI:
    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace

    def list(self, *, status: str | None = None, scenario: str | None = None) -> list[PlaybookCard]:
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
    ) -> list[PlaybookHandoffContract] | PlaybookHandoffContract:
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
    ) -> list[PlaybookFailure] | PlaybookFailure:
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
    ) -> list[PlaybookSubagentRecipe] | PlaybookSubagentRecipe:
        recipes = self._subagent_recipes()
        if playbook is not None:
            recipes = [recipe for recipe in recipes if recipe.playbook == playbook]
        if name is None:
            return recipes
        for recipe in recipes:
            if recipe.name.casefold() == name.casefold():
                return recipe
        raise RecordNotFound(f"Unknown playbook subagent recipe: {name}")

    def automation_seeds(self, playbook_id_or_name: str | None = None) -> list[PlaybookAutomationSeed]:
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

    def _registry(self) -> list[PlaybookCard]:
        data = load_surface(self.workspace, "aoa-playbooks.playbook_registry.min")
        return [PlaybookCard.model_validate(item) for item in data.get("playbooks", [])]

    def _activation_surfaces(self) -> list[PlaybookActivationSurface]:
        data = load_surface(self.workspace, "aoa-playbooks.playbook_activation_surfaces.min")
        return [PlaybookActivationSurface.model_validate(item) for item in data]

    def _federation_surfaces(self) -> list[PlaybookFederationSurface]:
        data = load_surface(self.workspace, "aoa-playbooks.playbook_federation_surfaces.min")
        return [PlaybookFederationSurface.model_validate(item) for item in data]

    def _handoff_contracts(self) -> list[PlaybookHandoffContract]:
        data = load_surface(self.workspace, "aoa-playbooks.playbook_handoff_contracts")
        return [PlaybookHandoffContract.model_validate(item) for item in data.get("playbooks", [])]

    def _failure_catalog(self) -> list[PlaybookFailure]:
        data = load_surface(self.workspace, "aoa-playbooks.playbook_failure_catalog")
        return [PlaybookFailure.model_validate(item) for item in data.get("failures", [])]

    def _subagent_recipes(self) -> list[PlaybookSubagentRecipe]:
        data = load_surface(self.workspace, "aoa-playbooks.playbook_subagent_recipes")
        return [PlaybookSubagentRecipe.model_validate(item) for item in data.get("recipes", [])]

    def _automation_seeds(self) -> list[PlaybookAutomationSeed]:
        data = load_surface(self.workspace, "aoa-playbooks.playbook_automation_seeds")
        return [PlaybookAutomationSeed.model_validate(item) for item in data.get("seeds", [])]
