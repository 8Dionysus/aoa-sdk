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

ManifestKind = Literal[
    "recurrence_component",
    "hook_binding_set",
    "agon_recurrence_adapter",
    "review_surface",
    "rollout_bundle",
    "wiring_plan",
    "unknown",
]

ManifestDiagnosticKind = Literal[
    "loaded_manifest",
    "known_foreign_manifest",
    "adapter_required",
    "manifest_json_error",
    "invalid_manifest_shape",
    "unknown_manifest_kind",
    "owner_repo_mismatch",
]

ManifestDiagnosticSeverity = Literal["low", "medium", "high", "critical"]
EdgeStrength = Literal["required", "recommended", "advisory", "forbidden"]


class StrictModel(BaseModel):
    model_config = {
        "extra": "forbid",
        "populate_by_name": True,
    }


class ManifestDiagnostic(StrictModel):
    manifest_ref: str
    repo: str
    path: str
    manifest_kind: ManifestKind = "unknown"
    diagnostic_kind: ManifestDiagnosticKind
    severity: ManifestDiagnosticSeverity
    message: str
    evidence: dict[str, Any] = Field(default_factory=dict)


class ManifestScanReport(StrictModel):
    schema_version: Literal["aoa_manifest_scan_report_v1"] = (
        "aoa_manifest_scan_report_v1"
    )
    report_ref: str
    workspace_root: str
    loaded_components: list[str] = Field(default_factory=list)
    foreign_manifests: list[str] = Field(default_factory=list)
    diagnostics: list[ManifestDiagnostic] = Field(default_factory=list)
    by_kind: dict[str, int] = Field(default_factory=dict)
    by_severity: dict[str, int] = Field(default_factory=dict)


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
    manifest_kind: Literal["recurrence_component"] = "recurrence_component"
    schema_version: Literal[
        "aoa_recurrence_component_v1",
        "aoa_recurrence_component_v2",
        "aoa_recurrence_component_v3",
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
    batch_order: int = 0
    graph_depth: int = 0
    edge_strength: EdgeStrength = "required"


class PropagationBatch(StrictModel):
    batch_ref: str
    order: int
    step_refs: list[str] = Field(default_factory=list)
    depends_on_batch_refs: list[str] = Field(default_factory=list)
    rationale: str = ""


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
    graph_closure_ref: str | None = None
    propagation_batches: list[PropagationBatch] = Field(default_factory=list)
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
    severity: ManifestDiagnosticSeverity
    gap_kind: Literal[
        "unmapped_changed_path",
        "unresolved_edge",
        "missing_refresh_route",
        "missing_proof_surface",
        "orphan_generated_surface",
        "projected_without_generation",
        "weak_owner_handoff",
        "missing_target_route",
        "manifest_json_error",
        "invalid_manifest_shape",
        "unknown_manifest_kind",
        "foreign_manifest_requires_adapter",
        "owner_repo_mismatch",
        "graph_cycle",
        "graph_depth_limit_reached",
        "graph_snapshot_delta_missing",
    ]
    component_ref: str | None = None
    owner_repo: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    recommendation: str


class ConnectivityGapReport(StrictModel):
    schema_version: Literal["aoa_connectivity_gap_report_v1"] = (
        "aoa_connectivity_gap_report_v1"
    )
    report_ref: str
    workspace_root: str
    signal_ref: str | None = None
    components_checked: list[str] = Field(default_factory=list)
    gaps: list[ConnectivityGap] = Field(default_factory=list)
    manifest_diagnostics: list[ManifestDiagnostic] = Field(default_factory=list)


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
    manifest_kind: Literal["hook_binding_set"] = "hook_binding_set"
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


ProjectionTargetRepo = Literal["aoa-routing", "aoa-stats", "aoa-kag"]
ProjectionPosture = Literal["hint_only", "derived_summary_only", "regrounding_only"]
ProjectionGuardSeverity = Literal["warning", "blocked", "critical"]
ProjectionGuardViolationKind = Literal[
    "routing_authority_transfer",
    "routing_full_graph_export",
    "stats_verdict_transfer",
    "stats_source_truth_claim",
    "kag_canon_transfer",
    "kag_graph_sovereign_claim",
    "mutation_request",
]
KagRegroundingMode = Literal[
    "source_export_reentry",
    "bridge_axis_reentry",
    "projection_boundary_reentry",
    "handoff_guardrail_reentry",
    "owner_boundary_reentry",
]


class DownstreamProjectionSurface(StrictModel):
    surface_ref: str
    target_repo: ProjectionTargetRepo
    path: str
    posture: ProjectionPosture
    source_packet_refs: list[str] = Field(default_factory=list)
    notes: str = ""


class RoutingOwnerHint(StrictModel):
    hint_ref: str
    owner_repo: str
    component_ref: str | None = None
    reason: str
    inspect_surfaces: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    advisory_only: Literal[True] = True


class RoutingReturnHint(StrictModel):
    hint_ref: str
    owner_repo: str
    component_ref: str | None = None
    target: str
    target_kind: str
    reason: str
    source_refs: list[str] = Field(default_factory=list)
    advisory_only: Literal[True] = True


class RoutingGapHint(StrictModel):
    hint_ref: str
    gap_kind: str
    severity: str
    owner_repo: str | None = None
    component_ref: str | None = None
    recommendation: str
    evidence_refs: list[str] = Field(default_factory=list)
    advisory_only: Literal[True] = True


class RecurrenceRoutingProjection(StrictModel):
    schema_version: Literal["aoa_recurrence_routing_projection_v1"] = (
        "aoa_recurrence_routing_projection_v1"
    )
    projection_ref: str
    workspace_root: str
    source_packet_refs: list[str] = Field(default_factory=list)
    owner_hints: list[RoutingOwnerHint] = Field(default_factory=list)
    return_hints: list[RoutingReturnHint] = Field(default_factory=list)
    gap_hints: list[RoutingGapHint] = Field(default_factory=list)
    boundary_notes: list[str] = Field(default_factory=list)


class StatsRecurrenceCountBucket(StrictModel):
    name: str
    total: int
    by_kind: dict[str, int] = Field(default_factory=dict)
    by_owner: dict[str, int] = Field(default_factory=dict)
    by_status: dict[str, int] = Field(default_factory=dict)
    by_severity: dict[str, int] = Field(default_factory=dict)


class RecurrenceStatsProjection(StrictModel):
    schema_version: Literal["aoa_recurrence_stats_projection_v1"] = (
        "aoa_recurrence_stats_projection_v1"
    )
    projection_ref: str
    workspace_root: str
    source_packet_refs: list[str] = Field(default_factory=list)
    coverage: StatsRecurrenceCountBucket
    gaps: StatsRecurrenceCountBucket
    beacons: StatsRecurrenceCountBucket
    review: StatsRecurrenceCountBucket
    decisions: StatsRecurrenceCountBucket
    surface_strength: Literal["derived_observability_only"] = (
        "derived_observability_only"
    )
    boundary_notes: list[str] = Field(default_factory=list)


class KagDonorRefreshObligation(StrictModel):
    obligation_ref: str
    owner_repo: str
    component_ref: str | None = None
    donor_surface_refs: list[str] = Field(default_factory=list)
    reason: str
    mode: KagRegroundingMode = "owner_boundary_reentry"


class KagRetrievalInvalidationHint(StrictModel):
    hint_ref: str
    affected_surface_ref: str
    reason: str
    replacement_source_refs: list[str] = Field(default_factory=list)
    mode: KagRegroundingMode = "projection_boundary_reentry"


class KagSourceStrengthHint(StrictModel):
    hint_ref: str
    owner_repo: str
    stronger_source_refs: list[str] = Field(default_factory=list)
    weaker_derived_refs: list[str] = Field(default_factory=list)
    reason: str
    mode: KagRegroundingMode = "source_export_reentry"


class RecurrenceKagProjection(StrictModel):
    schema_version: Literal["aoa_recurrence_kag_projection_v1"] = (
        "aoa_recurrence_kag_projection_v1"
    )
    projection_ref: str
    workspace_root: str
    source_packet_refs: list[str] = Field(default_factory=list)
    donor_refresh_obligations: list[KagDonorRefreshObligation] = Field(
        default_factory=list
    )
    retrieval_invalidation_hints: list[KagRetrievalInvalidationHint] = Field(
        default_factory=list
    )
    source_strength_hints: list[KagSourceStrengthHint] = Field(default_factory=list)
    regrounding_modes: list[KagRegroundingMode] = Field(default_factory=list)
    boundary_notes: list[str] = Field(default_factory=list)


class ProjectionGuardViolation(StrictModel):
    violation_ref: str
    target_repo: ProjectionTargetRepo
    kind: ProjectionGuardViolationKind
    severity: ProjectionGuardSeverity
    message: str
    evidence_refs: list[str] = Field(default_factory=list)
    recommended_action: str


class DownstreamProjectionGuardReport(StrictModel):
    schema_version: Literal["aoa_downstream_projection_guard_report_v1"] = (
        "aoa_downstream_projection_guard_report_v1"
    )
    report_ref: str
    workspace_root: str
    source_packet_refs: list[str] = Field(default_factory=list)
    violations: list[ProjectionGuardViolation] = Field(default_factory=list)
    boundary_notes: list[str] = Field(default_factory=list)


class DownstreamProjectionBundle(StrictModel):
    schema_version: Literal["aoa_downstream_projection_bundle_v1"] = (
        "aoa_downstream_projection_bundle_v1"
    )
    bundle_ref: str
    workspace_root: str
    source_packet_refs: list[str] = Field(default_factory=list)
    surfaces: list[DownstreamProjectionSurface] = Field(default_factory=list)
    routing: RecurrenceRoutingProjection | None = None
    stats: RecurrenceStatsProjection | None = None
    kag: RecurrenceKagProjection | None = None
    guard_report: DownstreamProjectionGuardReport
    boundary_notes: list[str] = Field(default_factory=list)


WiringScope = Literal[
    "session_start",
    "user_prompt_submit",
    "session_stop",
    "pre_commit",
    "pre_push",
    "ci",
]

RolloutPhase = Literal[
    "prepared",
    "activated",
    "monitoring",
    "repairing",
    "rollback_open",
    "rolled_back",
]


class WiringSnippet(StrictModel):
    snippet_ref: str
    scope: WiringScope
    title: str
    target_path: str
    commands: list[str] = Field(default_factory=list)
    notes: str = ""


class WiringPlan(StrictModel):
    schema_version: Literal["aoa_wiring_plan_v1"] = "aoa_wiring_plan_v1"
    plan_ref: str
    workspace_root: str
    snippets: list[WiringSnippet] = Field(default_factory=list)


class DriftTrigger(StrictModel):
    signal: str
    severity: Literal["low", "medium", "high"]
    source: str
    notes: str = ""


class RolloutWindow(StrictModel):
    window_ref: str
    campaign_ref: str
    phase: RolloutPhase
    title: str
    wiring_scopes: list[WiringScope] = Field(default_factory=list)
    review_surfaces: list[str] = Field(default_factory=list)
    guard_commands: list[str] = Field(default_factory=list)
    drift_triggers: list[DriftTrigger] = Field(default_factory=list)
    rollback_anchors: list[str] = Field(default_factory=list)
    notes: str = ""


class RolloutWindowBundle(StrictModel):
    schema_version: Literal["aoa_rollout_window_bundle_v1"] = (
        "aoa_rollout_window_bundle_v1"
    )
    bundle_ref: str
    workspace_root: str
    wiring_plan_ref: str
    campaign_window: RolloutWindow
    drift_review_window: RolloutWindow
    rollback_followthrough_window: RolloutWindow
