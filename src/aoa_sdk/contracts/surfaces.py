from __future__ import annotations

from typing import Literal

from pydantic import AliasChoices, BaseModel, Field

from .checkpoints import CheckpointCandidateCluster, ProgressionAxisSignal, SessionCheckpointCluster
from .routing import RoutingOwnerLayerShortlistHint
from .stats import StatsRegroundingSignal


class SurfaceOpportunityExecutionHint(BaseModel):
    model_config = {"populate_by_name": True}

    lane: Literal[
        "skill-dispatch",
        "inspect-expand-use",
        "manual-equivalence",
        "closeout-harvest",
        "defer",
    ]
    executable_now: bool = False
    requires_confirmation: bool = False
    existing_command: str | None = None
    existing_surface: str | None = None
    manual_equivalence_allowed: bool = Field(
        default=False,
        validation_alias=AliasChoices("manual_equivalence_allowed", "manual_fallback_allowed"),
    )
    manual_equivalence_note: str | None = Field(
        default=None,
        validation_alias=AliasChoices("manual_equivalence_note", "manual_fallback_note"),
    )
    host_availability_status: Literal["host-executable", "router-only", "unknown"] | None = None


class SurfaceOpportunityReference(BaseModel):
    role: Literal[
        "family-entry",
        "inspect",
        "runtime-receipt",
        "skill-report",
        "closeout-handoff",
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
    state: Literal["activated", "manual-equivalent", "candidate-now", "candidate-later"]
    phase_detected: Literal["ingress", "in-flight", "pre-mutation", "checkpoint", "closeout"]
    reason: str
    signals: list[
        Literal[
            "explicit-request",
            "risk-gate",
            "router-match",
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
    related_skill_names: list[str] = Field(default_factory=list)
    closeout_family_candidates: list[str] = Field(default_factory=list)
    promotion_hint: str | None = None
    shortlist_hints: list[RoutingOwnerLayerShortlistHint] = Field(default_factory=list)
    owner_layer_ambiguity_note: str | None = None
    family_entry_refs: list[SurfaceOpportunityReference] = Field(default_factory=list)
    evidence_refs: list[SurfaceOpportunityReference] = Field(default_factory=list)


class SurfaceDetectionReport(BaseModel):
    schema_version: int = 1
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
    skill_report_path: str | None = None
    skill_report_included: bool = False
    shortlist_included: bool = False
    active_skill_names: list[str] = Field(default_factory=list)
    immediate_skill_dispatch: list[str] = Field(default_factory=list)
    items: list[SurfaceOpportunityItem] = Field(default_factory=list)
    regrounding_hints: list[StatsRegroundingSignal] = Field(default_factory=list)
    regrounding_required: bool = False
    regrounding_reason_codes: list[str] = Field(default_factory=list)
    checkpoint_should_capture: bool = False
    candidate_clusters: list["CheckpointCandidateCluster"] = Field(default_factory=list)
    promotion_recommendation: Literal["none", "local_note", "dionysus_note", "harvest_handoff"] = "none"
    blocked_by: list[str] = Field(default_factory=list)
    closeout_followups: list[str] = Field(default_factory=list)
    owner_layer_notes: list[str] = Field(default_factory=list)
    actionability_gaps: list[str] = Field(default_factory=list)

class SurfaceCloseoutHandoffTarget(BaseModel):
    skill_name: Literal[
        "aoa-session-donor-harvest",
        "aoa-automation-opportunity-scan",
        "aoa-session-route-forks",
        "aoa-session-self-diagnose",
        "aoa-session-self-repair",
        "aoa-session-progression-lift",
        "aoa-quest-harvest",
    ]
    why: str
    triggered_by: list[str] = Field(default_factory=list)


class SurfaceCloseoutHandoff(BaseModel):
    schema_version: int = 1
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
