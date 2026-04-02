from __future__ import annotations

from builtins import list as builtin_list
import re

from ..compatibility import load_surface
from ..errors import RecordNotFound
from ..models import (
    MemoCapsule,
    MemoObjectCapsule,
    MemoObjectCard,
    MemoObjectSectionBundle,
    MemoSectionBundle,
    MemoSurface,
    MemoWritebackMap,
    MemoWritebackRule,
    MemoWritebackIntakeTarget,
    MemoWritebackTarget,
)
from ..workspace.discovery import Workspace


def _tokens(query: str) -> list[str]:
    return re.findall(r"[a-z0-9_-]+", query.casefold())


def _score_texts(query: str, *texts: str) -> int:
    query_text = query.casefold().strip()
    if not query_text:
        return 1

    score = 0
    lowered = [text.casefold() for text in texts if text]
    if any(query_text == text for text in lowered):
        score += 100
    if any(query_text in text for text in lowered):
        score += 40
    for token in _tokens(query):
        for text in lowered:
            if token in text:
                score += 10
    return score


def _filter_sections(sections: list, requested: list[str] | None):
    if not requested:
        return sections

    needles = {item.casefold() for item in requested}
    filtered = [
        section
        for section in sections
        if getattr(section, "section_id", "").casefold() in needles
        or getattr(section, "heading", "").casefold() in needles
    ]
    return filtered


class MemoAPI:
    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace

    def list(self) -> builtin_list[MemoSurface]:
        data = load_surface(self.workspace, "aoa-memo.memory_catalog.min")
        return [MemoSurface.model_validate(item) for item in data.get("memo_surfaces", [])]

    def inspect(self, id_or_name: str) -> MemoSurface:
        for entry in self.list():
            if id_or_name.casefold() in {entry.id.casefold(), entry.name.casefold()}:
                return entry
        raise RecordNotFound(f"Unknown memo surface: {id_or_name}")

    def capsule(self, id_or_name: str) -> MemoCapsule:
        data = load_surface(self.workspace, "aoa-memo.memory_capsules")
        for entry in data.get("memo_surfaces", []):
            capsule = MemoCapsule.model_validate(entry)
            if id_or_name.casefold() in {capsule.id.casefold(), capsule.name.casefold()}:
                return capsule
        raise RecordNotFound(f"Unknown memo capsule: {id_or_name}")

    def expand(
        self,
        id_or_name: str,
        sections: builtin_list[str] | None = None,
    ) -> MemoSectionBundle:
        data = load_surface(self.workspace, "aoa-memo.memory_sections.full")
        for entry in data.get("memo_surfaces", []):
            bundle = MemoSectionBundle.model_validate(entry)
            if id_or_name.casefold() in {bundle.id.casefold(), bundle.name.casefold()}:
                return MemoSectionBundle(
                    id=bundle.id,
                    name=bundle.name,
                    source_path=bundle.source_path,
                    sections=_filter_sections(bundle.sections, sections),
                )
        raise RecordNotFound(f"Unknown memo section bundle: {id_or_name}")

    def recall(self, *, mode: str = "semantic", query: str) -> builtin_list[MemoSurface]:
        candidates = [entry for entry in self.list() if mode in entry.recall_modes]
        ranked = sorted(
            candidates,
            key=lambda entry: _score_texts(query, entry.name, entry.summary, entry.primary_focus),
            reverse=True,
        )
        return [entry for entry in ranked if _score_texts(query, entry.name, entry.summary, entry.primary_focus) > 0]

    def recall_object(
        self,
        *,
        mode: str = "working",
        query: str,
    ) -> builtin_list[MemoObjectCard]:
        candidates = [entry for entry in self.object_list() if mode in entry.primary_recall_modes]
        ranked = sorted(
            candidates,
            key=lambda entry: _score_texts(query, entry.id, entry.title, entry.summary, entry.kind),
            reverse=True,
        )
        return [entry for entry in ranked if _score_texts(query, entry.id, entry.title, entry.summary, entry.kind) > 0]

    def object_list(self) -> builtin_list[MemoObjectCard]:
        data = load_surface(self.workspace, "aoa-memo.memory_object_catalog.min")
        return [MemoObjectCard.model_validate(item) for item in data.get("memory_objects", [])]

    def inspect_object(self, id_or_title: str) -> MemoObjectCard:
        for entry in self.object_list():
            if id_or_title.casefold() in {entry.id.casefold(), entry.title.casefold()}:
                return entry
        raise RecordNotFound(f"Unknown memo object: {id_or_title}")

    def capsule_object(self, id_or_title: str) -> MemoObjectCapsule:
        data = load_surface(self.workspace, "aoa-memo.memory_object_capsules")
        for entry in data.get("memory_objects", []):
            capsule = MemoObjectCapsule.model_validate(entry)
            if id_or_title.casefold() in {capsule.id.casefold(), capsule.title.casefold()}:
                return capsule
        raise RecordNotFound(f"Unknown memo object capsule: {id_or_title}")

    def expand_object(
        self,
        id_or_title: str,
        sections: builtin_list[str] | None = None,
    ) -> MemoObjectSectionBundle:
        data = load_surface(self.workspace, "aoa-memo.memory_object_sections.full")
        for entry in data.get("memory_objects", []):
            bundle = MemoObjectSectionBundle.model_validate(entry)
            if id_or_title.casefold() in {bundle.id.casefold(), bundle.title.casefold()}:
                return MemoObjectSectionBundle(
                    id=bundle.id,
                    kind=bundle.kind,
                    title=bundle.title,
                    source_path=bundle.source_path,
                    sections=_filter_sections(bundle.sections, sections),
                )
        raise RecordNotFound(f"Unknown memo object section bundle: {id_or_title}")

    def writeback_map(self, runtime_surface: str) -> MemoWritebackMap:
        data = load_surface(self.workspace, "aoa-memo.checkpoint_to_memory_contract.example")
        for item in data.get("mapping_rules", []):
            if item.get("runtime_surface") != runtime_surface:
                continue
            return MemoWritebackMap(
                runtime_surface=runtime_surface,
                contract_type=data["contract_type"],
                contract_id=data["contract_id"],
                runtime_boundary=data.get("runtime_boundary", {}),
                mapping=MemoWritebackRule.model_validate(item),
                source_files=[
                    str(self.workspace.surface_path("aoa-memo", "examples/checkpoint_to_memory_contract.example.json")),
                    str(self.workspace.surface_path("aoa-memo", "docs/RUNTIME_WRITEBACK_SEAM.md")),
                ],
            )
        raise RecordNotFound(f"Unknown memo writeback runtime surface: {runtime_surface}")

    def writeback_targets(self) -> builtin_list[MemoWritebackTarget]:
        data = load_surface(self.workspace, "aoa-memo.runtime_writeback_targets.min")
        return [MemoWritebackTarget.model_validate(item) for item in data.get("targets", [])]

    def writeback_target(self, runtime_surface: str) -> MemoWritebackTarget:
        for target in self.writeback_targets():
            if target.runtime_surface == runtime_surface:
                return target
        raise RecordNotFound(f"Unknown memo writeback target runtime surface: {runtime_surface}")

    def writeback_intake(
        self,
        runtime_surface: str | None = None,
    ) -> builtin_list[MemoWritebackIntakeTarget] | MemoWritebackIntakeTarget:
        entries = self._writeback_intake_entries()
        if runtime_surface is None:
            return entries
        for entry in entries:
            if entry.runtime_surface == runtime_surface:
                return entry
        raise RecordNotFound(f"Unknown memo writeback intake runtime surface: {runtime_surface}")

    def _writeback_intake_entries(self) -> builtin_list[MemoWritebackIntakeTarget]:
        data = load_surface(self.workspace, "aoa-memo.runtime_writeback_intake.min")
        return [MemoWritebackIntakeTarget.model_validate(item) for item in data.get("targets", [])]
