from __future__ import annotations

from ..errors import IncompatibleSurfaceVersion, RepoNotFound, SurfaceNotFound
from ..models import (
    RoutingOwnerLayerShortlistHint,
    StatsRegroundingSignal,
    SurfaceOpportunityItem,
    SurfaceOpportunityReference,
)
from ..routing.hints import load_owner_layer_shortlist_hints
from ..stats import StatsAPI
from ..workspace.discovery import Workspace
from .common import dedupe_refs, dedupe_shortlist_hints


CURRENT_AOA_SKILL_SURFACES = {
    "aoa-skills.agent_skill_catalog",
    "aoa-skills.skill_pack_profiles.resolved",
    "aoa-skills.capability_graph",
    "aoa-skills.portable_export_map",
    "aoa-skills.mcp_dependency_manifest",
}


def load_shortlist_hints(workspace: Workspace) -> list[RoutingOwnerLayerShortlistHint]:
    try:
        return load_owner_layer_shortlist_hints(workspace)
    except (RepoNotFound, SurfaceNotFound):
        return []


def partition_current_shortlist_hints(
    hints: list[RoutingOwnerLayerShortlistHint],
) -> tuple[list[RoutingOwnerLayerShortlistHint], list[str]]:
    current: list[RoutingOwnerLayerShortlistHint] = []
    gaps: list[str] = []
    for hint in hints:
        refs = [hint.target_surface, hint.inspect_surface]
        stale_refs = [
            ref
            for ref in refs
            if ref
            and ref.startswith("aoa-skills.")
            and ref not in CURRENT_AOA_SKILL_SURFACES
        ]
        if stale_refs:
            gaps.append(
                f"{hint.shortlist_id} references retired aoa-skills surface(s): "
                + ", ".join(dict.fromkeys(stale_refs))
            )
            continue
        current.append(hint)
    return current, gaps


def load_stats_regrounding_hints(
    workspace: Workspace,
    *,
    intent_text: str,
    phase: str,
    mutation_surface: str,
) -> list[StatsRegroundingSignal]:
    try:
        return StatsAPI(workspace).regrounding_signals_for_intent(
            intent_text=intent_text,
            phase=phase,
            mutation_surface=mutation_surface,
        )
    except (RepoNotFound, SurfaceNotFound, IncompatibleSurfaceVersion):
        return []


def regrounding_reason_codes(
    regrounding_hints: list[StatsRegroundingSignal],
) -> list[str]:
    codes: list[str] = []
    for hint in regrounding_hints:
        codes.extend(hint.reason_codes)
    return list(dict.fromkeys(codes))


def enrich_surface_items(
    items: list[SurfaceOpportunityItem],
    *,
    shortlist_hints: list[RoutingOwnerLayerShortlistHint],
) -> list[SurfaceOpportunityItem]:
    return [
        enrich_item_with_shortlist(item, shortlist_hints=shortlist_hints)
        for item in items
    ]


def enrich_item_with_shortlist(
    item: SurfaceOpportunityItem,
    *,
    shortlist_hints: list[RoutingOwnerLayerShortlistHint],
) -> SurfaceOpportunityItem:
    matching = [hint for hint in shortlist_hints if hint.signal in item.signals]
    if not matching:
        return item

    ambiguity_note: str | None = item.owner_layer_ambiguity_note
    matching_repos = {hint.owner_repo for hint in matching}
    if ambiguity_note is None and (
        len(matching_repos) > 1
        or any(hint.ambiguity == "ambiguous" for hint in matching)
    ):
        ambiguity_note = (
            "routing shortlist keeps "
            + ", ".join(sorted(matching_repos))
            + " visible as adjacent owner-layer options until reviewed evidence resolves the ambiguity"
        )

    shortlist_refs = [
        *item.family_entry_refs,
        *[
            SurfaceOpportunityReference(
                role="inspect",
                ref=hint.inspect_surface,
                owner_repo=hint.owner_repo,
                note=hint.hint_reason,
            )
            for hint in matching
            if hint.inspect_surface
        ],
        *[
            SurfaceOpportunityReference(
                role="family-entry",
                ref=hint.target_surface,
                owner_repo=hint.owner_repo,
                note=hint.hint_reason,
            )
            for hint in matching
        ],
    ]
    return item.model_copy(
        update={
            "shortlist_hints": dedupe_shortlist_hints(
                [*item.shortlist_hints, *matching]
            ),
            "owner_layer_ambiguity_note": ambiguity_note,
            "family_entry_refs": dedupe_refs(shortlist_refs),
        }
    )
