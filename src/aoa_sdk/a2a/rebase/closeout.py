from __future__ import annotations

from typing import Any

from .models import (
    CANONICAL_RUNTIME_EVENT_KINDS,
    CheckpointEvidenceHandoffPlan,
    CodexLocalAgentTarget,
    EvidenceRef,
    MemoExportPlan,
    OwnerEvidenceHandoff,
    RemoteTaskResult,
    ReturnPlan,
    StressBundle,
    SummonDecision,
)
from .utils import slugify, to_jsonable, unique_preserve_order, utc_now_z


def build_runtime_return_closeout_receipt(
    remote_task: RemoteTaskResult,
    decision: SummonDecision,
    *,
    session_ref: str,
    reviewed_artifact_path: str | None = None,
    stress_bundle: StressBundle | None = None,
    return_plan: ReturnPlan | None = None,
    checkpoint_handoff_plan: CheckpointEvidenceHandoffPlan | None = None,
    codex_target: CodexLocalAgentTarget | None = None,
    observed_at: str | None = None,
    owner_repo: str = "abyss-stack",
    actor_ref: str = "abyss-stack.runtime-a2a",
) -> dict[str, Any]:
    """Build a candidate runtime receipt without publishing it or claiming a skill run."""

    event_kind = "runtime_return_closeout_receipt"
    if event_kind not in CANONICAL_RUNTIME_EVENT_KINDS:
        raise ValueError(f"unsupported event kind: {event_kind}")

    evidence_refs: list[EvidenceRef] = [
        EvidenceRef(
            kind="remote_task",
            ref=f"a2a:task:{remote_task.task_id}",
            role="child_task",
        )
    ]
    if reviewed_artifact_path:
        evidence_refs.append(
            EvidenceRef(
                kind="reviewed_artifact",
                ref=reviewed_artifact_path,
                role="return_review",
            )
        )
    if stress_bundle:
        evidence_refs.extend(stress_bundle.evidence_refs)
    evidence_refs.extend(
        EvidenceRef(kind="remote_artifact", ref=ref, role="returned_artifact")
        for ref in remote_task.artifact_refs
    )

    payload: dict[str, Any] = {
        "selected_agent_id": remote_task.agent_id,
        "endpoint": remote_task.endpoint,
        "parent_task_id": remote_task.parent_task_id,
        "child_task_id": remote_task.task_id,
        "context_id": remote_task.context_id,
        "terminal_state": remote_task.state,
        "returned_artifacts": list(remote_task.returned_artifacts),
        "decision_lane": decision.lane,
        "execution_surface": decision.execution_surface,
        "cohort_pattern": decision.cohort_pattern,
        "requested_posture": decision.requested_posture,
        "blocked_actions": list(decision.blocked_actions),
        "expected_outputs": list(decision.expected_outputs),
        "capability_execution_claimed": False,
    }
    if return_plan:
        payload.update(
            {
                "return_required": True,
                "return_anchor_artifact": return_plan.anchor_artifact,
                "return_reentry_mode": return_plan.reentry_mode,
                "checkpoint_note_ref": return_plan.checkpoint_note_ref,
                "codex_trace_ref": return_plan.codex_trace_ref,
            }
        )
    if checkpoint_handoff_plan:
        if checkpoint_handoff_plan.checkpoint_note_ref is not None:
            payload["checkpoint_note_ref"] = checkpoint_handoff_plan.checkpoint_note_ref
        if checkpoint_handoff_plan.codex_trace_ref is not None:
            payload["codex_trace_ref"] = checkpoint_handoff_plan.codex_trace_ref
        payload["capability_candidates"] = list(
            checkpoint_handoff_plan.capability_candidates
        )
    if codex_target:
        payload["codex_role"] = codex_target.role
        payload["codex_config_path"] = codex_target.config_path

    return {
        "event_kind": event_kind,
        "event_id": f"runtime-return-closeout::{slugify(remote_task.task_id)}",
        "observed_at": observed_at or utc_now_z(),
        "run_ref": f"run:a2a:{remote_task.task_id}",
        "session_ref": session_ref,
        "actor_ref": actor_ref,
        "object_ref": {
            "repo": owner_repo,
            "kind": "a2a_child_route",
            "id": remote_task.task_id,
        },
        "evidence_refs": [
            to_jsonable(item) for item in unique_preserve_order(evidence_refs)
        ],
        "payload": payload,
    }


def build_owner_evidence_handoff(
    *,
    owner_ref: str,
    candidate_kind: str,
    reason: str,
    evidence_refs: list[str],
    capability_ref: str | None = None,
    review_required: bool = True,
) -> OwnerEvidenceHandoff:
    """Create one explicit owner candidate; do not infer or invoke an owner publisher."""

    if not owner_ref.strip():
        raise ValueError("owner_ref must be non-empty")
    if not candidate_kind.strip():
        raise ValueError("candidate_kind must be non-empty")
    if not reason.strip():
        raise ValueError("reason must be non-empty")
    refs = [ref for ref in unique_preserve_order(evidence_refs) if ref.strip()]
    if not refs:
        raise ValueError("owner evidence handoff requires at least one evidence ref")
    return OwnerEvidenceHandoff(
        owner_ref=owner_ref,
        candidate_kind=candidate_kind,
        reason=reason,
        evidence_refs=refs,
        capability_ref=capability_ref,
        review_required=review_required,
    )


def return_summary_lines(
    remote_task: RemoteTaskResult,
    decision: SummonDecision,
    *,
    stress_bundle: StressBundle | None = None,
    memo_export_plan: MemoExportPlan | None = None,
    return_plan: ReturnPlan | None = None,
    codex_target: CodexLocalAgentTarget | None = None,
) -> list[str]:
    lines = [
        f"selected_agent={remote_task.agent_id}",
        f"endpoint={remote_task.endpoint}",
        f"child_task_id={remote_task.task_id}",
        f"terminal_state={remote_task.state}",
        f"decision_lane={decision.lane}",
        f"execution_surface={decision.execution_surface}",
        f"cohort_pattern={decision.cohort_pattern}",
        f"returned_artifacts={','.join(remote_task.returned_artifacts) if remote_task.returned_artifacts else 'none'}",
    ]
    if codex_target:
        lines.append(f"codex_role={codex_target.role}")
        lines.append(f"codex_config_path={codex_target.config_path}")
    if return_plan:
        lines.append(f"return_anchor={return_plan.anchor_artifact}")
        lines.append(f"return_reentry_mode={return_plan.reentry_mode}")
    if stress_bundle and stress_bundle.selected_posture:
        lines.append(f"stress_posture={stress_bundle.selected_posture}")
    if memo_export_plan:
        lines.append(
            f"memo_writeback_targets={len(memo_export_plan.writeback_targets)}"
        )
        lines.append(f"memo_candidates={len(memo_export_plan.candidate_targets)}")
        lines.append(f"memo_adjuncts={len(memo_export_plan.adjunct_targets)}")
    return lines


def build_reviewed_return_handoff(
    remote_task: RemoteTaskResult,
    decision: SummonDecision,
    *,
    session_ref: str,
    reviewed_artifact_path: str,
    owner_handoffs: list[OwnerEvidenceHandoff],
    audit_refs: list[str] | None = None,
    stress_bundle: StressBundle | None = None,
    memo_export_plan: MemoExportPlan | None = None,
    return_plan: ReturnPlan | None = None,
    checkpoint_handoff_plan: CheckpointEvidenceHandoffPlan | None = None,
    codex_target: CodexLocalAgentTarget | None = None,
) -> dict[str, Any]:
    refs = unique_preserve_order([*(audit_refs or []), reviewed_artifact_path])
    request: dict[str, Any] = {
        "schema_version": 2,
        "request_kind": "a2a_return_evidence_handoff",
        "handoff_id": f"return-handoff-{slugify(remote_task.task_id)}",
        "session_ref": session_ref,
        "reviewed": True,
        "reviewed_artifact_path": reviewed_artifact_path,
        "audit_refs": refs,
        "capability_execution_claimed": False,
        "owner_handoffs": [to_jsonable(item) for item in owner_handoffs],
        "a2a_child": {
            "selected_agent_id": remote_task.agent_id,
            "endpoint": remote_task.endpoint,
            "child_task_id": remote_task.task_id,
            "context_id": remote_task.context_id,
            "terminal_state": remote_task.state,
            "returned_artifacts": list(remote_task.returned_artifacts),
            "expected_outputs": list(decision.expected_outputs),
            "decision_lane": decision.lane,
            "execution_surface": decision.execution_surface,
        },
        "summary_lines": return_summary_lines(
            remote_task,
            decision,
            stress_bundle=stress_bundle,
            memo_export_plan=memo_export_plan,
            return_plan=return_plan,
            codex_target=codex_target,
        ),
    }
    if stress_bundle:
        request["stress_bundle"] = to_jsonable(stress_bundle)
    if memo_export_plan:
        request["memo_export_plan"] = {
            "writeback_targets": len(memo_export_plan.writeback_targets),
            "candidate_targets": len(memo_export_plan.candidate_targets),
            "adjunct_targets": len(memo_export_plan.adjunct_targets),
            "contains_raw_trace": memo_export_plan.contains_raw_trace,
        }
    if return_plan:
        request["return_plan"] = to_jsonable(return_plan)
    if checkpoint_handoff_plan:
        request["checkpoint_handoff_plan"] = to_jsonable(checkpoint_handoff_plan)
    if codex_target:
        request["codex_local_target"] = to_jsonable(codex_target)
    return request
