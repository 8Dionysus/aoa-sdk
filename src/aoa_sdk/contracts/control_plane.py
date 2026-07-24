"""Typed, runtime-neutral contracts for the AoA Agent OS control plane.

These models describe handles, plans, lifecycle commands, and evidence
references.  They do not resolve routes, authorize work, activate
capabilities, execute models or tools, compute eval verdicts, or retain
durable memory.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from typing import Annotated, Literal, Protocol, TypeAlias, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..errors import AoASDKError


CONTROL_PLANE_SCHEMA_VERSION: Literal["aoa_control_plane_v1"] = (
    "aoa_control_plane_v1"
)
CONTROL_PLANE_LIFECYCLE_VERSION: Literal["aoa_run_lifecycle_v1"] = (
    "aoa_run_lifecycle_v1"
)
RUNTIME_ADAPTER_PROTOCOL_VERSION: Literal["aoa_runtime_adapter_v1"] = (
    "aoa_runtime_adapter_v1"
)

Digest = Annotated[str, Field(pattern=r"^sha256:[0-9a-f]{64}$")]
NonEmptyStr = Annotated[str, Field(min_length=1)]
RunState: TypeAlias = Literal[
    "prepared",
    "awaiting_approval",
    "running",
    "paused",
    "recoverable_failure",
    "failed",
    "completed",
    "cancelled",
    "closed",
]
LifecycleTrigger: TypeAlias = Literal[
    "start",
    "approval_required",
    "approval_granted",
    "approval_rejected",
    "approval_expired",
    "pause",
    "resume",
    "runtime_interrupted",
    "runtime_failed",
    "runtime_completed",
    "cancel",
    "recover",
    "closeout",
]


class ControlPlaneContractError(AoASDKError, ValueError):
    """Raised when a control-plane object violates a cross-object invariant."""


class StrictControlPlaneModel(BaseModel):
    """Fail-closed base for the public v1 control-plane contract family."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class ProvenanceRef(StrictControlPlaneModel):
    """Exact owner-qualified provenance for a source or projected artifact."""

    owner_repo: NonEmptyStr
    artifact_ref: NonEmptyStr
    source_ref: NonEmptyStr
    artifact_digest: Digest
    schema_ref: NonEmptyStr
    schema_version: NonEmptyStr


class ContentRef(StrictControlPlaneModel):
    """Content-addressed reference to another control-plane object."""

    object_id: NonEmptyStr
    owner_repo: NonEmptyStr
    schema_version: NonEmptyStr
    digest: Digest


class AgentRef(StrictControlPlaneModel):
    agent_id: NonEmptyStr
    provenance: ProvenanceRef


class CapabilityRef(StrictControlPlaneModel):
    capability_id: NonEmptyStr
    capability_kind: NonEmptyStr
    provenance: ProvenanceRef


class ScenarioRef(StrictControlPlaneModel):
    scenario_id: NonEmptyStr
    provenance: ProvenanceRef


class ResolvedAgentProfile(StrictControlPlaneModel):
    """SDK projection of an owner-authored agent; never an agent definition."""

    schema_version: Literal["aoa_control_plane_v1"] = CONTROL_PLANE_SCHEMA_VERSION
    profile_id: NonEmptyStr
    agent: AgentRef
    capability_refs: tuple[CapabilityRef, ...] = ()
    constraint_refs: tuple[ProvenanceRef, ...] = ()
    projection_provenance: ProvenanceRef


class RouteConstraint(StrictControlPlaneModel):
    constraint_id: NonEmptyStr
    kind: Literal[
        "required_owner",
        "forbidden_owner",
        "required_capability",
        "forbidden_capability",
        "risk_ceiling",
        "effect_ceiling",
        "runtime_requirement",
        "approval_requirement",
        "compatibility_requirement",
    ]
    value: NonEmptyStr
    source: ProvenanceRef


class RouteIntent(StrictControlPlaneModel):
    schema_version: Literal["aoa_control_plane_v1"] = CONTROL_PLANE_SCHEMA_VERSION
    intent_id: NonEmptyStr
    correlation_id: NonEmptyStr
    objective: NonEmptyStr
    requested_by: AgentRef
    scenario: ScenarioRef | None = None
    requested_capability_kinds: tuple[NonEmptyStr, ...] = ()
    constraints: tuple[RouteConstraint, ...] = ()
    context_refs: tuple[ProvenanceRef, ...] = ()
    authored_at: datetime

    @field_validator("authored_at")
    @classmethod
    def require_aware_authored_at(cls, value: datetime) -> datetime:
        return _require_aware(value, "authored_at")


class RouteCandidate(StrictControlPlaneModel):
    candidate_id: NonEmptyStr
    capability: CapabilityRef
    agent: AgentRef | None = None
    scenario: ScenarioRef | None = None
    rank: Annotated[int, Field(ge=0)]
    compatibility: Literal["compatible", "degraded", "incompatible"]
    policy_posture: Literal["eligible", "approval_required", "forbidden"]
    reason_codes: tuple[NonEmptyStr, ...]
    evidence_refs: tuple[ProvenanceRef, ...]


class ApprovalRequirement(StrictControlPlaneModel):
    requirement_id: NonEmptyStr
    approval_owner: ProvenanceRef
    operation: NonEmptyStr
    risk_class: NonEmptyStr
    applies_to_step_ids: tuple[NonEmptyStr, ...] = ()
    required_evidence_refs: tuple[ProvenanceRef, ...] = ()
    expires_after_seconds: Annotated[int | None, Field(gt=0)] = None
    renewable: bool = False


class RouteDecision(StrictControlPlaneModel):
    schema_version: Literal["aoa_control_plane_v1"] = CONTROL_PLANE_SCHEMA_VERSION
    decision_id: NonEmptyStr
    correlation_id: NonEmptyStr
    intent_ref: ContentRef
    status: Literal["resolved", "degraded", "blocked"]
    candidates: tuple[RouteCandidate, ...]
    selected_candidate_id: str | None = None
    approval_requirements: tuple[ApprovalRequirement, ...] = ()
    resolver_version: NonEmptyStr
    reason_codes: tuple[NonEmptyStr, ...]
    input_snapshot_digest: Digest
    provenance: ProvenanceRef

    @model_validator(mode="after")
    def validate_selection(self) -> RouteDecision:
        candidate_ids = [candidate.candidate_id for candidate in self.candidates]
        if len(candidate_ids) != len(set(candidate_ids)):
            raise ValueError("route candidate ids must be unique")
        if self.status in {"resolved", "degraded"}:
            if self.selected_candidate_id not in candidate_ids:
                raise ValueError("resolved or degraded decisions must select a listed candidate")
        elif self.selected_candidate_id is not None:
            raise ValueError("blocked decisions cannot select a candidate")
        if self.selected_candidate_id is not None:
            selected = next(
                candidate
                for candidate in self.candidates
                if candidate.candidate_id == self.selected_candidate_id
            )
            if selected.compatibility == "incompatible" or selected.policy_posture == "forbidden":
                raise ValueError("an incompatible or forbidden candidate cannot be selected")
        return self


class CandidateExplanation(StrictControlPlaneModel):
    candidate_id: NonEmptyStr
    disposition: Literal["selected", "eligible", "degraded", "rejected"]
    reason_codes: tuple[NonEmptyStr, ...]
    evidence_refs: tuple[ProvenanceRef, ...]


class RouteExplanation(StrictControlPlaneModel):
    schema_version: Literal["aoa_control_plane_v1"] = CONTROL_PLANE_SCHEMA_VERSION
    explanation_id: NonEmptyStr
    correlation_id: NonEmptyStr
    decision_ref: ContentRef
    decision_status: Literal["resolved", "degraded", "blocked"]
    candidate_explanations: tuple[CandidateExplanation, ...]
    selected_candidate_id: str | None = None
    fallback_used: Literal[False] = False
    ambiguity_codes: tuple[NonEmptyStr, ...] = ()
    provenance: ProvenanceRef

    @model_validator(mode="after")
    def validate_explanation(self) -> RouteExplanation:
        selected = [
            item.candidate_id
            for item in self.candidate_explanations
            if item.disposition == "selected"
        ]
        if self.decision_status == "blocked":
            if selected or self.selected_candidate_id is not None:
                raise ValueError("a blocked explanation cannot contain a selected candidate")
        elif selected != [self.selected_candidate_id]:
            raise ValueError("explanation selection must identify exactly the decision selection")
        return self


class ScenarioBinding(StrictControlPlaneModel):
    schema_version: Literal["aoa_control_plane_v1"] = CONTROL_PLANE_SCHEMA_VERSION
    binding_id: NonEmptyStr
    correlation_id: NonEmptyStr
    scenario: ScenarioRef
    decision_ref: ContentRef
    agent_refs: tuple[AgentRef, ...]
    capability_refs: tuple[CapabilityRef, ...]
    input_refs: tuple[ProvenanceRef, ...] = ()
    expected_artifact_kinds: tuple[NonEmptyStr, ...] = ()
    provenance: ProvenanceRef


class RuntimeProfile(StrictControlPlaneModel):
    """Runtime-owner projection negotiated by the SDK, not runtime policy."""

    schema_version: Literal["aoa_control_plane_v1"] = CONTROL_PLANE_SCHEMA_VERSION
    profile_id: NonEmptyStr
    runtime_owner: NonEmptyStr
    adapter_id: NonEmptyStr
    adapter_protocol_version: Literal["aoa_runtime_adapter_v1"] = (
        RUNTIME_ADAPTER_PROTOCOL_VERSION
    )
    supported_plan_schema_versions: tuple[NonEmptyStr, ...]
    supported_event_schema_versions: tuple[NonEmptyStr, ...]
    supported_effect_classes: tuple[NonEmptyStr, ...]
    constraint_refs: tuple[ProvenanceRef, ...] = ()
    provenance: ProvenanceRef

    @model_validator(mode="after")
    def validate_runtime_owner(self) -> RuntimeProfile:
        if self.runtime_owner != self.provenance.owner_repo:
            raise ValueError("runtime profile provenance must come from runtime_owner")
        if not self.supported_plan_schema_versions:
            raise ValueError("runtime profile must declare supported plan versions")
        if not self.supported_event_schema_versions:
            raise ValueError("runtime profile must declare supported event versions")
        return self


class ABIRef(StrictControlPlaneModel):
    abi_id: NonEmptyStr
    abi_version: NonEmptyStr
    owner_repo: NonEmptyStr
    schema_ref: NonEmptyStr
    source_ref: NonEmptyStr
    artifact_digest: Digest


class PlanSnapshot(StrictControlPlaneModel):
    snapshot_id: NonEmptyStr
    source_refs: tuple[ProvenanceRef, ...]
    abi_refs: tuple[ABIRef, ...]
    snapshot_digest: Digest

    @model_validator(mode="after")
    def validate_snapshot(self) -> PlanSnapshot:
        source_keys = [
            (source.owner_repo, source.artifact_ref) for source in self.source_refs
        ]
        abi_keys = [(abi.owner_repo, abi.abi_id) for abi in self.abi_refs]
        if len(source_keys) != len(set(source_keys)):
            raise ValueError("plan snapshot source refs must be unique")
        if len(abi_keys) != len(set(abi_keys)):
            raise ValueError("plan snapshot ABI refs must be unique")
        if not self.source_refs or not self.abi_refs:
            raise ValueError("a run plan must pin at least one source ref and ABI ref")
        return self


class PlanStep(StrictControlPlaneModel):
    step_id: NonEmptyStr
    operation_kind: Literal[
        "inspect",
        "mutate",
        "summon",
        "return",
        "validate",
        "evaluate",
        "checkpoint",
        "retain",
        "closeout",
    ]
    effect_class: Literal["read_only", "repo_mutation", "runtime_mutation", "external"]
    depends_on: tuple[NonEmptyStr, ...] = ()
    agent_refs: tuple[AgentRef, ...] = ()
    capability_refs: tuple[CapabilityRef, ...] = ()
    input_refs: tuple[ProvenanceRef, ...] = ()
    expected_output_kinds: tuple[NonEmptyStr, ...] = ()
    approval_requirement_ids: tuple[NonEmptyStr, ...] = ()


class CheckpointPolicy(StrictControlPlaneModel):
    owner: ProvenanceRef
    required_after_step_ids: tuple[NonEmptyStr, ...] = ()
    required_on_pause: bool = True
    required_on_recoverable_failure: bool = True


class RetryPolicy(StrictControlPlaneModel):
    max_attempts: Annotated[int, Field(ge=1)]
    retryable_failure_codes: tuple[NonEmptyStr, ...] = ()
    duplicate_effect_strategy: Literal["same_idempotency_key_no_new_effect"] = (
        "same_idempotency_key_no_new_effect"
    )
    replay_strategy: Literal["verify_snapshot_and_event_cursor_before_retry"] = (
        "verify_snapshot_and_event_cursor_before_retry"
    )


class RollbackPolicy(StrictControlPlaneModel):
    required: bool
    owner: ProvenanceRef
    trigger_codes: tuple[NonEmptyStr, ...] = ()
    rollback_artifact_ref: ProvenanceRef | None = None
    rollback_failure_is_terminal: Literal[True] = True

    @model_validator(mode="after")
    def validate_required_rollback(self) -> RollbackPolicy:
        if self.required and self.rollback_artifact_ref is None:
            raise ValueError("required rollback must name its owner artifact")
        return self


class EvidenceRequirement(StrictControlPlaneModel):
    requirement_id: NonEmptyStr
    artifact_kind: NonEmptyStr
    producer_owner: NonEmptyStr
    required_after_step_id: str | None = None
    terminal_required: bool = False


class EvalRequirement(StrictControlPlaneModel):
    requirement_id: NonEmptyStr
    eval_owner_ref: ProvenanceRef
    eval_contract_ref: ProvenanceRef
    required_evidence_ids: tuple[NonEmptyStr, ...] = ()
    verdict_required_for_closeout: bool = True


class RetentionRequirement(StrictControlPlaneModel):
    requirement_id: NonEmptyStr
    memory_owner_ref: ProvenanceRef
    retention_contract_ref: ProvenanceRef
    receipt_required_for_closeout: bool = True


class CloseoutRequirement(StrictControlPlaneModel):
    requirement_id: NonEmptyStr
    owner_ref: ProvenanceRef
    required_ref_kinds: tuple[NonEmptyStr, ...]


class RunPlan(StrictControlPlaneModel):
    schema_version: Literal["aoa_control_plane_v1"] = CONTROL_PLANE_SCHEMA_VERSION
    plan_id: NonEmptyStr
    correlation_id: NonEmptyStr
    decision_ref: ContentRef
    scenario_binding: ScenarioBinding
    runtime_profile: RuntimeProfile
    snapshot: PlanSnapshot
    steps: tuple[PlanStep, ...]
    approval_requirements: tuple[ApprovalRequirement, ...] = ()
    checkpoint_policy: CheckpointPolicy
    retry_policy: RetryPolicy
    rollback_policy: RollbackPolicy
    evidence_requirements: tuple[EvidenceRequirement, ...]
    eval_requirements: tuple[EvalRequirement, ...] = ()
    retention_requirements: tuple[RetentionRequirement, ...] = ()
    closeout_requirements: tuple[CloseoutRequirement, ...]
    plan_digest: Digest
    provenance: ProvenanceRef

    @model_validator(mode="after")
    def validate_plan_graph(self) -> RunPlan:
        if self.correlation_id != self.scenario_binding.correlation_id:
            raise ValueError("plan and scenario binding correlation ids must match")
        if self.schema_version not in self.runtime_profile.supported_plan_schema_versions:
            raise ValueError("runtime profile does not support the run plan schema")
        if (
            CONTROL_PLANE_SCHEMA_VERSION
            not in self.runtime_profile.supported_event_schema_versions
        ):
            raise ValueError(
                "runtime profile does not support the control-plane event schema"
            )
        step_ids = [step.step_id for step in self.steps]
        if len(step_ids) != len(set(step_ids)):
            raise ValueError("run plan step ids must be unique")
        known_steps = set(step_ids)
        approval_ids = {
            requirement.requirement_id for requirement in self.approval_requirements
        }
        bound_agents = set(self.scenario_binding.agent_refs)
        bound_capabilities = set(self.scenario_binding.capability_refs)
        for step in self.steps:
            unknown_dependencies = set(step.depends_on) - known_steps
            if unknown_dependencies:
                raise ValueError(
                    f"step {step.step_id!r} has unknown dependencies: "
                    f"{sorted(unknown_dependencies)}"
                )
            unknown_approvals = set(step.approval_requirement_ids) - approval_ids
            if unknown_approvals:
                raise ValueError(
                    f"step {step.step_id!r} has unknown approval requirements: "
                    f"{sorted(unknown_approvals)}"
                )
            if not set(step.agent_refs).issubset(bound_agents):
                raise ValueError(
                    f"step {step.step_id!r} uses an agent outside ScenarioBinding"
                )
            if not set(step.capability_refs).issubset(bound_capabilities):
                raise ValueError(
                    f"step {step.step_id!r} uses a capability outside ScenarioBinding"
                )
            if step.effect_class not in self.runtime_profile.supported_effect_classes:
                raise ValueError(
                    f"runtime profile does not support effect class "
                    f"{step.effect_class!r} for step {step.step_id!r}"
                )
        _assert_acyclic(self.steps)
        required_step_refs = {
            step_id
            for requirement in self.approval_requirements
            for step_id in requirement.applies_to_step_ids
        }
        required_step_refs.update(self.checkpoint_policy.required_after_step_ids)
        required_step_refs.update(
            requirement.required_after_step_id
            for requirement in self.evidence_requirements
            if requirement.required_after_step_id is not None
        )
        unknown_step_refs = required_step_refs - known_steps
        if unknown_step_refs:
            raise ValueError(
                f"plan policies reference unknown steps: {sorted(unknown_step_refs)}"
            )
        return self


class ApprovalRequest(StrictControlPlaneModel):
    schema_version: Literal["aoa_control_plane_v1"] = CONTROL_PLANE_SCHEMA_VERSION
    request_id: NonEmptyStr
    requirement_id: NonEmptyStr
    approval_authority: ProvenanceRef
    session_id: NonEmptyStr
    correlation_id: NonEmptyStr
    plan_digest: Digest
    snapshot_digest: Digest
    requested_at: datetime
    expires_at: datetime | None = None
    request_provenance: ProvenanceRef

    @model_validator(mode="after")
    def validate_request_window(self) -> ApprovalRequest:
        requested_at = _require_aware(self.requested_at, "requested_at")
        if self.expires_at is not None:
            expires_at = _require_aware(self.expires_at, "expires_at")
            if expires_at <= requested_at:
                raise ValueError("approval expiry must be after request time")
        return self


class ApprovalDecision(StrictControlPlaneModel):
    schema_version: Literal["aoa_control_plane_v1"] = CONTROL_PLANE_SCHEMA_VERSION
    decision_id: NonEmptyStr
    request_id: NonEmptyStr
    requirement_id: NonEmptyStr
    session_id: NonEmptyStr
    correlation_id: NonEmptyStr
    plan_digest: Digest
    snapshot_digest: Digest
    verdict: Literal["approved", "rejected", "expired"]
    approval_authority: ProvenanceRef
    decided_by: ProvenanceRef
    decided_at: datetime
    reason: NonEmptyStr
    evidence_refs: tuple[ProvenanceRef, ...] = ()

    @field_validator("decided_at")
    @classmethod
    def require_aware_decided_at(cls, value: datetime) -> datetime:
        return _require_aware(value, "decided_at")


class SessionHandle(StrictControlPlaneModel):
    schema_version: Literal["aoa_control_plane_v1"] = CONTROL_PLANE_SCHEMA_VERSION
    lifecycle_version: Literal["aoa_run_lifecycle_v1"] = CONTROL_PLANE_LIFECYCLE_VERSION
    session_id: NonEmptyStr
    correlation_id: NonEmptyStr
    plan_ref: ContentRef
    plan_digest: Digest
    snapshot_digest: Digest
    event_stream_id: NonEmptyStr
    prepared_at: datetime
    prepared_by: ProvenanceRef

    @field_validator("prepared_at")
    @classmethod
    def require_aware_prepared_at(cls, value: datetime) -> datetime:
        return _require_aware(value, "prepared_at")


class OwnedArtifactRef(StrictControlPlaneModel):
    ref_id: NonEmptyStr
    artifact_kind: NonEmptyStr
    provenance: ProvenanceRef
    satisfies_requirement_ids: tuple[NonEmptyStr, ...] = ()


class EvidenceBundleRef(OwnedArtifactRef):
    artifact_kind: Literal["evidence_bundle"] = "evidence_bundle"


class EvalVerdictRef(OwnedArtifactRef):
    artifact_kind: Literal["eval_verdict"] = "eval_verdict"


class MemoryReceiptRef(OwnedArtifactRef):
    artifact_kind: Literal["memory_receipt"] = "memory_receipt"


class CloseoutBundleRef(OwnedArtifactRef):
    artifact_kind: Literal["closeout_bundle"] = "closeout_bundle"


class RunStatus(StrictControlPlaneModel):
    schema_version: Literal["aoa_control_plane_v1"] = CONTROL_PLANE_SCHEMA_VERSION
    session_id: NonEmptyStr
    correlation_id: NonEmptyStr
    state: RunState
    revision: Annotated[int, Field(ge=0)]
    last_event_sequence: Annotated[int, Field(ge=-1)] = -1
    pending_approval_ids: tuple[NonEmptyStr, ...] = ()
    failure_code: str | None = None
    recover_from_event_sequence: Annotated[int | None, Field(ge=-1)] = None
    closeout_ref: CloseoutBundleRef | None = None
    updated_at: datetime
    observed_by: ProvenanceRef

    @model_validator(mode="after")
    def validate_state_details(self) -> RunStatus:
        _require_aware(self.updated_at, "updated_at")
        if self.state == "awaiting_approval" and not self.pending_approval_ids:
            raise ValueError("awaiting_approval must name pending approval ids")
        if self.state != "awaiting_approval" and self.pending_approval_ids:
            raise ValueError("pending approvals are only valid while awaiting_approval")
        if self.state == "recoverable_failure":
            if self.failure_code is None or self.recover_from_event_sequence is None:
                raise ValueError(
                    "recoverable_failure must name a failure code and recovery cursor"
                )
        elif self.recover_from_event_sequence is not None:
            raise ValueError(
                "a recovery cursor is only valid for recoverable_failure"
            )
        if self.state == "failed" and self.failure_code is None:
            raise ValueError("failed status must name a failure code")
        if self.state not in {"failed", "recoverable_failure"} and self.failure_code:
            raise ValueError(
                "failure_code is only valid for failed or recoverable_failure"
            )
        if self.state == "closed" and self.closeout_ref is None:
            raise ValueError("closed status must name a closeout bundle")
        if self.state != "closed" and self.closeout_ref is not None:
            raise ValueError("closeout bundle is only valid in closed state")
        return self


class LifecycleCommand(StrictControlPlaneModel):
    schema_version: Literal["aoa_control_plane_v1"] = CONTROL_PLANE_SCHEMA_VERSION
    command_id: NonEmptyStr
    idempotency_key: NonEmptyStr
    command_kind: Literal["start", "pause", "resume", "cancel", "recover"]
    session_id: NonEmptyStr
    correlation_id: NonEmptyStr
    plan_digest: Digest
    expected_revision: Annotated[int, Field(ge=0)]
    issued_at: datetime
    issued_by: ProvenanceRef
    reason: NonEmptyStr

    @field_validator("issued_at")
    @classmethod
    def require_aware_issued_at(cls, value: datetime) -> datetime:
        return _require_aware(value, "issued_at")


class StartCommand(LifecycleCommand):
    command_kind: Literal["start"] = "start"


class PauseCommand(LifecycleCommand):
    command_kind: Literal["pause"] = "pause"


class ResumeCommand(LifecycleCommand):
    command_kind: Literal["resume"] = "resume"
    resume_after_sequence: Annotated[int, Field(ge=-1)]


class CancelCommand(LifecycleCommand):
    command_kind: Literal["cancel"] = "cancel"
    rollback_requested: bool = False


class RecoverCommand(LifecycleCommand):
    command_kind: Literal["recover"] = "recover"
    recover_after_sequence: Annotated[int, Field(ge=-1)]
    recovery_evidence_ref: ProvenanceRef


RuntimeCommand: TypeAlias = (
    StartCommand | PauseCommand | ResumeCommand | CancelCommand | RecoverCommand
)


class CommandReceipt(StrictControlPlaneModel):
    schema_version: Literal["aoa_control_plane_v1"] = CONTROL_PLANE_SCHEMA_VERSION
    command_id: NonEmptyStr
    idempotency_key: NonEmptyStr
    command_digest: Digest
    session_id: NonEmptyStr
    status: Literal["applied", "duplicate", "rejected"]
    resulting_revision: Annotated[int, Field(ge=0)]
    event_refs: tuple[ContentRef, ...] = ()
    rejection_code: str | None = None
    produced_by: ProvenanceRef

    @model_validator(mode="after")
    def validate_receipt(self) -> CommandReceipt:
        if self.status == "rejected" and self.rejection_code is None:
            raise ValueError("a rejected command receipt must include rejection_code")
        if self.status != "rejected" and self.rejection_code is not None:
            raise ValueError("only a rejected command receipt may include rejection_code")
        return self


class ExecutionEvent(StrictControlPlaneModel):
    schema_version: Literal["aoa_control_plane_v1"] = CONTROL_PLANE_SCHEMA_VERSION
    event_id: NonEmptyStr
    event_stream_id: NonEmptyStr
    session_id: NonEmptyStr
    correlation_id: NonEmptyStr
    sequence: Annotated[int, Field(ge=0)]
    previous_event_digest: Digest | None = None
    event_digest: Digest
    event_kind: Literal[
        "state_transition",
        "command_ack",
        "progress",
        "approval_requested",
        "evidence_emitted",
        "outcome",
        "heartbeat",
    ]
    emitted_at: datetime
    emitted_by: ProvenanceRef
    state_before: RunState | None = None
    state_after: RunState | None = None
    trigger: LifecycleTrigger | None = None
    command_id: str | None = None
    idempotency_key: str | None = None
    payload_ref: ProvenanceRef | None = None
    evidence_refs: tuple[EvidenceBundleRef, ...] = ()
    outcome_ref: ContentRef | None = None

    @model_validator(mode="after")
    def validate_event_shape(self) -> ExecutionEvent:
        _require_aware(self.emitted_at, "emitted_at")
        if self.sequence == 0 and self.previous_event_digest is not None:
            raise ValueError("the first event cannot name a previous event digest")
        if self.sequence > 0 and self.previous_event_digest is None:
            raise ValueError("non-initial events must name the previous event digest")
        if self.event_kind == "state_transition":
            if (
                self.state_before is None
                or self.state_after is None
                or self.trigger is None
            ):
                raise ValueError(
                    "state_transition events require before, after, and trigger"
                )
            assert_transition_allowed(
                self.state_before,
                self.state_after,
                self.trigger,
            )
        elif any(
            value is not None
            for value in (self.state_before, self.state_after, self.trigger)
        ):
            raise ValueError(
                "lifecycle transition fields are only valid on state_transition events"
            )
        if self.event_kind == "command_ack":
            if self.command_id is None or self.idempotency_key is None:
                raise ValueError(
                    "command_ack events require command_id and idempotency_key"
                )
        elif self.command_id is not None or self.idempotency_key is not None:
            raise ValueError("command fields are only valid on command_ack events")
        if self.event_kind == "evidence_emitted" and not self.evidence_refs:
            raise ValueError("evidence_emitted events require evidence refs")
        if self.event_kind == "outcome" and self.outcome_ref is None:
            raise ValueError("outcome events require an outcome ref")
        return self


class RunOutcome(StrictControlPlaneModel):
    schema_version: Literal["aoa_control_plane_v1"] = CONTROL_PLANE_SCHEMA_VERSION
    outcome_id: NonEmptyStr
    session_id: NonEmptyStr
    correlation_id: NonEmptyStr
    plan_digest: Digest
    execution_status: Literal["succeeded", "partial", "failed", "cancelled"]
    terminal_state: Literal["completed", "failed", "cancelled"]
    completed_at: datetime
    runtime_result_ref: ProvenanceRef
    evidence_bundle_refs: tuple[EvidenceBundleRef, ...]
    eval_verdict_refs: tuple[EvalVerdictRef, ...] = ()
    memory_receipt_refs: tuple[MemoryReceiptRef, ...] = ()
    closeout_bundle_ref: CloseoutBundleRef | None = None
    failure_codes: tuple[NonEmptyStr, ...] = ()

    @model_validator(mode="after")
    def validate_outcome(self) -> RunOutcome:
        _require_aware(self.completed_at, "completed_at")
        terminal_for_status = {
            "succeeded": "completed",
            "partial": "failed",
            "failed": "failed",
            "cancelled": "cancelled",
        }
        if self.terminal_state != terminal_for_status[self.execution_status]:
            raise ValueError("execution status and terminal lifecycle state disagree")
        if self.execution_status in {"partial", "failed"} and not self.failure_codes:
            raise ValueError("partial or failed outcomes must name failure codes")
        return self


ALLOWED_LIFECYCLE_TRANSITIONS: frozenset[
    tuple[RunState, LifecycleTrigger, RunState]
] = frozenset(
    {
        ("prepared", "start", "running"),
        ("prepared", "approval_required", "awaiting_approval"),
        ("awaiting_approval", "approval_granted", "running"),
        ("awaiting_approval", "approval_rejected", "cancelled"),
        ("awaiting_approval", "approval_expired", "paused"),
        ("running", "pause", "paused"),
        ("paused", "resume", "running"),
        ("running", "runtime_interrupted", "recoverable_failure"),
        ("paused", "runtime_interrupted", "recoverable_failure"),
        ("awaiting_approval", "runtime_interrupted", "recoverable_failure"),
        ("recoverable_failure", "recover", "paused"),
        ("running", "runtime_failed", "failed"),
        ("running", "runtime_completed", "completed"),
        ("prepared", "cancel", "cancelled"),
        ("awaiting_approval", "cancel", "cancelled"),
        ("running", "cancel", "cancelled"),
        ("paused", "cancel", "cancelled"),
        ("recoverable_failure", "cancel", "cancelled"),
        ("failed", "closeout", "closed"),
        ("completed", "closeout", "closed"),
        ("cancelled", "closeout", "closed"),
    }
)


def canonical_digest(
    model: BaseModel,
    *,
    exclude: set[str] | None = None,
) -> str:
    """Return a stable SHA-256 digest for a JSON-serializable model."""

    payload = model.model_dump(mode="json", exclude=exclude or set())
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def assert_run_plan_digest(plan: RunPlan) -> None:
    expected = canonical_digest(plan, exclude={"plan_digest"})
    if plan.plan_digest != expected:
        raise ControlPlaneContractError(
            f"run plan digest mismatch: expected {expected}, got {plan.plan_digest}"
        )


def assert_plan_snapshot_digest(snapshot: PlanSnapshot) -> None:
    expected = canonical_digest(snapshot, exclude={"snapshot_digest"})
    if snapshot.snapshot_digest != expected:
        raise ControlPlaneContractError(
            "plan snapshot digest does not match its pinned source and ABI refs"
        )


def assert_snapshot_current(
    snapshot: PlanSnapshot,
    *,
    observed_sources: Mapping[tuple[str, str], str],
    observed_abis: Mapping[tuple[str, str], tuple[str, str]],
) -> None:
    """Fail closed if a pinned owner artifact or ABI no longer matches."""

    assert_plan_snapshot_digest(snapshot)
    expected_source_keys = {
        (source.owner_repo, source.artifact_ref) for source in snapshot.source_refs
    }
    expected_abi_keys = {(abi.owner_repo, abi.abi_id) for abi in snapshot.abi_refs}
    if set(observed_sources) != expected_source_keys:
        raise ControlPlaneContractError("observed source set does not match plan snapshot")
    if set(observed_abis) != expected_abi_keys:
        raise ControlPlaneContractError("observed ABI set does not match plan snapshot")
    for source in snapshot.source_refs:
        key = (source.owner_repo, source.artifact_ref)
        if observed_sources[key] != source.artifact_digest:
            raise ControlPlaneContractError(
                f"stale or spoofed source artifact for {source.owner_repo}:{source.artifact_ref}"
            )
    for abi in snapshot.abi_refs:
        key = (abi.owner_repo, abi.abi_id)
        if observed_abis[key] != (abi.abi_version, abi.artifact_digest):
            raise ControlPlaneContractError(
                f"stale or incompatible ABI for {abi.owner_repo}:{abi.abi_id}"
            )


def assert_explanation_matches_decision(
    decision: RouteDecision,
    explanation: RouteExplanation,
) -> None:
    """Require an explanation disposition for every candidate in the decision."""

    if (
        explanation.correlation_id != decision.correlation_id
        or explanation.decision_ref.object_id != decision.decision_id
        or explanation.decision_status != decision.status
        or explanation.selected_candidate_id != decision.selected_candidate_id
    ):
        raise ControlPlaneContractError(
            "route explanation scope does not match the route decision"
        )
    decision_candidate_ids = {candidate.candidate_id for candidate in decision.candidates}
    explanation_candidate_ids = {
        candidate.candidate_id for candidate in explanation.candidate_explanations
    }
    if decision_candidate_ids != explanation_candidate_ids:
        raise ControlPlaneContractError(
            "route explanation does not account for every decision candidate"
        )


def assert_transition_allowed(
    state_before: RunState,
    state_after: RunState,
    trigger: LifecycleTrigger,
) -> None:
    if (state_before, trigger, state_after) not in ALLOWED_LIFECYCLE_TRANSITIONS:
        raise ControlPlaneContractError(
            f"invalid lifecycle transition: {state_before} --{trigger}--> {state_after}"
        )


def assert_approvals_satisfied(
    plan: RunPlan,
    decisions: Iterable[ApprovalDecision],
    *,
    session: SessionHandle,
    at: datetime,
) -> None:
    """Require one exact, current approval for every plan requirement."""

    at = _require_aware(at, "at")
    decisions_by_requirement: dict[str, ApprovalDecision] = {}
    for supplied_decision in decisions:
        if supplied_decision.requirement_id in decisions_by_requirement:
            raise ControlPlaneContractError(
                f"duplicate approval decision for {supplied_decision.requirement_id}"
            )
        decisions_by_requirement[supplied_decision.requirement_id] = supplied_decision
    for requirement in plan.approval_requirements:
        approved_decision = decisions_by_requirement.get(requirement.requirement_id)
        if approved_decision is None or approved_decision.verdict != "approved":
            raise ControlPlaneContractError(
                f"missing approved decision for {requirement.requirement_id}"
            )
        if (
            approved_decision.session_id != session.session_id
            or approved_decision.correlation_id != session.correlation_id
            or approved_decision.plan_digest != plan.plan_digest
            or approved_decision.snapshot_digest != plan.snapshot.snapshot_digest
        ):
            raise ControlPlaneContractError(
                f"approval scope mismatch for {requirement.requirement_id}"
            )
        if approved_decision.approval_authority != requirement.approval_owner:
            raise ControlPlaneContractError(
                f"approval owner mismatch for {requirement.requirement_id}"
            )
        if approved_decision.decided_at > at:
            raise ControlPlaneContractError(
                f"approval decision is from the future for {requirement.requirement_id}"
            )
        if requirement.expires_after_seconds is not None:
            age = (at - approved_decision.decided_at).total_seconds()
            if age > requirement.expires_after_seconds:
                raise ControlPlaneContractError(
                    f"approval expired for {requirement.requirement_id}"
                )


def command_digest(command: RuntimeCommand) -> str:
    return canonical_digest(command)


def assert_idempotent_replay(
    previous: RuntimeCommand,
    replay: RuntimeCommand,
) -> None:
    """Allow a duplicate only when key, scope, and full command are identical."""

    if (
        previous.idempotency_key != replay.idempotency_key
        or previous.session_id != replay.session_id
    ):
        raise ControlPlaneContractError("commands are not in the same replay scope")
    if command_digest(previous) != command_digest(replay):
        raise ControlPlaneContractError(
            "idempotency key was reused with a different command payload"
        )


def execution_event_digest(event: ExecutionEvent) -> str:
    return canonical_digest(event, exclude={"event_digest"})


def deduplicate_execution_events(
    events: Iterable[ExecutionEvent],
) -> tuple[ExecutionEvent, ...]:
    """Collapse identical redelivery and reject event-id payload substitution."""

    ordered: list[ExecutionEvent] = []
    seen: dict[str, str] = {}
    for event in events:
        digest = execution_event_digest(event)
        if event.event_digest != digest:
            raise ControlPlaneContractError(
                f"event digest mismatch for {event.event_id!r}"
            )
        if event.event_id in seen:
            if seen[event.event_id] != digest:
                raise ControlPlaneContractError(
                    f"event id {event.event_id!r} was replayed with different content"
                )
            continue
        seen[event.event_id] = digest
        ordered.append(event)
    return tuple(ordered)


def assert_execution_event_chain(
    events: Iterable[ExecutionEvent],
    *,
    session: SessionHandle,
    after_sequence: int = -1,
    previous_digest: str | None = None,
) -> None:
    """Validate exact ordering, correlation, digest linkage, and event identity."""

    normalized = deduplicate_execution_events(events)
    expected_sequence = after_sequence + 1
    expected_previous_digest = previous_digest
    for event in normalized:
        if (
            event.session_id != session.session_id
            or event.correlation_id != session.correlation_id
            or event.event_stream_id != session.event_stream_id
        ):
            raise ControlPlaneContractError(
                f"event {event.event_id!r} is outside the session correlation scope"
            )
        if event.sequence != expected_sequence:
            raise ControlPlaneContractError(
                f"event sequence gap or reorder: expected {expected_sequence}, "
                f"got {event.sequence}"
            )
        if event.previous_event_digest != expected_previous_digest:
            raise ControlPlaneContractError(
                f"event {event.event_id!r} does not link to the previous digest"
            )
        computed_digest = execution_event_digest(event)
        if event.event_digest != computed_digest:
            raise ControlPlaneContractError(
                f"event digest mismatch for {event.event_id!r}"
            )
        expected_sequence += 1
        expected_previous_digest = event.event_digest


def assert_closeout_ready(
    plan: RunPlan,
    session: SessionHandle,
    outcome: RunOutcome,
    bundle: CloseoutBundleRef,
) -> None:
    """Prove required evidence refs exist before lifecycle closure."""

    if (
        outcome.session_id != session.session_id
        or outcome.correlation_id != session.correlation_id
        or outcome.plan_digest != plan.plan_digest
    ):
        raise ControlPlaneContractError("run outcome is outside closeout scope")
    missing_evidence = {
        requirement.requirement_id
        for requirement in plan.evidence_requirements
        if requirement.terminal_required
        and not any(
            requirement.requirement_id in ref.satisfies_requirement_ids
            and ref.provenance.owner_repo == requirement.producer_owner
            for ref in outcome.evidence_bundle_refs
        )
    }
    if missing_evidence:
        raise ControlPlaneContractError(
            f"closeout is missing terminal evidence: {sorted(missing_evidence)}"
        )
    missing_evals = {
        requirement.requirement_id
        for requirement in plan.eval_requirements
        if requirement.verdict_required_for_closeout
        and not any(
            requirement.requirement_id in ref.satisfies_requirement_ids
            and ref.provenance.owner_repo == requirement.eval_owner_ref.owner_repo
            for ref in outcome.eval_verdict_refs
        )
    }
    if missing_evals:
        raise ControlPlaneContractError(
            f"closeout is missing eval verdict refs: {sorted(missing_evals)}"
        )
    missing_retention = {
        requirement.requirement_id
        for requirement in plan.retention_requirements
        if requirement.receipt_required_for_closeout
        and not any(
            requirement.requirement_id in ref.satisfies_requirement_ids
            and ref.provenance.owner_repo == requirement.memory_owner_ref.owner_repo
            for ref in outcome.memory_receipt_refs
        )
    }
    if missing_retention:
        raise ControlPlaneContractError(
            f"closeout is missing memory receipt refs: {sorted(missing_retention)}"
        )
    missing_closeout = {
        requirement.requirement_id
        for requirement in plan.closeout_requirements
        if requirement.requirement_id not in bundle.satisfies_requirement_ids
        or bundle.provenance.owner_repo != requirement.owner_ref.owner_repo
    }
    if missing_closeout:
        raise ControlPlaneContractError(
            f"closeout bundle does not satisfy requirements: {sorted(missing_closeout)}"
        )


@runtime_checkable
class ControlPlaneProtocol(Protocol):
    """Future C1/C2 behavior surface; R2 defines the contract only."""

    def resolve(self, intent: RouteIntent) -> RouteDecision: ...

    def explain(self, decision: RouteDecision) -> RouteExplanation: ...

    def compile(
        self,
        decision: RouteDecision,
        scenario: ScenarioBinding,
        runtime_profile: RuntimeProfile,
    ) -> RunPlan: ...


@runtime_checkable
class RuntimeAdapterProtocol(Protocol):
    """Runtime-owned execution bridge consumed by the future AoARunner."""

    @property
    def profile(self) -> RuntimeProfile: ...

    def dispatch(
        self,
        plan: RunPlan,
        session: SessionHandle,
        command: RuntimeCommand,
    ) -> CommandReceipt: ...

    def status(self, session: SessionHandle) -> RunStatus: ...

    def events(
        self,
        session: SessionHandle,
        *,
        after_sequence: int,
    ) -> Iterable[ExecutionEvent]: ...


@runtime_checkable
class AoARunnerProtocol(Protocol):
    """Lifecycle client contract; implementations must delegate execution."""

    def prepare(self, plan: RunPlan) -> SessionHandle: ...

    def start(
        self,
        session: SessionHandle,
        adapter: RuntimeAdapterProtocol,
        command: StartCommand,
    ) -> RunStatus: ...

    def pause(
        self,
        session: SessionHandle,
        adapter: RuntimeAdapterProtocol,
        command: PauseCommand,
    ) -> RunStatus: ...

    def approve(
        self,
        session: SessionHandle,
        approval: ApprovalDecision,
    ) -> RunStatus: ...

    def resume(
        self,
        session: SessionHandle,
        adapter: RuntimeAdapterProtocol,
        command: ResumeCommand,
    ) -> RunStatus: ...

    def cancel(
        self,
        session: SessionHandle,
        adapter: RuntimeAdapterProtocol,
        command: CancelCommand,
    ) -> RunStatus: ...

    def recover(
        self,
        session: SessionHandle,
        adapter: RuntimeAdapterProtocol,
        command: RecoverCommand,
    ) -> RunStatus: ...

    def closeout(
        self,
        session: SessionHandle,
        outcome: RunOutcome,
        bundle: CloseoutBundleRef,
    ) -> RunStatus: ...


def _require_aware(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _assert_acyclic(steps: tuple[PlanStep, ...]) -> None:
    dependencies = {step.step_id: set(step.depends_on) for step in steps}
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(step_id: str) -> None:
        if step_id in visiting:
            raise ValueError(f"run plan contains a dependency cycle at {step_id!r}")
        if step_id in visited:
            return
        visiting.add(step_id)
        for dependency in dependencies[step_id]:
            visit(dependency)
        visiting.remove(step_id)
        visited.add(step_id)

    for step_id in dependencies:
        visit(step_id)
