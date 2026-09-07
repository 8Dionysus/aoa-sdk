"""Typed, optional routing for an explicitly presented AoA responsibility.

Ordinary Codex helpers do not need this contract. The compatibility pre-tool
entry records the current holder's input without acquiring native orchestration
or permission authority. A session phase is not a change of responsibility.
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
    "aoa_agent_tool_routing_intent_v2"
] = "aoa_agent_tool_routing_intent_v2"
AGENT_TOOL_ROUTING_DECISION_VERSION: Literal[
    "aoa_agent_tool_routing_decision_v2"
] = "aoa_agent_tool_routing_decision_v2"

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
    "native_codex",
    "present_responsibility_boundary",
    "invoke_role_first_entry",
    "inspect_existing_responsibility",
    "allow_codex_local_after_classification",
]
BuiltInCodexAgentPosture: TypeAlias = Literal[
    "not_requested",
    "native",
    "blocked",
    "deferred_until_classified",
]
AgentToolRouteStatus: TypeAlias = Literal[
    "not_applicable",
    "native_codex",
    "awaiting_classification",
    "owner_route",
    "compatibility_local",
]


class AgentToolRoutingIntent(StrictControlPlaneModel):
    """A current-holder responsibility request, not a prerequisite to spawn.

    V1 inputs remain readable by the passive adapter; new outputs use v2.
    Reusing an owner ref does not attest its currentness or authorize execution.
    """

    schema_version: Literal[
        "aoa_agent_tool_routing_intent_v1", "aoa_agent_tool_routing_intent_v2"
    ] = AGENT_TOOL_ROUTING_INTENT_VERSION
    intent_id: NonEmptyStr
    correlation_id: NonEmptyStr
    goal_ref: ContentRef
    current_holder_ref: ContentRef
    route_anchor: NonEmptyStr
    phase: AgentToolRoutingPhase
    agent_tool_requested: bool
    boundary_state: AgentToolBoundaryState
    responsibility_changed: bool = False
    responsibility_result_ref: ContentRef | None = None
    local_next_route: Literal["codex_local"] | None = None
    provenance: ProvenanceRef

    @model_validator(mode="after")
    def validate_boundary_shape(self) -> "AgentToolRoutingIntent":
        if self.route_anchor != self.goal_ref.object_id:
            raise ValueError("route_anchor must equal goal_ref.object_id")

        if (
            self.schema_version == "aoa_agent_tool_routing_intent_v1"
            and self.responsibility_changed
        ):
            raise ValueError("responsibility_changed requires the v2 intent contract")

        if self.responsibility_changed and self.boundary_state != "unresolved":
            raise ValueError("changed responsibility requires an unresolved boundary")

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
            if self.responsibility_result_ref is not None:
                raise ValueError(
                    "an absent responsibility boundary cannot carry a classification result"
                )
            if self.local_next_route is not None:
                raise ValueError("an absent responsibility boundary cannot carry a classified local route")
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
            if self.responsibility_result_ref.schema_version != "agent-obligation-v1":
                raise ValueError(
                    "independent responsibility result must use agent-obligation-v1"
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
    """A passive owner route; native posture is not execution permission."""

    schema_version: Literal[
        "aoa_agent_tool_routing_decision_v1", "aoa_agent_tool_routing_decision_v2"
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
