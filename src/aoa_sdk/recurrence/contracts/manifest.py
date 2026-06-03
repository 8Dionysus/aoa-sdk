from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from .base import (
    BeaconKind,
    BeaconStatus,
    EdgeKind,
    ManifestDiagnosticKind,
    ManifestDiagnosticSeverity,
    ManifestKind,
    ObservationCategory,
    ObservationInputKind,
    RouteClass,
    SignalEdgeKind,
    StrictModel,
)


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
