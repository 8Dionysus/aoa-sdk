from __future__ import annotations

from .models import CheckpointBridgePlan, CloseoutBatchPlan, ReturnPlan
from .utils import to_jsonable


def build_checkpoint_bridge_plan(
    *,
    session_ref: str,
    reviewed_artifact_path: str,
    checkpoint_note_ref: str | None = None,
    codex_trace_ref: str | None = None,
    surviving_checkpoint_clusters: list[str] | None = None,
    return_plan: ReturnPlan | None = None,
) -> CheckpointBridgePlan:
    return CheckpointBridgePlan(
        session_ref=session_ref,
        reviewed_artifact_path=reviewed_artifact_path,
        checkpoint_note_ref=checkpoint_note_ref,
        codex_trace_ref=codex_trace_ref,
        surviving_checkpoint_clusters=list(surviving_checkpoint_clusters or []),
        return_anchor_artifact=return_plan.anchor_artifact if return_plan else None,
    )


def build_checkpoint_context_bundle(
    plan: CheckpointBridgePlan,
    *,
    owner_publication_plan: list[CloseoutBatchPlan] | None = None,
) -> dict:
    return {
        "mode": plan.mode,
        "session_ref": plan.session_ref,
        "reviewed_artifact_path": plan.reviewed_artifact_path,
        "checkpoint_note_ref": plan.checkpoint_note_ref,
        "codex_trace_ref": plan.codex_trace_ref,
        "surviving_checkpoint_clusters": list(plan.surviving_checkpoint_clusters),
        "execution_order": list(plan.execution_order),
        "authority_contract": plan.authority_contract,
        "mechanical_bridge_only": plan.mechanical_bridge_only,
        "agent_skill_application_required": plan.agent_skill_application_required,
        "return_anchor_artifact": plan.return_anchor_artifact,
        "owner_publication_plan": [
            to_jsonable(item) for item in owner_publication_plan or []
        ],
    }
