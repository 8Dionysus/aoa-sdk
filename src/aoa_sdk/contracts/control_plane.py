"""Typed, runtime-neutral contracts for the AoA Agent OS control plane.

These models describe handles, plans, lifecycle commands, and evidence
references.  They do not resolve routes, authorize work, activate
capabilities, execute models or tools, compute eval verdicts, or retain
durable memory.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from typing import Annotated, Literal, Protocol, TypeAlias, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..errors import AoASDKError


CONTROL_PLANE_SCHEMA_VERSION: Literal["aoa_control_plane_v1"] = "aoa_control_plane_v1"
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


class ScenarioArtifactBinding(StrictControlPlaneModel):
    """Owner-qualified scenario input selected by its reviewed artifact kind."""

    artifact_kind: NonEmptyStr
    artifact_ref: ProvenanceRef


class ScenarioConditionBinding(StrictControlPlaneModel):
    """Exact reviewed boolean used to select a guarded plan contour."""

    condition_id: NonEmptyStr
    value: bool
    provenance: ProvenanceRef


class ScenarioCapabilityBinding(StrictControlPlaneModel):
    """Resolve one playbook requirement through the current owner graph or alias map."""

    requirement_id: NonEmptyStr
    capability: CapabilityRef
    semantic_owner_repo: NonEmptyStr
    binding_action: NonEmptyStr
    compatibility: NonEmptyStr
    availability: NonEmptyStr
    lifecycle_state: NonEmptyStr
    lifecycle_health: NonEmptyStr
    migration_provenance: ProvenanceRef


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
    provenance: ProvenanceRef

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
                raise ValueError(
                    "resolved or degraded decisions must select a listed candidate"
                )
        elif self.selected_candidate_id is not None:
            raise ValueError("blocked decisions cannot select a candidate")
        if self.selected_candidate_id is not None:
            selected = next(
                candidate
                for candidate in self.candidates
                if candidate.candidate_id == self.selected_candidate_id
            )
            if (
                selected.compatibility == "incompatible"
                or selected.policy_posture == "forbidden"
            ):
                raise ValueError(
                    "an incompatible or forbidden candidate cannot be selected"
                )
        return self


class CandidateExplanation(StrictControlPlaneModel):
    candidate_id: NonEmptyStr
    disposition: Literal["selected", "eligible", "degraded", "rejected"]
    reason_codes: tuple[NonEmptyStr, ...]
    evidence_refs: tuple[ProvenanceRef, ...]


def candidate_explanation_disposition(
    candidate: RouteCandidate,
    *,
    selected_candidate_id: str | None,
) -> Literal["selected", "eligible", "degraded", "rejected"]:
    """Derive one exact explanation disposition from a route candidate."""

    if candidate.candidate_id == selected_candidate_id:
        return "selected"
    score_codes = tuple(
        reason
        for reason in candidate.reason_codes
        if reason.startswith("resolver_score:")
    )
    score: int | None = None
    if len(score_codes) == 1:
        raw_score = score_codes[0].removeprefix("resolver_score:")
        if re.fullmatch(r"-?\d+", raw_score) is not None:
            score = int(raw_score)
    if score is None or score <= 0:
        return "rejected"
    if (
        candidate.compatibility == "incompatible"
        or candidate.policy_posture == "forbidden"
    ):
        return "rejected"
    if (
        candidate.compatibility == "degraded"
        or candidate.policy_posture == "approval_required"
    ):
        return "degraded"
    return "eligible"


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
        candidate_ids = [item.candidate_id for item in self.candidate_explanations]
        if len(candidate_ids) != len(set(candidate_ids)):
            raise ValueError("candidate explanation ids must be unique")
        selected = [
            item.candidate_id
            for item in self.candidate_explanations
            if item.disposition == "selected"
        ]
        if self.decision_status == "blocked":
            if selected or self.selected_candidate_id is not None:
                raise ValueError(
                    "a blocked explanation cannot contain a selected candidate"
                )
        elif selected != [self.selected_candidate_id]:
            raise ValueError(
                "explanation selection must identify exactly the decision selection"
            )
        return self


class ScenarioBinding(StrictControlPlaneModel):
    schema_version: Literal["aoa_control_plane_v1"] = CONTROL_PLANE_SCHEMA_VERSION
    binding_id: NonEmptyStr
    correlation_id: NonEmptyStr
    scenario: ScenarioRef
    decision_ref: ContentRef
    agent_refs: tuple[AgentRef, ...]
    capability_refs: tuple[CapabilityRef, ...]
    capability_bindings: tuple[ScenarioCapabilityBinding, ...] = ()
    input_refs: tuple[ProvenanceRef, ...] = ()
    input_artifact_bindings: tuple[ScenarioArtifactBinding, ...] = ()
    condition_bindings: tuple[ScenarioConditionBinding, ...] = ()
    requirement_refs: tuple[ProvenanceRef, ...] = ()
    expected_artifact_kinds: tuple[NonEmptyStr, ...] = ()
    provenance: ProvenanceRef

    @model_validator(mode="after")
    def validate_binding_identities(self) -> ScenarioBinding:
        identities = (
            ("agent", [item.agent_id for item in self.agent_refs]),
            (
                "capability",
                [item.capability_id for item in self.capability_refs],
            ),
            (
                "capability requirement",
                [item.requirement_id for item in self.capability_bindings],
            ),
            (
                "input artifact",
                [item.artifact_kind for item in self.input_artifact_bindings],
            ),
            (
                "condition",
                [item.condition_id for item in self.condition_bindings],
            ),
        )
        for label, values in identities:
            if len(values) != len(set(values)):
                raise ValueError(f"scenario binding {label} ids must be unique")
        requirement_keys = [
            (item.owner_repo, item.artifact_ref) for item in self.requirement_refs
        ]
        if len(requirement_keys) != len(set(requirement_keys)):
            raise ValueError(
                "scenario binding requirement refs must be owner-path unique"
            )
        if self.capability_bindings and self.capability_refs != tuple(
            item.capability for item in self.capability_bindings
        ):
            raise ValueError(
                "scenario capability refs must match resolved capability bindings"
            )
        return self


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
    runtime_approval_requirements: tuple[ApprovalRequirement, ...] = ()
    provenance: ProvenanceRef

    @model_validator(mode="after")
    def validate_runtime_owner(self) -> RuntimeProfile:
        if self.runtime_owner != self.provenance.owner_repo:
            raise ValueError("runtime profile provenance must come from runtime_owner")
        if not self.supported_plan_schema_versions:
            raise ValueError("runtime profile must declare supported plan versions")
        if not self.supported_event_schema_versions:
            raise ValueError("runtime profile must declare supported event versions")
        requirement_ids = [
            item.requirement_id for item in self.runtime_approval_requirements
        ]
        if len(requirement_ids) != len(set(requirement_ids)):
            raise ValueError(
                "runtime profile approval requirement ids must be unique"
            )
        if any(
            item.approval_owner != self.provenance
            for item in self.runtime_approval_requirements
        ):
            raise ValueError(
                "runtime profile approval requirements must retain runtime-owner "
                "provenance"
            )
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
    artifact_binding: Literal["scenario_input", "step_output"] = "step_output"
    producer_owner: NonEmptyStr
    required_after_step_id: str | None = None
    terminal_required: bool = False


class EvalRequirement(StrictControlPlaneModel):
    requirement_id: NonEmptyStr
    eval_anchor: NonEmptyStr | None = None
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
        if self.decision_ref != self.scenario_binding.decision_ref:
            raise ValueError(
                "plan and scenario binding decision refs must match"
            )
        if (
            self.schema_version
            not in self.runtime_profile.supported_plan_schema_versions
        ):
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
        approval_id_list = [
            requirement.requirement_id for requirement in self.approval_requirements
        ]
        if len(approval_id_list) != len(set(approval_id_list)):
            raise ValueError("run plan approval requirement ids must be unique")
        approval_ids = set(approval_id_list)
        approval_step_bindings: dict[str, set[str]] = {
            requirement_id: set() for requirement_id in approval_ids
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
            for requirement_id in step.approval_requirement_ids:
                approval_step_bindings[requirement_id].add(step.step_id)
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
        for requirement in self.approval_requirements:
            actual_steps = approval_step_bindings[requirement.requirement_id]
            if not actual_steps:
                raise ValueError(
                    f"approval requirement {requirement.requirement_id!r} "
                    "must bind at least one plan step"
                )
            expected_steps = set(requirement.applies_to_step_ids)
            if expected_steps and actual_steps != expected_steps:
                raise ValueError(
                    f"approval requirement {requirement.requirement_id!r} "
                    "must preserve its explicit step bindings"
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


class ObservedSourceRef(StrictControlPlaneModel):
    """Runtime observation of one exact source pinned by a plan."""

    owner_repo: NonEmptyStr
    artifact_ref: NonEmptyStr
    artifact_digest: Digest


class ObservedABIRef(StrictControlPlaneModel):
    """Runtime observation of one exact ABI pinned by a plan."""

    owner_repo: NonEmptyStr
    abi_id: NonEmptyStr
    abi_version: NonEmptyStr
    artifact_digest: Digest


class RuntimeSnapshotObservation(StrictControlPlaneModel):
    """Runtime-owner observation used before dispatch, resume, or recovery."""

    schema_version: Literal["aoa_control_plane_v1"] = CONTROL_PLANE_SCHEMA_VERSION
    observation_id: NonEmptyStr
    session_id: NonEmptyStr
    correlation_id: NonEmptyStr
    plan_digest: Digest
    source_refs: tuple[ObservedSourceRef, ...]
    abi_refs: tuple[ObservedABIRef, ...]
    observed_at: datetime
    observed_by: ProvenanceRef

    @model_validator(mode="after")
    def validate_observation(self) -> RuntimeSnapshotObservation:
        _require_aware(self.observed_at, "observed_at")
        source_keys = [
            (source.owner_repo, source.artifact_ref) for source in self.source_refs
        ]
        abi_keys = [(abi.owner_repo, abi.abi_id) for abi in self.abi_refs]
        if len(source_keys) != len(set(source_keys)):
            raise ValueError("runtime snapshot observation source refs must be unique")
        if len(abi_keys) != len(set(abi_keys)):
            raise ValueError("runtime snapshot observation ABI refs must be unique")
        return self


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
            raise ValueError("a recovery cursor is only valid for recoverable_failure")
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
            raise ValueError(
                "only a rejected command receipt may include rejection_code"
            )
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
        "approval_decision",
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
    approval_request_ref: ContentRef | None = None
    approval_decision_ref: ContentRef | None = None
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
        if self.event_kind == "approval_requested":
            if self.approval_request_ref is None:
                raise ValueError(
                    "approval_requested events require an approval request ref"
                )
        elif self.approval_request_ref is not None:
            raise ValueError(
                "approval request refs are only valid on approval_requested events"
            )
        if self.event_kind == "approval_decision":
            if self.approval_decision_ref is None:
                raise ValueError(
                    "approval_decision events require an approval decision ref"
                )
        elif self.approval_decision_ref is not None:
            raise ValueError(
                "approval decision refs are only valid on approval_decision events"
            )
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
    assert_plan_snapshot_digest(plan.snapshot)
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
        raise ControlPlaneContractError(
            "observed source set does not match plan snapshot"
        )
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


def assert_runtime_snapshot_observation(
    plan: RunPlan,
    session: SessionHandle,
    observation: RuntimeSnapshotObservation,
) -> None:
    """Require an exact runtime-owner observation of the pinned plan snapshot."""

    assert_run_plan_digest(plan)
    if (
        observation.session_id != session.session_id
        or observation.correlation_id != session.correlation_id
        or observation.plan_digest != plan.plan_digest
    ):
        raise ControlPlaneContractError(
            "runtime snapshot observation is outside the session and plan scope"
        )
    if observation.observed_by.owner_repo != plan.runtime_profile.runtime_owner:
        raise ControlPlaneContractError(
            "runtime snapshot observation does not come from the runtime owner"
        )
    assert_snapshot_current(
        plan.snapshot,
        observed_sources={
            (source.owner_repo, source.artifact_ref): source.artifact_digest
            for source in observation.source_refs
        },
        observed_abis={
            (abi.owner_repo, abi.abi_id): (
                abi.abi_version,
                abi.artifact_digest,
            )
            for abi in observation.abi_refs
        },
    )


def assert_approval_decision_matches_request(
    requirement: ApprovalRequirement,
    request: ApprovalRequest,
    decision: ApprovalDecision,
) -> None:
    """Bind an approval decision to the exact current request and requirement."""

    if (
        request.requirement_id != requirement.requirement_id
        or request.approval_authority != requirement.approval_owner
    ):
        raise ControlPlaneContractError(
            f"approval request does not match requirement {requirement.requirement_id}"
        )
    if (
        decision.request_id != request.request_id
        or decision.requirement_id != request.requirement_id
        or decision.session_id != request.session_id
        or decision.correlation_id != request.correlation_id
        or decision.plan_digest != request.plan_digest
        or decision.snapshot_digest != request.snapshot_digest
        or decision.approval_authority != request.approval_authority
    ):
        raise ControlPlaneContractError(
            f"approval decision scope mismatch for {requirement.requirement_id}"
        )
    if decision.decided_at < request.requested_at:
        raise ControlPlaneContractError(
            f"approval decision predates request {request.request_id}"
        )
    if decision.verdict == "expired":
        if (
            request.expires_at is None
            or decision.decided_at < request.expires_at
        ):
            raise ControlPlaneContractError(
                f"approval expiry is outside request window for {request.request_id}"
            )
    elif (
        request.expires_at is not None
        and decision.decided_at >= request.expires_at
    ):
        raise ControlPlaneContractError(
            f"approval decision exceeded request window for {request.request_id}"
        )


def assert_explanation_matches_decision(
    decision: RouteDecision,
    explanation: RouteExplanation,
) -> None:
    """Require an explanation disposition for every candidate in the decision."""

    if (
        explanation.correlation_id != decision.correlation_id
        or explanation.decision_ref.object_id != decision.decision_id
        or explanation.decision_ref.owner_repo != decision.provenance.owner_repo
        or explanation.decision_ref.schema_version != decision.schema_version
        or explanation.decision_ref.digest != canonical_digest(decision)
        or explanation.decision_status != decision.status
        or explanation.selected_candidate_id != decision.selected_candidate_id
    ):
        raise ControlPlaneContractError(
            "route explanation scope does not match the route decision"
        )
    decision_candidate_ids = [
        candidate.candidate_id for candidate in decision.candidates
    ]
    explanation_ids = [
        candidate.candidate_id for candidate in explanation.candidate_explanations
    ]
    if len(explanation_ids) != len(set(explanation_ids)):
        raise ControlPlaneContractError(
            "route explanation candidate ids must be unique"
        )
    if decision_candidate_ids != explanation_ids:
        raise ControlPlaneContractError(
            "route explanation does not account for candidates in decision order"
        )
    decision_by_id = {
        candidate.candidate_id: candidate for candidate in decision.candidates
    }
    for item in explanation.candidate_explanations:
        candidate = decision_by_id[item.candidate_id]
        if (
            item.reason_codes != candidate.reason_codes
            or item.evidence_refs != candidate.evidence_refs
        ):
            raise ControlPlaneContractError(
                "route explanation does not preserve candidate reasons and evidence"
            )
        expected_disposition = candidate_explanation_disposition(
            candidate,
            selected_candidate_id=decision.selected_candidate_id,
        )
        if item.disposition != expected_disposition:
            raise ControlPlaneContractError(
                "route explanation disposition contradicts the decision candidate"
            )
    expected_ambiguity_codes = tuple(
        reason for reason in decision.reason_codes if reason.startswith("ambiguous_")
    )
    if explanation.ambiguity_codes != expected_ambiguity_codes:
        raise ControlPlaneContractError(
            "route explanation ambiguity codes do not match the decision"
        )


def assert_decision_matches_intent(
    intent: RouteIntent,
    decision: RouteDecision,
) -> None:
    """Require a decision to address the exact owner-qualified intent."""

    if (
        decision.correlation_id != intent.correlation_id
        or decision.intent_ref.object_id != intent.intent_id
        or decision.intent_ref.owner_repo != intent.provenance.owner_repo
        or decision.intent_ref.schema_version != intent.schema_version
        or decision.intent_ref.digest != canonical_digest(intent)
    ):
        raise ControlPlaneContractError(
            "route decision does not reference the exact route intent"
        )


def assert_route_plan_chain(
    intent: RouteIntent,
    decision: RouteDecision,
    explanation: RouteExplanation,
    plan: RunPlan,
) -> None:
    """Validate the content-addressed intent-to-plan control-plane chain."""

    assert_decision_matches_intent(intent, decision)
    assert_explanation_matches_decision(decision, explanation)
    assert_run_plan_digest(plan)
    expected_decision_digest = canonical_digest(decision)
    for decision_ref in (plan.decision_ref, plan.scenario_binding.decision_ref):
        if (
            decision_ref.object_id != decision.decision_id
            or decision_ref.owner_repo != decision.provenance.owner_repo
            or decision_ref.schema_version != decision.schema_version
            or decision_ref.digest != expected_decision_digest
        ):
            raise ControlPlaneContractError(
                "scenario binding or run plan does not reference the exact decision"
            )
    if plan.correlation_id != intent.correlation_id:
        raise ControlPlaneContractError(
            "run plan correlation id does not match the route intent"
        )
    expected_approval_requirements = (
        *decision.approval_requirements,
        *plan.runtime_profile.runtime_approval_requirements,
    )
    if plan.approval_requirements != expected_approval_requirements:
        raise ControlPlaneContractError(
            "run plan approval requirements differ from the exact route and "
            "runtime-profile projections"
        )
    if decision.selected_candidate_id is None:
        raise ControlPlaneContractError(
            "a blocked decision cannot compile into a run plan"
        )
    selected = next(
        candidate
        for candidate in decision.candidates
        if candidate.candidate_id == decision.selected_candidate_id
    )
    binding = plan.scenario_binding
    if selected.scenario != binding.scenario:
        raise ControlPlaneContractError(
            "scenario binding must match an explicit selected scenario"
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

    assert_run_plan_digest(plan)
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
            if age >= requirement.expires_after_seconds:
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

    assert_closeout_bundle_scope(plan, session, outcome, bundle)
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


def assert_closeout_bundle_scope(
    plan: RunPlan,
    session: SessionHandle,
    outcome: RunOutcome,
    bundle: CloseoutBundleRef,
) -> None:
    """Validate runtime scope and the exact owner closeout receipt only."""

    assert_run_plan_digest(plan)
    if (
        outcome.session_id != session.session_id
        or outcome.correlation_id != session.correlation_id
        or outcome.plan_digest != plan.plan_digest
    ):
        raise ControlPlaneContractError("run outcome is outside closeout scope")
    if (
        outcome.closeout_bundle_ref is not None
        and outcome.closeout_bundle_ref != bundle
    ):
        raise ControlPlaneContractError(
            "run outcome names a different closeout bundle"
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
    """Runtime-neutral C1/C2 control-plane behavior surface."""

    def resolve(self, intent: RouteIntent) -> RouteDecision: ...

    def explain(self, decision: RouteDecision) -> RouteExplanation: ...

    def scenario_ref(self, scenario_id: str) -> ScenarioRef: ...

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
    ) -> ScenarioBinding: ...

    def compile(
        self,
        decision: RouteDecision,
        scenario: ScenarioBinding,
        runtime_profile: RuntimeProfile,
    ) -> RunPlan: ...


@runtime_checkable
class RuntimeAdapterProtocol(Protocol):
    """Runtime-owned lifecycle and execution bridge consumed by AoARunner."""

    @property
    def profile(self) -> RuntimeProfile: ...

    def observe_snapshot(
        self,
        plan: RunPlan,
        session: SessionHandle,
    ) -> RuntimeSnapshotObservation: ...

    def dispatch(
        self,
        plan: RunPlan,
        session: SessionHandle,
        command: RuntimeCommand,
    ) -> CommandReceipt: ...

    def approval_requests(
        self,
        session: SessionHandle,
    ) -> Iterable[ApprovalRequest]: ...

    def approval_decisions(
        self,
        session: SessionHandle,
    ) -> Iterable[ApprovalDecision]: ...

    def command_receipts(
        self,
        session: SessionHandle,
    ) -> Iterable[CommandReceipt]: ...

    def renew_approvals(
        self,
        plan: RunPlan,
        session: SessionHandle,
        *,
        requested_at: datetime,
    ) -> Iterable[ApprovalRequest]: ...

    def apply_approval(
        self,
        plan: RunPlan,
        session: SessionHandle,
        approval: ApprovalDecision,
    ) -> RunStatus: ...

    def status(self, session: SessionHandle) -> RunStatus: ...

    def events(
        self,
        session: SessionHandle,
        *,
        after_sequence: int,
    ) -> Iterable[ExecutionEvent]: ...

    def outcome(self, session: SessionHandle) -> RunOutcome | None: ...

    def closeout(
        self,
        plan: RunPlan,
        session: SessionHandle,
        outcome: RunOutcome,
        bundle: CloseoutBundleRef,
    ) -> RunStatus: ...


@runtime_checkable
class AoARunnerProtocol(Protocol):
    """Lifecycle client contract; implementations must delegate execution."""

    def prepare(self, plan: RunPlan) -> SessionHandle: ...

    def restore(
        self,
        plan: RunPlan,
        session: SessionHandle,
        adapter: RuntimeAdapterProtocol,
    ) -> RunStatus: ...

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

    def renew_approvals(
        self,
        session: SessionHandle,
        *,
        requested_at: datetime,
    ) -> tuple[ApprovalRequest, ...]: ...

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

    def sync(
        self,
        session: SessionHandle,
        adapter: RuntimeAdapterProtocol,
    ) -> RunStatus: ...

    def status(self, session: SessionHandle) -> RunStatus: ...

    def approval_requests(
        self,
        session: SessionHandle,
    ) -> tuple[ApprovalRequest, ...]: ...

    def approval_decisions(
        self,
        session: SessionHandle,
    ) -> tuple[ApprovalDecision, ...]: ...

    def events(
        self,
        session: SessionHandle,
    ) -> tuple[ExecutionEvent, ...]: ...

    def command_receipts(
        self,
        session: SessionHandle,
    ) -> tuple[CommandReceipt, ...]: ...

    def outcome(self, session: SessionHandle) -> RunOutcome | None: ...

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
