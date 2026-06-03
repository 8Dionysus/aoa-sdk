from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


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
    input_posture: str | None = None
    owner_truth_inputs: list[str] = Field(default_factory=list)
    authority_ceiling: str | None = None
    consumer_risk: Literal["low", "medium", "high"] | None = None
    live_state_capable: bool | None = None

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


class StatsSourceCoverageOwner(BaseModel):
    owner_repo: str
    receipt_count: int
    share_of_total_receipts: float
    coverage_class: str
    event_kind_counts: dict[str, int] = Field(default_factory=dict)
    first_observed_at: str | None = None
    last_observed_at: str | None = None


class StatsSourceCoverageSummary(BaseModel):
    schema_version: Literal["aoa_stats_source_coverage_summary_v1"]
    generated_from: StatsGeneratedFrom
    source_mode: str
    input_registry_ref: str | None = None
    expected_owner_repos: list[str] = Field(default_factory=list)
    missing_owner_repos: list[str] = Field(default_factory=list)
    unexpected_owner_repos: list[str] = Field(default_factory=list)
    active_receipt_total: int
    observed_owner_repo_count: int
    expected_owner_repo_count: int | None = None
    owner_repo_counts: dict[str, int] = Field(default_factory=dict)
    event_kind_counts: dict[str, int] = Field(default_factory=dict)
    owners: list[StatsSourceCoverageOwner] = Field(default_factory=list)
    thin_signal_flags: list[str] = Field(default_factory=list)


class StatsRegroundingAction(BaseModel):
    action_ref: str
    owner_repo: str | None = None
    target_ref: str
    action_kind: Literal["inspect_owner_truth", "inspect_source_coverage", "inspect_surface_profile"]
    reason: str


class StatsRegroundingSignal(BaseModel):
    schema_version: Literal["aoa_stats_regrounding_signal_v1"] = "aoa_stats_regrounding_signal_v1"
    surface_name: str
    surface_ref: str | None = None
    decision: Literal["clear", "reground_recommended", "reground_required"]
    phase: Literal["ingress", "in-flight", "pre-mutation", "checkpoint", "closeout"] = "ingress"
    mutation_surface: Literal["none", "code", "repo-config", "infra", "runtime", "public-share"] = "none"
    reason_codes: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    owner_truth_inputs: list[str] = Field(default_factory=list)
    authority_ceiling: str | None = None
    consumer_risk: Literal["low", "medium", "high"] | None = None
    input_posture: str | None = None
    live_state_capable: bool | None = None
    coverage_thin_signal_flags: list[str] = Field(default_factory=list)
    next_actions: list[StatsRegroundingAction] = Field(default_factory=list)
    boundary_note: str = (
        "This signal constrains derived-summary use; it is not an eval verdict "
        "and does not replace owner-local truth."
    )
