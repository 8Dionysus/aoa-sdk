from __future__ import annotations

from .models import CheckpointEvidenceHandoffPlan, OwnerEvidenceHandoff, ReturnPlan
from .utils import to_jsonable


def build_checkpoint_evidence_handoff_plan(
    *,
    session_ref: str,
    reviewed_artifact_path: str,
    checkpoint_note_ref: str | None = None,
    codex_trace_ref: str | None = None,
    surviving_checkpoint_clusters: list[str] | None = None,
    return_plan: ReturnPlan | None = None,
) -> CheckpointEvidenceHandoffPlan:
    return CheckpointEvidenceHandoffPlan(
        session_ref=session_ref,
        reviewed_artifact_path=reviewed_artifact_path,
        checkpoint_note_ref=checkpoint_note_ref,
        codex_trace_ref=codex_trace_ref,
        surviving_checkpoint_clusters=list(surviving_checkpoint_clusters or []),
        return_anchor_artifact=return_plan.anchor_artifact if return_plan else None,
    )


def build_checkpoint_evidence_bundle(
    plan: CheckpointEvidenceHandoffPlan,
    *,
    owner_handoffs: list[OwnerEvidenceHandoff] | None = None,
) -> dict:
    return {
        "mode": plan.mode,
        "session_ref": plan.session_ref,
        "reviewed_artifact_path": plan.reviewed_artifact_path,
        "checkpoint_note_ref": plan.checkpoint_note_ref,
        "codex_trace_ref": plan.codex_trace_ref,
        "surviving_checkpoint_clusters": list(plan.surviving_checkpoint_clusters),
        "capability_candidates": list(plan.capability_candidates),
        "authority_contract": plan.authority_contract,
        "capability_execution_claimed": plan.capability_execution_claimed,
        "return_anchor_artifact": plan.return_anchor_artifact,
        "owner_handoffs": [
            to_jsonable(item) for item in owner_handoffs or []
        ],
    }
