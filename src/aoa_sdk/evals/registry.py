from __future__ import annotations

from ..compatibility import load_surface
from ..errors import RecordNotFound
from ..models import ComparisonEntry, EvalCapsule, EvalCard, EvalSectionBundle
from ..workspace.discovery import Workspace


class EvalsAPI:
    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace

    def list(
        self,
        *,
        category: str | None = None,
        status: str | None = None,
        skill_dependency: str | None = None,
    ) -> list[EvalCard]:
        cards = self._cards()
        if category is not None:
            cards = [card for card in cards if card.category == category]
        if status is not None:
            cards = [card for card in cards if card.status == status]
        if skill_dependency is not None:
            cards = [card for card in cards if skill_dependency in card.skill_dependencies]
        return cards

    def inspect(self, name: str) -> EvalCapsule:
        for capsule in self._capsules():
            if capsule.name.casefold() == name.casefold():
                return capsule
        raise RecordNotFound(f"Unknown eval: {name}")

    def expand(self, name: str, sections: list[str] | None = None) -> EvalSectionBundle:
        for bundle in self._section_bundles():
            if bundle.name.casefold() == name.casefold():
                if not sections:
                    return bundle
                needles = {item.casefold() for item in sections}
                return EvalSectionBundle(
                    category=bundle.category,
                    eval_path=bundle.eval_path,
                    name=bundle.name,
                    sections=[
                        section
                        for section in bundle.sections
                        if section.key.casefold() in needles or section.heading.casefold() in needles
                    ],
                    status=bundle.status,
                    verdict_shape=bundle.verdict_shape,
                )
        raise RecordNotFound(f"Unknown eval section bundle: {name}")

    def comparison_entries(
        self,
        *,
        name: str | None = None,
        baseline_mode: str | None = None,
    ) -> list[ComparisonEntry] | ComparisonEntry:
        entries = self._comparison_entries()
        if baseline_mode is not None:
            entries = [entry for entry in entries if entry.baseline_mode == baseline_mode]
        if name is None:
            return entries
        for entry in entries:
            if entry.name.casefold() == name.casefold():
                return entry
        raise RecordNotFound(f"Unknown comparison entry: {name}")

    def _cards(self) -> list[EvalCard]:
        data = load_surface(self.workspace, "aoa-evals.eval_catalog.min")
        return [EvalCard.model_validate(item) for item in data.get("evals", [])]

    def _capsules(self) -> list[EvalCapsule]:
        data = load_surface(self.workspace, "aoa-evals.eval_capsules")
        return [EvalCapsule.model_validate(item) for item in data.get("evals", [])]

    def _section_bundles(self) -> list[EvalSectionBundle]:
        data = load_surface(self.workspace, "aoa-evals.eval_sections.full")
        return [EvalSectionBundle.model_validate(item) for item in data.get("evals", [])]

    def _comparison_entries(self) -> list[ComparisonEntry]:
        data = load_surface(self.workspace, "aoa-evals.comparison_spine")
        return [ComparisonEntry.model_validate(item) for item in data.get("evals", [])]
