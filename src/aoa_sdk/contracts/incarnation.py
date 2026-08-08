"""Runtime-neutral binding of one role obligation to one model realization.

The SDK owns the binding shape and its cross-object validation. Role meaning,
model knowledge, runtime execution, proof, acceptance, and external effects
remain with their stronger owners.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from .control_plane import (
    ContentRef,
    Digest,
    NonEmptyStr,
    ProvenanceRef,
    StrictControlPlaneModel,
)


AGENT_INCARNATION_BINDING_VERSION: Literal[
    "aoa_agent_incarnation_binding_v1"
] = "aoa_agent_incarnation_binding_v1"


class IncarnationPermissionPosture(StrictControlPlaneModel):
    """Exact effect and sandbox ceiling requested for one incarnation."""

    sandbox_mode: Literal["read_only", "workspace_write", "danger_full_access"]
    approval_policy: Literal["never", "on_request", "on_failure", "untrusted"]
    allowed_effect_classes: tuple[
        Literal["read_only", "repo_mutation", "runtime_mutation", "external"], ...
    ] = Field(min_length=1)
    network_access: Literal["disabled", "allowlisted", "enabled"]
    secret_access: bool = False
    external_effects: bool = False

    @model_validator(mode="after")
    def validate_effect_ceiling(self) -> IncarnationPermissionPosture:
        if len(self.allowed_effect_classes) != len(set(self.allowed_effect_classes)):
            raise ValueError("incarnation effect classes must be unique")
        if self.external_effects != ("external" in self.allowed_effect_classes):
            raise ValueError(
                "external_effects must exactly match the external effect-class ceiling"
            )
        if self.sandbox_mode == "read_only" and set(self.allowed_effect_classes) != {
            "read_only"
        }:
            raise ValueError("read_only sandbox may admit read_only effects only")
        if self.secret_access and self.approval_policy == "never":
            raise ValueError("secret access cannot use approval_policy=never")
        return self


class IncarnationToolProfile(StrictControlPlaneModel):
    """Owner-qualified tool surface; no implicit user configuration."""

    profile_id: NonEmptyStr
    profile_ref: ProvenanceRef
    required_tool_ids: tuple[NonEmptyStr, ...] = Field(min_length=1)
    required_mcp_server_ids: tuple[NonEmptyStr, ...] = ()
    inherit_user_configuration: Literal[False] = False

    @model_validator(mode="after")
    def validate_unique_tools(self) -> IncarnationToolProfile:
        if len(self.required_tool_ids) != len(set(self.required_tool_ids)):
            raise ValueError("required tool ids must be unique")
        if len(self.required_mcp_server_ids) != len(
            set(self.required_mcp_server_ids)
        ):
            raise ValueError("required MCP server ids must be unique")
        return self


class IncarnationUsageMetering(StrictControlPlaneModel):
    """Observe actual agent usage without turning observations into ceilings."""

    mode: Literal["observe_only"] = "observe_only"
    execution_limit_policy: Literal["none"] = "none"
    metering_regime: NonEmptyStr
    dimensions: tuple[
        Literal[
            "input_tokens",
            "cached_input_tokens",
            "output_tokens",
            "active_wall_seconds",
            "turn_count",
            "output_bytes",
            "executed_commands",
        ],
        ...,
    ] = Field(min_length=7, max_length=7)
    cost_interpretation: Literal["measurement_owner"] = "measurement_owner"

    @model_validator(mode="after")
    def validate_complete_observation_set(self) -> IncarnationUsageMetering:
        expected = {
            "input_tokens",
            "cached_input_tokens",
            "output_tokens",
            "active_wall_seconds",
            "turn_count",
            "output_bytes",
            "executed_commands",
        }
        if set(self.dimensions) != expected or len(self.dimensions) != len(expected):
            raise ValueError("incarnation metering must count every runtime dimension")
        return self


class IncarnationStopCondition(StrictControlPlaneModel):
    condition_id: NonEmptyStr
    kind: Literal[
        "authority_boundary",
        "scope_boundary",
        "validation_failure",
        "ambiguity",
        "external_effect_required",
        "runtime_failure",
        "custom",
    ]
    description: NonEmptyStr
    terminal: bool = True


class WakeCondition(StrictControlPlaneModel):
    condition_id: NonEmptyStr
    event_kind: NonEmptyStr
    action: Literal[
        "continue_without_parent",
        "activate_review_role",
        "wake_parent",
        "stop",
    ]
    description: NonEmptyStr


class WakeEscalationPolicy(StrictControlPlaneModel):
    """Event-shaped re-entry policy; child completion alone has no fixed action."""

    mode: Literal["event_filtered_reentry"] = "event_filtered_reentry"
    default_action: Literal[
        "continue_without_parent", "activate_review_role", "wake_parent", "stop"
    ]
    conditions: tuple[WakeCondition, ...] = Field(min_length=1)
    escalation_conditions: tuple[NonEmptyStr, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_condition_ids(self) -> WakeEscalationPolicy:
        ids = [item.condition_id for item in self.conditions]
        if len(ids) != len(set(ids)):
            raise ValueError("wake condition ids must be unique")
        return self


class ContinuationObligation(StrictControlPlaneModel):
    """Compact durable state required after the parent inference yields."""

    continuation_id: NonEmptyStr
    parent_objective_ref: ProvenanceRef
    established_decision_refs: tuple[ProvenanceRef, ...]
    delegated_obligation: NonEmptyStr
    delegation_reason: NonEmptyStr
    exact_child_identity: NonEmptyStr
    owner_scope: tuple[NonEmptyStr, ...] = Field(min_length=1)
    immutable_input_refs: tuple[ProvenanceRef, ...] = Field(min_length=1)
    expected_output: NonEmptyStr
    validation_refs: tuple[ProvenanceRef, ...] = Field(min_length=1)
    deferred_parent_decisions: tuple[NonEmptyStr, ...]
    invariants: tuple[NonEmptyStr, ...] = Field(min_length=1)
    stop_condition_ids: tuple[NonEmptyStr, ...] = Field(min_length=1)
    wake_condition_ids: tuple[NonEmptyStr, ...] = Field(min_length=1)
    return_owner: ProvenanceRef
    rollback_reentry_anchor: ProvenanceRef

    @model_validator(mode="after")
    def validate_continuation_sets(self) -> ContinuationObligation:
        for label, values in (
            ("owner scope", self.owner_scope),
            ("immutable input", self.immutable_input_refs),
            ("validation", self.validation_refs),
            ("invariant", self.invariants),
            ("stop condition", self.stop_condition_ids),
            ("wake condition", self.wake_condition_ids),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"continuation {label} entries must be unique")
        return self


class AgentIncarnationBinding(StrictControlPlaneModel):
    """One exact, non-executing binding across task, role, model, and runtime."""

    schema_version: Literal["aoa_agent_incarnation_binding_v1"] = (
        AGENT_INCARNATION_BINDING_VERSION
    )
    binding_id: NonEmptyStr
    incarnation_id: NonEmptyStr
    correlation_id: NonEmptyStr
    causation_id: NonEmptyStr
    trace_id: NonEmptyStr
    run_plan_ref: ContentRef
    task_request_ref: ProvenanceRef
    role_id: NonEmptyStr
    role_contract_ref: ProvenanceRef
    model_realization_ref: ProvenanceRef
    runtime_profile_ref: ProvenanceRef
    workspace_source_ref: ProvenanceRef
    permission_posture: IncarnationPermissionPosture
    tool_profile: IncarnationToolProfile
    usage_metering: IncarnationUsageMetering
    stop_conditions: tuple[IncarnationStopCondition, ...] = Field(min_length=1)
    expected_result_schema_ref: ProvenanceRef
    continuation: ContinuationObligation
    wake_policy: WakeEscalationPolicy
    binding_digest: Digest
    provenance: ProvenanceRef

    @model_validator(mode="after")
    def validate_owner_and_continuation_boundaries(self) -> AgentIncarnationBinding:
        if self.provenance.owner_repo != "aoa-sdk":
            raise ValueError("incarnation binding provenance must remain with aoa-sdk")
        if self.run_plan_ref.owner_repo != "aoa-sdk":
            raise ValueError("incarnation binding must reference an aoa-sdk run plan")
        if self.role_contract_ref.owner_repo != "aoa-agents":
            raise ValueError("role contract meaning must remain with aoa-agents")
        if self.model_realization_ref.owner_repo != "aoa-models":
            raise ValueError("model realization meaning must remain with aoa-models")
        if self.runtime_profile_ref.owner_repo == "aoa-sdk":
            raise ValueError("runtime profile provenance must remain with a runtime owner")
        if self.tool_profile.profile_ref.owner_repo != self.runtime_profile_ref.owner_repo:
            raise ValueError("tool profile and runtime profile must retain one runtime owner")
        if self.continuation.exact_child_identity != self.incarnation_id:
            raise ValueError("continuation child identity must match incarnation_id")
        stop_ids = [item.condition_id for item in self.stop_conditions]
        if len(stop_ids) != len(set(stop_ids)):
            raise ValueError("incarnation stop condition ids must be unique")
        if set(self.continuation.stop_condition_ids) != set(stop_ids):
            raise ValueError("continuation must preserve every incarnation stop condition")
        wake_ids = {item.condition_id for item in self.wake_policy.conditions}
        if set(self.continuation.wake_condition_ids) != wake_ids:
            raise ValueError("continuation must preserve every wake condition")
        return self
