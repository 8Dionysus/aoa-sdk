from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from .base import EdgeStrength, ManifestDiagnosticSeverity, RouteClass, StrictModel, SurfaceClass
from .manifest import ManifestDiagnostic


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
