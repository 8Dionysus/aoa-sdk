from __future__ import annotations

from typing import Literal

from pydantic import Field

from .base import StrictModel


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
