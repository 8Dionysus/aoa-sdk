"""Shared contracts for checkpoint closeout mechanical bridge outputs."""

from __future__ import annotations

from typing import TypedDict

ALLOWED_OWNER_REPOS = {
    "aoa-techniques",
    "aoa-skills",
    "aoa-evals",
    "aoa-memo",
    "aoa-playbooks",
    "aoa-agents",
}
CHECKPOINT_CLOSEOUT_AUTHORITY_CONTRACT: dict[str, object] = {
    "contract": "reviewed_artifact_primary_checkpoint_hints_provisional",
    "bridge_output": "mechanical_artifact_build",
    "checkpoint_notes": "focus_hints_only_not_final_authority",
    "reviewed_artifact": "primary_closeout_evidence",
    "agent_skill_application": "required_for_final_session_analysis",
}

class DonorHarvestOutputs(TypedDict):
    packet: dict[str, object]
    artifact_refs: list[str]
    receipt_refs: list[str]
    reviewed_tokens: set[str]
    receipt_payloads: list[dict[str, object]]


class ProgressionLiftOutputs(TypedDict):
    packet: dict[str, object]
    artifact_refs: list[str]
    receipt_refs: list[str]


class QuestHarvestOutputs(TypedDict):
    packet: dict[str, object]
    artifact_refs: list[str]
    receipt_refs: list[str]
