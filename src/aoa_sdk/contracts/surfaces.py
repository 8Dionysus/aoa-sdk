from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from .checkpoints import (
    ActionSignature,
    CheckpointActionEvent,
    CheckpointCandidateCluster,
    ProgressionAxisSignal,
    SessionCheckpointCluster,
    WrapperGapCandidate,
)
from .routing import RoutingOwnerLayerShortlistHint
from .stats import StatsRegroundingSignal


class SurfaceOpportunityExecutionHint(BaseModel):
    lane: Literal[
        "inspect-expand-use",
        "closeout-harvest",
        "defer",
    ]
    executable_now: bool = False
    requires_confirmation: bool = False
    existing_command: str | None = None
    existing_surface: str | None = None


class SurfaceOpportunityReference(BaseModel):
    role: Literal[
        "family-entry",
        "inspect",
    ]
    ref: str
    owner_repo: str | None = None
    note: str | None = None


class SurfaceOpportunityItem(BaseModel):
    surface_ref: str
    display_name: str
    object_kind: Literal["technique", "skill", "eval", "memo", "playbook", "agent"]
    owner_repo: Literal[
        "aoa-techniques",
        "aoa-skills",
        "aoa-evals",
        "aoa-memo",
        "aoa-playbooks",
        "aoa-agents",
    ]
    state: Literal["candidate-now", "candidate-later"]
    phase_detected: Literal["ingress", "in-flight", "pre-mutation", "checkpoint", "closeout"]
    reason: str
    signals: list[
        Literal[
            "explicit-request",
            "repeated-pattern",
            "proof-need",
            "recall-need",
            "scenario-recurring",
            "role-posture",
            "closeout-chain",
        ]
    ] = Field(default_factory=list)
    confidence: Literal["low", "medium", "high"] = "medium"
    execution: SurfaceOpportunityExecutionHint
    related_capability_refs: list[str] = Field(default_factory=list)
    closeout_capability_candidates: list[str] = Field(default_factory=list)
    promotion_hint: str | None = None
    shortlist_hints: list[RoutingOwnerLayerShortlistHint] = Field(default_factory=list)
    owner_layer_ambiguity_note: str | None = None
    family_entry_refs: list[SurfaceOpportunityReference] = Field(default_factory=list)
    evidence_refs: list[SurfaceOpportunityReference] = Field(default_factory=list)


class SurfaceDetectionReport(BaseModel):
    schema_version: Literal[2] = 2
    repo_root: str
    workspace_root: str
    phase: Literal["ingress", "in-flight", "pre-mutation", "checkpoint", "closeout"]
    intent_text: str = ""
    mutation_surface: Literal["none", "code", "repo-config", "infra", "runtime", "public-share"] = "none"
    checkpoint_kind: Literal[
        "manual",
        "commit",
        "verify_green",
        "pr_opened",
        "pr_merged",
        "pause",
        "owner_followthrough",
    ] | None = None
    source_inputs: list[str] = Field(default_factory=list)
    shortlist_included: bool = False
    items: list[SurfaceOpportunityItem] = Field(default_factory=list)
    regrounding_hints: list[StatsRegroundingSignal] = Field(default_factory=list)
    regrounding_required: bool = False
    regrounding_reason_codes: list[str] = Field(default_factory=list)
    checkpoint_should_capture: bool = False
    candidate_clusters: list["CheckpointCandidateCluster"] = Field(default_factory=list)
    action_events: list[CheckpointActionEvent] = Field(default_factory=list)
    action_signatures: list[ActionSignature] = Field(default_factory=list)
    wrapper_gap_candidates: list[WrapperGapCandidate] = Field(default_factory=list)
    promotion_recommendation: Literal["none", "local_note", "dionysus_note", "harvest_handoff"] = "none"
    blocked_by: list[str] = Field(default_factory=list)
    closeout_followups: list[str] = Field(default_factory=list)
    owner_layer_notes: list[str] = Field(default_factory=list)
    inspection_gaps: list[str] = Field(default_factory=list)

class SurfaceCloseoutHandoffTarget(BaseModel):
    target_ref: str
    target_kind: Literal["capability", "owner-surface"]
    owner_repo: str
    why: str
    triggered_by: list[str] = Field(default_factory=list)


class SurfaceCloseoutHandoff(BaseModel):
    schema_version: Literal[2] = 2
    session_ref: str
    reviewed: bool
    surface_detection_report_ref: str
    checkpoint_note_ref: str | None = None
    surviving_items: list[SurfaceOpportunityItem] = Field(default_factory=list)
    surviving_checkpoint_clusters: list[SessionCheckpointCluster] = Field(default_factory=list)
    checkpoint_harvest_candidates: list[SessionCheckpointCluster] = Field(default_factory=list)
    checkpoint_progression_candidates: list[SessionCheckpointCluster] = Field(default_factory=list)
    checkpoint_upgrade_candidates: list[SessionCheckpointCluster] = Field(default_factory=list)
    checkpoint_progression_axes: list[ProgressionAxisSignal] = Field(default_factory=list)
    stats_refresh_recommended: bool = False
    handoff_targets: list[SurfaceCloseoutHandoffTarget] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
