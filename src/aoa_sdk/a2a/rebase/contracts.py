from __future__ import annotations

from typing import Any, Iterable

from .models import (
    CheckpointBridgePlan,
    CloseoutBatchPlan,
    CodexLocalAgentTarget,
    MemoExportPlan,
    QuestPassport,
    ReturnPlan,
    SummonDecision,
    SummonIntent,
)
from .utils import to_jsonable, unique_preserve_order


def build_summon_request_payload(
    passport: QuestPassport,
    intent: SummonIntent,
    *,
    expected_outputs: Iterable[str] | None = None,
    progression_overlay_ref: str | None = None,
    self_agent_checkpoint_ref: str | None = None,
    stress_bundle_ref: str | None = None,
    checkpoint_note_ref: str | None = None,
    codex_trace_ref: str | None = None,
    reviewed_artifact_path: str | None = None,
    audit_refs: Iterable[str] | None = None,
) -> dict[str, Any]:
    resolved_outputs = unique_preserve_order(
        list(expected_outputs or intent.expected_outputs or passport.expected_artifacts)
    )
    resolved_reviewed_artifact_path = (
        reviewed_artifact_path or intent.reviewed_artifact_path
    )
    request_payload = to_jsonable(intent)
    request_payload["expected_outputs"] = list(resolved_outputs)
    request_payload["reviewed_artifact_path"] = resolved_reviewed_artifact_path

    return {
        "quest_passport": to_jsonable(passport),
        "summon_request": request_payload,
        "expected_outputs": list(resolved_outputs),
        "progression_overlay_ref": progression_overlay_ref,
        "self_agent_checkpoint_ref": self_agent_checkpoint_ref,
        "stress_bundle_ref": stress_bundle_ref,
        "checkpoint_note_ref": checkpoint_note_ref,
        "codex_trace_ref": codex_trace_ref,
        "reviewed_artifact_path": resolved_reviewed_artifact_path,
        "audit_refs": list(audit_refs or intent.audit_refs),
    }


def build_summon_result_payload(
    decision: SummonDecision,
    *,
    codex_local_target: CodexLocalAgentTarget | None = None,
    return_plan: ReturnPlan | None = None,
    checkpoint_bridge_plan: CheckpointBridgePlan | None = None,
    memo_export_plan: MemoExportPlan | None = None,
    owner_publication_plan: Iterable[CloseoutBatchPlan] | None = None,
) -> dict[str, Any]:
    payload = to_jsonable(decision)
    payload["codex_local_target"] = (
        to_jsonable(codex_local_target) if codex_local_target is not None else None
    )
    payload["return_plan"] = (
        to_jsonable(return_plan) if return_plan is not None else None
    )
    payload["checkpoint_bridge_plan"] = (
        to_jsonable(checkpoint_bridge_plan)
        if checkpoint_bridge_plan is not None
        else None
    )
    payload["memo_export_plan"] = (
        to_jsonable(memo_export_plan) if memo_export_plan is not None else None
    )
    payload["owner_publication_plan"] = [
        to_jsonable(item) for item in owner_publication_plan or []
    ]
    return payload
