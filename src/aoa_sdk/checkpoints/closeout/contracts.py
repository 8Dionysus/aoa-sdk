"""Contracts for checkpoint closeout evidence materialization."""

from __future__ import annotations

from typing import TypedDict


CHECKPOINT_CLOSEOUT_AUTHORITY_CONTRACT: dict[str, object] = {
    "contract": "reviewed_evidence_primary_candidates_are_routing_only",
    "materialization": "reviewed_evidence_bundle",
    "checkpoint_notes": "focus_hints_only_not_final_authority",
    "reviewed_artifact": "primary_closeout_evidence",
    "capability_execution_claimed": False,
    "owner_decision_required": True,
}


class ReviewedEvidenceBundleOutputs(TypedDict):
    packet: dict[str, object]
    artifact_refs: list[str]
    receipt_refs: list[str]
