from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


EdgeKind = Literal[
    "owns",
    "generates",
    "projects_to",
    "validated_by",
    "documents",
    "evaluated_by",
    "routes_via",
    "summarized_by",
    "donates_to_kag",
    "requires_regrounding",
    "handoff_home",
]

RouteClass = Literal[
    "observe",
    "revalidate",
    "rebuild",
    "reexport",
    "regenerate",
    "reproject",
    "repair",
    "reroute",
    "restat",
    "reground",
    "handoff",
    "defer",
]

SurfaceClass = Literal[
    "source",
    "generated",
    "projected",
    "contract",
    "docs",
    "test",
    "proof",
    "receipt",
    "other",
]

ObservationInputKind = Literal[
    "change_signal",
    "receipt",
    "closeout",
    "evaluation_matrix",
    "trigger_eval",
    "review_note",
    "runtime_artifact",
    "harvest",
    "other",
]

ObservationCategory = Literal[
    "change_pressure",
    "evidence_pressure",
    "usage_gap",
    "repeat_pattern",
    "review_signal",
    "overclaim_risk",
]

BeaconStatus = Literal["hint", "watch", "candidate", "review_ready"]

BeaconKind = Literal[
    "new_technique_candidate",
    "technique_overlap_hold",
    "canonical_pressure",
    "unused_skill_opportunity",
    "skill_trigger_drift",
    "skill_bundle_candidate",
    "portable_eval_candidate",
    "progression_evidence_candidate",
    "overclaim_alarm",
    "playbook_candidate",
    "subagent_recipe_candidate",
    "automation_seed_candidate",
]

SignalEdgeKind = Literal[
    "implemented_by_skill",
    "proved_by_eval",
    "composed_by_playbook",
    "incubated_by_technique",
    "documents_decision",
    "summarized_by",
]

HookEvent = Literal[
    "manual_run",
    "session_start",
    "user_prompt_submit",
    "session_stop",
    "receipt_published",
    "generated_surface_refreshed",
    "harvest_written",
    "real_run_published",
    "gate_review_written",
    "runtime_evidence_selected",
]

HookProducerKind = Literal[
    "jsonl_receipt_watch",
    "skill_trigger_gap_watch",
    "harvest_pattern_watch",
    "runtime_candidate_watch",
]

HookMatchMode = Literal["always", "exists", "equals", "contains"]


class StrictModel(BaseModel):
    model_config = {
        "extra": "forbid",
        "populate_by_name": True,
    }


class RefreshRoute(StrictModel):
    action: RouteClass
    commands: list[str] = Field(default_factory=list)
    notes: str = ""


class ConsumerEdge(StrictModel):
    kind: EdgeKind
    target: str
    target_repo: str | None = None
    required: bool = True
    suggested_action: RouteClass | None = None
    suggested_commands: list[str] = Field(default_factory=list)
    notes: str = ""


class DriftSignalRule(StrictModel):
    signal: str
    recommended_action: RouteClass
    severity: Literal["low", "medium", "high"] = "medium"


class FreshnessWindow(StrictModel):
    stale_after_days: int | None = None
    repeat_trigger_threshold: int | None = None
    open_window_days: int | None = None


class SignalEdge(StrictModel):
    kind: SignalEdgeKind
    target: str
    target_repo: str | None = None
    notes: str = ""


class ObservationInputSpec(StrictModel):
    input_ref: str
    kind: ObservationInputKind
    path_globs: list[str] = Field(default_factory=list)
    notes: str = ""


class BeaconThresholds(StrictModel):
    watch_observations: int = 1
    candidate_observations: int = 2
    review_ready_observations: int = 3
    min_unique_sources: int = 1
    min_unique_evidence_refs: int = 1


def _default_status_ladder() -> list[BeaconStatus]:
    return ["hint", "watch", "candidate", "review_ready"]


class BeaconRule(StrictModel):
    beacon_ref: str
    kind: BeaconKind
    decision_surface: str | None = None
    target_repo: str | None = None
    observation_inputs: list[str] = Field(default_factory=list)
    match_signals: list[str] = Field(default_factory=list)
    match_categories: list[ObservationCategory] = Field(default_factory=list)
    thresholds: BeaconThresholds = Field(default_factory=BeaconThresholds)
    status_ladder: list[BeaconStatus] = Field(default_factory=_default_status_ladder)
    suppress_when: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    notes: str = ""


class RecurrenceComponent(StrictModel):
    schema_version: Literal[
        "aoa_recurrence_component_v1",
        "aoa_recurrence_component_v2",
    ] = "aoa_recurrence_component_v2"
    component_ref: str
    owner_repo: str
    description: str = ""
    source_inputs: list[str] = Field(default_factory=list)
    generated_surfaces: list[str] = Field(default_factory=list)
    projected_surfaces: list[str] = Field(default_factory=list)
    contract_surfaces: list[str] = Field(default_factory=list)
    documentation_surfaces: list[str] = Field(default_factory=list)
    test_surfaces: list[str] = Field(default_factory=list)
    proof_surfaces: list[str] = Field(default_factory=list)
    receipt_surfaces: list[str] = Field(default_factory=list)
    refresh_routes: list[RefreshRoute] = Field(default_factory=list)
    consumer_edges: list[ConsumerEdge] = Field(default_factory=list)
    drift_signals: list[DriftSignalRule] = Field(default_factory=list)
    freshness: FreshnessWindow = Field(default_factory=FreshnessWindow)
    rollback_anchors: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    signal_edges: list[SignalEdge] = Field(default_factory=list)
    observation_inputs: list[ObservationInputSpec] = Field(default_factory=list)
    beacon_rules: list[BeaconRule] = Field(default_factory=list)
    decision_surfaces: list[str] = Field(default_factory=list)
    candidate_targets: list[str] = Field(default_factory=list)


class ChangedPath(StrictModel):
    repo: str
    path: str
    matched_component_refs: list[str] = Field(default_factory=list)
    matched_classes: list[SurfaceClass] = Field(default_factory=list)


class MatchedComponent(StrictModel):
    component_ref: str
    owner_repo: str
    match_class: SurfaceClass
    matched_paths: list[str] = Field(default_factory=list)
    inferred_signals: list[str] = Field(default_factory=list)


class ChangeSignal(StrictModel):
    schema_version: Literal["aoa_change_signal_v1"] = "aoa_change_signal_v1"
    signal_ref: str
    workspace_root: str
    repo_root: str
    repo_name: str | None = None
    observed_at: datetime
    diff_base: str | None = None
    changed_paths: list[ChangedPath] = Field(default_factory=list)
    direct_components: list[MatchedComponent] = Field(default_factory=list)
    unmatched_paths: list[str] = Field(default_factory=list)


class PlanStep(StrictModel):
    step_ref: str
    order: int
    component_ref: str
    owner_repo: str
    action: RouteClass
    reason: str
    surface_refs: list[str] = Field(default_factory=list)
    commands: list[str] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list)
    review_required: bool = True
    status: Literal["planned", "blocked"] = "planned"


class PropagationPlan(StrictModel):
    schema_version: Literal["aoa_propagation_plan_v1"] = "aoa_propagation_plan_v1"
    plan_ref: str
    signal_ref: str
    workspace_root: str
    direct_components: list[str] = Field(default_factory=list)
    impacted_components: list[str] = Field(default_factory=list)
    impacted_targets: list[str] = Field(default_factory=list)
    ordered_steps: list[PlanStep] = Field(default_factory=list)
    unresolved_edges: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    summary: str = ""


class ReturnTarget(StrictModel):
    owner_repo: str
    component_ref: str | None = None
    target: str
    target_kind: Literal["source", "contract", "docs", "route", "summary", "playbook"]
    reason: str


class ReturnHandoff(StrictModel):
    schema_version: Literal["aoa_return_handoff_v1"] = "aoa_return_handoff_v1"
    handoff_ref: str
    plan_ref: str
    reviewed: Literal[True] = True
    surviving_fields: list[str] = Field(default_factory=list)
    targets: list[ReturnTarget] = Field(default_factory=list)
    unresolved_items: list[str] = Field(default_factory=list)


class ConnectivityGap(StrictModel):
    gap_ref: str
    severity: Literal["low", "medium", "high"]
    gap_kind: Literal[
        "unmapped_changed_path",
        "unresolved_edge",
        "missing_refresh_route",
        "missing_proof_surface",
        "orphan_generated_surface",
        "projected_without_generation",
        "weak_owner_handoff",
        "missing_target_route",
    ]
    component_ref: str | None = None
    owner_repo: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    recommendation: str


class ConnectivityGapReport(StrictModel):
    schema_version: Literal["aoa_connectivity_gap_report_v1"] = "aoa_connectivity_gap_report_v1"
    report_ref: str
    workspace_root: str
    signal_ref: str | None = None
    components_checked: list[str] = Field(default_factory=list)
    gaps: list[ConnectivityGap] = Field(default_factory=list)


class ObservationRecord(StrictModel):
    observation_ref: str
    component_ref: str
    owner_repo: str
    observed_at: datetime
    category: ObservationCategory
    signal: str
    source_inputs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    attributes: dict[str, Any] = Field(default_factory=dict)
    notes: str = ""


class ObservationPacket(StrictModel):
    schema_version: Literal["aoa_observation_packet_v1"] = "aoa_observation_packet_v1"
    packet_ref: str
    workspace_root: str
    signal_ref: str | None = None
    observations: list[ObservationRecord] = Field(default_factory=list)


class HookSignalRule(StrictModel):
    signal: str
    category: ObservationCategory
    match: HookMatchMode = "always"
    field: str | None = None
    value: Any | None = None
    source_inputs: list[str] = Field(default_factory=list)
    attributes_from_fields: list[str] = Field(default_factory=list)
    notes: str = ""


class HookBinding(StrictModel):
    binding_ref: str
    event: HookEvent
    producer: HookProducerKind
    component_ref: str
    owner_repo: str
    input_ref: str
    path_globs: list[str] = Field(default_factory=list)
    config: dict[str, Any] = Field(default_factory=dict)
    signal_rules: list[HookSignalRule] = Field(default_factory=list)
    notes: str = ""


class HookBindingSet(StrictModel):
    schema_version: Literal["aoa_hook_binding_set_v1"] = "aoa_hook_binding_set_v1"
    component_ref: str
    owner_repo: str
    bindings: list[HookBinding] = Field(default_factory=list)
    notes: str = ""


class HookRunWarning(StrictModel):
    binding_ref: str
    message: str
    paths: list[str] = Field(default_factory=list)


class HookRunReport(StrictModel):
    schema_version: Literal["aoa_hook_run_report_v1"] = "aoa_hook_run_report_v1"
    run_ref: str
    workspace_root: str
    event: HookEvent
    signal_ref: str | None = None
    bindings_run: list[str] = Field(default_factory=list)
    missing_paths: list[str] = Field(default_factory=list)
    warnings: list[HookRunWarning] = Field(default_factory=list)
    observations: list[ObservationRecord] = Field(default_factory=list)


class BeaconEntry(StrictModel):
    beacon_ref: str
    kind: BeaconKind
    status: BeaconStatus
    component_ref: str
    owner_repo: str
    target_repo: str
    decision_surface: str | None = None
    reason: str
    evidence_refs: list[str] = Field(default_factory=list)
    source_inputs: list[str] = Field(default_factory=list)
    related_signals: list[str] = Field(default_factory=list)
    suppression_flags: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)


class BeaconPacket(StrictModel):
    schema_version: Literal["aoa_beacon_packet_v1"] = "aoa_beacon_packet_v1"
    packet_ref: str
    workspace_root: str
    signal_ref: str | None = None
    entries: list[BeaconEntry] = Field(default_factory=list)


class CandidateLedgerEntry(StrictModel):
    entry_ref: str
    recorded_at: datetime
    beacon_ref: str
    kind: BeaconKind
    status: BeaconStatus
    component_ref: str
    owner_repo: str
    target_repo: str
    decision_surface: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    source_inputs: list[str] = Field(default_factory=list)
    notes: str = ""


class CandidateLedger(StrictModel):
    schema_version: Literal["aoa_candidate_ledger_v1"] = "aoa_candidate_ledger_v1"
    ledger_ref: str
    workspace_root: str
    signal_ref: str | None = None
    entries: list[CandidateLedgerEntry] = Field(default_factory=list)


class UsageGapItem(StrictModel):
    gap_ref: str
    component_ref: str
    owner_repo: str
    beacon_ref: str
    status: BeaconStatus
    reason: str
    decision_surface: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)


class UsageGapReport(StrictModel):
    schema_version: Literal["aoa_usage_gap_report_v1"] = "aoa_usage_gap_report_v1"
    report_ref: str
    workspace_root: str
    signal_ref: str | None = None
    items: list[UsageGapItem] = Field(default_factory=list)
