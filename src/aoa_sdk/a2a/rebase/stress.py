from __future__ import annotations

from typing import Literal

from .models import EvidenceRef, StressBundle, StressPosture, StressSignal
from .utils import unique_preserve_order


SOURCE_PRIORITY = {
    "owner_receipt": 0,
    "runtime_receipt": 0,
    "eval": 1,
    "stats": 2,
    "route_hint": 3,
    "memo": 4,
}

SEVERITY_ORDER = {"low": 1, "medium": 2, "high": 3, "critical": 4}
POSTURE_RESTRICTIVENESS = {
    "degrade_preferred": 1,
    "route_around_unhealthy_surface": 2,
    "reground_first": 3,
    "human_review_first": 4,
    "stop_before_mutation": 5,
}


def default_blocked_actions(posture: StressPosture | None) -> list[str]:
    if posture is None:
        return []
    mapping = {
        "degrade_preferred": ["scope_widening"],
        "route_around_unhealthy_surface": ["unsafe_surface_reuse"],
        "reground_first": ["unreviewed_resume"],
        "human_review_first": ["auto_activation", "unreviewed_mutation"],
        "stop_before_mutation": ["mutation", "auto_activation"],
    }
    return mapping[posture]


def merge_stress_signals(signals: list[StressSignal]) -> StressBundle:
    if not signals:
        return StressBundle(
            selected_posture=None,
            dominant_source_family=None,
            suppression="disabled",
        )

    ordered = sorted(
        signals,
        key=lambda item: (
            SOURCE_PRIORITY[item.source_family],
            -SEVERITY_ORDER[item.severity],
            -POSTURE_RESTRICTIVENESS[item.posture],
        ),
    )
    primary = ordered[0]

    suppression: Literal["active", "low_evidence", "disabled"] = "active"
    if len(ordered) == 1 and SOURCE_PRIORITY[primary.source_family] >= 2:
        suppression = "low_evidence"

    blocked_actions = unique_preserve_order(
        list(primary.blocked_actions) + default_blocked_actions(primary.posture)
    )

    evidence_refs: list[EvidenceRef] = []
    for signal in ordered:
        evidence_refs.extend(signal.evidence_refs)

    reentry_conditions: list[str] = []
    for signal in ordered:
        reentry_conditions.extend(signal.reentry_conditions)

    return StressBundle(
        selected_posture=primary.posture,
        dominant_source_family=primary.source_family,
        suppression=suppression,
        blocked_actions=blocked_actions,
        evidence_refs=unique_preserve_order(evidence_refs),
        reentry_conditions=unique_preserve_order(reentry_conditions),
        considered_sources=[signal.source_family for signal in ordered],
    )
