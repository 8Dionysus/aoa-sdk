from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from .base import BeaconKind, BeaconStatus, StrictModel


ReviewLane = Literal["technique", "skill", "eval", "playbook", "general"]

ReviewPriority = Literal["low", "medium", "high", "critical"]

ReviewDecisionAction = Literal[
    "accept", "reject", "defer", "reanchor", "split", "merge", "suppress"
]

ReviewDecisionFollowthroughKind = Literal[
    "update_surface",
    "create_candidate",
    "update_trigger_eval",
    "write_review_note",
    "open_pr",
    "rerun_proof",
    "rebuild_generated",
    "no_action",
]

SuppressionScope = Literal["beacon", "component", "kind", "owner", "decision_surface"]


class ReviewQueueItem(StrictModel):
    item_ref: str
    lane: ReviewLane
    priority: ReviewPriority
    target_repo: str
    owner_repo: str
    component_ref: str
    beacon_ref: str
    kind: BeaconKind
    status: BeaconStatus
    decision_surface: str | None = None
    summary: str
    evidence_refs: list[str] = Field(default_factory=list)
    source_inputs: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)


class ReviewQueue(StrictModel):
    schema_version: Literal["aoa_review_queue_v1"] = "aoa_review_queue_v1"
    queue_ref: str
    workspace_root: str
    signal_ref: str | None = None
    items: list[ReviewQueueItem] = Field(default_factory=list)


class DossierQuestion(StrictModel):
    prompt: str
    why: str = ""


class CandidateDossier(StrictModel):
    dossier_ref: str
    lane: ReviewLane
    target_repo: str
    owner_repo: str
    component_ref: str
    beacon_ref: str
    kind: BeaconKind
    status: BeaconStatus
    decision_surface: str | None = None
    title: str
    summary: str
    evidence_refs: list[str] = Field(default_factory=list)
    source_inputs: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    review_questions: list[DossierQuestion] = Field(default_factory=list)


class CandidateDossierPacket(StrictModel):
    schema_version: Literal["aoa_candidate_dossier_packet_v1"] = (
        "aoa_candidate_dossier_packet_v1"
    )
    packet_ref: str
    workspace_root: str
    signal_ref: str | None = None
    dossiers: list[CandidateDossier] = Field(default_factory=list)


class OwnerReviewSummaryItem(StrictModel):
    target_repo: str
    total_items: int
    by_lane: dict[str, int] = Field(default_factory=dict)
    by_status: dict[str, int] = Field(default_factory=dict)
    by_kind: dict[str, int] = Field(default_factory=dict)
    decision_surfaces: list[str] = Field(default_factory=list)


class OwnerReviewSummary(StrictModel):
    schema_version: Literal["aoa_owner_review_summary_v1"] = (
        "aoa_owner_review_summary_v1"
    )
    summary_ref: str
    workspace_root: str
    signal_ref: str | None = None
    owners: list[OwnerReviewSummaryItem] = Field(default_factory=list)


class ReviewDecisionFollowthrough(StrictModel):
    action_ref: str
    kind: ReviewDecisionFollowthroughKind
    target_repo: str
    surface: str | None = None
    commands: list[str] = Field(default_factory=list)
    notes: str = ""


class ReviewDecisionSuppressionRule(StrictModel):
    rule_ref: str
    scope: SuppressionScope
    target_repo: str
    component_ref: str | None = None
    beacon_ref: str | None = None
    kind: BeaconKind | None = None
    decision_surface: str | None = None
    reason: str
    expires_after: str | None = None
    notes: str = ""


class ReviewDecisionLineageBridge(StrictModel):
    cluster_ref: str | None = None
    owner_shape: str | None = None
    owner_assigned_ref: str | None = None
    supersedes: list[str] = Field(default_factory=list)
    merged_into: str | None = None
    split_into: list[str] = Field(default_factory=list)
    notes: str = ""


class OwnerReviewDecision(StrictModel):
    schema_version: Literal["aoa_owner_review_decision_v1"] = (
        "aoa_owner_review_decision_v1"
    )
    decision_ref: str
    decided_at: datetime
    owner_repo: str
    target_repo: str
    reviewer: str = "owner-review"
    queue_ref: str | None = None
    item_ref: str | None = None
    input_beacon_refs: list[str] = Field(default_factory=list)
    lane: ReviewLane
    kind: BeaconKind
    component_ref: str
    decision: ReviewDecisionAction
    rationale: str
    decision_surface: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    source_inputs: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    applied_surfaces: list[str] = Field(default_factory=list)
    followthrough: list[ReviewDecisionFollowthrough] = Field(default_factory=list)
    suppression_rules: list[ReviewDecisionSuppressionRule] = Field(default_factory=list)
    lineage_bridge: ReviewDecisionLineageBridge | None = None
    next_review_after: str | None = None
    boundaries_preserved: list[str] = Field(default_factory=list)
    forbidden_implications: list[str] = Field(default_factory=list)
    notes: str = ""


class ReviewDecisionLedgerEntry(StrictModel):
    entry_ref: str
    recorded_at: datetime
    decision_ref: str
    owner_repo: str
    target_repo: str
    input_beacon_refs: list[str] = Field(default_factory=list)
    decision: ReviewDecisionAction
    lane: ReviewLane
    kind: BeaconKind
    component_ref: str
    decision_surface: str | None = None
    applied_surfaces: list[str] = Field(default_factory=list)
    followthrough_refs: list[str] = Field(default_factory=list)
    suppression_rule_refs: list[str] = Field(default_factory=list)
    owner_assigned_ref: str | None = None
    notes: str = ""


class ReviewDecisionLedger(StrictModel):
    schema_version: Literal["aoa_review_decision_ledger_v1"] = (
        "aoa_review_decision_ledger_v1"
    )
    ledger_ref: str
    workspace_root: str
    source_queue_ref: str | None = None
    entries: list[ReviewDecisionLedgerEntry] = Field(default_factory=list)
    by_decision: dict[str, int] = Field(default_factory=dict)
    by_owner: dict[str, int] = Field(default_factory=dict)


class ReviewSuppressionMemory(StrictModel):
    schema_version: Literal["aoa_review_suppression_memory_v1"] = (
        "aoa_review_suppression_memory_v1"
    )
    memory_ref: str
    workspace_root: str
    rules: list[ReviewDecisionSuppressionRule] = Field(default_factory=list)


class ReviewDecisionCloseReport(StrictModel):
    schema_version: Literal["aoa_review_decision_close_report_v1"] = (
        "aoa_review_decision_close_report_v1"
    )
    report_ref: str
    workspace_root: str
    source_queue_ref: str | None = None
    decisions: list[str] = Field(default_factory=list)
    ledger: ReviewDecisionLedger
    suppression_memory: ReviewSuppressionMemory
    closed_item_refs: list[str] = Field(default_factory=list)
    unresolved_item_refs: list[str] = Field(default_factory=list)
    suppressed_beacon_refs: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
