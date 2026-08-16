"""Typed pre-tool routing contracts for agent responsibility boundaries.

The contract is deliberately narrower than a tool hook. It records the
current holder's typed routing input and the next owner that must be presented;
it never selects a model, transport, runtime, or tool.
"""

from __future__ import annotations

from typing import Literal, TypeAlias

from pydantic import model_validator

from .control_plane import (
    ContentRef,
    NonEmptyStr,
    ProvenanceRef,
    StrictControlPlaneModel,
)


AGENT_TOOL_ROUTING_INTENT_VERSION: Literal[
    "aoa_agent_tool_routing_intent_v1"
] = "aoa_agent_tool_routing_intent_v1"
AGENT_TOOL_ROUTING_DECISION_VERSION: Literal[
    "aoa_agent_tool_routing_decision_v1"
] = "aoa_agent_tool_routing_decision_v1"

AgentToolRoutingPhase: TypeAlias = Literal[
    "initial",
    "compaction_resume",
    "reentry",
    "plan_change",
]
AgentToolBoundaryState: TypeAlias = Literal[
    "not_present",
    "unresolved",
    "independent",
    "not_independent",
]
AgentToolNextOwner: TypeAlias = Literal[
    "none",
    "aoa-agents-skills",
    "aoa-summon",
]
AgentToolDispatchPosture: TypeAlias = Literal[
    "no_agent_tool",
    "present_responsibility_boundary",
    "invoke_role_first_entry",
    "allow_codex_local_after_classification",
]
BuiltInCodexAgentPosture: TypeAlias = Literal[
    "not_requested",
    "blocked",
    "deferred_until_classified",
]
AgentToolRouteStatus: TypeAlias = Literal[
    "not_applicable",
    "awaiting_classification",
    "owner_route",
    "compatibility_local",
]


class AgentToolRoutingIntent(StrictControlPlaneModel):
    """A current-holder request to route one possible agent-tool decision."""

    schema_version: Literal[
        "aoa_agent_tool_routing_intent_v1"
    ] = AGENT_TOOL_ROUTING_INTENT_VERSION
    intent_id: NonEmptyStr
    correlation_id: NonEmptyStr
    goal_ref: ContentRef
    current_holder_ref: ContentRef
    route_anchor: NonEmptyStr
    phase: AgentToolRoutingPhase
    agent_tool_requested: bool
    boundary_state: AgentToolBoundaryState
    responsibility_result_ref: ContentRef | None = None
    local_next_route: Literal["codex_local"] | None = None
    provenance: ProvenanceRef

    @model_validator(mode="after")
    def validate_boundary_shape(self) -> "AgentToolRoutingIntent":
        if self.route_anchor != self.goal_ref.object_id:
            raise ValueError("route_anchor must equal goal_ref.object_id")

        if not self.agent_tool_requested:
            if self.boundary_state != "not_present":
                raise ValueError(
                    "a non-agent request must use boundary_state=not_present"
                )
            if self.responsibility_result_ref is not None:
                raise ValueError(
                    "a non-agent request cannot carry a responsibility result"
                )
            if self.local_next_route is not None:
                raise ValueError(
                    "a non-agent request cannot carry a local next route"
                )
            return self

        if self.boundary_state == "not_present":
            raise ValueError(
                "an agent-tool request must present unresolved or classified responsibility"
            )

        if self.phase != "initial":
            if self.boundary_state != "unresolved":
                raise ValueError(
                    "compaction, resume, reentry, and plan change require fresh unresolved classification"
                )
            if self.responsibility_result_ref is not None:
                raise ValueError(
                    "fresh re-entry routing cannot reuse a prior responsibility result"
                )
            if self.local_next_route is not None:
                raise ValueError(
                    "fresh re-entry routing cannot carry a local next route"
                )
            return self

        if self.boundary_state == "unresolved":
            if self.responsibility_result_ref is not None:
                raise ValueError(
                    "unresolved responsibility cannot carry a classification result"
                )
            if self.local_next_route is not None:
                raise ValueError(
                    "unresolved responsibility cannot carry a local next route"
                )
        elif self.boundary_state == "independent":
            if self.responsibility_result_ref is None:
                raise ValueError(
                    "independent responsibility requires an aoa-agents result reference"
                )
            if self.responsibility_result_ref.owner_repo != "aoa-agents":
                raise ValueError(
                    "independent responsibility result must be owned by aoa-agents"
                )
            if self.local_next_route is not None:
                raise ValueError(
                    "independent responsibility cannot carry a codex-local next route"
                )
        elif self.boundary_state == "not_independent":
            result = self.responsibility_result_ref
            if result is None:
                raise ValueError(
                    "not_independent responsibility requires an aoa-agents result reference"
                )
            if result.owner_repo != "aoa-agents":
                raise ValueError(
                    "local responsibility result must be owned by aoa-agents"
                )
            if result.schema_version != "responsibility-classification-v1":
                raise ValueError(
                    "local responsibility result must use responsibility-classification-v1"
                )
            if self.local_next_route != "codex_local":
                raise ValueError(
                    "not_independent responsibility must name codex_local as its next route"
                )
        return self


class AgentToolRoutingDecision(StrictControlPlaneModel):
    """The SDK-owned next-owner posture for one pre-tool routing intent."""

    schema_version: Literal[
        "aoa_agent_tool_routing_decision_v1"
    ] = AGENT_TOOL_ROUTING_DECISION_VERSION
    decision_id: NonEmptyStr
    correlation_id: NonEmptyStr
    intent_ref: ContentRef
    status: AgentToolRouteStatus
    next_owner: AgentToolNextOwner
    dispatch_posture: AgentToolDispatchPosture
    built_in_codex_agent: BuiltInCodexAgentPosture
    must_reclassify: bool
    reason_codes: tuple[NonEmptyStr, ...]
    responsibility_result_ref: ContentRef | None = None
    resolver_version: NonEmptyStr
    provenance: ProvenanceRef
