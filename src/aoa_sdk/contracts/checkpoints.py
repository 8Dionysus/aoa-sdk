from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .closeout import OwnerFollowThroughBrief, WorkflowFollowThroughBrief


class CheckpointLineageHint(BaseModel):
    schema_version: Literal["aoa_checkpoint_lineage_hint_v1"] = "aoa_checkpoint_lineage_hint_v1"
    cluster_ref: str
    owner_hypothesis: str
    owner_shape: str
    nearest_wrong_target: str | None = None
    status_posture: Literal["early", "reanchor", "thin-evidence", "stable"]
    evidence_refs: list[str] = Field(default_factory=list)
    axis_pressure: dict[str, int] = Field(default_factory=dict)
    supersedes: list[str] = Field(default_factory=list)
    merged_into: str | None = None
    drop_reason: str | None = None


class CloseoutOwnerFollowthroughHint(BaseModel):
    schema_version: Literal["aoa_closeout_owner_followthrough_hint_v1"] = (
        "aoa_closeout_owner_followthrough_hint_v1"
    )
    cluster_ref: str
    candidate_slot: str | None = None
    owner_hypothesis: str
    owner_shape: str
    nearest_wrong_target: str | None = None
    status_posture: Literal["early", "reanchor", "thin-evidence", "stable"]
    recommended_owner_status_surface: str
    requested_next_decision_class: Literal[
        "land_direct",
        "stage_seed",
        "reanchor_owner",
        "prove_first",
        "merge_into_existing",
        "defer",
        "drop",
    ]
    evidence_refs: list[str] = Field(default_factory=list)


class CloseoutFollowthroughDecision(BaseModel):
    schema_version: Literal["aoa_sdk_closeout_followthrough_decision_v1"] = (
        "aoa_sdk_closeout_followthrough_decision_v1"
    )
    session_ref: str
    reviewed_closeout_context_ref: str
    cluster_ref: str
    candidate_ref: str | None = None
    recommended_next_skill: Literal[
        "aoa-session-route-forks",
        "aoa-session-self-diagnose",
        "aoa-session-self-repair",
        "aoa-session-progression-lift",
        "aoa-automation-opportunity-scan",
        "aoa-quest-harvest",
    ]
    also_considered: list[
        Literal[
            "aoa-session-route-forks",
            "aoa-session-self-diagnose",
            "aoa-session-self-repair",
            "aoa-session-progression-lift",
            "aoa-automation-opportunity-scan",
            "aoa-quest-harvest",
        ]
    ] = Field(default_factory=list)
    reason_codes: list[
        Literal[
            "multiple_plausible_next_moves",
            "repeated_friction",
            "blocked_automation_readiness",
            "reviewed_diagnosis_present",
            "smallest_repair_clear",
            "explicit_axis_movement",
            "no_repair_needed",
            "repeated_manual_route",
            "stable_output_shape",
            "checkpoint_sensitive",
            "reviewed_quest_unit",
            "promotion_pressure",
        ]
    ] = Field(default_factory=list)
    checkpoint_required: bool
    approval_posture: Literal["not_required", "review_required", "approval_required"]
    defer_allowed: bool
    owner_hypothesis: str
    nearest_wrong_target: str | None = None
    status_posture: Literal["early", "reanchor", "thin-evidence", "stable"]

    @model_validator(mode="after")
    def _validate_also_considered(self) -> "CloseoutFollowthroughDecision":
        if self.recommended_next_skill in self.also_considered:
            raise ValueError("also_considered must not repeat recommended_next_skill")
        return self


class CheckpointSessionMemoryRouteSignalSummary(BaseModel):
    layer: str
    signal_count: int
    top_keys: dict[str, int] = Field(default_factory=dict)


class CheckpointSessionMemoryRef(BaseModel):
    schema_version: Literal["aoa_checkpoint_session_memory_ref_v1"] = (
        "aoa_checkpoint_session_memory_ref_v1"
    )
    source: Literal["aoa-session-memory"] = "aoa-session-memory"
    authority_contract: Literal["archive_indexes_are_route_evidence_not_reviewed_truth"] = (
        "archive_indexes_are_route_evidence_not_reviewed_truth"
    )
    aoa_root: str
    session_id: str
    session_label: str | None = None
    session_title: str | None = None
    archive_path: str
    manifest_ref: str
    session_index_ref: str | None = None
    raw_ref: str | None = None
    raw_blocks_index_ref: str | None = None
    source_trace_ref: str | None = None
    archive_status: str | None = None
    distillation_status: str | None = None
    review_status: str | None = None
    event_count: int | None = None
    segment_count: int | None = None
    updated_at: str | None = None
    work_context: dict[str, Any] = Field(default_factory=dict)
    conversation_act_counts: dict[str, int] = Field(default_factory=dict)
    session_act_counts: dict[str, int] = Field(default_factory=dict)
    route_signal_layers: list[str] = Field(default_factory=list)
    route_signal_summary: list[CheckpointSessionMemoryRouteSignalSummary] = Field(
        default_factory=list
    )
    evidence_refs: list[str] = Field(default_factory=list)
    cautions: list[str] = Field(default_factory=list)


class CheckpointSessionMemoryFreshness(BaseModel):
    schema_version: Literal["aoa_checkpoint_session_memory_freshness_v1"] = (
        "aoa_checkpoint_session_memory_freshness_v1"
    )
    status: Literal["current", "partial", "missing", "unavailable"] = "unavailable"
    local_manifest_status: Literal["current", "missing", "not_checked"] = "not_checked"
    local_session_index_status: Literal["current", "missing", "not_checked"] = "not_checked"
    local_raw_status: Literal["current", "missing", "not_checked"] = "not_checked"
    global_search_status: Literal["not_checked"] = "not_checked"
    global_atlas_status: Literal["not_checked"] = "not_checked"
    global_graph_status: Literal["not_checked"] = "not_checked"
    checked_at: datetime | None = None
    cautions: list[str] = Field(default_factory=list)


class CheckpointRuntimeTraceRef(BaseModel):
    schema_version: Literal["aoa_checkpoint_runtime_trace_ref_v1"] = (
        "aoa_checkpoint_runtime_trace_ref_v1"
    )
    source: Literal["aoa-sdk-skill-runtime-session"] = "aoa-sdk-skill-runtime-session"
    runtime_session_id: str
    runtime_session_file_ref: str
    codex_thread_id: str | None = None
    codex_rollout_path: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)


class CheckpointCandidateCluster(BaseModel):
    candidate_id: str
    candidate_kind: str
    owner_hint: str
    display_name: str
    source_surface_ref: str
    evidence_refs: list[str] = Field(default_factory=list)
    confidence: Literal["low", "medium", "high"] = "medium"
    session_end_targets: list[Literal["harvest", "progression", "upgrade"]] = Field(default_factory=list)
    progression_axis_signals: list["ProgressionAxisSignal"] = Field(default_factory=list)
    promote_if: list[str] = Field(default_factory=list)
    defer_reason: str | None = None
    blocked_by: list[str] = Field(default_factory=list)
    next_owner_moves: list[str] = Field(default_factory=list)
    lineage_hint: CheckpointLineageHint | None = None
    action_signature_refs: list[str] = Field(default_factory=list)


class ActionFacetSet(BaseModel):
    schema_version: Literal["aoa_checkpoint_action_facets_v1"] = (
        "aoa_checkpoint_action_facets_v1"
    )
    event_type: str
    family: Literal[
        "communication",
        "command_execution",
        "workspace_mutation",
        "context_memory",
        "verification",
        "owner_routing",
        "risk",
        "wrapper_gap",
        "unknown",
    ]
    phase: Literal[
        "ingress",
        "in_flight",
        "pre_mutation",
        "checkpoint",
        "closeout",
        "review",
        "unknown",
    ] = "checkpoint"
    actor: Literal["user", "assistant", "tool", "codex_runtime", "unknown"] = "assistant"
    action: str
    object: str
    outcome: str
    session_act: str | None = None
    route_signals: list[str] = Field(default_factory=list)
    relationships: list[str] = Field(default_factory=list)
    confidence: Literal["low", "medium", "high"] = "medium"


class CheckpointActionEvent(BaseModel):
    schema_version: Literal["aoa_checkpoint_action_event_v1"] = (
        "aoa_checkpoint_action_event_v1"
    )
    event_id: str
    source_ref: str
    facets: ActionFacetSet
    trigger_text: str = ""
    evidence_refs: list[str] = Field(default_factory=list)
    candidate_ids: list[str] = Field(default_factory=list)
    surface_refs: list[str] = Field(default_factory=list)
    action_signature_ref: str | None = None


class ActionSignature(BaseModel):
    schema_version: Literal["aoa_checkpoint_action_signature_v1"] = (
        "aoa_checkpoint_action_signature_v1"
    )
    signature_id: str
    family: str
    action: str
    object: str
    trigger: str
    inputs: list[str] = Field(default_factory=list)
    steps: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    verification: list[str] = Field(default_factory=list)
    failure_modes: list[str] = Field(default_factory=list)
    stop_lines: list[str] = Field(default_factory=list)
    owner_pressure: list[str] = Field(default_factory=list)
    event_types: list[str] = Field(default_factory=list)
    route_signals: list[str] = Field(default_factory=list)
    mutation_surfaces: list[str] = Field(default_factory=list)
    authority_surfaces: list[str] = Field(default_factory=list)
    memory_provenance_refs: list[str] = Field(default_factory=list)
    negative_evidence: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    action_event_ids: list[str] = Field(default_factory=list)
    wrapper_family_hint: Literal[
        "skill",
        "playbook",
        "technique",
        "eval",
        "memo",
        "sdk_mechanic",
        "owner_local",
        "unknown",
    ] = "unknown"
    confidence: Literal["low", "medium", "high"] = "medium"


class ExistingWrapperFit(BaseModel):
    schema_version: Literal["aoa_checkpoint_existing_wrapper_fit_v1"] = (
        "aoa_checkpoint_existing_wrapper_fit_v1"
    )
    wrapper_family: Literal[
        "skill",
        "playbook",
        "technique",
        "eval",
        "memo",
        "sdk_mechanic",
        "owner_local",
        "unknown",
    ]
    fit_status: Literal["strong", "weak", "none"] = "none"
    existing_surface_ref: str | None = None
    nearest_existing_wrapper: str | None = None
    fit_reason: str
    evidence_refs: list[str] = Field(default_factory=list)


class WrapperReadiness(BaseModel):
    schema_version: Literal["aoa_checkpoint_wrapper_readiness_v1"] = (
        "aoa_checkpoint_wrapper_readiness_v1"
    )
    proposed_wrapper_family: Literal[
        "skill",
        "playbook",
        "technique",
        "eval",
        "memo",
        "sdk_mechanic",
        "owner_local",
        "unknown",
    ]
    draftability: Literal["observe", "reviewable", "draftable", "blocked"] = "observe"
    review_status: Literal["unreviewed", "reviewed", "rejected"] = "unreviewed"
    score: int = 0
    reasons: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    stop_lines: list[str] = Field(default_factory=list)


class WrapperGapCandidate(BaseModel):
    schema_version: Literal["aoa_checkpoint_wrapper_gap_candidate_v1"] = (
        "aoa_checkpoint_wrapper_gap_candidate_v1"
    )
    candidate_id: str
    signature_id: str
    proposed_wrapper_family: Literal[
        "skill",
        "playbook",
        "technique",
        "eval",
        "memo",
        "sdk_mechanic",
        "owner_local",
        "unknown",
    ]
    nearest_existing_wrapper: str | None = None
    novelty_reason: str
    draftability: Literal["observe", "reviewable", "draftable", "blocked"] = "observe"
    review_status: Literal["unreviewed", "reviewed", "rejected"] = "unreviewed"
    evidence_refs: list[str] = Field(default_factory=list)


class RepetitionCluster(BaseModel):
    schema_version: Literal["aoa_checkpoint_repetition_cluster_v1"] = (
        "aoa_checkpoint_repetition_cluster_v1"
    )
    cluster_id: str
    signature_id: str
    repeat_count: int = 0
    cross_session_count: int = 0
    trigger_stability: Literal["low", "medium", "high"] = "low"
    step_stability: Literal["low", "medium", "high"] = "low"
    verification_stability: Literal["low", "medium", "high"] = "low"
    failure_recurrence: Literal["none", "low", "medium", "high"] = "none"
    owner_clarity: Literal["low", "medium", "high"] = "low"
    novelty_pressure: Literal["low", "medium", "high"] = "low"
    automation_risk: Literal["low", "medium", "high"] = "medium"
    review_debt: Literal["low", "medium", "high"] = "medium"
    action_event_ids: list[str] = Field(default_factory=list)
    runtime_session_ids: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    existing_wrapper_fit: ExistingWrapperFit
    wrapper_readiness: WrapperReadiness
    wrapper_gap: WrapperGapCandidate | None = None


class CandidateClassifierFeedback(BaseModel):
    schema_version: Literal["aoa_checkpoint_candidate_classifier_feedback_v1"] = (
        "aoa_checkpoint_candidate_classifier_feedback_v1"
    )
    target_ref: str
    verdict: Literal["accept", "reject", "weaken", "split", "add_rule"]
    reason: str
    reviewer: str = "agent"
    evidence_refs: list[str] = Field(default_factory=list)


class CandidateIntelligenceSample(BaseModel):
    schema_version: Literal["aoa_checkpoint_candidate_intelligence_sample_v1"] = (
        "aoa_checkpoint_candidate_intelligence_sample_v1"
    )
    sample_id: str
    target_ref: str
    sample_kind: Literal["signature", "wrapper_gap", "repetition_cluster"]
    verdict: Literal["unreviewed", "accept", "reject", "weaken", "split", "add_rule"] = (
        "unreviewed"
    )
    reason: str
    evidence_refs: list[str] = Field(default_factory=list)


class CandidateIntelligenceReport(BaseModel):
    schema_version: int = 1
    report_type: Literal["checkpoint_candidate_intelligence_report_v1"] = (
        "checkpoint_candidate_intelligence_report_v1"
    )
    repo_root: str
    repo_label: str
    generated_at: datetime
    generated_at_local: str | None = None
    generated_tz: str | None = None
    source: Literal["surface_detection", "checkpoint_note", "lifecycle_audit"] = (
        "surface_detection"
    )
    boundary_note: str = (
        "Candidate intelligence is generated route evidence, not reviewed truth "
        "or promotion authority."
    )
    action_events: list[CheckpointActionEvent] = Field(default_factory=list)
    action_signatures: list[ActionSignature] = Field(default_factory=list)
    repetition_clusters: list[RepetitionCluster] = Field(default_factory=list)
    wrapper_gap_candidates: list[WrapperGapCandidate] = Field(default_factory=list)
    existing_wrapper_fits: list[ExistingWrapperFit] = Field(default_factory=list)
    feedback_items: list[CandidateClassifierFeedback] = Field(default_factory=list)
    sample_audit: list[CandidateIntelligenceSample] = Field(default_factory=list)
    generated_index_ref: str | None = None


class ExistingCarrierFit(BaseModel):
    schema_version: Literal["aoa_checkpoint_existing_carrier_fit_v1"] = (
        "aoa_checkpoint_existing_carrier_fit_v1"
    )
    carrier_kind: Literal[
        "mechanic",
        "tool",
        "mcp",
        "hook",
        "script",
        "daemon",
        "service",
        "index",
        "unknown",
    ]
    fit_status: Literal["strong", "weak", "none"] = "none"
    existing_surface_ref: str | None = None
    nearest_existing_carrier: str | None = None
    fit_reason: str
    evidence_refs: list[str] = Field(default_factory=list)


class CarrierReadiness(BaseModel):
    schema_version: Literal["aoa_checkpoint_carrier_readiness_v1"] = (
        "aoa_checkpoint_carrier_readiness_v1"
    )
    proposed_carrier_kind: Literal[
        "mechanic",
        "tool",
        "mcp",
        "hook",
        "script",
        "daemon",
        "service",
        "index",
        "unknown",
    ]
    owner_scope: Literal["center", "owner_repo", "cross_repo", "sdk_local", "unknown"] = (
        "unknown"
    )
    draftability: Literal["observe", "reviewable", "draftable", "blocked"] = "observe"
    review_status: Literal["unreviewed", "reviewed", "rejected"] = "unreviewed"
    execution_posture: Literal[
        "descriptive_only",
        "manual_only",
        "review_required",
        "install_blocked",
        "callable_blocked",
    ] = "descriptive_only"
    installability: Literal[
        "not_installable",
        "candidate_only",
        "review_required",
        "owner_required",
        "install_blocked",
    ] = "not_installable"
    score: int = 0
    reasons: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    stop_lines: list[str] = Field(default_factory=list)


class CarrierCandidate(BaseModel):
    schema_version: Literal["aoa_checkpoint_carrier_candidate_v1"] = (
        "aoa_checkpoint_carrier_candidate_v1"
    )
    candidate_id: str
    signature_id: str
    carrier_kind: Literal[
        "mechanic",
        "tool",
        "mcp",
        "hook",
        "script",
        "daemon",
        "service",
        "index",
        "unknown",
    ]
    owner_scope: Literal["center", "owner_repo", "cross_repo", "sdk_local", "unknown"] = (
        "unknown"
    )
    source_wrapper_family: Literal[
        "skill",
        "playbook",
        "technique",
        "eval",
        "memo",
        "sdk_mechanic",
        "owner_local",
        "unknown",
    ] = "unknown"
    action_family: str
    action: str
    object: str
    trigger: str
    route_signals: list[str] = Field(default_factory=list)
    owner_pressure: list[str] = Field(default_factory=list)
    cross_repo_pressure: bool = False
    execution_risk: Literal["low", "medium", "high", "critical"] = "medium"
    execution_posture: Literal[
        "descriptive_only",
        "manual_only",
        "review_required",
        "install_blocked",
        "callable_blocked",
    ] = "descriptive_only"
    installability: Literal[
        "not_installable",
        "candidate_only",
        "review_required",
        "owner_required",
        "install_blocked",
    ] = "not_installable"
    existing_carrier_fit: ExistingCarrierFit
    carrier_readiness: CarrierReadiness
    evidence_refs: list[str] = Field(default_factory=list)
    stop_lines: list[str] = Field(default_factory=list)


class CarrierClassifierFeedback(BaseModel):
    schema_version: Literal["aoa_checkpoint_carrier_classifier_feedback_v1"] = (
        "aoa_checkpoint_carrier_classifier_feedback_v1"
    )
    target_ref: str
    verdict: Literal["accept", "reject", "weaken", "split", "add_rule"]
    reason: str
    reviewer: str = "agent"
    evidence_refs: list[str] = Field(default_factory=list)


class CarrierIntelligenceSample(BaseModel):
    schema_version: Literal["aoa_checkpoint_carrier_intelligence_sample_v1"] = (
        "aoa_checkpoint_carrier_intelligence_sample_v1"
    )
    sample_id: str
    target_ref: str
    sample_kind: Literal["carrier_candidate", "existing_fit", "readiness"]
    verdict: Literal["unreviewed", "accept", "reject", "weaken", "split", "add_rule"] = (
        "unreviewed"
    )
    reason: str
    evidence_refs: list[str] = Field(default_factory=list)


class CarrierIntelligenceReport(BaseModel):
    schema_version: int = 1
    report_type: Literal["checkpoint_carrier_candidate_intelligence_report_v1"] = (
        "checkpoint_carrier_candidate_intelligence_report_v1"
    )
    repo_root: str
    repo_label: str
    generated_at: datetime
    generated_at_local: str | None = None
    generated_tz: str | None = None
    source: Literal[
        "candidate_intelligence_report",
        "checkpoint_note",
        "surface_detection",
        "lifecycle_audit",
    ] = "candidate_intelligence_report"
    boundary_note: str = (
        "Carrier intelligence is generated ecosystem route evidence, not "
        "accepted mechanics, installed tools, registered MCP services, hooks, "
        "automation, owner verdicts, memory, proof, RAG, or GraphRAG authority."
    )
    carrier_candidates: list[CarrierCandidate] = Field(default_factory=list)
    existing_carrier_fits: list[ExistingCarrierFit] = Field(default_factory=list)
    feedback_items: list[CarrierClassifierFeedback] = Field(default_factory=list)
    sample_audit: list[CarrierIntelligenceSample] = Field(default_factory=list)
    source_candidate_intelligence_ref: str | None = None
    generated_index_ref: str | None = None


class SessionCheckpointAutoObservation(BaseModel):
    schema_version: int = 1
    observation_type: Literal["auto_post_commit_checkpoint_observation_v1"] = (
        "auto_post_commit_checkpoint_observation_v1"
    )
    observation_id: str
    observed_at: datetime
    observed_at_local: str | None = None
    observed_tz: str | None = None
    repo_root: str
    repo_label: str
    commit_ref: str
    commit_sha: str | None = None
    commit_short_sha: str | None = None
    commit_subject: str | None = None
    summary: str
    applied_skill_names: list[str] = Field(default_factory=list)
    findings: list[str] = Field(default_factory=list)
    candidate_notes: list[str] = Field(default_factory=list)
    stats_hints: list[str] = Field(default_factory=list)
    mechanic_hints: list[str] = Field(default_factory=list)
    closeout_questions: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    next_owner_moves: list[str] = Field(default_factory=list)


class SessionCheckpointAgentReview(BaseModel):
    schema_version: int = 1
    review_type: Literal["agent_post_commit_checkpoint_review_v1"] = (
        "agent_post_commit_checkpoint_review_v1"
    )
    review_id: str
    auto_observation_ref: str | None = None
    reviewed_at: datetime
    reviewed_at_local: str | None = None
    reviewed_tz: str | None = None
    repo_root: str
    repo_label: str
    commit_ref: str
    commit_sha: str | None = None
    commit_short_sha: str | None = None
    commit_subject: str | None = None
    summary: str
    applied_skill_names: list[str] = Field(default_factory=list)
    findings: list[str] = Field(default_factory=list)
    candidate_notes: list[str] = Field(default_factory=list)
    stats_hints: list[str] = Field(default_factory=list)
    mechanic_hints: list[str] = Field(default_factory=list)
    closeout_questions: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    next_owner_moves: list[str] = Field(default_factory=list)
    defer_until_closeout: bool = True


class SessionCheckpointLifecycleEvent(BaseModel):
    schema_version: int = 1
    event_type: Literal[
        "checkpoint_lifecycle_closed_v1",
        "checkpoint_session_archived_without_closeout_v1",
    ] = "checkpoint_lifecycle_closed_v1"
    event_id: str
    observed_at: datetime
    observed_at_local: str | None = None
    observed_tz: str | None = None
    repo_root: str
    repo_label: str
    session_ref: str
    runtime_session_id: str | None = None
    lifecycle_state: Literal["closed", "archived_without_closeout"] = "closed"
    closeout_context_ref: str | None = None
    closeout_execution_report_ref: str | None = None
    session_memory_archive_ref: str | None = None
    archive_reason: str
    evidence_refs: list[str] = Field(default_factory=list)


class SessionCheckpointHistoryEntry(BaseModel):
    checkpoint_kind: Literal[
        "manual",
        "commit",
        "verify_green",
        "pr_opened",
        "pr_merged",
        "pause",
        "owner_followthrough",
    ]
    observed_at: datetime
    observed_at_local: str | None = None
    observed_tz: str | None = None
    report_ref: str | None = None
    intent_text: str = ""
    checkpoint_should_capture: bool = False
    blocked_by: list[str] = Field(default_factory=list)
    candidate_clusters: list[CheckpointCandidateCluster] = Field(default_factory=list)
    action_events: list[CheckpointActionEvent] = Field(default_factory=list)
    action_signatures: list[ActionSignature] = Field(default_factory=list)
    wrapper_gap_candidates: list[WrapperGapCandidate] = Field(default_factory=list)
    manual_review_requested: bool = False
    commit_sha: str | None = None
    commit_short_sha: str | None = None
    agent_review_status: Literal["not_required", "pending", "reviewed"] = "not_required"
    agent_review_ref: str | None = None
    auto_observation: SessionCheckpointAutoObservation | None = None


class SessionCheckpointCluster(BaseModel):
    candidate_id: str
    candidate_kind: str
    owner_hint: str
    display_name: str
    source_surface_ref: str
    checkpoint_hits: int
    evidence_refs: list[str] = Field(default_factory=list)
    confidence: Literal["low", "medium", "high"] = "medium"
    review_status: Literal["collecting", "reviewable", "promoted", "closed"] = "collecting"
    session_end_targets: list[Literal["harvest", "progression", "upgrade"]] = Field(default_factory=list)
    progression_axis_signals: list["ProgressionAxisSignal"] = Field(default_factory=list)
    promote_if: list[str] = Field(default_factory=list)
    defer_reason: str | None = None
    blocked_by: list[str] = Field(default_factory=list)
    next_owner_moves: list[str] = Field(default_factory=list)
    lineage_hint: CheckpointLineageHint | None = None
    action_signature_refs: list[str] = Field(default_factory=list)


class ProgressionAxisSignal(BaseModel):
    axis: Literal[
        "boundary_integrity",
        "execution_reliability",
        "change_legibility",
        "review_sharpness",
        "proof_discipline",
        "provenance_hygiene",
        "deep_readiness",
    ]
    movement: Literal["advance", "hold", "reanchor", "downgrade"]
    why: str
    evidence_refs: list[str] = Field(default_factory=list)
    candidate_ids: list[str] = Field(default_factory=list)


class SessionCheckpointNote(BaseModel):
    schema_version: int = 1
    contract_type: Literal["session_checkpoint_note_v1"] = "session_checkpoint_note_v1"
    session_ref: str
    runtime_session_id: str | None = None
    runtime_session_created_at: datetime | None = None
    state: Literal["collecting", "reviewable", "promoted", "closed"] = "collecting"
    repo_scope: list[str] = Field(default_factory=list)
    checkpoint_history: list[SessionCheckpointHistoryEntry] = Field(default_factory=list)
    candidate_clusters: list[SessionCheckpointCluster] = Field(default_factory=list)
    action_events: list[CheckpointActionEvent] = Field(default_factory=list)
    action_signatures: list[ActionSignature] = Field(default_factory=list)
    repetition_clusters: list[RepetitionCluster] = Field(default_factory=list)
    wrapper_gap_candidates: list[WrapperGapCandidate] = Field(default_factory=list)
    promotion_recommendation: Literal["none", "local_note", "dionysus_note", "harvest_handoff"] = "none"
    carry_until_session_closeout: bool = True
    session_end_recommendation: Literal[
        "hold",
        "harvest",
        "progression",
        "upgrade",
        "harvest_and_progression",
        "progression_and_upgrade",
        "harvest_and_upgrade",
        "harvest_progression_and_upgrade",
    ] = "hold"
    harvest_candidate_ids: list[str] = Field(default_factory=list)
    progression_candidate_ids: list[str] = Field(default_factory=list)
    upgrade_candidate_ids: list[str] = Field(default_factory=list)
    progression_axis_signals: list[ProgressionAxisSignal] = Field(default_factory=list)
    stats_refresh_recommended: bool = False
    agent_review_status: Literal["none", "pending", "reviewed"] = "none"
    agent_review_required: bool = False
    agent_review_pending_refs: list[str] = Field(default_factory=list)
    review_refs: list[str] = Field(default_factory=list)
    auto_observation_refs: list[str] = Field(default_factory=list)
    applied_skill_names: list[str] = Field(default_factory=list)
    summaries: list[str] = Field(default_factory=list)
    findings: list[str] = Field(default_factory=list)
    candidate_notes: list[str] = Field(default_factory=list)
    stats_hints: list[str] = Field(default_factory=list)
    mechanic_hints: list[str] = Field(default_factory=list)
    closeout_questions: list[str] = Field(default_factory=list)
    agent_reviews: list[SessionCheckpointAgentReview] = Field(default_factory=list)
    lifecycle_events: list[SessionCheckpointLifecycleEvent] = Field(default_factory=list)
    blocked_by: list[str] = Field(default_factory=list)
    review_status: Literal["unreviewed", "reviewed"] = "unreviewed"
    evidence_refs: list[str] = Field(default_factory=list)
    next_owner_moves: list[str] = Field(default_factory=list)


class SessionCheckpointPromotion(BaseModel):
    schema_version: int = 1
    session_ref: str
    target: Literal["dionysus-note", "harvest-handoff"]
    promoted_at: datetime
    promoted_at_local: str | None = None
    promoted_tz: str | None = None
    source_note_ref: str
    output_refs: list[str] = Field(default_factory=list)
    resulting_state: Literal["collecting", "reviewable", "promoted", "closed"]


class CheckpointCaptureResult(BaseModel):
    schema_version: int = 1
    mode: Literal["auto", "explicit"]
    attempted: bool = True
    appended: bool = False
    checkpoint_kind: Literal[
        "manual",
        "commit",
        "verify_green",
        "pr_opened",
        "pr_merged",
        "pause",
        "owner_followthrough",
    ] | None = None
    captured_at: datetime | None = None
    captured_at_local: str | None = None
    captured_tz: str | None = None
    reason: Literal["explicit_request", "checkpoint_signal", "no_checkpoint_signal", "auto_disabled"]
    note_ref: str | None = None
    session_end_skill_targets: list["SessionEndSkillTarget"] = Field(default_factory=list)
    session_end_next_honest_move: str | None = None
    harvest_candidate_ids: list[str] = Field(default_factory=list)
    progression_candidate_ids: list[str] = Field(default_factory=list)
    upgrade_candidate_ids: list[str] = Field(default_factory=list)
    progression_axis_signals: list[ProgressionAxisSignal] = Field(default_factory=list)
    stats_refresh_recommended: bool = False
    note: SessionCheckpointNote | None = None


class CheckpointAfterCommitReport(BaseModel):
    schema_version: int = 1
    contract_type: Literal["checkpoint_after_commit_report_v1"] = "checkpoint_after_commit_report_v1"
    status: Literal[
        "captured",
        "recorded_closed_session_followthrough",
        "recorded_reviewed_closeout_followthrough",
        "skipped_no_active_session",
        "skipped_closed_session",
        "failed",
    ]
    repo_root: str
    repo_label: str
    report_path: str
    commit_ref: str
    commit_sha: str | None = None
    commit_short_sha: str | None = None
    commit_subject: str | None = None
    commit_body: str | None = None
    changed_paths: list[str] = Field(default_factory=list)
    checkpoint_kind: Literal["commit", "owner_followthrough"] = "commit"
    mutation_surface: Literal["code", "public-share"] = "code"
    manual_review_requested: bool = True
    captured_at: datetime
    captured_at_local: str | None = None
    captured_tz: str | None = None
    session_file: str | None = None
    runtime_session_id: str | None = None
    runtime_session_created_at: datetime | None = None
    skill_report_path: str | None = None
    surface_report_path: str | None = None
    note_ref: str | None = None
    agent_review_required: bool = False
    agent_review_status: Literal["not_required", "pending", "reviewed"] = "not_required"
    agent_review_command: str | None = None
    agent_review_ref: str | None = None
    error_text: str | None = None


class CheckpointHookStatus(BaseModel):
    repo: str
    hook_name: Literal["post-commit", "pre-push", "pre-merge-commit"]
    repo_root: str
    hook_path: str
    template_path: str
    template_version: str
    status: Literal["missing", "stale", "current"]


class CheckpointHookInstallResult(BaseModel):
    repo: str
    hook_name: Literal["post-commit", "pre-push", "pre-merge-commit"]
    repo_root: str
    hook_path: str
    template_path: str
    template_version: str
    status_before: Literal["missing", "stale", "current"]
    action: Literal["installed", "updated", "unchanged"]


class CheckpointGitBoundaryCheck(BaseModel):
    repo_root: str
    repo_label: str
    boundary: Literal["push", "merge"]
    status: Literal[
        "clear",
        "clear_no_active_session",
        "clear_no_note",
        "blocked_pending_review",
        "blocked_unresolved_checkpoint",
    ]
    runtime_session_id: str | None = None
    note_ref: str | None = None
    post_commit_status_ref: str | None = None
    pending_refs: list[str] = Field(default_factory=list)
    blocking_repo_labels: list[str] = Field(default_factory=list)
    required_action: str | None = None


class CheckpointLifecycleEntry(BaseModel):
    repo_label: str
    runtime_session_id: str | None = None
    runtime_scope_key: str | None = None
    session_ref: str | None = None
    current_dir: str
    note_ref: str | None = None
    post_commit_report_ref: str | None = None
    closeout_context_ref: str | None = None
    closeout_execution_report_ref: str | None = None
    runtime_trace_ref: str | None = None
    runtime_trace_thread_id: str | None = None
    runtime_trace_status: Literal["resolved", "missing", "not_checked"] | None = None
    source_trace_ref: str | None = None
    session_memory_archive_ref: str | None = None
    session_memory_session_id: str | None = None
    session_memory_status: Literal["current", "partial", "missing", "unavailable"] | None = None
    raw_refs: list[str] = Field(default_factory=list)
    state: Literal["collecting", "reviewable", "promoted", "closed"] | None = None
    review_status: Literal["unreviewed", "reviewed"] | None = None
    agent_review_status: Literal["none", "pending", "reviewed"] | None = None
    lifecycle_state: Literal[
        "active_current",
        "pending_review",
        "session_closed_pending_review",
        "session_closed_reviewed_no_closeout",
        "session_closed_collecting_no_closeout",
        "reviewed_awaiting_closeout",
        "closeout_built",
        "closeout_executed",
        "closed",
        "stale_current_scope",
    ]
    active_runtime_scope: bool = False
    closable: bool = False
    archiveable: bool = False
    pending_refs: list[str] = Field(default_factory=list)
    blocked_by: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    required_action: str | None = None
    next_route: str | None = None
    reason: str


class CheckpointLifecycleAuditReport(BaseModel):
    schema_version: int = 1
    report_type: Literal["checkpoint_lifecycle_audit_v1"] = (
        "checkpoint_lifecycle_audit_v1"
    )
    checked_at: datetime
    checked_at_local: str | None = None
    checked_tz: str | None = None
    repo_root: str | None = None
    repo_label: str | None = None
    session_file: str | None = None
    active_runtime_session_id: str | None = None
    current_scope_count: int = 0
    note_count: int = 0
    archive_scope_count: int = 0
    closeout_context_count: int = 0
    closeout_execution_count: int = 0
    session_memory_ref_count: int = 0
    session_closed_without_closeout_count: int = 0
    pending_review_count: int = 0
    reviewed_not_closed_count: int = 0
    closable_count: int = 0
    archiveable_count: int = 0
    lifecycle_counts: dict[str, int] = Field(default_factory=dict)
    entries: list[CheckpointLifecycleEntry] = Field(default_factory=list)
    generated_index_ref: str | None = None
    notes: list[str] = Field(default_factory=list)


class CheckpointLifecycleArchiveResult(BaseModel):
    schema_version: int = 1
    report_type: Literal["checkpoint_lifecycle_archive_result_v1"] = (
        "checkpoint_lifecycle_archive_result_v1"
    )
    executed_at: datetime
    executed_at_local: str | None = None
    executed_tz: str | None = None
    dry_run: bool = True
    repo_root: str | None = None
    repo_label: str | None = None
    runtime_session_id: str | None = None
    archived_count: int = 0
    skipped_count: int = 0
    archived_entries: list[CheckpointLifecycleEntry] = Field(default_factory=list)
    skipped_entries: list[CheckpointLifecycleEntry] = Field(default_factory=list)
    archive_refs: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class CheckpointSessionReconcileResult(BaseModel):
    schema_version: int = 1
    report_type: Literal["checkpoint_session_reconcile_result_v1"] = (
        "checkpoint_session_reconcile_result_v1"
    )
    executed_at: datetime
    executed_at_local: str | None = None
    executed_tz: str | None = None
    dry_run: bool = True
    repo_root: str | None = None
    repo_label: str | None = None
    runtime_session_id: str | None = None
    session_filter: str | None = None
    since: str | None = None
    until: str | None = None
    selected_count: int = 0
    archived_count: int = 0
    skipped_count: int = 0
    required_action_count: int = 0
    archived_entries: list[CheckpointLifecycleEntry] = Field(default_factory=list)
    skipped_entries: list[CheckpointLifecycleEntry] = Field(default_factory=list)
    required_actions: list[str] = Field(default_factory=list)
    archive_refs: list[str] = Field(default_factory=list)
    generated_index_ref: str | None = None
    notes: list[str] = Field(default_factory=list)


class CheckpointBacklogEntry(BaseModel):
    schema_version: Literal["aoa_checkpoint_backlog_entry_v1"] = (
        "aoa_checkpoint_backlog_entry_v1"
    )
    repo_label: str
    runtime_session_id: str | None = None
    lifecycle_state: str
    review_status: str | None = None
    agent_review_status: str | None = None
    active_runtime_scope: bool = False
    age_days: int | None = None
    note_ref: str | None = None
    current_dir: str
    post_commit_report_ref: str | None = None
    runtime_trace_status: Literal["resolved", "missing", "not_checked"] | None = None
    runtime_trace_thread_id: str | None = None
    runtime_trace_ref: str | None = None
    source_trace_ref: str | None = None
    session_memory_status: Literal["current", "partial", "missing", "unavailable"] | None = None
    session_memory_session_id: str | None = None
    session_memory_archive_ref: str | None = None
    raw_refs: list[str] = Field(default_factory=list)
    why_open: str
    next_route: str
    required_action: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)


class CheckpointBacklogAuditReport(BaseModel):
    schema_version: int = 1
    report_type: Literal["checkpoint_backlog_audit_v1"] = "checkpoint_backlog_audit_v1"
    boundary_note: str = (
        "Backlog audit is generated navigation evidence. It does not mutate "
        ".aoa, run closeout, archive notes, promote candidates, or assign owner truth."
    )
    checked_at: datetime
    checked_at_local: str | None = None
    checked_tz: str | None = None
    repo_root: str | None = None
    repo_label: str | None = None
    active_runtime_session_id: str | None = None
    counts: dict[str, int] = Field(default_factory=dict)
    entries: list[CheckpointBacklogEntry] = Field(default_factory=list)
    generated_index_ref: str | None = None
    stop_lines: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class SessionEndSkillTarget(BaseModel):
    skill_name: Literal[
        "aoa-session-donor-harvest",
        "aoa-session-progression-lift",
        "aoa-quest-harvest",
    ]
    phase: Literal["reviewed-closeout"] = "reviewed-closeout"
    why: str
    candidate_ids: list[str] = Field(default_factory=list)


class CloseoutContextCandidateMap(BaseModel):
    harvest_candidate_ids: list[str] = Field(default_factory=list)
    progression_candidate_ids: list[str] = Field(default_factory=list)
    upgrade_candidate_ids: list[str] = Field(default_factory=list)


class CheckpointCloseoutReviewCarry(BaseModel):
    review_refs: list[str] = Field(default_factory=list)
    auto_observation_refs: list[str] = Field(default_factory=list)
    applied_skill_names: list[str] = Field(default_factory=list)
    summaries: list[str] = Field(default_factory=list)
    findings: list[str] = Field(default_factory=list)
    candidate_notes: list[str] = Field(default_factory=list)
    stats_hints: list[str] = Field(default_factory=list)
    mechanic_hints: list[str] = Field(default_factory=list)
    closeout_questions: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    next_owner_moves: list[str] = Field(default_factory=list)


class CheckpointCloseoutContext(BaseModel):
    schema_version: int = 1
    context_type: Literal["checkpoint_closeout_context_v1"] = "checkpoint_closeout_context_v1"
    execution_mode: Literal["mechanical_bridge_context"] = "mechanical_bridge_context"
    mechanical_bridge_only: bool = True
    agent_skill_application_required: bool = True
    authority_contract: Literal["reviewed_artifact_primary_checkpoint_hints_provisional"] = (
        "reviewed_artifact_primary_checkpoint_hints_provisional"
    )
    orchestrator_skill_name: Literal["aoa-checkpoint-closeout-bridge"] = (
        "aoa-checkpoint-closeout-bridge"
    )
    session_ref: str
    built_at: datetime
    built_at_local: str | None = None
    built_tz: str | None = None
    repo_root: str
    reviewed_artifact_ref: str
    runtime_session_id: str | None = None
    session_trace_ref: str | None = None
    session_trace_thread_id: str | None = None
    session_memory_ref: CheckpointSessionMemoryRef | None = None
    session_memory_freshness: CheckpointSessionMemoryFreshness = Field(
        default_factory=CheckpointSessionMemoryFreshness
    )
    checkpoint_note_ref: str | None = None
    checkpoint_note_refs: list[str] = Field(default_factory=list)
    surface_handoff_ref: str | None = None
    receipt_refs: list[str] = Field(default_factory=list)
    repo_scope: list[str] = Field(default_factory=list)
    candidate_map: CloseoutContextCandidateMap = Field(default_factory=CloseoutContextCandidateMap)
    checkpoint_review_carry: CheckpointCloseoutReviewCarry = Field(default_factory=CheckpointCloseoutReviewCarry)
    candidate_lineage_map: list[CheckpointLineageHint] = Field(default_factory=list)
    owner_followthrough_map: list[CloseoutOwnerFollowthroughHint] = Field(default_factory=list)
    followthrough_decision: CloseoutFollowthroughDecision | None = None
    progression_axis_signals: list[ProgressionAxisSignal] = Field(default_factory=list)
    ordered_skill_plan: list[SessionEndSkillTarget] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class CloseoutExecutionStep(BaseModel):
    skill_name: Literal[
        "aoa-session-donor-harvest",
        "aoa-session-progression-lift",
        "aoa-quest-harvest",
    ]
    execution_mode: Literal["mechanical_artifact_builder"] = "mechanical_artifact_builder"
    agent_skill_application_required: bool = True
    status: Literal["executed", "skipped"]
    reason: str
    artifact_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)


class CheckpointCloseoutExecutionReport(BaseModel):
    schema_version: int = 1
    report_type: Literal["checkpoint_closeout_execution_report_v1"] = (
        "checkpoint_closeout_execution_report_v1"
    )
    execution_mode: Literal["mechanical_bridge_artifact_build"] = (
        "mechanical_bridge_artifact_build"
    )
    mechanical_bridge_only: bool = True
    agent_skill_application_required: bool = True
    authority_contract: Literal["reviewed_artifact_primary_checkpoint_hints_provisional"] = (
        "reviewed_artifact_primary_checkpoint_hints_provisional"
    )
    orchestrator_skill_name: Literal["aoa-checkpoint-closeout-bridge"] = (
        "aoa-checkpoint-closeout-bridge"
    )
    session_ref: str
    executed_at: datetime
    executed_at_local: str | None = None
    executed_tz: str | None = None
    reviewed_artifact_ref: str
    runtime_session_id: str | None = None
    session_trace_ref: str | None = None
    session_trace_thread_id: str | None = None
    session_memory_ref: CheckpointSessionMemoryRef | None = None
    session_memory_freshness: CheckpointSessionMemoryFreshness = Field(
        default_factory=CheckpointSessionMemoryFreshness
    )
    checkpoint_note_ref: str | None = None
    checkpoint_note_refs: list[str] = Field(default_factory=list)
    surface_handoff_ref: str | None = None
    context_ref: str
    owner_handoff_path: str | None = None
    owner_follow_through_briefs: list["OwnerFollowThroughBrief"] = Field(default_factory=list)
    workflow_follow_through_briefs: list["WorkflowFollowThroughBrief"] = Field(default_factory=list)
    executed_skills: list[CloseoutExecutionStep] = Field(default_factory=list)
    skipped_skills: list[CloseoutExecutionStep] = Field(default_factory=list)
    produced_artifact_refs: list[str] = Field(default_factory=list)
    produced_receipt_refs: list[str] = Field(default_factory=list)
    final_stop_reason: str
