from __future__ import annotations

import re

from ..compatibility import load_surface
from ..errors import UnknownKind
from ..loaders import extract_records
from ..models import RegistryEntry, RoutingHint
from ..workspace.discovery import Workspace

def load_routing_hints(workspace: Workspace) -> list[RoutingHint]:
    data = load_surface(workspace, "aoa-routing.task_to_surface_hints")
    return [RoutingHint.model_validate(item) for item in data.get("hints", [])]


def load_cross_repo_registry(workspace: Workspace) -> list[RegistryEntry]:
    data = load_surface(workspace, "aoa-routing.cross_repo_registry.min")
    records = extract_records(data, preferred_keys=("entries",))
    return [RegistryEntry.model_validate(item) for item in records]


def hint_for_kind(workspace: Workspace, kind: str) -> RoutingHint:
    for hint in load_routing_hints(workspace):
        if hint.kind == kind:
            return hint

    raise UnknownKind(f"Unsupported routing kind: {kind}")


def rank_registry_entries(entries: list[RegistryEntry], query: str) -> list[RegistryEntry]:
    if not query.strip():
        return sorted(entries, key=lambda entry: entry.name)

    query_text = query.casefold()
    tokens = re.findall(r"[a-z0-9_-]+", query_text)

    def score(entry: RegistryEntry) -> tuple[int, str]:
        total = 0
        if query_text == entry.id.casefold():
            total += 100
        if query_text == entry.name.casefold():
            total += 100
        if query_text in entry.name.casefold():
            total += 40
        if query_text in entry.summary.casefold():
            total += 20

        for token in tokens:
            if token in entry.id.casefold():
                total += 25
            if token in entry.name.casefold():
                total += 20
            if token in entry.summary.casefold():
                total += 10

        return total, entry.name

    ranked = sorted(entries, key=score, reverse=True)
    return [entry for entry in ranked if score(entry)[0] > 0]
