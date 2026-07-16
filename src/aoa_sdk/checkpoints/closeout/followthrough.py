"""Owner-routing hints for reviewed checkpoint closeout evidence."""

from __future__ import annotations

from typing import Literal

from ...models import CheckpointLineageHint, CloseoutOwnerFollowthroughHint


FOLLOWTHROUGH_DECISION_BY_STATUS: dict[
    Literal["early", "reanchor", "thin-evidence", "stable"],
    Literal["land_direct", "reanchor_owner", "prove_first"],
] = {
    "early": "land_direct",
    "reanchor": "reanchor_owner",
    "thin-evidence": "prove_first",
    "stable": "land_direct",
}


def _requested_followthrough_decision_class(
    hint: CheckpointLineageHint,
) -> Literal[
    "land_direct",
    "stage_seed",
    "reanchor_owner",
    "prove_first",
    "merge_into_existing",
    "defer",
    "drop",
]:
    if hint.merged_into:
        return "merge_into_existing"
    return FOLLOWTHROUGH_DECISION_BY_STATUS[hint.status_posture]


def _build_owner_followthrough_map(
    hints: list[CheckpointLineageHint],
) -> list[CloseoutOwnerFollowthroughHint]:
    return [
        CloseoutOwnerFollowthroughHint(
            cluster_ref=hint.cluster_ref,
            owner_hypothesis=hint.owner_hypothesis,
            owner_shape=hint.owner_shape,
            nearest_wrong_target=hint.nearest_wrong_target,
            status_posture=hint.status_posture,
            owner_ref=f"repo:{hint.owner_hypothesis}",
            requested_next_decision_class=_requested_followthrough_decision_class(hint),
            evidence_refs=list(hint.evidence_refs),
        )
        for hint in hints
    ]
