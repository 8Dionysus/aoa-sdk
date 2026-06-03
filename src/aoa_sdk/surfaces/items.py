from __future__ import annotations

from ..models import (
    SkillDetectionReport,
    SurfaceOpportunityExecutionHint,
    SurfaceOpportunityItem,
    SurfaceOpportunityReference,
)
from .common import SIGNAL_ORDER, TOKEN_RE, SurfacePhase, SurfaceSignal, dedupe_refs
from .heuristics import EXPLICIT_LAYER_RULES_BY_TOKEN, HEURISTIC_RULES


STATE_RANK = {
    "activated": 4,
    "manual-equivalent": 3,
    "candidate-now": 2,
    "candidate-later": 1,
}
CONFIDENCE_RANK = {"high": 3, "medium": 2, "low": 1}


def derive_surface_items(
    *,
    skill_report: SkillDetectionReport,
    surface_phase: SurfacePhase,
    intent_text: str,
    active_skill_names: list[str],
    closeout_signal: bool,
) -> list[SurfaceOpportunityItem]:
    items: list[SurfaceOpportunityItem] = []
    items.extend(
        derive_skill_surface_items(
            skill_report=skill_report,
            surface_phase=surface_phase,
            closeout_signal=closeout_signal,
        )
    )
    items.extend(
        derive_heuristic_items(
            intent_text=intent_text,
            surface_phase=surface_phase,
            active_skill_names=active_skill_names,
            closeout_signal=closeout_signal,
        )
    )
    return dedupe_surface_items(items)


def derive_skill_surface_items(
    *,
    skill_report: SkillDetectionReport,
    surface_phase: SurfacePhase,
    closeout_signal: bool,
) -> list[SurfaceOpportunityItem]:
    items: list[SurfaceOpportunityItem] = []
    for item in skill_report.activate_now:
        signals: list[SurfaceSignal] = ["router-match"]
        if closeout_signal:
            signals.append("closeout-chain")
        items.append(
            SurfaceOpportunityItem(
                surface_ref=f"aoa-skills:{item.skill_name}",
                display_name=display_name(item.skill_name),
                object_kind="skill",
                owner_repo="aoa-skills",
                state="activated",
                phase_detected=surface_phase,
                reason=item.reason,
                signals=ordered_signals(signals),
                confidence="high",
                execution=SurfaceOpportunityExecutionHint(
                    lane="skill-dispatch",
                    executable_now=True,
                    requires_confirmation=False,
                    existing_command="aoa skills dispatch",
                    existing_surface=f".agents/skills/{item.skill_name}/SKILL.md",
                    manual_equivalence_allowed=False,
                    manual_equivalence_note=None,
                    host_availability_status=item.host_availability.status,
                ),
                related_skill_names=[],
                closeout_family_candidates=["aoa-session-donor-harvest"],
                promotion_hint=None,
                family_entry_refs=default_family_entry_refs(
                    owner_repo="aoa-skills",
                    surface_ref=None,
                    inspect_surface=f".agents/skills/{item.skill_name}/SKILL.md",
                ),
            )
        )

    manual_equivalence_items = [*skill_report.must_confirm, *skill_report.suggest_next]
    for item in manual_equivalence_items:
        if item.host_availability.status != "router-only" or not item.host_availability.manual_equivalence_allowed:
            continue
        manual_equivalence_signals: list[SurfaceSignal] = ["router-match"]
        if item in skill_report.must_confirm:
            manual_equivalence_signals.append("risk-gate")
        if closeout_signal:
            manual_equivalence_signals.append("closeout-chain")
        items.append(
            SurfaceOpportunityItem(
                surface_ref=f"aoa-skills:{item.skill_name}",
                display_name=display_name(item.skill_name),
                object_kind="skill",
                owner_repo="aoa-skills",
                state="manual-equivalent",
                phase_detected=surface_phase,
                reason=item.reason,
                signals=ordered_signals(manual_equivalence_signals),
                confidence="high" if item in skill_report.must_confirm else "medium",
                execution=SurfaceOpportunityExecutionHint(
                    lane="manual-equivalence",
                    executable_now=False,
                    requires_confirmation=item in skill_report.must_confirm,
                    existing_command=(
                        "aoa skills guard"
                        if surface_phase == "pre-mutation"
                        else "aoa skills detect --phase checkpoint"
                        if surface_phase == "checkpoint"
                        else "aoa skills detect"
                    ),
                    existing_surface=None,
                    manual_equivalence_allowed=True,
                    manual_equivalence_note="keep the distinction visible: the same discipline was followed manually, not claimed as a real activation",
                    host_availability_status=item.host_availability.status,
                ),
                related_skill_names=related_skill_names(skill_report, item.skill_name),
                closeout_family_candidates=["aoa-session-donor-harvest"],
                promotion_hint=None,
                family_entry_refs=[],
            )
        )

    return items


def derive_heuristic_items(
    *,
    intent_text: str,
    surface_phase: SurfacePhase,
    active_skill_names: list[str],
    closeout_signal: bool,
) -> list[SurfaceOpportunityItem]:
    items: list[SurfaceOpportunityItem] = []
    tokens = set(TOKEN_RE.findall(intent_text.casefold()))

    for rule in HEURISTIC_RULES:
        if rule.id == "repeated-pattern":
            if not repeated_pattern_detected(tokens=tokens, active_skill_names=active_skill_names, phase=surface_phase):
                continue
        elif not tokens.intersection(rule.tokens):
            continue
        rule_signals: list[SurfaceSignal] = [rule.signal]
        if closeout_signal:
            rule_signals.append("closeout-chain")
        items.append(
            SurfaceOpportunityItem(
                surface_ref=rule.surface_ref,
                display_name=rule.display_name,
                object_kind=rule.object_kind,
                owner_repo=rule.owner_repo,
                state=rule.default_state,
                phase_detected=surface_phase,
                reason=rule.reason_template,
                signals=ordered_signals(rule_signals),
                confidence=rule.confidence,
                execution=SurfaceOpportunityExecutionHint(
                    lane=rule.execution_lane,
                    executable_now=False,
                    requires_confirmation=False,
                    existing_command=None,
                    existing_surface=rule.existing_surface,
                    manual_equivalence_allowed=False,
                    manual_equivalence_note=None,
                    host_availability_status=None,
                ),
                related_skill_names=[],
                closeout_family_candidates=list(rule.closeout_family_candidates),
                promotion_hint=rule.promotion_hint,
                family_entry_refs=default_family_entry_refs(
                    owner_repo=rule.owner_repo,
                    surface_ref=rule.surface_ref,
                    inspect_surface=rule.existing_surface,
                ),
            )
        )

    for token in sorted(tokens):
        explicit_rule = EXPLICIT_LAYER_RULES_BY_TOKEN.get(token)
        if explicit_rule is None:
            continue
        explicit_signals: list[SurfaceSignal] = ["explicit-request"]
        if closeout_signal:
            explicit_signals.append("closeout-chain")
        items.append(
            SurfaceOpportunityItem(
                surface_ref=explicit_rule.surface_ref,
                display_name=explicit_rule.display_name,
                object_kind=explicit_rule.object_kind,
                owner_repo=explicit_rule.owner_repo,
                state="candidate-now",
                phase_detected=surface_phase,
                reason=f"intent names the {explicit_rule.owner_repo} layer directly; prefer owner-layer-aware routing over silent guessing",
                signals=ordered_signals(explicit_signals),
                confidence="high",
                execution=SurfaceOpportunityExecutionHint(
                    lane="inspect-expand-use",
                    executable_now=False,
                    requires_confirmation=False,
                    existing_command=None,
                    existing_surface=explicit_rule.existing_surface,
                    manual_equivalence_allowed=False,
                    manual_equivalence_note=None,
                    host_availability_status=None,
                ),
                related_skill_names=[],
                closeout_family_candidates=[],
                promotion_hint=None,
                family_entry_refs=default_family_entry_refs(
                    owner_repo=explicit_rule.owner_repo,
                    surface_ref=None if explicit_rule.surface_ref.startswith("aoa-skills:") else explicit_rule.surface_ref,
                    inspect_surface=explicit_rule.existing_surface,
                ),
            )
        )

    return items


def dedupe_surface_items(items: list[SurfaceOpportunityItem]) -> list[SurfaceOpportunityItem]:
    deduped: dict[str, SurfaceOpportunityItem] = {}
    order: list[str] = []
    for item in items:
        existing = deduped.get(item.surface_ref)
        if existing is None:
            deduped[item.surface_ref] = item
            order.append(item.surface_ref)
            continue
        deduped[item.surface_ref] = merge_surface_items(existing, item)
    return [deduped[key] for key in order]


def merge_surface_items(left: SurfaceOpportunityItem, right: SurfaceOpportunityItem) -> SurfaceOpportunityItem:
    chosen = left
    if STATE_RANK[right.state] > STATE_RANK[left.state]:
        chosen = right
    elif STATE_RANK[right.state] == STATE_RANK[left.state] and CONFIDENCE_RANK[right.confidence] > CONFIDENCE_RANK[left.confidence]:
        chosen = right

    merged_reason = left.reason if left.reason == right.reason else f"{left.reason}; {right.reason}"
    chosen_execution = chosen.execution
    other_execution = right.execution if chosen is left else left.execution
    if chosen_execution.existing_surface is None and other_execution.existing_surface is not None:
        chosen_execution = chosen_execution.model_copy(update={"existing_surface": other_execution.existing_surface})
    if chosen_execution.existing_command is None and other_execution.existing_command is not None:
        chosen_execution = chosen_execution.model_copy(update={"existing_command": other_execution.existing_command})

    return chosen.model_copy(
        update={
            "reason": merged_reason,
            "signals": ordered_signals([*left.signals, *right.signals]),
            "related_skill_names": list(dict.fromkeys([*left.related_skill_names, *right.related_skill_names])),
            "closeout_family_candidates": list(
                dict.fromkeys([*left.closeout_family_candidates, *right.closeout_family_candidates])
            ),
            "promotion_hint": left.promotion_hint or right.promotion_hint,
            "execution": chosen_execution,
            "shortlist_hints": list({hint.shortlist_id: hint for hint in [*left.shortlist_hints, *right.shortlist_hints]}.values()),
            "owner_layer_ambiguity_note": left.owner_layer_ambiguity_note or right.owner_layer_ambiguity_note,
            "family_entry_refs": dedupe_refs([*left.family_entry_refs, *right.family_entry_refs]),
            "evidence_refs": dedupe_refs([*left.evidence_refs, *right.evidence_refs]),
        }
    )


def ordered_signals(signals: list[SurfaceSignal]) -> list[SurfaceSignal]:
    unique = list(dict.fromkeys(signal for signal in signals if signal))
    return sorted(unique, key=lambda signal: SIGNAL_ORDER.index(signal) if signal in SIGNAL_ORDER else len(SIGNAL_ORDER))


def display_name(skill_name: str) -> str:
    words = [part for part in skill_name.replace("aoa-", "").split("-") if part]
    return "AoA " + " ".join(word.capitalize() for word in words)


def related_skill_names(skill_report: SkillDetectionReport, skill_name: str) -> list[str]:
    related = [
        item.skill_name
        for item in [*skill_report.must_confirm, *skill_report.suggest_next]
        if item.skill_name != skill_name and item.host_availability.status == "router-only"
    ]
    return list(dict.fromkeys(related))


def default_family_entry_refs(
    *,
    owner_repo: str,
    surface_ref: str | None,
    inspect_surface: str | None,
) -> list[SurfaceOpportunityReference]:
    refs: list[SurfaceOpportunityReference] = []
    if inspect_surface:
        refs.append(
            SurfaceOpportunityReference(
                role="inspect",
                ref=inspect_surface,
                owner_repo=owner_repo,
                note="stable inspect surface",
            )
        )
    if surface_ref:
        refs.append(
            SurfaceOpportunityReference(
                role="family-entry",
                ref=surface_ref,
                owner_repo=owner_repo,
                note="canonical family entry surface",
            )
        )
    return refs


def repeated_pattern_detected(
    *,
    tokens: set[str],
    active_skill_names: list[str],
    phase: SurfacePhase,
) -> bool:
    repeated_tokens = {"repeat", "repeated", "again", "pattern", "recurring"}
    return bool(tokens.intersection(repeated_tokens)) and (phase in {"closeout", "checkpoint"} or bool(active_skill_names))
