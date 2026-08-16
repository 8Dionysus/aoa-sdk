"""Public C1 control-plane facade."""

from __future__ import annotations

from pathlib import Path

from ..contracts.agent_tool_routing import (
    AgentToolRoutingDecision,
    AgentToolRoutingIntent,
)
from ..contracts.control_plane import (
    ProvenanceRef,
    RouteDecision,
    RouteExplanation,
    RouteIntent,
    RunPlan,
    RuntimeProfile,
    ScenarioArtifactBinding,
    ScenarioBinding,
    ScenarioConditionBinding,
    ScenarioRef,
)
from ..workspace.discovery import Workspace
from .planning import (
    PlanCompilationSnapshot,
    bind_scenario,
    compile_run_plan,
    load_plan_compilation_snapshot,
    resolve_scenario_ref,
)
from .routing.resolver import explain_route_decision, resolve_route_intent
from .agent_tool_routing import route_agent_tool_decision
from .routing.snapshot import (
    RoutingResolutionSnapshot,
    load_routing_resolution_snapshot,
)


class ControlPlaneAPI:
    """Resolve, bind, and compile routes without activating a capability."""

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

    def pre_tool_route(
        self, intent: AgentToolRoutingIntent
    ) -> AgentToolRoutingDecision:
        """Route one agent-tool boundary to its owner without invocation."""

        return route_agent_tool_decision(intent)

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

    def scenario_ref(self, scenario_id: str) -> ScenarioRef:
        return resolve_scenario_ref(
            self.workspace,
            scenario_id,
            self.plan_contours(),
        )

    def bind_scenario(
        self,
        decision: RouteDecision,
        scenario_id: str,
        *,
        binding_id: str,
        provenance: ProvenanceRef,
        input_refs: tuple[ProvenanceRef, ...] = (),
        input_artifact_bindings: tuple[ScenarioArtifactBinding, ...] = (),
        condition_bindings: tuple[ScenarioConditionBinding, ...] = (),
    ) -> ScenarioBinding:
        return bind_scenario(
            self.workspace,
            decision,
            scenario_id,
            self.snapshot(),
            self.plan_contours(),
            binding_id=binding_id,
            provenance=provenance,
            input_refs=input_refs,
            input_artifact_bindings=input_artifact_bindings,
            condition_bindings=condition_bindings,
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
