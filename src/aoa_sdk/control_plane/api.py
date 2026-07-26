"""Public C1 control-plane facade."""

from __future__ import annotations

from pathlib import Path

from ..contracts.control_plane import (
    RouteDecision,
    RouteExplanation,
    RouteIntent,
    RunPlan,
    RuntimeProfile,
    ScenarioBinding,
)
from ..workspace.discovery import Workspace
from .planning import (
    PlanCompilationSnapshot,
    compile_run_plan,
    load_plan_compilation_snapshot,
)
from .routing.resolver import explain_route_decision, resolve_route_intent
from .routing.snapshot import (
    RoutingResolutionSnapshot,
    load_routing_resolution_snapshot,
)


class ControlPlaneAPI:
    """Resolve and explain routes without activating a capability."""

    def __init__(
        self,
        workspace: Workspace,
        *,
        routing_bundle_root: str | Path | None = None,
        routing_source_lock: str | Path | None = None,
        plan_contour_resource_root: str | Path | None = None,
    ) -> None:
        self.workspace = workspace
        self.routing_bundle_root = routing_bundle_root
        self.routing_source_lock = routing_source_lock
        self.plan_contour_resource_root = plan_contour_resource_root

    def resolve(self, intent: RouteIntent) -> RouteDecision:
        return resolve_route_intent(intent, self.snapshot())

    def explain(self, decision: RouteDecision) -> RouteExplanation:
        return explain_route_decision(decision)

    def compile(
        self,
        decision: RouteDecision,
        scenario: ScenarioBinding,
        runtime_profile: RuntimeProfile,
    ) -> RunPlan:
        return compile_run_plan(
            decision,
            scenario,
            runtime_profile,
            self.plan_contours(),
        )

    def snapshot(self) -> RoutingResolutionSnapshot:
        return load_routing_resolution_snapshot(
            self.workspace,
            routing_bundle_root=self.routing_bundle_root,
            source_lock_path=self.routing_source_lock,
        )

    def plan_contours(self) -> PlanCompilationSnapshot:
        return load_plan_compilation_snapshot(
            resource_root=self.plan_contour_resource_root,
        )
