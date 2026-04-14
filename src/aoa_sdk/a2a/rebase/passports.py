from __future__ import annotations

from .models import (
    CohortPattern,
    ExecutionSurface,
    ProgressionOverlay,
    QuestPassport,
    SelfAgentCheckpoint,
    SummonDecision,
    SummonIntent,
)
from .models import StressBundle
from .progression import progression_allows
from .stress import default_blocked_actions
from .utils import unique_preserve_order


DIFFICULTY_ORDER = {
    "d0_probe": 0,
    "d1_patch": 1,
    "d2_slice": 2,
    "d3_seam": 3,
    "d4_architecture": 4,
    "d5_doctrine": 5,
}


def recommended_cohort(passport: QuestPassport) -> CohortPattern:
    if passport.self_agent or passport.risk in {"r2_contract", "r3_side_effect"}:
        return "checkpoint_cohort"
    if DIFFICULTY_ORDER[passport.difficulty] >= DIFFICULTY_ORDER["d3_seam"]:
        return "orchestrated_loop"
    if passport.difficulty == "d2_slice":
        return "pair"
    return "solo"


def _has_anchor(passport: QuestPassport, intent: SummonIntent) -> bool:
    return bool(passport.route_anchor or intent.parent_task_id or intent.session_ref)


def _expected_outputs(passport: QuestPassport, intent: SummonIntent) -> list[str]:
    return unique_preserve_order(intent.expected_outputs or passport.expected_artifacts)


def _select_execution_surface(intent: SummonIntent) -> ExecutionSurface:
    return (
        "a2a_remote" if intent.transport_preference == "a2a_remote" else "codex_local"
    )


def assess_summon(
    passport: QuestPassport,
    intent: SummonIntent,
    *,
    stress_bundle: StressBundle | None = None,
    progression: ProgressionOverlay | None = None,
    self_agent_checkpoint: SelfAgentCheckpoint | None = None,
) -> SummonDecision:
    outputs = _expected_outputs(passport, intent)
    anchor_present = _has_anchor(passport, intent)
    cohort: CohortPattern = recommended_cohort(passport)
    execution_surface: ExecutionSurface = _select_execution_surface(intent)
    reasons: list[str] = []
    blocked_actions: list[str] = []

    if not anchor_present:
        reasons.append("missing_parent_anchor")
    if not outputs:
        reasons.append("missing_expected_outputs")

    if intent.require_progression:
        allowed_progression, progression_reasons = progression_allows(
            passport, cohort, progression
        )
        if not allowed_progression:
            reasons.extend(progression_reasons)
            return SummonDecision(
                allowed=False,
                lane="human_gate",
                execution_surface="human_gate",
                cohort_pattern=cohort,
                closeout_required=True,
                progression_required=True,
                requested_posture=stress_bundle.selected_posture
                if stress_bundle
                else None,
                reason_codes=unique_preserve_order(reasons),
                blocked_actions=["delegation"],
                expected_outputs=outputs,
            )

    if passport.self_agent:
        if self_agent_checkpoint is None:
            reasons.append("missing_self_agent_checkpoint")
            return SummonDecision(
                allowed=False,
                lane="human_gate",
                execution_surface="human_gate",
                cohort_pattern=cohort,
                closeout_required=True,
                checkpoint_required=True,
                requested_posture=stress_bundle.selected_posture
                if stress_bundle
                else None,
                reason_codes=unique_preserve_order(reasons),
                blocked_actions=["delegation", "mutation"],
                expected_outputs=outputs,
            )
        if (
            not self_agent_checkpoint.approved
            or not self_agent_checkpoint.rollback_marker
            or not self_agent_checkpoint.health_check
        ):
            reasons.append("incomplete_self_agent_checkpoint")
            return SummonDecision(
                allowed=False,
                lane="human_gate",
                execution_surface="human_gate",
                cohort_pattern=cohort,
                closeout_required=True,
                checkpoint_required=True,
                requested_posture=stress_bundle.selected_posture
                if stress_bundle
                else None,
                reason_codes=unique_preserve_order(reasons),
                blocked_actions=["delegation", "mutation"],
                expected_outputs=outputs,
            )

    if DIFFICULTY_ORDER[passport.difficulty] >= DIFFICULTY_ORDER["d3_seam"]:
        reasons.append("split_required_for_d3_plus")
        return SummonDecision(
            allowed=False,
            lane="split_required",
            execution_surface="split",
            cohort_pattern=cohort,
            require_split=True,
            closeout_required=True,
            requested_posture=stress_bundle.selected_posture if stress_bundle else None,
            reason_codes=unique_preserve_order(reasons),
            blocked_actions=unique_preserve_order(
                blocked_actions + ["direct_child_execution"]
            ),
            expected_outputs=outputs,
        )

    if passport.control_mode == "blocked":
        reasons.append("control_mode_blocked")
        return SummonDecision(
            allowed=False,
            lane="blocked",
            execution_surface="human_gate",
            cohort_pattern=cohort,
            closeout_required=True,
            requested_posture=stress_bundle.selected_posture if stress_bundle else None,
            reason_codes=unique_preserve_order(reasons),
            blocked_actions=unique_preserve_order(blocked_actions + ["delegation"]),
            expected_outputs=outputs,
        )

    if stress_bundle and stress_bundle.selected_posture is not None:
        reasons.append(f"stress:{stress_bundle.selected_posture}")
        blocked_actions.extend(stress_bundle.blocked_actions)
        blocked_actions.extend(default_blocked_actions(stress_bundle.selected_posture))

    high_risk_or_gate = passport.risk in {
        "r2_contract",
        "r3_side_effect",
    } or passport.control_mode in {
        "human_gate",
        "human_codex_copilot",
    }

    narrowed_child_role = intent.desired_role in {"reviewer", "evaluator", "architect"}
    if high_risk_or_gate:
        if anchor_present and outputs and narrowed_child_role:
            reasons.append("review_lane_only")
            lane = (
                "codex_local_reviewed"
                if execution_surface == "codex_local"
                else "remote_reviewed"
            )
            return SummonDecision(
                allowed=True,
                lane=lane,
                execution_surface=execution_surface,
                cohort_pattern=cohort,
                closeout_required=True,
                codex_projection_required=execution_surface == "codex_local",
                requested_posture=stress_bundle.selected_posture
                if stress_bundle
                else None,
                reason_codes=unique_preserve_order(reasons),
                blocked_actions=unique_preserve_order(blocked_actions),
                expected_outputs=outputs,
            )
        reasons.append("human_gate_required")
        return SummonDecision(
            allowed=False,
            lane="human_gate",
            execution_surface="human_gate",
            cohort_pattern=cohort,
            closeout_required=True,
            requested_posture=stress_bundle.selected_posture if stress_bundle else None,
            reason_codes=unique_preserve_order(reasons),
            blocked_actions=unique_preserve_order(blocked_actions),
            expected_outputs=outputs,
        )

    if (
        stress_bundle
        and stress_bundle.selected_posture == "stop_before_mutation"
        and not narrowed_child_role
    ):
        reasons.append("stress_blocks_mutation_lane")
        return SummonDecision(
            allowed=False,
            lane="human_gate",
            execution_surface="human_gate",
            cohort_pattern=cohort,
            closeout_required=True,
            requested_posture=stress_bundle.selected_posture,
            reason_codes=unique_preserve_order(reasons),
            blocked_actions=unique_preserve_order(blocked_actions),
            expected_outputs=outputs,
        )

    allowed = anchor_present and bool(outputs)
    if execution_surface == "codex_local":
        lane = "codex_local_leaf" if allowed else "human_gate"
    else:
        lane = "remote_leaf" if allowed else "human_gate"

    if allowed:
        reasons.append("leaf_allowed")
    else:
        reasons.append("incomplete_request")

    return SummonDecision(
        allowed=allowed,
        lane=lane,
        execution_surface=execution_surface if allowed else "human_gate",
        cohort_pattern=cohort,
        closeout_required=True,
        codex_projection_required=allowed and execution_surface == "codex_local",
        requested_posture=stress_bundle.selected_posture if stress_bundle else None,
        reason_codes=unique_preserve_order(reasons),
        blocked_actions=unique_preserve_order(blocked_actions),
        expected_outputs=outputs,
    )
