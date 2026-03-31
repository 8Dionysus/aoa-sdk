from __future__ import annotations

from typing import Any

from ..loaders import extract_records, find_record, load_json
from ..models import RegistryEntry, RoutingHint
from .hints import hint_for_kind, load_cross_repo_registry, load_routing_hints, rank_registry_entries


class RoutingAPI:
    def __init__(self, workspace) -> None:
        self.workspace = workspace

    def hints(self) -> list[RoutingHint]:
        return load_routing_hints(self.workspace)

    def pick(self, *, kind: str, query: str) -> list[RegistryEntry]:
        hint = hint_for_kind(self.workspace, kind)
        if not hint.enabled or not hint.actions.get("pick", None) or not hint.actions["pick"].enabled:
            return []

        entries = [entry for entry in load_cross_repo_registry(self.workspace) if entry.kind == kind]
        return rank_registry_entries(entries, query)

    def inspect(self, *, kind: str, id_or_name: str) -> dict[str, Any]:
        hint = hint_for_kind(self.workspace, kind)
        action = hint.actions["inspect"]
        return self._load_action_record(hint, action_repo=action.surface_repo or hint.source_repo, surface_file=action.surface_file, match_field=action.match_field, value=id_or_name)

    def expand(self, *, kind: str, id_or_name: str, sections: list[str] | None = None) -> dict[str, Any]:
        hint = hint_for_kind(self.workspace, kind)
        action = hint.actions["expand"]
        record = self._load_action_record(
            hint,
            action_repo=action.surface_repo or hint.source_repo,
            surface_file=action.surface_file,
            match_field=action.match_field,
            value=id_or_name,
        )

        section_key_field = action.section_key_field
        if not section_key_field or "sections" not in record:
            return record

        requested = sections or action.default_sections
        if not requested:
            return record

        filtered = [
            section
            for section in record["sections"]
            if section.get(section_key_field) in requested
        ]
        return {**record, "sections": filtered}

    def _load_action_record(
        self,
        hint: RoutingHint,
        *,
        action_repo: str,
        surface_file: str | None,
        match_field: str | None,
        value: str,
    ) -> dict[str, Any]:
        if not surface_file or not match_field:
            raise ValueError(f"Routing action for {hint.kind!r} does not define a record surface")

        data = load_json(self.workspace.surface_path(action_repo, surface_file))
        records = extract_records(data, preferred_keys=("skills", "entries", "items", "bindings", "hints"))
        return find_record(records, field=match_field, value=value)
