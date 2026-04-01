from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

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
    version_field: str | None = None
    supported_versions: list[int | str] = Field(default_factory=list)
    notes: str = ""


class SurfaceCompatibilityCheck(BaseModel):
    surface_id: str
    repo: str
    relative_path: str
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
