from __future__ import annotations

from typing import Literal

from ..compatibility import load_surface
from ..errors import RecordNotFound
from ..models import (
    KagFederationSpine,
    KagInspectResult,
    KagQueryModeResult,
    KagRegistrySurface,
    KagRegroundingMode,
    KagRepoEntry,
    KagTinyConsumerBundle,
)
from ..workspace.discovery import Workspace


INSPECT_PACK_SURFACES = {
    "AOA-K-0005": "aoa-kag.tos_text_chunk_map.min",
    "AOA-K-0006": "aoa-kag.cross_source_node_projection.min",
    "AOA-K-0007": "aoa-kag.tos_retrieval_axis_pack.min",
    "AOA-K-0008": "aoa-kag.counterpart_federation_exposure_review.min",
    "AOA-K-0009": "aoa-kag.federation_spine.min",
    "AOA-K-0011": "aoa-kag.tos_zarathustra_route_retrieval_pack.min",
}

KagQueryModeName = Literal["local_search", "global_search", "drift_search"]


class KagAPI:
    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace

    def registry(self) -> list[KagRegistrySurface]:
        data = load_surface(self.workspace, "aoa-kag.kag_registry.min")
        return [KagRegistrySurface.model_validate(item) for item in data.get("surfaces", [])]

    def federation_spine(self) -> KagFederationSpine:
        data = load_surface(self.workspace, "aoa-kag.federation_spine.min")
        return KagFederationSpine.model_validate(data)

    def tiny_bundle(self) -> KagTinyConsumerBundle:
        data = load_surface(self.workspace, "aoa-kag.tiny_consumer_bundle.min")
        return KagTinyConsumerBundle.model_validate(data)

    def inspect(self, surface_id: str) -> KagInspectResult:
        surface_rule_id = INSPECT_PACK_SURFACES.get(surface_id)
        if surface_rule_id is None:
            raise RecordNotFound(f"Unknown inspectable KAG surface: {surface_id}")

        registry_entry = next((entry for entry in self.registry() if entry.id == surface_id), None)
        if registry_entry is None:
            raise RecordNotFound(f"KAG registry entry not found: {surface_id}")

        pack = load_surface(self.workspace, surface_rule_id)
        return KagInspectResult(
            surface_id=surface_id,
            registry_entry=registry_entry,
            pack=pack,
            source_files=[
                str(self.workspace.surface_path("aoa-kag", "generated/kag_registry.min.json")),
                str(self.workspace.surface_path("aoa-kag", _relative_path_for(surface_rule_id))),
            ],
        )

    def query_mode(self, mode: str) -> KagQueryModeResult:
        validated_mode: KagQueryModeName
        if mode == "local_search":
            validated_mode = "local_search"
        elif mode == "global_search":
            validated_mode = "global_search"
        elif mode == "drift_search":
            validated_mode = "drift_search"
        else:
            raise RecordNotFound(f"Unknown KAG query mode: {mode}")

        handoff_pack = load_surface(self.workspace, "aoa-kag.reasoning_handoff_pack.min")
        regrounding_pack = load_surface(self.workspace, "aoa-kag.return_regrounding_pack.min")

        scenarios = [
            scenario
            for scenario in handoff_pack.get("scenarios", [])
            if mode in scenario.get("compatible_query_modes", [])
        ]
        regrounding_modes = [
            KagRegroundingMode.model_validate(item)
            for item in regrounding_pack.get("modes", [])
            if item.get("query_mode_hint") == mode
        ]
        if not scenarios and not regrounding_modes:
            raise RecordNotFound(f"No KAG query-mode support for: {mode}")

        return KagQueryModeResult(
            mode=validated_mode,
            reasoning_scenarios=scenarios,
            regrounding_modes=regrounding_modes,
            source_files=[
                str(self.workspace.surface_path("aoa-kag", "generated/reasoning_handoff_pack.min.json")),
                str(self.workspace.surface_path("aoa-kag", "generated/return_regrounding_pack.min.json")),
            ],
        )

    def regrounding(self, mode_id: str) -> KagRegroundingMode:
        data = load_surface(self.workspace, "aoa-kag.return_regrounding_pack.min")
        for item in data.get("modes", []):
            mode = KagRegroundingMode.model_validate(item)
            if mode.mode_id == mode_id:
                return mode
        raise RecordNotFound(f"Unknown KAG regrounding mode: {mode_id}")

    def repo_entry(self, repo: str) -> KagRepoEntry:
        if repo not in {"Tree-of-Sophia", "aoa-techniques"}:
            raise RecordNotFound(f"Unknown KAG repo entry: {repo}")

        for item in self.federation_spine().repos:
            entry = KagRepoEntry.model_validate(item.model_dump())
            if entry.repo == repo:
                return entry
        raise RecordNotFound(f"KAG federation entry not found: {repo}")


def _relative_path_for(surface_rule_id: str) -> str:
    relative_paths = {
        "aoa-kag.tos_text_chunk_map.min": "generated/tos_text_chunk_map.min.json",
        "aoa-kag.cross_source_node_projection.min": "generated/cross_source_node_projection.min.json",
        "aoa-kag.tos_retrieval_axis_pack.min": "generated/tos_retrieval_axis_pack.min.json",
        "aoa-kag.counterpart_federation_exposure_review.min": "generated/counterpart_federation_exposure_review.min.json",
        "aoa-kag.federation_spine.min": "generated/federation_spine.min.json",
        "aoa-kag.tos_zarathustra_route_retrieval_pack.min": "generated/tos_zarathustra_route_retrieval_pack.min.json",
    }
    return relative_paths[surface_rule_id]
