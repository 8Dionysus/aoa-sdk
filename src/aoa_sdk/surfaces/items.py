from __future__ import annotations

from ..models import (
    SurfaceOpportunityExecutionHint,
    SurfaceOpportunityItem,
    SurfaceOpportunityReference,
)
from .common import SIGNAL_ORDER, TOKEN_RE, SurfacePhase, SurfaceSignal, dedupe_refs
from .heuristics import (
    EXPLICIT_LAYER_RULES,
    EXPLICIT_LAYER_RULES_BY_TOKEN,
    HEURISTIC_RULES,
    HEURISTIC_RULES_BY_ID,
    ExplicitLayerRule,
)


STATE_RANK = {"candidate-now": 2, "candidate-later": 1}
CONFIDENCE_RANK = {"high": 3, "medium": 2, "low": 1}


def derive_surface_items(
    *,
    surface_phase: SurfacePhase,
    intent_text: str,
    closeout_signal: bool,
    requested_owner_layers: list[str] | None = None,
    declared_signals: list[str] | None = None,
) -> list[SurfaceOpportunityItem]:
    return dedupe_surface_items(
        derive_heuristic_items(
            intent_text=intent_text,
            surface_phase=surface_phase,
            closeout_signal=closeout_signal,
            requested_owner_layers=requested_owner_layers,
            declared_signals=declared_signals,
        )
    )


def derive_heuristic_items(
    *,
    intent_text: str,
    surface_phase: SurfacePhase,
    closeout_signal: bool,
    requested_owner_layers: list[str] | None = None,
    declared_signals: list[str] | None = None,
) -> list[SurfaceOpportunityItem]:
    items: list[SurfaceOpportunityItem] = []
    tokens = set(TOKEN_RE.findall(intent_text.casefold()))
    requested = set(requested_owner_layers or [])
    declared = set(declared_signals or [])
    unknown_owners = requested - {rule.owner_repo for rule in EXPLICIT_LAYER_RULES}
    unknown_signals = declared - HEURISTIC_RULES_BY_ID.keys()
    if unknown_owners or unknown_signals:
        raise ValueError(f"unsupported owner layers or declared signals: {sorted(unknown_owners | unknown_signals)}")

    for rule in HEURISTIC_RULES:
        asserted = rule.id in declared
        if rule.id == "repeated-pattern":
            if surface_phase not in {"checkpoint", "closeout"}:
                continue
            if not asserted and not repeated_pattern_detected(tokens=tokens, phase=surface_phase):
                continue
        elif not asserted and not tokens.intersection(rule.tokens):
            continue
        rule_signals: list[SurfaceSignal] = [rule.signal] if asserted else []
        if closeout_signal and asserted:
            rule_signals.append("closeout-chain")
        items.append(
            SurfaceOpportunityItem(
                surface_ref=rule.surface_ref,
                display_name=rule.display_name if asserted else f"{rule.owner_repo} topic hint",
                object_kind=rule.object_kind,
                owner_repo=rule.owner_repo,
                state=rule.default_state if asserted else "candidate-later",
                phase_detected=surface_phase,
                reason=(
                    f"caller declares {rule.signal}; inspect the owner surface"
                    if asserted else
                    "lexical topic match only; no request, recurrence, or proof need is inferred"
                ),
                signals=ordered_signals(rule_signals),
                confidence=rule.confidence if asserted else "low",
                execution=SurfaceOpportunityExecutionHint(
                    lane=rule.execution_lane if asserted else "inspect-expand-use",
                    executable_now=False,
                    requires_confirmation=False,
                    existing_command=None,
                    existing_surface=rule.existing_surface,
                ),
                related_capability_refs=[],
                closeout_capability_candidates=list(
                    rule.closeout_capability_candidates if asserted else ()
                ),
                promotion_hint=rule.promotion_hint if asserted else None,
                family_entry_refs=default_family_entry_refs(
                    owner_repo=rule.owner_repo,
                    surface_ref=rule.surface_ref,
                    inspect_surface=rule.existing_surface,
                ),
            )
        )

    layer_rules: dict[str, ExplicitLayerRule] = {rule.owner_repo: rule for rule in EXPLICIT_LAYER_RULES}
    mentioned = {
        EXPLICIT_LAYER_RULES_BY_TOKEN[token].owner_repo
        for token in tokens if token in EXPLICIT_LAYER_RULES_BY_TOKEN
    }
    for owner in sorted(requested | mentioned):
        explicit_rule = layer_rules[owner]
        asserted = owner in requested
        explicit_signals: list[SurfaceSignal] = ["explicit-request"] if asserted else []
        if closeout_signal and asserted:
            explicit_signals.append("closeout-chain")
        items.append(
            SurfaceOpportunityItem(
                surface_ref=explicit_rule.surface_ref,
                display_name=explicit_rule.display_name if asserted else f"{owner} topic hint",
                object_kind=explicit_rule.object_kind,
                owner_repo=explicit_rule.owner_repo,
                state="candidate-now" if asserted else "candidate-later",
                phase_detected=surface_phase,
                reason=(
                    f"caller explicitly requests the {owner} layer; inspect without runtime activation"
                    if asserted else
                    f"lexical mention of {owner} only; no operator request is inferred"
                ),
                signals=ordered_signals(explicit_signals),
                confidence="high" if asserted else "low",
                execution=SurfaceOpportunityExecutionHint(
                    lane="inspect-expand-use",
                    executable_now=False,
                    requires_confirmation=False,
                    existing_command=None,
                    existing_surface=explicit_rule.existing_surface,
                ),
                related_capability_refs=[],
                closeout_capability_candidates=[],
                promotion_hint=None,
                family_entry_refs=default_family_entry_refs(
                    owner_repo=explicit_rule.owner_repo,
                    surface_ref=(
                        None
                        if explicit_rule.surface_ref.startswith("aoa-skills:")
                        else explicit_rule.surface_ref
                    ),
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
        else:
            deduped[item.surface_ref] = merge_surface_items(existing, item)
    return [deduped[key] for key in order]


def merge_surface_items(
    left: SurfaceOpportunityItem,
    right: SurfaceOpportunityItem,
) -> SurfaceOpportunityItem:
    chosen = left
    if STATE_RANK[right.state] > STATE_RANK[left.state]:
        chosen = right
    elif (
        STATE_RANK[right.state] == STATE_RANK[left.state]
        and CONFIDENCE_RANK[right.confidence] > CONFIDENCE_RANK[left.confidence]
    ):
        chosen = right

    merged_reason = left.reason if left.reason == right.reason else f"{left.reason}; {right.reason}"
    chosen_execution = chosen.execution
    other_execution = right.execution if chosen is left else left.execution
    if chosen_execution.existing_surface is None and other_execution.existing_surface is not None:
        chosen_execution = chosen_execution.model_copy(
            update={"existing_surface": other_execution.existing_surface}
        )
    if chosen_execution.existing_command is None and other_execution.existing_command is not None:
        chosen_execution = chosen_execution.model_copy(
            update={"existing_command": other_execution.existing_command}
        )

    return chosen.model_copy(
        update={
            "reason": merged_reason,
            "signals": ordered_signals([*left.signals, *right.signals]),
            "related_capability_refs": list(
                dict.fromkeys(
                    [*left.related_capability_refs, *right.related_capability_refs]
                )
            ),
            "closeout_capability_candidates": list(
                dict.fromkeys(
                    [
                        *left.closeout_capability_candidates,
                        *right.closeout_capability_candidates,
                    ]
                )
            ),
            "promotion_hint": left.promotion_hint or right.promotion_hint,
            "execution": chosen_execution,
            "shortlist_hints": list(
                {
                    hint.shortlist_id: hint
                    for hint in [*left.shortlist_hints, *right.shortlist_hints]
                }.values()
            ),
            "owner_layer_ambiguity_note": (
                left.owner_layer_ambiguity_note or right.owner_layer_ambiguity_note
            ),
            "family_entry_refs": dedupe_refs(
                [*left.family_entry_refs, *right.family_entry_refs]
            ),
            "evidence_refs": dedupe_refs([*left.evidence_refs, *right.evidence_refs]),
        }
    )


def ordered_signals(signals: list[SurfaceSignal]) -> list[SurfaceSignal]:
    unique = list(dict.fromkeys(signal for signal in signals if signal))
    return sorted(
        unique,
        key=lambda signal: (
            SIGNAL_ORDER.index(signal) if signal in SIGNAL_ORDER else len(SIGNAL_ORDER)
        ),
    )


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


def repeated_pattern_detected(*, tokens: set[str], phase: SurfacePhase) -> bool:
    repeated_tokens = {"repeat", "repeated", "again", "pattern", "recurring"}
    return bool(tokens.intersection(repeated_tokens)) and phase in {"closeout", "checkpoint"}
