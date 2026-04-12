from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

class SurfaceRef(BaseModel):
    repo: str
    path: str
    kind: str


class RouterAction(BaseModel):
    enabled: bool
    surface_repo: str | None = None
    surface_file: str | None = None
    match_field: str | None = None
    section_key_field: str | None = None
    default_sections: list[str] = Field(default_factory=list)
    supported_sections: list[str] = Field(default_factory=list)


class RoutingHint(BaseModel):
    kind: str
    enabled: bool = True
    source_repo: str
    use_when: str
    actions: dict[str, RouterAction]


class RoutingOwnerLayerShortlistHint(BaseModel):
    shortlist_id: str
    signal: Literal[
        "explicit-request",
        "proof-need",
        "recall-need",
        "scenario-recurring",
        "role-posture",
        "repeated-pattern",
        "risk-gate",
    ]
    owner_repo: Literal[
        "aoa-techniques",
        "aoa-skills",
        "aoa-evals",
        "aoa-memo",
        "aoa-playbooks",
        "aoa-agents",
        "aoa-sdk",
        "aoa-stats",
        "Dionysus",
        "8Dionysus",
        "abyss-stack",
    ]
    object_kind: Literal[
        "technique",
        "skill",
        "eval",
        "memo",
        "playbook",
        "agent",
        "seed",
        "runtime_surface",
        "orientation_surface",
    ]
    target_surface: str
    inspect_surface: str | None = None
    hint_reason: str
    confidence: Literal["low", "medium", "high"] = "medium"
    ambiguity: Literal["clear", "ambiguous"] = "clear"


class RegistryEntry(BaseModel):
    kind: str
    id: str
    name: str
    repo: str
    path: str
    status: str
    summary: str
    source_type: str
    attributes: dict[str, Any] = Field(default_factory=dict)


class SurfaceCompatibilityRule(BaseModel):
    surface_id: str
    repo: str
    relative_path: str
    preferred_relative_paths: list[str] = Field(default_factory=list)
    version_field: str | None = None
    legacy_version_fields: list[str] = Field(default_factory=list)
    supported_versions: list[int | str] = Field(default_factory=list)
    expected_json_kind: Literal["object", "array", "any"] = "object"
    required_top_level_keys: list[str] = Field(default_factory=list)
    notes: str = ""


class SurfaceCompatibilityCheck(BaseModel):
    surface_id: str
    repo: str
    relative_path: str
    resolved_relative_path: str | None = None
    exists: bool = True
    compatibility_mode: Literal["versioned", "unversioned"]
    version_field: str | None = None
    supported_versions: list[int | str] = Field(default_factory=list)
    detected_version: int | str | None = None
    compatible: bool
    reason: str


class SkillCard(BaseModel):
    name: str
    display_name: str
    description: str
    short_description: str
    path: str
    trust_posture: Literal["explicit-risk", "portable-core", "project-overlay"]
    invocation_mode: Literal["explicit-only", "explicit-preferred"]
    allow_implicit_invocation: bool
    mutation_surface: Literal["none", "repo", "runtime", "sharing"]
    keywords: list[str] = Field(default_factory=list)
    recommended_install_scopes: list[str] = Field(default_factory=list)
    explicit_handles: dict[str, Any] = Field(default_factory=dict)


class SkillDisclosure(BaseModel):
    name: str
    display_name: str
    description: str
    short_description: str
    path: str
    skill_dir: str
    compatibility: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    headings_available: list[str] = Field(default_factory=list)
    section_summaries: dict[str, str] = Field(default_factory=dict)
    resource_inventory: dict[str, list[str]] = Field(default_factory=dict)
    policy: dict[str, Any] = Field(default_factory=dict)
    interface: dict[str, Any] = Field(default_factory=dict)
    runtime_contract_ref: str | None = None
    context_retention_ref: str | None = None
    trust_policy_ref: str | None = None
    collision_family: str | None = None


class SkillHostAvailability(BaseModel):
    status: Literal["host-executable", "router-only", "unknown"]
    source: Literal[
        "host-manifest",
        "host-skill-list",
        "repo-install",
        "workspace-install",
        "user-install",
        "not-provided",
    ]
    manual_fallback_allowed: bool
    reason: str


class SkillActivationRequest(BaseModel):
    skill_name: str
    session_file: str | None = None
    explicit_handle: str | None = None
    include_frontmatter: bool = False
    wrap_mode: Literal["structured", "markdown", "raw"] = "structured"


class ActiveSkillRecord(BaseModel):
    name: str
    activated_at: datetime
    activation_count: int
    protected_from_compaction: bool
    allowlist_paths: list[str] = Field(default_factory=list)
    compact_summary: str
    must_keep: list[str] = Field(default_factory=list)
    rehydration_hint: str


class SkillSession(BaseModel):
    schema_version: int
    profile: str
    session_id: str
    created_at: datetime
    updated_at: datetime
    codex_thread_id: str | None = None
    codex_rollout_path: str | None = None
    codex_thread_title: str | None = None
    codex_first_user_message: str | None = None
    codex_thread_updated_at: datetime | None = None
    active_skills: list[ActiveSkillRecord] = Field(default_factory=list)
    activation_log: list[dict[str, Any]] = Field(default_factory=list)


class PlaybookCard(BaseModel):
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
    fallback_mode: str
    expected_artifacts: list[str] = Field(default_factory=list)


class PlaybookActivationSurface(BaseModel):
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
    fallback_mode: str
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


class MemoSurface(BaseModel):
    id: str
    name: str
    surface_kind: str
    summary: str
    primary_focus: str
    recall_modes: list[str] = Field(default_factory=list)
    status: str
    temperature: str
    inspect_surface: str
    expand_surface: str
    source_path: str


class MemoCapsule(BaseModel):
    id: str
    name: str
    summary: str
    one_line_intent: str
    use_when_short: str
    do_not_use_short: str
    inputs_short: str
    outputs_short: str
    core_contract_short: str
    main_risk_short: str
    validation_short: str
    source_path: str


class MemoSection(BaseModel):
    section_id: str
    heading: str
    ordinal: int
    summary: str
    body: str


class MemoSectionBundle(BaseModel):
    id: str
    name: str
    source_path: str
    sections: list[MemoSection] = Field(default_factory=list)


class MemoObjectCard(BaseModel):
    id: str
    kind: str
    title: str
    summary: str
    temperature: str
    review_state: str
    current_recall_status: str
    authority_kind: str
    primary_recall_modes: list[str] = Field(default_factory=list)
    source_path: str
    inspect_key: str
    expand_key: str


class MemoObjectCapsule(BaseModel):
    id: str
    kind: str
    title: str
    summary: str
    recall_posture_short: str
    trust_posture_short: str
    use_when_short: str
    do_not_use_short: str
    strongest_next_source: str
    source_path: str


class MemoObjectSectionBundle(BaseModel):
    id: str
    kind: str
    title: str
    source_path: str
    sections: list[MemoSection] = Field(default_factory=list)


class MemoWritebackRule(BaseModel):
    runtime_surface: str
    runtime_refs: list[str] = Field(default_factory=list)
    target_kind: str
    writeback_class: str
    temperature_hint: str
    review_state_default: str
    requires_human_review: bool
    notes: str


class MemoWritebackMap(BaseModel):
    runtime_surface: str
    contract_type: str
    contract_id: str
    runtime_boundary: dict[str, Any] = Field(default_factory=dict)
    mapping: MemoWritebackRule
    source_files: list[str] = Field(default_factory=list)


class MemoWritebackTarget(BaseModel):
    runtime_surface: str
    target_kind: str
    writeback_class: str
    requires_human_review: bool
    review_state_default: str
    runtime_refs: list[str] = Field(default_factory=list)
    notes: str


class EvalCard(BaseModel):
    baseline_mode: str
    category: str
    claim_type: str
    eval_path: str
    export_ready: bool
    maturity_score: int
    name: str
    object_under_evaluation: str
    portability_level: str
    repeatability: str
    report_format: str
    review_required: bool
    rigor_level: str
    skill_dependencies: list[str] = Field(default_factory=list)
    status: str
    summary: str
    technique_dependencies: list[str] = Field(default_factory=list)
    validation_strength: str
    verdict_shape: str


class EvalCapsule(BaseModel):
    blind_spot_short: str
    bounded_claim_short: str
    category: str
    comparison_surface: dict[str, Any] | None = None
    do_not_use_short: str
    eval_path: str
    name: str
    proof_artifact_short: str
    skill_dependencies: list[str] = Field(default_factory=list)
    status: str
    summary: str
    technique_dependencies: list[str] = Field(default_factory=list)
    use_when_short: str
    verdict_shape: str
    what_this_does_not_prove: str


class EvalSection(BaseModel):
    heading: str
    key: str
    content_markdown: str


class EvalSectionBundle(BaseModel):
    category: str
    eval_path: str
    name: str
    sections: list[EvalSection] = Field(default_factory=list)
    status: str
    verdict_shape: str


class ComparisonEntry(BaseModel):
    baseline_mode: str
    comparison_surface: dict[str, Any]
    eval_path: str
    interpretation_boundary: str
    name: str
    proof_artifacts: dict[str, Any] = Field(default_factory=dict)
    relations: list[dict[str, Any]] = Field(default_factory=list)
    selection_summary: str
    status: str


class EvalRuntimeCandidateTemplate(BaseModel):
    template_kind: Literal["runtime_evidence_selection", "artifact_to_verdict_hook"]
    template_name: str
    playbook_id: str | None = None
    eval_anchor: str | None = None
    verdict_bundle_ref: str | None = None
    required_runtime_artifacts: list[str] = Field(default_factory=list)
    review_required: bool
    source_example_ref: str


class EvalRuntimeCandidateIntake(BaseModel):
    template_kind: Literal["runtime_evidence_selection", "artifact_to_verdict_hook"]
    template_name: str
    playbook_id: str | None = None
    eval_anchor: str | None = None
    verdict_bundle_ref: str | None = None
    required_runtime_artifacts: list[str] = Field(default_factory=list)
    review_required: bool
    review_guide_ref: str
    owner_review_refs: list[str] = Field(default_factory=list)
    candidate_acceptance_posture: str


class MemoWritebackIntakeTarget(BaseModel):
    runtime_surface: str
    target_kind: str
    writeback_class: str
    requires_human_review: bool
    review_state_default: str
    runtime_refs: list[str] = Field(default_factory=list)
    owner_review_refs: list[str] = Field(default_factory=list)
    intake_posture: str


class MemoWritebackGovernanceTarget(BaseModel):
    runtime_surface: str
    target_kind: str | None = None
    writeback_class: str | None = None
    requires_human_review: bool | None = None
    review_state_default: str | None = None
    intake_posture: str | None = None
    in_writeback_targets: bool
    in_writeback_intake: bool
    governance_passed: bool
    blockers: list[str] = Field(default_factory=list)


class TechniquePromotionReadinessEntry(BaseModel):
    technique_id: str
    technique_name: str
    status: str
    export_ready: bool
    review_required: bool
    has_canonical_readiness_note: bool
    has_adverse_effects_review: bool
    readiness_passed: bool
    blockers: list[str] = Field(default_factory=list)


class PhaseBinding(BaseModel):
    phase: Literal["route", "plan", "do", "verify", "transition", "deep", "distill"]
    tier_id: str
    role_names: list[str]
    artifact_type: str

class ArtifactEnvelope(BaseModel):
    artifact_type: str
    phase: str
    produced_by_role: str | None = None
    produced_at: datetime
    payload: dict[str, Any] = Field(default_factory=dict)
    refs: list[SurfaceRef] = Field(default_factory=list)


class KagRegistrySurface(BaseModel):
    id: str
    name: str
    status: str
    summary: str
    source_class: str
    derived_kind: str
    provenance_mode: str
    normalization_scope: str
    framework_readiness: str
    source_repos: list[str] = Field(default_factory=list)


class KagFederationRepoEntry(BaseModel):
    repo: str
    pilot_posture: str
    export_ref: str
    kind: str
    object_id: str
    entry_surface_ref: str
    adjunct_surfaces: list[dict[str, Any]] = Field(default_factory=list)
    summary_50: str
    provenance_note: str
    non_identity_boundary: str


class KagFederationSpine(BaseModel):
    pack_version: int
    pack_type: str
    source_manifest_ref: str
    source_inputs: list[dict[str, Any]] = Field(default_factory=list)
    repo_count: int
    repos: list[KagFederationRepoEntry] = Field(default_factory=list)
    bounded_output_contract: dict[str, Any] = Field(default_factory=dict)


class KagTinyBundleItem(BaseModel):
    order: int
    name: str
    role: str
    ref: str


class KagTinyConsumerBundle(BaseModel):
    bundle_version: int
    bundle_type: str
    source_manifest_ref: str
    source_inputs: list[dict[str, Any]] = Field(default_factory=list)
    bundle_item_count: int
    bundle_items: list[KagTinyBundleItem] = Field(default_factory=list)
    deferred_counterpart: dict[str, Any] = Field(default_factory=dict)


class KagRegroundingMode(BaseModel):
    mode_id: str
    used_when: str
    query_mode_hint: str
    trigger_surface_refs: list[str] = Field(default_factory=list)
    stronger_refs: list[str] = Field(default_factory=list)
    supporting_surface_refs: list[str] = Field(default_factory=list)
    preserved_fields: list[str] = Field(default_factory=list)
    reentry_note: str
    non_identity_boundary: str
    prohibited_promotions: list[str] = Field(default_factory=list)


class KagInspectResult(BaseModel):
    ok: bool = True
    surface_id: str
    registry_entry: KagRegistrySurface
    pack: dict[str, Any] = Field(default_factory=dict)
    source_files: list[str] = Field(default_factory=list)


class KagQueryModeResult(BaseModel):
    ok: bool = True
    mode: Literal["local_search", "global_search", "drift_search"]
    reasoning_scenarios: list[dict[str, Any]] = Field(default_factory=list)
    regrounding_modes: list[KagRegroundingMode] = Field(default_factory=list)
    source_files: list[str] = Field(default_factory=list)


class KagRepoEntry(BaseModel):
    repo: Literal["Tree-of-Sophia", "aoa-techniques"]
    pilot_posture: str
    export_ref: str
    kind: str
    object_id: str
    entry_surface_ref: str
    adjunct_surfaces: list[dict[str, Any]] = Field(default_factory=list)
    summary_50: str
    provenance_note: str
    non_identity_boundary: str


class GovernedRunReviewPacketManifest(BaseModel):
    artifact_kind: str
    schema_version: str
    run_id: str
    generated_at: str
    selected_playbook: dict[str, Any] | None = None
    matched_playbook_packet_contract: dict[str, Any] | None = None
    matched_eval_template_entries: list[dict[str, Any]] = Field(default_factory=list)
    matched_memo_writeback_targets: list[dict[str, Any]] = Field(default_factory=list)
    advisory_trace_ref: str | None = None
    emitted_candidate_artifact_refs: list[dict[str, Any]] = Field(default_factory=list)
    skipped_packet_kinds: list[dict[str, Any]] = Field(default_factory=list)


class GovernedRunPacketStatus(BaseModel):
    packet_kind: str
    status: Literal["emitted", "skipped", "missing", "stale"]
    artifact_refs: list[str] = Field(default_factory=list)
    reason: str | None = None


class GovernedRunReviewPacketAudit(BaseModel):
    schema_version: int
    run_id: str
    playbook_id: str
    audit_verdict: Literal["ready", "partial", "blocked"]
    review_packet_manifest_ref: str
    advisory_trace_ref: str | None = None
    packet_statuses: list[GovernedRunPacketStatus] = Field(default_factory=list)
    contract_refs: list[str] = Field(default_factory=list)
    recommended_review_targets: list[dict[str, str]] = Field(default_factory=list)
    replayable: bool
    safe_replay_command: str | None = None


class GovernedRunReviewHandoffBundle(BaseModel):
    schema_version: int
    run_id: str
    playbook_id: str
    audit_verdict: Literal["ready", "partial", "blocked"]
    replayable: bool
    playbook_intake: PlaybookReviewIntake | None = None
    eval_intake_entries: list[EvalRuntimeCandidateIntake] = Field(default_factory=list)
    memo_intake_entries: list[MemoWritebackIntakeTarget] = Field(default_factory=list)
    emitted_candidate_artifact_refs: list[dict[str, Any]] = Field(default_factory=list)
    recommended_review_targets: dict[str, list[dict[str, str]]] = Field(default_factory=dict)
    missing_or_blocked_packet_kinds: list[dict[str, Any]] = Field(default_factory=list)
    operator_next_steps: list[str] = Field(default_factory=list)


class StatsGeneratedFrom(BaseModel):
    receipt_input_paths: list[str] = Field(default_factory=list)
    total_receipts: int
    latest_observed_at: str


class StatsObjectRef(BaseModel):
    repo: str
    kind: str
    id: str
    version: str | None = None


class StatsAutomationCandidateCounts(BaseModel):
    total: int
    seed_ready: int
    checkpoint_required: int


class StatsObjectSummaryEntry(BaseModel):
    object_ref: StatsObjectRef
    receipt_count_total: int
    receipt_counts_by_event_kind: dict[str, int] = Field(default_factory=dict)
    first_observed_at: str
    last_observed_at: str
    latest_session_ref: str
    latest_run_ref: str
    evidence_ref_count: int
    latest_eval_verdict: str | None = None
    latest_progression_verdict: str | None = None
    automation_candidate_counts: StatsAutomationCandidateCounts


class StatsCoreSkillApplication(BaseModel):
    kernel_id: str
    skill_name: str
    application_count: int
    latest_observed_at: str
    latest_session_ref: str
    latest_run_ref: str
    detail_event_kind_counts: dict[str, int] = Field(default_factory=dict)


class StatsRepeatedWindow(BaseModel):
    window_id: str
    window_date: str
    total_receipts: int
    unique_objects: int
    event_counts_by_kind: dict[str, int] = Field(default_factory=dict)
    eval_result_count: int
    progression_delta_count: int
    automation_candidate_count: int
    evidence_ref_count: int


class StatsRouteProgression(BaseModel):
    route_ref: str
    total_progression_receipts: int
    latest_verdict: str
    latest_observed_at: str
    cumulative_axis_deltas: dict[str, int] = Field(default_factory=dict)
    caution_count: int
    evidence_ref_count: int


class StatsForkCalibration(BaseModel):
    route_ref: str
    decision_count: int
    chosen_branch_counts: dict[str, int] = Field(default_factory=dict)
    max_option_count: int
    realized_outcome_link_count: int
    evidence_ref_count: int
    latest_observed_at: str


class StatsAutomationPipeline(BaseModel):
    pipeline_ref: str
    candidate_count: int
    seed_ready_count: int
    checkpoint_required_count: int
    deterministic_ready_count: int
    reversible_ready_count: int
    next_artifact_hints: list[str] = Field(default_factory=list)
    evidence_ref_count: int
    latest_observed_at: str


class StatsSurfaceDetectionWindow(BaseModel):
    window_id: str
    window_date: str
    core_skill_receipt_count: int
    activated_count: int
    manual_equivalent_adjacent_count: int
    candidate_now_count: int
    candidate_later_count: int
    owner_layer_ambiguity_count: int
    adjacent_owner_repo_counts: dict[str, int] = Field(default_factory=dict)
    handoff_target_counts: dict[str, int] = Field(default_factory=dict)
    repeated_pattern_signal_count: int
    promotion_discussion_count: int
    family_entry_ref_count: int
    evidence_ref_count: int
    first_observed_at: str
    last_observed_at: str


class StatsSummarySurface(BaseModel):
    name: str
    surface_ref: str
    path: str | None = None
    schema_ref: str
    primary_question: str
    derivation_rule: str

    @model_validator(mode="before")
    @classmethod
    def _normalize_legacy_path(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value
        payload = dict(value)
        surface_ref = payload.get("surface_ref")
        legacy_path = payload.get("path")
        if not isinstance(surface_ref, str) and isinstance(legacy_path, str):
            payload["surface_ref"] = legacy_path
        if "path" not in payload and isinstance(legacy_path, str):
            payload["path"] = legacy_path
        return payload


class ProjectCoreKernelGovernanceContract(BaseModel):
    core_receipt_kind: str
    core_receipt_schema_ref: str
    detail_publisher: str
    core_publisher: str
    stats_surface: str
    application_stage: str


class ProjectCoreKernelSkillContract(BaseModel):
    skill_name: str
    detail_event_kind: str
    detail_receipt_schema_ref: str


class ProjectCoreSkillKernelSurface(BaseModel):
    schema_version: int
    source_config: str | None = None
    kernel_id: str
    owner_repo: str
    description: str | None = None
    canonical_install_profile: str
    backward_compatible_aliases: list[str] = Field(default_factory=list)
    skill_count: int | None = None
    skills: list[str] = Field(default_factory=list)
    governance_contract: ProjectCoreKernelGovernanceContract
    skill_contracts: list[ProjectCoreKernelSkillContract] = Field(default_factory=list)


class ProjectCoreOuterRingCluster(BaseModel):
    cluster_id: str
    skill_count: int | None = None
    skills: list[str] = Field(default_factory=list)


class ProjectCoreOuterRingSurface(BaseModel):
    schema_version: int
    source_config: str | None = None
    ring_id: str
    owner_repo: str
    description: str | None = None
    canonical_install_profile: str
    adjacent_kernel_id: str
    skill_count: int | None = None
    skills: list[str] = Field(default_factory=list)
    clusters: list[ProjectCoreOuterRingCluster] = Field(default_factory=list)


class ProjectCoreOuterRingReadinessEntry(BaseModel):
    skill_name: str
    cluster_id: str
    scope: str
    status: str
    invocation_mode: str
    in_repo_core_only: bool
    in_repo_project_core_outer_ring: bool
    in_user_curated_core: bool
    collision_family: str | None = None
    readiness_passed: bool
    blockers: list[str] = Field(default_factory=list)


class ProjectCoreOuterRingReadinessSurface(BaseModel):
    schema_version: int
    source_config: str | None = None
    ring_id: str
    canonical_install_profile: str
    repo_core_only_profile: str
    user_curated_core_profile: str
    skills: list[ProjectCoreOuterRingReadinessEntry] = Field(default_factory=list)


class ProjectRiskGuardRingCluster(BaseModel):
    cluster_id: str
    skill_count: int | None = None
    skills: list[str] = Field(default_factory=list)


class ProjectRiskGuardRingAdjacentOverlay(BaseModel):
    base_skill_name: str
    overlay_skill_name: str


class ProjectRiskGuardRingSurface(BaseModel):
    schema_version: int
    source_config: str | None = None
    ring_id: str
    owner_repo: str
    description: str | None = None
    canonical_install_profile: str
    backcompat_alias_profile: str
    adjacent_kernel_id: str
    adjacent_outer_ring_id: str
    skill_count: int | None = None
    skills: list[str] = Field(default_factory=list)
    clusters: list[ProjectRiskGuardRingCluster] = Field(default_factory=list)
    adjacent_overlays: list[ProjectRiskGuardRingAdjacentOverlay] = Field(default_factory=list)


class ProjectRiskGuardRingGovernanceEntry(BaseModel):
    skill_name: str
    cluster_id: str
    scope: str
    status: str
    invocation_mode: str
    in_repo_project_risk_guard_ring: bool
    in_repo_risk_explicit: bool
    in_repo_default: bool
    collision_family: str | None = None
    adjacent_overlay_skill_name: str | None = None
    adjacent_overlay_present: bool
    governance_passed: bool
    blockers: list[str] = Field(default_factory=list)


class ProjectRiskGuardRingGovernanceSurface(BaseModel):
    schema_version: int
    source_config: str | None = None
    ring_id: str
    canonical_install_profile: str
    backcompat_alias_profile: str
    repo_default_profile: str
    skills: list[ProjectRiskGuardRingGovernanceEntry] = Field(default_factory=list)


class ProjectFoundationProfileSurface(BaseModel):
    schema_version: int
    source_config: str | None = None
    foundation_id: str
    owner_repo: str
    description: str | None = None
    canonical_install_profile: str
    kernel_id: str
    outer_ring_id: str
    risk_ring_id: str
    skill_count: int | None = None
    skills: list[str] = Field(default_factory=list)
    kernel_skills: list[str] = Field(default_factory=list)
    outer_ring_skills: list[str] = Field(default_factory=list)
    risk_ring_skills: list[str] = Field(default_factory=list)


class WorkspaceBootstrapInstallStep(BaseModel):
    skill_name: str
    source_dir: str
    target_dir: str
    action: Literal["create", "replace", "unchanged", "conflict", "missing-source"]


class WorkspaceBootstrapAgentsFile(BaseModel):
    path: str
    action: Literal["write", "overwrite", "unchanged", "preserve-existing", "skipped"]


class WorkspaceBootstrapReport(BaseModel):
    workspace_root: str
    foundation_id: str
    canonical_install_profile: str
    mode: Literal["symlink", "copy"]
    strict_layout: bool
    execute_requested: bool
    overwrite: bool
    ready: bool
    executed: bool
    verified: bool | None = None
    required_repos: list[str] = Field(default_factory=list)
    missing_required_repos: list[str] = Field(default_factory=list)
    optional_repos_present: list[str] = Field(default_factory=list)
    optional_repos_missing: list[str] = Field(default_factory=list)
    install_root: str
    install_steps: list[WorkspaceBootstrapInstallStep] = Field(default_factory=list)
    agents_file: WorkspaceBootstrapAgentsFile | None = None
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)


class SkillDispatchItem(BaseModel):
    skill_name: str
    layer: Literal["kernel", "outer-ring", "risk-ring"]
    collision_family: str | None = None
    reason: str
    host_availability: SkillHostAvailability = Field(
        default_factory=lambda: SkillHostAvailability(
            status="unknown",
            source="not-provided",
            manual_fallback_allowed=False,
            reason="no host skill inventory was supplied",
        )
    )


class SkillDetectionReport(BaseModel):
    phase: Literal["ingress", "pre-mutation", "checkpoint", "closeout"]
    repo_root: str
    foundation_id: str
    activate_now: list[SkillDispatchItem] = Field(default_factory=list)
    must_confirm: list[SkillDispatchItem] = Field(default_factory=list)
    suggest_next: list[SkillDispatchItem] = Field(default_factory=list)
    host_inventory_provided: bool = False
    actionability_gaps: list[str] = Field(default_factory=list)
    blocked_actions: list[str] = Field(default_factory=list)
    closeout_chain: KernelNextStepBrief | None = None
    reasoning: list[str] = Field(default_factory=list)


class SurfaceOpportunityExecutionHint(BaseModel):
    lane: Literal[
        "skill-dispatch",
        "inspect-expand-use",
        "manual-fallback",
        "closeout-harvest",
        "defer",
    ]
    executable_now: bool = False
    requires_confirmation: bool = False
    existing_command: str | None = None
    existing_surface: str | None = None
    manual_fallback_allowed: bool = False
    manual_fallback_note: str | None = None
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
    checkpoint_should_capture: bool = False
    candidate_clusters: list["CheckpointCandidateCluster"] = Field(default_factory=list)
    promotion_recommendation: Literal["none", "local_note", "dionysus_note", "harvest_handoff"] = "none"
    blocked_by: list[str] = Field(default_factory=list)
    closeout_followups: list[str] = Field(default_factory=list)
    owner_layer_notes: list[str] = Field(default_factory=list)
    actionability_gaps: list[str] = Field(default_factory=list)


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


class CodexPlaneDeployStatusSnapshot(BaseModel):
    schema_version: Literal["aoa_sdk_codex_plane_deploy_status_snapshot_v1"] = (
        "aoa_sdk_codex_plane_deploy_status_snapshot_v1"
    )
    workspace_root: str
    trust_posture: Literal[
        "unknown",
        "root_mismatch",
        "config_inactive",
        "trusted_ready",
        "rollout_active",
        "rollback_recommended",
    ]
    latest_trust_state_ref: str
    latest_rollout_receipt_ref: str
    project_config_active: bool
    hooks_active: bool
    active_mcp_servers: list[str] = Field(default_factory=list)
    rollout_state: Literal[
        "render_only",
        "dry_run_ready",
        "applied",
        "verified",
        "drifted",
        "rollback_recommended",
    ]
    drift_detected: bool
    next_action: Literal["none", "run_doctor", "rerender", "rerollout", "rollback"]
    observed_at: datetime


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


class SessionCheckpointAgentReview(BaseModel):
    schema_version: int = 1
    review_type: Literal["agent_post_commit_checkpoint_review_v1"] = (
        "agent_post_commit_checkpoint_review_v1"
    )
    review_id: str
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
    manual_review_requested: bool = False
    commit_sha: str | None = None
    commit_short_sha: str | None = None
    agent_review_status: Literal["not_required", "pending", "reviewed"] = "not_required"
    agent_review_ref: str | None = None


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
    agent_reviews: list[SessionCheckpointAgentReview] = Field(default_factory=list)
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
    repo_root: str
    hook_path: str
    template_path: str
    template_version: str
    status: Literal["missing", "stale", "current"]


class CheckpointHookInstallResult(BaseModel):
    repo: str
    repo_root: str
    hook_path: str
    template_path: str
    template_version: str
    status_before: Literal["missing", "stale", "current"]
    action: Literal["installed", "updated", "unchanged"]


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
    checkpoint_note_ref: str | None = None
    checkpoint_note_refs: list[str] = Field(default_factory=list)
    surface_handoff_ref: str | None = None
    receipt_refs: list[str] = Field(default_factory=list)
    repo_scope: list[str] = Field(default_factory=list)
    candidate_map: CloseoutContextCandidateMap = Field(default_factory=CloseoutContextCandidateMap)
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
    checkpoint_note_ref: str | None = None
    checkpoint_note_refs: list[str] = Field(default_factory=list)
    surface_handoff_ref: str | None = None
    context_ref: str
    executed_skills: list[CloseoutExecutionStep] = Field(default_factory=list)
    skipped_skills: list[CloseoutExecutionStep] = Field(default_factory=list)
    produced_artifact_refs: list[str] = Field(default_factory=list)
    produced_receipt_refs: list[str] = Field(default_factory=list)
    final_stop_reason: str


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


class KernelNextStepBrief(BaseModel):
    kernel_id: str
    current_session_skill_names: list[str] = Field(default_factory=list)
    current_session_detail_event_kinds: list[str] = Field(default_factory=list)
    missing_kernel_skill_names: list[str] = Field(default_factory=list)
    kernel_usage_counts: dict[str, int] = Field(default_factory=dict)
    suggested_action: Literal["invoke-core-skill", "shift-to-owner-layer", "hold"]
    suggested_skill_name: str | None = None
    suggested_owner_repo: str | None = None
    reason: str
    stats_surface_ref: str


class OwnerFollowThroughBrief(BaseModel):
    source_kind: Literal["harvest-candidate", "quest-promotion"]
    unit_ref: str
    unit_name: str | None = None
    owner_repo: str
    next_surface: str
    suggested_action: Literal["draft-owner-artifact", "author-owner-artifact"]
    abstraction_shape: str | None = None
    promotion_verdict: str | None = None
    nearest_wrong_target: str | None = None
    reason: str
    evidence_refs: list[str] = Field(default_factory=list)


class WorkflowFollowThroughBrief(BaseModel):
    source_kind: Literal["kernel-next-step", "progression-caution", "diagnosis-gap"]
    skill_name: str
    suggested_action: Literal["invoke-core-skill"]
    phase: Literal["post-closeout"] = "post-closeout"
    reason: str
    evidence_refs: list[str] = Field(default_factory=list)


class CloseoutOwnerHandoff(BaseModel):
    schema_version: int
    closeout_id: str
    session_ref: str
    manifest_path: str
    generated_at: datetime
    items: list[OwnerFollowThroughBrief] = Field(default_factory=list)
    workflow_items: list[WorkflowFollowThroughBrief] = Field(default_factory=list)


class CloseoutPublisherBatch(BaseModel):
    publisher: str
    input_paths: list[str] = Field(default_factory=list)


class CloseoutManifest(BaseModel):
    schema_version: int
    closeout_id: str
    session_ref: str
    reviewed: bool
    audit_only: bool = False
    trigger: str
    batches: list[CloseoutPublisherBatch] = Field(default_factory=list)
    audit_refs: list[str] = Field(default_factory=list)
    notes: str | None = None


class CloseoutBuildRequest(BaseModel):
    schema_version: int
    closeout_id: str
    session_ref: str
    reviewed: bool
    audit_only: bool = False
    reviewed_artifact_path: str
    trigger: str
    batches: list[CloseoutPublisherBatch] = Field(default_factory=list)
    audit_refs: list[str] = Field(default_factory=list)
    notes: str | None = None


class CloseoutBuildReport(BaseModel):
    schema_version: int
    closeout_id: str
    session_ref: str
    request_path: str
    manifest_path: str
    built_at: datetime
    reviewed_artifact_path: str
    audit_only: bool = False
    enqueue_report: CloseoutEnqueueReport | None = None


class CloseoutSubmitReviewedReport(BaseModel):
    schema_version: int
    closeout_id: str
    session_ref: str
    request_path: str
    submitted_at: datetime
    reviewed_artifact_path: str
    audit_only: bool = False
    receipt_paths: list[str] = Field(default_factory=list)
    detected_publishers: list[str] = Field(default_factory=list)
    build_report: CloseoutBuildReport


class CloseoutEnqueueReport(BaseModel):
    schema_version: int
    closeout_id: str
    session_ref: str
    source_manifest_path: str
    queued_manifest_path: str
    enqueued_at: datetime
    queue_depth: int
    overwritten: bool = False


class CloseoutPublisherRun(BaseModel):
    publisher: str
    repo: str
    input_paths: list[str] = Field(default_factory=list)
    log_path: str
    command: list[str] = Field(default_factory=list)
    appended_count: int | None = None
    duplicate_skip_count: int | None = None
    stdout: str = ""


class CloseoutStatsRefresh(BaseModel):
    command: list[str] = Field(default_factory=list)
    source_count: int | None = None
    receipt_count: int | None = None
    cleared: bool = False
    feed_output: str | None = None
    summary_output_dir: str | None = None
    stdout: str = ""


class CloseoutRunReport(BaseModel):
    schema_version: int
    closeout_id: str
    session_ref: str
    manifest_path: str
    processed_at: datetime
    trigger: str
    reviewed: bool
    audit_only: bool = False
    audit_refs: list[str] = Field(default_factory=list)
    notes: str | None = None
    publisher_runs: list[CloseoutPublisherRun] = Field(default_factory=list)
    stats_refresh: CloseoutStatsRefresh
    kernel_next_step_brief: KernelNextStepBrief | None = None
    owner_handoff_path: str | None = None
    owner_follow_through_briefs: list[OwnerFollowThroughBrief] = Field(default_factory=list)
    workflow_follow_through_briefs: list[WorkflowFollowThroughBrief] = Field(default_factory=list)


class CloseoutInboxItemResult(BaseModel):
    manifest_path: str
    archived_manifest_path: str | None = None
    report_path: str | None = None
    status: Literal["processed", "failed"]
    closeout_id: str | None = None
    session_ref: str | None = None
    error: str | None = None
    kernel_next_step_brief: KernelNextStepBrief | None = None
    owner_handoff_path: str | None = None
    owner_follow_through_briefs: list[OwnerFollowThroughBrief] = Field(default_factory=list)
    workflow_follow_through_briefs: list[WorkflowFollowThroughBrief] = Field(default_factory=list)


class CloseoutInboxReport(BaseModel):
    schema_version: int
    inbox_dir: str
    processed_dir: str
    failed_dir: str
    report_dir: str
    processed_count: int
    failed_count: int
    items: list[CloseoutInboxItemResult] = Field(default_factory=list)


class CloseoutStatusReport(BaseModel):
    schema_version: int
    root_dir: str
    request_dir: str
    manifest_dir: str
    inbox_dir: str
    processed_dir: str
    failed_dir: str
    report_dir: str
    handoff_dir: str
    request_count: int
    manifest_count: int
    pending_manifest_count: int
    processed_manifest_count: int
    failed_manifest_count: int
    report_count: int
    handoff_count: int
    pending_manifest_paths: list[str] = Field(default_factory=list)
    latest_request_path: str | None = None
    latest_manifest_path: str | None = None
    latest_report_path: str | None = None
    latest_handoff_path: str | None = None
    latest_processed_manifest_path: str | None = None
    latest_failed_manifest_path: str | None = None
