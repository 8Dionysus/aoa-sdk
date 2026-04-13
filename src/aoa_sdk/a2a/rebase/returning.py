from __future__ import annotations

from .models import ReturnPlan, ReturnReentryMode, RemoteTaskResult, SummonDecision


TERMINAL_FAILURE_STATES = {
    "failed",
    "error",
    "canceled",
    "cancelled",
    "timed_out",
    "timeout",
    "stalled",
}


def _select_reentry_mode(
    decision: SummonDecision,
    checkpoint_note_ref: str | None,
) -> ReturnReentryMode:
    if checkpoint_note_ref:
        return "checkpoint_relaunch"
    if decision.requested_posture == "human_review_first":
        return "review_gate"
    if decision.requested_posture == "stop_before_mutation":
        return "rollback_gate"
    return "router_reentry"


def _select_next_hop(reentry_mode: ReturnReentryMode) -> str:
    mapping = {
        "checkpoint_relaunch": "aoa-checkpoint-closeout-bridge",
        "review_gate": "review_gate",
        "rollback_gate": "rollback_marker",
        "router_reentry": "aoa-routing/generated/return_navigation_hints.min.json",
        "same_phase": "same_phase",
        "previous_phase": "previous_phase",
        "safe_stop": "safe_stop",
    }
    return mapping[reentry_mode]


def build_return_plan(
    remote_task: RemoteTaskResult,
    decision: SummonDecision,
    *,
    anchor_artifact: str = "bounded_plan",
    checkpoint_note_ref: str | None = None,
    codex_trace_ref: str | None = None,
    force: bool = False,
) -> ReturnPlan | None:
    reasons: list[str] = []
    if remote_task.state.lower() in TERMINAL_FAILURE_STATES:
        reasons.append("remote_terminal_failure")
    if decision.requested_posture in {
        "reground_first",
        "human_review_first",
        "stop_before_mutation",
    }:
        reasons.append(f"stress:{decision.requested_posture}")
    if not reasons and not force:
        return None

    reentry_mode = _select_reentry_mode(decision, checkpoint_note_ref)
    next_hop = _select_next_hop(reentry_mode)

    if reentry_mode == "checkpoint_relaunch":
        note = "Remote child lost shape or ended in terminal state. Re-enter through checkpoint relaunch with the reviewed artifact primary and checkpoint hints provisional."
    elif reentry_mode == "review_gate":
        note = "Remote child requires review-gated re-entry before more change work."
    elif reentry_mode == "rollback_gate":
        note = "Remote child should return to rollback or stop posture before more mutation."
    else:
        note = "Remote child should reground through the bounded return-navigation surface before continuing."

    return ReturnPlan(
        anchor_artifact=anchor_artifact,
        reentry_mode=reentry_mode,
        next_hop=next_hop,
        reentry_note=note,
        reason_codes=reasons,
        checkpoint_note_ref=checkpoint_note_ref,
        codex_trace_ref=codex_trace_ref,
        navigation_target="aoa-routing/generated/return_navigation_hints.min.json",
    )


def build_transition_decision_payload(return_plan: ReturnPlan) -> dict:
    return {
        "artifact_kind": "transition_decision",
        "decision": "return",
        "next_hop": return_plan.next_hop,
        "anchor_artifact": return_plan.anchor_artifact,
        "reentry_note": return_plan.reentry_note,
        "reason_codes": list(return_plan.reason_codes),
        "checkpoint_note_ref": return_plan.checkpoint_note_ref,
        "codex_trace_ref": return_plan.codex_trace_ref,
    }
