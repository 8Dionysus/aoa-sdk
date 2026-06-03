"""Followthrough decision logic for checkpoint reviewed closeout."""

from __future__ import annotations

from typing import Literal

from ...models import (
    CheckpointLineageHint,
    CloseoutFollowthroughDecision,
    CloseoutOwnerFollowthroughHint,
    ProgressionAxisSignal,
    SessionCheckpointCluster,
)

FollowthroughSkillName = Literal[
    "aoa-session-route-forks",
    "aoa-session-self-diagnose",
    "aoa-session-self-repair",
    "aoa-session-progression-lift",
    "aoa-automation-opportunity-scan",
    "aoa-quest-harvest",
]
FollowthroughReasonCode = Literal[
    "multiple_plausible_next_moves",
    "repeated_friction",
    "blocked_automation_readiness",
    "reviewed_diagnosis_present",
    "smallest_repair_clear",
    "explicit_axis_movement",
    "no_repair_needed",
    "repeated_manual_route",
    "stable_output_shape",
    "checkpoint_sensitive",
    "reviewed_quest_unit",
    "promotion_pressure",
]
ApprovalPosture = Literal["not_required", "review_required", "approval_required"]
FOLLOWTHROUGH_DECISION_BY_STATUS: dict[
    Literal["early", "reanchor", "thin-evidence", "stable"],
    Literal["land_direct", "reanchor_owner", "prove_first"],
] = {
    "early": "land_direct",
    "reanchor": "reanchor_owner",
    "thin-evidence": "prove_first",
    "stable": "land_direct",
}
OWNER_STATUS_SURFACE_BY_REPO = {
    "aoa-agents": "aoa-agents:reviewed_owner_landing_bundle",
    "aoa-evals": "aoa-evals:reviewed_owner_landing_bundle",
    "aoa-memo": "aoa-memo:reviewed_owner_landing_bundle",
    "aoa-playbooks": "aoa-playbooks:reviewed_owner_landing_bundle",
    "aoa-skills": "aoa-skills:reviewed_owner_landing_bundle",
    "aoa-techniques": "aoa-techniques:reviewed_owner_landing_bundle",
}
KERNEL_SIGNAL_SKILLS: tuple[FollowthroughSkillName, ...] = (
    "aoa-session-route-forks",
    "aoa-session-self-diagnose",
    "aoa-session-self-repair",
    "aoa-session-progression-lift",
    "aoa-automation-opportunity-scan",
    "aoa-quest-harvest",
)


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
            recommended_owner_status_surface=OWNER_STATUS_SURFACE_BY_REPO.get(
                hint.owner_hypothesis,
                f"{hint.owner_hypothesis}:reviewed_owner_landing_bundle",
            ),
            requested_next_decision_class=_requested_followthrough_decision_class(hint),
            evidence_refs=list(hint.evidence_refs),
        )
        for hint in hints
    ]


def _cluster_text(cluster: SessionCheckpointCluster) -> str:
    return " ".join(
        [
            cluster.candidate_kind,
            cluster.owner_hint,
            cluster.display_name,
            cluster.source_surface_ref,
            cluster.defer_reason or "",
            *cluster.blocked_by,
            *cluster.promote_if,
            *cluster.next_owner_moves,
            *(cluster.evidence_refs or []),
            cluster.lineage_hint.owner_shape if cluster.lineage_hint is not None else "",
            cluster.lineage_hint.nearest_wrong_target if cluster.lineage_hint and cluster.lineage_hint.nearest_wrong_target else "",
        ]
    ).lower()


def _is_route_cluster(cluster: SessionCheckpointCluster) -> bool:
    cluster_text = _cluster_text(cluster)
    return (
        cluster.candidate_kind == "route"
        or cluster.owner_hint == "aoa-playbooks"
        or "playbook_registry" in cluster_text
        or "playbook" in cluster_text
    )


def _is_repair_cluster(cluster: SessionCheckpointCluster) -> bool:
    cluster_text = _cluster_text(cluster)
    return "repair" in cluster_text


def _has_blocked_signal(cluster: SessionCheckpointCluster) -> bool:
    return bool(
        cluster.blocked_by
        or cluster.defer_reason
        or (cluster.lineage_hint is not None and cluster.lineage_hint.status_posture == "thin-evidence")
    )


def _has_upgrade_pressure(cluster: SessionCheckpointCluster) -> bool:
    return "upgrade" in cluster.session_end_targets and bool(cluster.promote_if)


def _primary_lineage_cluster(clusters: list[SessionCheckpointCluster]) -> SessionCheckpointCluster:
    for cluster in clusters:
        if cluster.lineage_hint is not None and cluster.candidate_kind != "route":
            return cluster
    return clusters[0]


def _closeout_followthrough_alternatives(
    *,
    clusters: list[SessionCheckpointCluster],
    has_progression_signal: bool,
    recommended_next_skill: FollowthroughSkillName,
) -> list[FollowthroughSkillName]:
    candidates: list[FollowthroughSkillName] = []
    if len(clusters) > 1 or len({cluster.owner_hint for cluster in clusters}) > 1:
        candidates.append("aoa-session-route-forks")
    if any(_has_blocked_signal(cluster) for cluster in clusters):
        candidates.append("aoa-session-self-diagnose")
    if any(_is_repair_cluster(cluster) for cluster in clusters):
        candidates.append("aoa-session-self-repair")
    if has_progression_signal:
        candidates.append("aoa-session-progression-lift")
    if any(_is_route_cluster(cluster) for cluster in clusters):
        candidates.append("aoa-automation-opportunity-scan")
    if any(_has_upgrade_pressure(cluster) for cluster in clusters):
        candidates.append("aoa-quest-harvest")
    alternatives: list[FollowthroughSkillName] = []
    seen: set[FollowthroughSkillName] = set()
    for skill in candidates:
        if skill == recommended_next_skill or skill in seen:
            continue
        alternatives.append(skill)
        seen.add(skill)
    return alternatives[:2]


def _approval_posture_for_next_skill(
    skill_name: FollowthroughSkillName,
) -> ApprovalPosture:
    if skill_name == "aoa-session-self-repair":
        return "approval_required"
    if skill_name in {"aoa-session-route-forks", "aoa-automation-opportunity-scan", "aoa-quest-harvest"}:
        return "review_required"
    return "not_required"


def _build_closeout_followthrough_decision(
    *,
    session_ref: str,
    reviewed_closeout_context_ref: str,
    clusters: list[SessionCheckpointCluster],
    progression_axis_signals: list[ProgressionAxisSignal],
) -> CloseoutFollowthroughDecision | None:
    lineage_clusters = [cluster for cluster in clusters if cluster.lineage_hint is not None]
    if not lineage_clusters:
        return None

    selected_cluster: SessionCheckpointCluster
    recommended_next_skill: FollowthroughSkillName
    reason_codes: list[FollowthroughReasonCode]
    primary_cluster = _primary_lineage_cluster(lineage_clusters)
    route_cluster = next((cluster for cluster in lineage_clusters if _is_route_cluster(cluster)), None)
    repair_cluster = next((cluster for cluster in lineage_clusters if _is_repair_cluster(cluster)), None)
    blocked_cluster = next((cluster for cluster in lineage_clusters if _has_blocked_signal(cluster)), None)
    upgrade_cluster = next((cluster for cluster in lineage_clusters if _has_upgrade_pressure(cluster)), None)
    has_progression_signal = bool(
        any(signal.movement == "advance" for signal in progression_axis_signals)
        or any(signal.movement == "advance" for cluster in lineage_clusters for signal in cluster.progression_axis_signals)
        or any(
            value > 0
            for cluster in lineage_clusters
            for value in (cluster.lineage_hint.axis_pressure.values() if cluster.lineage_hint is not None else [])
        )
    )
    if route_cluster is not None:
        selected_cluster = route_cluster
        recommended_next_skill = "aoa-automation-opportunity-scan"
        reason_codes = ["repeated_manual_route", "stable_output_shape", "checkpoint_sensitive"]
    elif repair_cluster is not None:
        selected_cluster = repair_cluster
        recommended_next_skill = "aoa-session-self-repair"
        reason_codes = ["reviewed_diagnosis_present", "smallest_repair_clear", "checkpoint_sensitive"]
    elif blocked_cluster is not None:
        selected_cluster = blocked_cluster
        recommended_next_skill = "aoa-session-self-diagnose"
        reason_codes = ["repeated_friction", "blocked_automation_readiness", "checkpoint_sensitive"]
    elif has_progression_signal:
        selected_cluster = primary_cluster
        recommended_next_skill = "aoa-session-progression-lift"
        reason_codes = ["explicit_axis_movement", "no_repair_needed", "checkpoint_sensitive"]
    elif upgrade_cluster is not None:
        selected_cluster = upgrade_cluster
        recommended_next_skill = "aoa-quest-harvest"
        reason_codes = ["reviewed_quest_unit", "promotion_pressure", "checkpoint_sensitive"]
    else:
        selected_cluster = primary_cluster
        recommended_next_skill = "aoa-session-route-forks"
        reason_codes = ["multiple_plausible_next_moves", "checkpoint_sensitive"]

    selected_hint = selected_cluster.lineage_hint
    assert selected_hint is not None
    approval_posture = _approval_posture_for_next_skill(recommended_next_skill)
    defer_allowed = bool(
        selected_cluster.blocked_by
        or selected_cluster.defer_reason
        or selected_hint.status_posture != "stable"
        or approval_posture != "not_required"
    )
    return CloseoutFollowthroughDecision(
        session_ref=session_ref,
        reviewed_closeout_context_ref=reviewed_closeout_context_ref,
        cluster_ref=selected_hint.cluster_ref,
        recommended_next_skill=recommended_next_skill,
        also_considered=_closeout_followthrough_alternatives(
            clusters=lineage_clusters,
            has_progression_signal=has_progression_signal,
            recommended_next_skill=recommended_next_skill,
        ),
        reason_codes=reason_codes,
        checkpoint_required=selected_cluster.checkpoint_hits > 0,
        approval_posture=approval_posture,
        defer_allowed=defer_allowed,
        owner_hypothesis=selected_hint.owner_hypothesis,
        nearest_wrong_target=selected_hint.nearest_wrong_target,
        status_posture=selected_hint.status_posture,
    )
