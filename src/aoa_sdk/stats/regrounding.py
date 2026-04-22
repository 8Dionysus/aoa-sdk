from __future__ import annotations

import re
from typing import Literal

from ..models import (
    StatsRegroundingAction,
    StatsRegroundingSignal,
    StatsSourceCoverageSummary,
    StatsSummarySurface,
)

PHASES = {"ingress", "in-flight", "pre-mutation", "checkpoint", "closeout"}
MUTATION_SURFACES = {"none", "code", "repo-config", "infra", "runtime", "public-share"}
RISKY_MUTATION_SURFACES = {"code", "repo-config", "infra", "runtime", "public-share"}
REGROUNDING_INTENT_TOKENS = {
    "stats",
    "summary",
    "summaries",
    "derived",
    "observability",
    "source_coverage",
    "source-coverage",
    "surface_profile",
    "surface-profile",
    "reground",
    "regrounding",
    "re-ground",
    "re-grounding",
}


def build_regrounding_signal(
    *,
    surface: StatsSummarySurface,
    coverage: StatsSourceCoverageSummary,
    phase: Literal["ingress", "in-flight", "pre-mutation", "checkpoint", "closeout"] = "ingress",
    mutation_surface: Literal["none", "code", "repo-config", "infra", "runtime", "public-share"] = "none",
) -> StatsRegroundingSignal:
    if phase not in PHASES:
        raise ValueError(f"unsupported phase {phase!r}")
    if mutation_surface not in MUTATION_SURFACES:
        raise ValueError(f"unsupported mutation_surface {mutation_surface!r}")

    reason_codes: list[str] = []
    decision: Literal["clear", "reground_recommended", "reground_required"] = "clear"

    if surface.consumer_risk == "high":
        reason_codes.append("high_consumer_risk")
        decision = _raise_decision(decision, "reground_recommended")
    elif surface.consumer_risk == "medium":
        reason_codes.append("medium_consumer_risk")

    if surface.input_posture in {"checked_in_owner_history", "reviewed_example_chain"}:
        reason_codes.append(f"{surface.input_posture}_posture")
        decision = _raise_decision(decision, "reground_recommended")

    if surface.input_posture == "receipt_backed_with_external_reports":
        reason_codes.append("external_report_dependency")
        decision = _raise_decision(decision, "reground_recommended")

    if surface.live_state_capable is False:
        reason_codes.append("not_live_state_capable")
        decision = _raise_decision(decision, "reground_recommended")

    for flag in coverage.thin_signal_flags:
        reason_codes.append(f"coverage_{flag}")

    if coverage.source_mode != "registry_backed_receipt_feed":
        reason_codes.append(f"coverage_source_mode_{coverage.source_mode}")

    if coverage.active_receipt_total == 0:
        reason_codes.append("coverage_no_active_receipts")

    risky_context = phase == "pre-mutation" or mutation_surface in RISKY_MUTATION_SURFACES
    thin_coverage = bool(coverage.thin_signal_flags) or coverage.active_receipt_total == 0
    if thin_coverage and risky_context:
        decision = _raise_decision(decision, "reground_required")
    elif thin_coverage:
        decision = _raise_decision(decision, "reground_recommended")

    if surface.input_posture == "receipt_backed_with_external_reports" and thin_coverage:
        decision = _raise_decision(decision, "reground_required" if risky_context else "reground_recommended")

    reason_codes = _dedupe(reason_codes)
    return StatsRegroundingSignal(
        surface_name=surface.name,
        surface_ref=surface.surface_ref,
        decision=decision,
        phase=phase,
        mutation_surface=mutation_surface,
        reason_codes=reason_codes,
        source_refs=[
            "aoa-stats.summary_surface_catalog.min",
            "aoa-stats.source_coverage_summary.min",
        ],
        owner_truth_inputs=list(surface.owner_truth_inputs),
        authority_ceiling=surface.authority_ceiling,
        consumer_risk=surface.consumer_risk,
        input_posture=surface.input_posture,
        live_state_capable=surface.live_state_capable,
        coverage_thin_signal_flags=list(coverage.thin_signal_flags),
        next_actions=_next_actions(surface=surface, coverage=coverage, reason_codes=reason_codes),
    )


def select_regrounding_surfaces(
    *,
    surfaces: list[StatsSummarySurface],
    intent_text: str = "",
) -> list[StatsSummarySurface]:
    intent = intent_text.casefold()
    if not is_regrounding_intent(intent):
        return []

    tokens = set(re.findall(r"[a-z0-9_-]+", intent))
    selected: list[StatsSummarySurface] = []
    for surface in surfaces:
        name_tokens = set(surface.name.casefold().replace("-", "_").split("_"))
        explicit_match = surface.name.casefold() in intent or bool(tokens & name_tokens)
        if explicit_match or surface.consumer_risk == "high" or surface.name == "source_coverage_summary":
            selected.append(surface)
    return selected


def is_regrounding_intent(intent_text: str) -> bool:
    return _is_regrounding_intent(intent_text.casefold())


def _is_regrounding_intent(intent: str) -> bool:
    normalized = intent.replace("_", "-")
    return any(token in intent or token in normalized for token in REGROUNDING_INTENT_TOKENS)


def _next_actions(
    *,
    surface: StatsSummarySurface,
    coverage: StatsSourceCoverageSummary,
    reason_codes: list[str],
) -> list[StatsRegroundingAction]:
    actions = [
        StatsRegroundingAction(
            action_ref=f"stats-profile:{surface.name}",
            owner_repo="aoa-stats",
            target_ref="aoa-stats.summary_surface_catalog.min",
            action_kind="inspect_surface_profile",
            reason="Read the stats surface profile before relying on the derived summary.",
        )
    ]
    if any(code.startswith("coverage_") for code in reason_codes):
        actions.append(
            StatsRegroundingAction(
                action_ref="stats-coverage:active-feed",
                owner_repo="aoa-stats",
                target_ref="aoa-stats.source_coverage_summary.min",
                action_kind="inspect_source_coverage",
                reason="Inspect the active stats feed coverage before using the summary as a decision input.",
            )
        )
    for index, target in enumerate(surface.owner_truth_inputs, start=1):
        actions.append(
            StatsRegroundingAction(
                action_ref=f"owner-truth:{surface.name}:{index}",
                owner_repo=_infer_owner_repo(target),
                target_ref=target,
                action_kind="inspect_owner_truth",
                reason="Owner-local truth remains stronger than the derived stats summary.",
            )
        )
    return actions


def _infer_owner_repo(target: str) -> str | None:
    for owner in (
        "Agents-of-Abyss",
        "Tree-of-Sophia",
        "8Dionysus",
        "Dionysus",
        "abyss-stack",
        "aoa-techniques",
        "aoa-skills",
        "aoa-evals",
        "aoa-memo",
        "aoa-playbooks",
        "aoa-agents",
        "aoa-sdk",
        "aoa-routing",
        "aoa-stats",
        "aoa-kag",
    ):
        if owner in target:
            return owner
    return None


def _raise_decision(
    current: Literal["clear", "reground_recommended", "reground_required"],
    candidate: Literal["clear", "reground_recommended", "reground_required"],
) -> Literal["clear", "reground_recommended", "reground_required"]:
    rank = {"clear": 0, "reground_recommended": 1, "reground_required": 2}
    return candidate if rank[candidate] > rank[current] else current


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result
