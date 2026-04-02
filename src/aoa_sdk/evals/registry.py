from __future__ import annotations

from builtins import list as builtin_list

from ..compatibility import load_surface
from ..errors import RecordNotFound
from ..models import (
    ComparisonEntry,
    EvalCapsule,
    EvalCard,
    EvalRuntimeCandidateIntake,
    EvalRuntimeCandidateTemplate,
    EvalSectionBundle,
)
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
    ) -> builtin_list[EvalCard]:
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

    def expand(
        self,
        name: str,
        sections: builtin_list[str] | None = None,
    ) -> EvalSectionBundle:
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
    ) -> builtin_list[ComparisonEntry] | ComparisonEntry:
        entries = self._comparison_entries()
        if baseline_mode is not None:
            entries = [entry for entry in entries if entry.baseline_mode == baseline_mode]
        if name is None:
            return entries
        for entry in entries:
            if entry.name.casefold() == name.casefold():
                return entry
        raise RecordNotFound(f"Unknown comparison entry: {name}")

    def runtime_candidate_templates(
        self,
        *,
        template_kind: str | None = None,
        playbook_id: str | None = None,
    ) -> builtin_list[EvalRuntimeCandidateTemplate]:
        templates = self._runtime_candidate_templates()
        if template_kind is not None:
            templates = [entry for entry in templates if entry.template_kind == template_kind]
        if playbook_id is not None:
            templates = [entry for entry in templates if entry.playbook_id == playbook_id]
        return templates

    def runtime_candidate_intake(
        self,
        *,
        template_kind: str | None = None,
        playbook_id: str | None = None,
    ) -> builtin_list[EvalRuntimeCandidateIntake]:
        entries = self._runtime_candidate_intake_entries()
        if template_kind is not None:
            entries = [entry for entry in entries if entry.template_kind == template_kind]
        if playbook_id is not None:
            entries = [entry for entry in entries if entry.playbook_id == playbook_id]
        return entries

    def _cards(self) -> builtin_list[EvalCard]:
        data = load_surface(self.workspace, "aoa-evals.eval_catalog.min")
        return [EvalCard.model_validate(item) for item in data.get("evals", [])]

    def _capsules(self) -> builtin_list[EvalCapsule]:
        data = load_surface(self.workspace, "aoa-evals.eval_capsules")
        return [EvalCapsule.model_validate(item) for item in data.get("evals", [])]

    def _section_bundles(self) -> builtin_list[EvalSectionBundle]:
        data = load_surface(self.workspace, "aoa-evals.eval_sections.full")
        return [EvalSectionBundle.model_validate(item) for item in data.get("evals", [])]

    def _comparison_entries(self) -> builtin_list[ComparisonEntry]:
        data = load_surface(self.workspace, "aoa-evals.comparison_spine")
        return [ComparisonEntry.model_validate(item) for item in data.get("evals", [])]

    def _runtime_candidate_templates(self) -> builtin_list[EvalRuntimeCandidateTemplate]:
        data = load_surface(self.workspace, "aoa-evals.runtime_candidate_template_index.min")
        return [EvalRuntimeCandidateTemplate.model_validate(item) for item in data.get("templates", [])]

    def _runtime_candidate_intake_entries(self) -> builtin_list[EvalRuntimeCandidateIntake]:
        data = load_surface(self.workspace, "aoa-evals.runtime_candidate_intake.min")
        return [EvalRuntimeCandidateIntake.model_validate(item) for item in data.get("templates", [])]
