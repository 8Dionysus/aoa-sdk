from __future__ import annotations

from typing import Any

from pydantic import AliasChoices, BaseModel, Field


class PlaybookCard(BaseModel):
    model_config = {"populate_by_name": True}

    id: str
    name: str
    status: str
    summary: str
    scenario: str
    trigger: str
    prerequisites: list[str] = Field(default_factory=list)
    participating_agents: list[str] = Field(default_factory=list)
    required_skill_families: list[str] = Field(default_factory=list)
    evaluation_posture: str
    memory_posture: str
    recovery_mode: str = Field(validation_alias=AliasChoices("recovery_mode", "fallback_mode"))
    expected_artifacts: list[str] = Field(default_factory=list)


class PlaybookActivationSurface(BaseModel):
    model_config = {"populate_by_name": True}

    surface_type: str
    playbook_id: str
    name: str
    scenario: str
    trigger: str
    participating_agents: list[str] = Field(default_factory=list)
    required_skill_families: list[str] = Field(default_factory=list)
    expected_artifacts: list[str] = Field(default_factory=list)
    evaluation_posture: str
    memory_posture: str
    recovery_mode: str = Field(validation_alias=AliasChoices("recovery_mode", "fallback_mode"))
    eval_anchors: list[str] = Field(default_factory=list)
    return_posture: str
    return_anchor_artifacts: list[str] = Field(default_factory=list)
    return_reentry_modes: list[str] = Field(default_factory=list)
    memo_recall_modes: list[str] = Field(default_factory=list)
    memo_scope_default: str | None = None
    memo_scope_ceiling: str | None = None
    memo_read_path: str | None = None
    memo_checkpoint_posture: str | None = None
    memo_source_route_policy: str | None = None


class PlaybookHandoffContract(BaseModel):
    playbook_id: str
    name: str
    required_skills: list[str] = Field(default_factory=list)
    upstream_skill_handoffs: list[dict[str, Any]] = Field(default_factory=list)
    decision_points: list[str] = Field(default_factory=list)
    handoffs: list[dict[str, Any]] = Field(default_factory=list)
    expected_artifacts: list[str] = Field(default_factory=list)
    return_anchor_artifacts: list[str] = Field(default_factory=list)
    handoff_packet_template: dict[str, Any] = Field(default_factory=dict)


class PlaybookFailure(BaseModel):
    code: str
    summary: str
    severity: str
    recommended_skills: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    used_by_playbooks: list[str] = Field(default_factory=list)


class PlaybookSubagentRecipe(BaseModel):
    name: str
    playbook: str
    description: str
    when_to_use: list[str] = Field(default_factory=list)
    roles: list[dict[str, Any]] = Field(default_factory=list)
    handoff_artifacts: list[str] = Field(default_factory=list)
    caution: str


class PlaybookFederationSurface(BaseModel):
    surface_type: str
    playbook_id: str
    name: str
    participating_agents: list[str] = Field(default_factory=list)
    memory_posture: str
    required_skills: list[str] = Field(default_factory=list)
    memo_contract_refs: list[str] = Field(default_factory=list)
    memo_writeback_targets: list[str] = Field(default_factory=list)
    eval_anchors: list[str] = Field(default_factory=list)
    memo_recall_modes: list[str] = Field(default_factory=list)
    memo_scope_default: str | None = None
    memo_scope_ceiling: str | None = None
    memo_read_path: str | None = None
    memo_checkpoint_posture: str | None = None
    memo_source_route_policy: str | None = None


class PlaybookAutomationSeed(BaseModel):
    name: str
    playbook: str
    title: str
    execution_mode: str
    worktree_recommended: bool
    skill_handles: list[str] = Field(default_factory=list)
    schedule_hint: str
    prompt: str


class PlaybookCompositionManifest(BaseModel):
    schema_version: int
    layer: str
    profile: str
    source_of_truth: dict[str, Any] = Field(default_factory=dict)
    generated_files: list[str] = Field(default_factory=list)
    managed_playbooks: list[str] = Field(default_factory=list)
    composition_playbook_count: int
    total_playbook_count: int


class PlaybookCompositionSignalSummary(BaseModel):
    failure_or_follow_up: str
    adjunct_candidate: str


class PlaybookReviewStatus(BaseModel):
    playbook_id: str
    playbook_name: str
    scenario: str
    gate_review_ref: str
    reviewed_run_count: int
    reviewed_run_refs: list[str] = Field(default_factory=list)
    latest_reviewed_run_ref: str | None = None
    minimum_evidence_threshold: str
    gate_verdict: str
    next_trigger: str
    composition_signal_summary: PlaybookCompositionSignalSummary


class PlaybookReviewPacketContract(BaseModel):
    playbook_id: str
    playbook_name: str
    scenario: str
    expected_artifacts: list[str] = Field(default_factory=list)
    eval_anchors: list[str] = Field(default_factory=list)
    memo_runtime_surfaces: list[str] = Field(default_factory=list)
    candidate_packet_kinds: list[str] = Field(default_factory=list)
    review_required: bool
    source_review_refs: list[str] = Field(default_factory=list)
    gate_verdict: str | None = None


class PlaybookReviewOutcomeTargets(BaseModel):
    real_runs: list[str] = Field(default_factory=list)
    gate_reviews: list[str] = Field(default_factory=list)


class PlaybookReviewIntake(BaseModel):
    playbook_id: str
    playbook_name: str
    scenario: str
    gate_verdict: str | None = None
    gate_review_ref: str | None = None
    real_run_template_ref: str | None = None
    required_artifact_set: list[str] = Field(default_factory=list)
    accepted_packet_kinds: list[str] = Field(default_factory=list)
    source_review_refs: list[str] = Field(default_factory=list)
    review_outcome_targets: PlaybookReviewOutcomeTargets
    composition_posture: str


class PlaybookLandingGovernanceEntry(BaseModel):
    playbook_id: str
    playbook_name: str | None = None
    registry_status: str | None = None
    in_registry: bool
    in_review_packet_contracts: bool
    in_review_intake: bool
    in_review_status: bool
    in_composition_manifest: bool
    gate_verdict: str | None = None
    landing_passed: bool
    blockers: list[str] = Field(default_factory=list)
