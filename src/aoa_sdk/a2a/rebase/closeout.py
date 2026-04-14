from __future__ import annotations

from typing import Any, Iterable

from .models import (
    CANONICAL_STATS_EVENT_KINDS,
    MANIFEST_BATCH_PUBLISHERS,
    CheckpointBridgePlan,
    CloseoutBatchPlan,
    CodexLocalAgentTarget,
    EvidenceRef,
    MemoExportPlan,
    RemoteTaskResult,
    ReturnPlan,
    StressBundle,
    SummonDecision,
)
from .utils import slugify, to_jsonable, unique_preserve_order, utc_now_z


def build_runtime_wave_closeout_receipt(
    remote_task: RemoteTaskResult,
    decision: SummonDecision,
    *,
    session_ref: str,
    reviewed_artifact_path: str | None = None,
    stress_bundle: StressBundle | None = None,
    return_plan: ReturnPlan | None = None,
    checkpoint_bridge_plan: CheckpointBridgePlan | None = None,
    codex_target: CodexLocalAgentTarget | None = None,
    observed_at: str | None = None,
    owner_repo: str = "abyss-stack",
    actor_ref: str = "abyss-stack.runtime-a2a",
) -> dict:
    event_kind = "runtime_wave_closeout_receipt"
    if event_kind not in CANONICAL_STATS_EVENT_KINDS:
        raise ValueError(f"unsupported event kind: {event_kind}")

    evidence_refs: list[EvidenceRef] = [
        EvidenceRef(
            kind="remote_task", ref=f"a2a:task:{remote_task.task_id}", role="child_task"
        )
    ]
    if reviewed_artifact_path:
        evidence_refs.append(
            EvidenceRef(
                kind="reviewed_artifact", ref=reviewed_artifact_path, role="closeout"
            )
        )
    if stress_bundle:
        evidence_refs.extend(stress_bundle.evidence_refs)
    for ref in remote_task.artifact_refs:
        evidence_refs.append(
            EvidenceRef(kind="remote_artifact", ref=ref, role="returned_artifact")
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
    if checkpoint_bridge_plan:
        payload["checkpoint_note_ref"] = checkpoint_bridge_plan.checkpoint_note_ref
        payload["codex_trace_ref"] = checkpoint_bridge_plan.codex_trace_ref
    if codex_target:
        payload["codex_role"] = codex_target.role
        payload["codex_config_path"] = codex_target.config_path

    return {
        "event_kind": event_kind,
        "event_id": f"runtime-wave-closeout::{slugify(remote_task.task_id)}",
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


def plan_owner_publications(
    *,
    runtime_receipt_paths: Iterable[str] | None = None,
    harvest_receipt_paths: Iterable[str] | None = None,
    core_skill_receipt_paths: Iterable[str] | None = None,
    eval_receipt_paths: Iterable[str] | None = None,
    playbook_receipt_paths: Iterable[str] | None = None,
    technique_receipt_paths: Iterable[str] | None = None,
    memo_receipt_paths: Iterable[str] | None = None,
) -> list[CloseoutBatchPlan]:
    plans: list[CloseoutBatchPlan] = []

    def _add(
        publisher: str,
        reason: str,
        receipt_kind: str | None,
        input_paths: Iterable[str] | None,
        required: bool,
    ) -> None:
        paths = [path for path in (input_paths or []) if path]
        if not paths:
            return
        plans.append(
            CloseoutBatchPlan(
                publisher=publisher,
                reason=reason,
                receipt_kind=receipt_kind,
                input_paths=paths,
                required=required,
            )
        )

    _add(
        "abyss-stack.runtime-wave-closeouts",
        "publish canonical runtime closeout receipts under the runtime owner lane",
        "runtime_wave_closeout_receipt",
        runtime_receipt_paths,
        True,
    )
    _add(
        "aoa-skills.session-harvest-family",
        "publish parent-session harvest and progression receipts when present",
        "harvest_packet_receipt",
        harvest_receipt_paths,
        False,
    )
    _add(
        "aoa-skills.core-kernel-applications",
        "publish generic core-skill application receipts when present",
        "core_skill_application_receipt",
        core_skill_receipt_paths,
        False,
    )
    _add(
        "aoa-evals.eval-result",
        "publish eval-backed proof receipts when present",
        "eval_result_receipt",
        eval_receipt_paths,
        False,
    )
    _add(
        "aoa-playbooks.reviewed-run",
        "publish reviewed playbook receipts when present",
        "playbook_review_harvest_receipt",
        playbook_receipt_paths,
        False,
    )
    _add(
        "aoa-techniques.promotion",
        "publish technique promotion receipts when present",
        "technique_promotion_receipt",
        technique_receipt_paths,
        False,
    )
    _add(
        "aoa-memo.writeback",
        "publish reviewed memo writeback receipts when present",
        "memo_writeback_receipt",
        memo_receipt_paths,
        False,
    )
    return plans


def closeout_summary_lines(
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


def build_reviewed_closeout_request(
    remote_task: RemoteTaskResult,
    decision: SummonDecision,
    *,
    session_ref: str,
    reviewed_artifact_path: str,
    publication_plan: list[CloseoutBatchPlan],
    audit_refs: list[str] | None = None,
    stress_bundle: StressBundle | None = None,
    memo_export_plan: MemoExportPlan | None = None,
    return_plan: ReturnPlan | None = None,
    checkpoint_bridge_plan: CheckpointBridgePlan | None = None,
    codex_target: CodexLocalAgentTarget | None = None,
) -> dict:
    refs = list(audit_refs or [])
    if reviewed_artifact_path not in refs:
        refs.append(reviewed_artifact_path)

    manifest_batches = [
        {"publisher": plan.publisher, "input_paths": list(plan.input_paths)}
        for plan in publication_plan
        if plan.publisher in MANIFEST_BATCH_PUBLISHERS and plan.input_paths
    ]

    request = {
        "schema_version": 1,
        "request_kind": "a2a_wave5_closeout_request",
        "closeout_id": f"closeout-{slugify(remote_task.task_id)}",
        "session_ref": session_ref,
        "reviewed": True,
        "reviewed_artifact_path": reviewed_artifact_path,
        "trigger": "reviewed-closeout",
        "audit_refs": refs,
        "batches": manifest_batches,
        "owner_local_publications": [to_jsonable(plan) for plan in publication_plan],
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
        "summary_lines": closeout_summary_lines(
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
    if checkpoint_bridge_plan:
        request["checkpoint_bridge_plan"] = to_jsonable(checkpoint_bridge_plan)
    if codex_target:
        request["codex_local_target"] = to_jsonable(codex_target)
    return request
