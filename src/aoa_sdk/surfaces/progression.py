from __future__ import annotations

from typing import cast

from ..models import ProgressionAxisSignal, SurfaceOpportunityItem
from .common import (
    ExplicitGrowthCheckpointKind,
    ProgressionAxis,
    ProgressionMovement,
    slugify,
)


AXIS_PRESSURE_BY_MOVEMENT = {
    "advance": 2,
    "hold": 1,
    "reanchor": -1,
    "downgrade": -2,
}


def axis_pressure_from_signals(signals: list[ProgressionAxisSignal]) -> dict[str, int]:
    return {
        signal.axis: AXIS_PRESSURE_BY_MOVEMENT.get(signal.movement, 0)
        for signal in signals
    }


def progression_axis_signals_for_explicit_growth(
    *,
    candidate_id: str,
    checkpoint_kind: ExplicitGrowthCheckpointKind,
    blocked_by: list[str],
    evidence_refs: list[str],
) -> list[ProgressionAxisSignal]:
    templates: list[tuple[str, str, str]] = [
        (
            "execution_reliability",
            "advance",
            "bounded mutation evidence suggests the session improved execution reliability, pending reviewed closeout",
        ),
        (
            "change_legibility",
            "advance",
            "the explicit checkpoint seam makes the change easier to narrate and verify later",
        ),
    ]
    if checkpoint_kind == "verify_green":
        templates.append(
            (
                "proof_discipline",
                "advance",
                "verify-green evidence strengthens proof discipline for the bounded mutation seam",
            )
        )
    if checkpoint_kind == "pr_opened":
        templates.append(
            (
                "review_sharpness",
                "advance",
                "opened-PR evidence makes the public review seam explicit for later closeout",
            )
        )
    if checkpoint_kind == "pr_merged":
        templates.extend(
            [
                (
                    "proof_discipline",
                    "advance",
                    "merged-PR evidence strengthens the proof chain for the bounded mutation seam",
                ),
                (
                    "boundary_integrity",
                    "advance",
                    "merged public-share evidence confirms the owner boundary reached a reviewed integration point",
                ),
            ]
        )
    if checkpoint_kind == "owner_followthrough":
        templates.extend(
            [
                (
                    "provenance_hygiene",
                    "advance",
                    "owner follow-through keeps the handoff provenance explicit for reviewed closeout",
                ),
                (
                    "boundary_integrity",
                    "advance",
                    "owner follow-through evidence confirms the next owner surface was not guessed silently",
                ),
            ]
        )
    signals: list[ProgressionAxisSignal] = []
    for axis, movement, why in templates:
        signals.append(
            ProgressionAxisSignal(
                axis=cast(ProgressionAxis, axis),
                movement=cast(
                    ProgressionMovement,
                    adjust_progression_movement(movement=movement, blocked_by=blocked_by),
                ),
                why=why,
                evidence_refs=list(evidence_refs),
                candidate_ids=[candidate_id],
            )
        )
    return signals


def progression_axis_signals_for_item(
    item: SurfaceOpportunityItem,
    *,
    candidate_kind: str,
    blocked_by: list[str],
    evidence_refs: list[str],
) -> list[ProgressionAxisSignal]:
    templates: list[tuple[str, str, str]]
    if candidate_kind == "route":
        templates = [
            (
                "change_legibility",
                "advance",
                "recurring-route evidence makes this session easier to hand off and review honestly",
            ),
            (
                "deep_readiness",
                "advance",
                "repeated route evidence hints that the route may be ready for a stronger reusable shape later",
            ),
        ]
    elif candidate_kind == "pattern":
        templates = [
            (
                "deep_readiness",
                "advance",
                "pattern-shaped evidence suggests the route is approaching reusable technique form",
            ),
            (
                "review_sharpness",
                "advance",
                "named pattern evidence sharpens later reviewed interpretation",
            ),
        ]
    elif candidate_kind == "proof":
        templates = [
            (
                "proof_discipline",
                "advance",
                "proof-shaped evidence strengthens the session's reviewed basis",
            ),
            (
                "review_sharpness",
                "advance",
                "explicit proof artifacts sharpen later closeout judgment",
            ),
        ]
    elif candidate_kind == "recall":
        templates = [
            (
                "provenance_hygiene",
                "advance",
                "recall surfaces preserve route memory and attribution for later review",
            ),
            (
                "change_legibility",
                "advance",
                "memo-shaped recall makes the route easier to narrate without replaying raw history",
            ),
        ]
    elif candidate_kind == "role":
        templates = [
            (
                "boundary_integrity",
                "hold",
                "role-posture evidence exists, but owner boundaries should stay explicit until reviewed closeout",
            ),
            (
                "deep_readiness",
                "advance",
                "role evidence may reflect deeper readiness once it is reviewed in owner context",
            ),
        ]
    elif candidate_kind == "risk":
        templates = [
            (
                "boundary_integrity",
                "reanchor",
                "risk-gated evidence says progression must stay bounded and reviewed",
            ),
            (
                "proof_discipline",
                "hold",
                "risk-shaped signals should hold until reviewed proof confirms the same concern",
            ),
        ]
    else:
        templates = [
            (
                "change_legibility",
                "hold",
                "checkpoint evidence exists, but the progression claim should stay provisional until reviewed closeout",
            )
        ]
    signals: list[ProgressionAxisSignal] = []
    for axis, movement, why in templates:
        signals.append(
            ProgressionAxisSignal(
                axis=cast(ProgressionAxis, axis),
                movement=cast(
                    ProgressionMovement,
                    adjust_progression_movement(movement=movement, blocked_by=blocked_by),
                ),
                why=why,
                evidence_refs=list(evidence_refs),
                candidate_ids=[f"candidate:{candidate_kind}:{slugify(item.surface_ref)}"],
            )
        )
    return signals


def adjust_progression_movement(
    *,
    movement: str,
    blocked_by: list[str],
) -> str:
    if movement in {"reanchor", "downgrade"}:
        return movement
    if "owner-ambiguity" in blocked_by or "thin-evidence" in blocked_by or "requires-reviewed-route" in blocked_by:
        return "hold"
    return movement
