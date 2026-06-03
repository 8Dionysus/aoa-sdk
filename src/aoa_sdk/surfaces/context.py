from __future__ import annotations

import json

from ..errors import IncompatibleSurfaceVersion, InvalidSurface, RepoNotFound, SurfaceNotFound
from ..models import (
    RoutingOwnerLayerShortlistHint,
    StatsRegroundingSignal,
    SurfaceOpportunityItem,
    SurfaceOpportunityReference,
)
from ..routing.hints import load_owner_layer_shortlist_hints
from ..skills.session import load_session
from ..stats import StatsAPI
from ..workspace.discovery import Workspace
from .common import dedupe_refs, dedupe_shortlist_hints


def load_active_skill_names(workspace: Workspace, *, session_file: str | None) -> list[str]:
    try:
        session = load_session(workspace, session_file)
    except (InvalidSurface, SurfaceNotFound):
        return []
    return [record.name for record in session.active_skills]


def load_shortlist_hints(workspace: Workspace) -> list[RoutingOwnerLayerShortlistHint]:
    try:
        return load_owner_layer_shortlist_hints(workspace)
    except (RepoNotFound, SurfaceNotFound):
        return []


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


def regrounding_reason_codes(regrounding_hints: list[StatsRegroundingSignal]) -> list[str]:
    codes: list[str] = []
    for hint in regrounding_hints:
        codes.extend(hint.reason_codes)
    return list(dict.fromkeys(codes))


def load_core_skill_receipt_contexts(workspace: Workspace) -> dict[str, dict[str, object]]:
    try:
        receipt_path = workspace.repo_path("aoa-skills") / ".aoa" / "live_receipts" / "core-skill-applications.jsonl"
    except RepoNotFound:
        return {}
    if not receipt_path.exists():
        return {}

    latest_by_skill: dict[str, dict[str, object]] = {}
    for line_number, raw_line in enumerate(receipt_path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        try:
            receipt = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(receipt, dict) or receipt.get("event_kind") != "core_skill_application_receipt":
            continue
        payload = receipt.get("payload")
        if not isinstance(payload, dict) or payload.get("application_stage") != "finish":
            continue
        skill_name = payload.get("skill_name")
        if not isinstance(skill_name, str) or not skill_name:
            continue
        sort_key = (str(receipt.get("observed_at") or ""), str(receipt.get("event_id") or ""), line_number)
        existing = latest_by_skill.get(skill_name)
        existing_sort_key = existing.get("_sort_key") if existing is not None else None
        if (
            isinstance(existing_sort_key, tuple)
            and len(existing_sort_key) == 3
            and isinstance(existing_sort_key[0], str)
            and isinstance(existing_sort_key[1], str)
            and isinstance(existing_sort_key[2], int)
            and existing_sort_key >= sort_key
        ):
            continue
        context = payload.get("surface_detection_context")
        latest_by_skill[skill_name] = {
            "_sort_key": sort_key,
            "event_id": receipt.get("event_id"),
            "detail_receipt_ref": payload.get("detail_receipt_ref"),
            "surface_detection_context": context if isinstance(context, dict) else {},
        }
    return latest_by_skill


def enrich_surface_items(
    items: list[SurfaceOpportunityItem],
    *,
    shortlist_hints: list[RoutingOwnerLayerShortlistHint],
    skill_receipt_contexts: dict[str, dict[str, object]],
) -> list[SurfaceOpportunityItem]:
    enriched = [
        enrich_item_with_shortlist(item, shortlist_hints=shortlist_hints)
        for item in items
    ]
    return [
        enrich_item_with_skill_receipt_context(item, skill_receipt_contexts=skill_receipt_contexts)
        for item in enriched
    ]


def enrich_item_with_shortlist(
    item: SurfaceOpportunityItem,
    *,
    shortlist_hints: list[RoutingOwnerLayerShortlistHint],
) -> SurfaceOpportunityItem:
    matching = [
        hint
        for hint in shortlist_hints
        if hint.signal in item.signals
    ]
    if not matching:
        return item

    ambiguity_note: str | None = item.owner_layer_ambiguity_note
    matching_repos = {hint.owner_repo for hint in matching}
    if ambiguity_note is None and (len(matching_repos) > 1 or any(hint.ambiguity == "ambiguous" for hint in matching)):
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
        *[
            SurfaceOpportunityReference(
                role="inspect",
                ref=hint.target_surface,
                owner_repo=hint.owner_repo,
                note=hint.hint_reason,
            )
            for hint in matching
            if hint.inspect_surface and hint.inspect_surface != hint.target_surface
        ],
    ]
    return item.model_copy(
        update={
            "shortlist_hints": dedupe_shortlist_hints([*item.shortlist_hints, *matching]),
            "owner_layer_ambiguity_note": ambiguity_note,
            "family_entry_refs": dedupe_refs(shortlist_refs),
        }
    )


def enrich_item_with_skill_receipt_context(
    item: SurfaceOpportunityItem,
    *,
    skill_receipt_contexts: dict[str, dict[str, object]],
) -> SurfaceOpportunityItem:
    if item.object_kind != "skill" or not item.surface_ref.startswith("aoa-skills:"):
        return item
    skill_name = item.surface_ref.split(":", 1)[1]
    receipt_info = skill_receipt_contexts.get(skill_name)
    if receipt_info is None:
        return item

    evidence_refs = list(item.evidence_refs)
    event_id = receipt_info.get("event_id")
    if isinstance(event_id, str) and event_id:
        evidence_refs.append(
            SurfaceOpportunityReference(
                role="runtime-receipt",
                ref=f"repo:aoa-skills/.aoa/live_receipts/core-skill-applications.jsonl#{event_id}",
                owner_repo="aoa-skills",
                note="latest finish-stage core skill receipt",
            )
        )
    detail_receipt_ref = receipt_info.get("detail_receipt_ref")
    if isinstance(detail_receipt_ref, str) and detail_receipt_ref:
        evidence_refs.append(
            SurfaceOpportunityReference(
                role="runtime-receipt",
                ref=detail_receipt_ref,
                owner_repo="aoa-skills",
                note="detail receipt linked from the latest finish-stage core skill receipt",
            )
        )

    context = receipt_info.get("surface_detection_context")
    if not isinstance(context, dict):
        context = {}
    if isinstance(context.get("surface_detection_report_ref"), str) and context["surface_detection_report_ref"]:
        evidence_refs.append(
            SurfaceOpportunityReference(
                role="skill-report",
                ref=context["surface_detection_report_ref"],
                owner_repo="aoa-sdk",
                note="reviewed surface detection report captured by the skill-side receipt",
            )
        )
    if isinstance(context.get("surface_closeout_handoff_ref"), str) and context["surface_closeout_handoff_ref"]:
        evidence_refs.append(
            SurfaceOpportunityReference(
                role="closeout-handoff",
                ref=context["surface_closeout_handoff_ref"],
                owner_repo="aoa-sdk",
                note="reviewed surface closeout handoff captured by the skill-side receipt",
            )
        )

    family_entry_refs = list(item.family_entry_refs)
    family_entry_refs.extend(
        SurfaceOpportunityReference(
            role="family-entry",
            ref=ref,
            note="adjacent owner-layer family entry preserved in the latest core skill receipt",
        )
        for ref in context.get("family_entry_refs", [])
        if isinstance(ref, str) and ref
    )

    ambiguity_note = item.owner_layer_ambiguity_note
    if ambiguity_note is None and bool(context.get("owner_layer_ambiguity")):
        adjacent_owner_repos = [
            repo
            for repo in context.get("adjacent_owner_repos", [])
            if isinstance(repo, str) and repo
        ]
        if adjacent_owner_repos:
            ambiguity_note = (
                "skill receipt preserved adjacent owner-layer relevance for "
                + ", ".join(adjacent_owner_repos)
            )

    return item.model_copy(
        update={
            "owner_layer_ambiguity_note": ambiguity_note,
            "family_entry_refs": dedupe_refs(family_entry_refs),
            "evidence_refs": dedupe_refs(evidence_refs),
        }
    )
