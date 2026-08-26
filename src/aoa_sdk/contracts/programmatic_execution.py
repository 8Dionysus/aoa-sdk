"""Provider-neutral contracts for governed programmatic tool execution.

These models describe the request, tool handles, effect ceiling, explicit
activation state, and runtime observations for one execution.  They do not
select a provider, launch a runtime, authorize an effect, or produce an eval
verdict.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal, TypeAlias

from pydantic import Field, field_validator, model_validator

from .control_plane import (
    ContentRef,
    ControlPlaneContractError,
    Digest,
    NonEmptyStr,
    ProvenanceRef,
    StrictControlPlaneModel,
    _require_aware,
    canonical_digest,
)


PROGRAMMATIC_EXECUTION_SCHEMA_VERSION: Literal[
    "aoa_programmatic_tool_execution_v1"
] = "aoa_programmatic_tool_execution_v1"
PROGRAMMATIC_EXECUTION_ADAPTER_PROTOCOL_VERSION: Literal[
    "aoa_programmatic_tool_adapter_v1"
] = "aoa_programmatic_tool_adapter_v1"

ExecutionMode: TypeAlias = Literal["direct", "programmatic"]
ProgrammaticActivationState: TypeAlias = Literal["not_admitted", "admitted"]
ProgrammaticExecutionStatus: TypeAlias = Literal[
    "succeeded", "partial", "failed", "cancelled"
]
ProgrammaticToolCallStatus: TypeAlias = Literal[
    "succeeded", "failed", "cancelled"
]
ProgrammaticEffectClass: TypeAlias = Literal[
    "read_only", "repo_mutation", "runtime_mutation", "external"
]
ObservationDimension: TypeAlias = Literal[
    "execution",
    "tool_calls",
    "intermediate_values",
    "failures",
    "economy",
    "wall_time",
    "rework",
]
ObservationAvailability: TypeAlias = Literal[
    "observed", "unavailable", "not_applicable"
]
EconomyAvailability: TypeAlias = Literal["observed", "partial", "unavailable"]
MeasurementSource: TypeAlias = Literal["runtime", "provider", "derived"]

NonNegativeInt = Annotated[int, Field(ge=0)]
PositiveInt = Annotated[int, Field(gt=0)]

PROGRAMMATIC_OBSERVATION_DIMENSIONS: tuple[ObservationDimension, ...] = (
    "execution",
    "tool_calls",
    "intermediate_values",
    "failures",
    "economy",
    "wall_time",
    "rework",
)


class ProgrammaticToolHandle(StrictControlPlaneModel):
    """Stable provider-neutral identity for one callable tool."""

    schema_version: Literal[
        "aoa_programmatic_tool_execution_v1"
    ] = PROGRAMMATIC_EXECUTION_SCHEMA_VERSION
    handle_id: NonEmptyStr
    tool_id: NonEmptyStr
    input_schema_ref: ContentRef
    output_schema_ref: ContentRef
    effect_class: ProgrammaticEffectClass
    provenance: ProvenanceRef


class ProgrammaticEffectCeiling(StrictControlPlaneModel):
    """The maximum effect contour admitted for a programmatic request."""

    allowed_effect_classes: tuple[ProgrammaticEffectClass, ...] = ("read_only",)
    sandbox_id: NonEmptyStr
    external_effects_allowed: bool = False
    approval_required: bool = True
    max_tool_calls: PositiveInt | None = None

    @model_validator(mode="after")
    def validate_effects(self) -> ProgrammaticEffectCeiling:
        if not self.allowed_effect_classes:
            raise ValueError("effect ceiling must allow at least one effect class")
        if len(self.allowed_effect_classes) != len(set(self.allowed_effect_classes)):
            raise ValueError("effect ceiling effect classes must be unique")
        has_external = "external" in self.allowed_effect_classes
        if has_external != self.external_effects_allowed:
            raise ValueError(
                "external effect admission must agree with the effect ceiling"
            )
        return self


class ProgrammaticActivationRequirements(StrictControlPlaneModel):
    """Exact bindings that a runtime must satisfy before activation."""

    required_plan_ref: ContentRef
    required_runtime_profile_ref: ContentRef
    required_conditions: tuple[NonEmptyStr, ...] = (
        "exact_plan",
        "exact_runtime_profile",
        "effect_ceiling",
        "observation_requirements",
    )
    default_enabled: Literal[False] = False

    @model_validator(mode="after")
    def validate_conditions(self) -> ProgrammaticActivationRequirements:
        if not self.required_conditions:
            raise ValueError("activation must declare at least one condition")
        if len(self.required_conditions) != len(set(self.required_conditions)):
            raise ValueError("activation conditions must be unique")
        return self


class ProgrammaticActivation(StrictControlPlaneModel):
    """Runtime admission state; source defaults to not admitted."""

    state: ProgrammaticActivationState = "not_admitted"
    admission_ref: ContentRef | None = None
    admitted_at: datetime | None = None

    @field_validator("admitted_at")
    @classmethod
    def require_aware_admission_time(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return _require_aware(value, "admitted_at")

    @model_validator(mode="after")
    def validate_admission_state(self) -> ProgrammaticActivation:
        admitted = self.state == "admitted"
        if admitted and (self.admission_ref is None or self.admitted_at is None):
            raise ValueError(
                "admitted programmatic execution requires an admission ref and time"
            )
        if not admitted and (self.admission_ref is not None or self.admitted_at is not None):
            raise ValueError(
                "unadmitted programmatic execution cannot carry admission evidence"
            )
        return self


class ProgrammaticObservationRequirements(StrictControlPlaneModel):
    """Required dimensions and explicit missingness policy for one run."""

    required_dimensions: tuple[ObservationDimension, ...] = (
        PROGRAMMATIC_OBSERVATION_DIMENSIONS
    )
    missingness_policy: Literal["reject_missing", "explicit_unavailable"] = (
        "reject_missing"
    )

    @model_validator(mode="after")
    def validate_dimensions(self) -> ProgrammaticObservationRequirements:
        if not self.required_dimensions:
            raise ValueError("observation requirements must name dimensions")
        if len(self.required_dimensions) != len(set(self.required_dimensions)):
            raise ValueError("observation dimensions must be unique")
        return self


class ProgrammaticExecutionRequest(StrictControlPlaneModel):
    """One exact direct or programmatic execution request."""

    schema_version: Literal[
        "aoa_programmatic_tool_execution_v1"
    ] = PROGRAMMATIC_EXECUTION_SCHEMA_VERSION
    execution_id: NonEmptyStr
    correlation_id: NonEmptyStr
    adapter_id: NonEmptyStr
    mode: ExecutionMode
    plan_ref: ContentRef
    runtime_profile_ref: ContentRef
    input_ref: ContentRef
    program_ref: ContentRef | None = None
    tool_handles: tuple[ProgrammaticToolHandle, ...]
    effect_ceiling: ProgrammaticEffectCeiling
    activation_requirements: ProgrammaticActivationRequirements
    activation: ProgrammaticActivation = Field(default_factory=ProgrammaticActivation)
    observation_requirements: ProgrammaticObservationRequirements
    requested_at: datetime
    provenance: ProvenanceRef

    @field_validator("requested_at")
    @classmethod
    def require_aware_request_time(cls, value: datetime) -> datetime:
        return _require_aware(value, "requested_at")

    @model_validator(mode="after")
    def validate_request(self) -> ProgrammaticExecutionRequest:
        if not self.tool_handles:
            raise ValueError("programmatic execution requires at least one tool handle")
        handle_ids = [handle.handle_id for handle in self.tool_handles]
        if len(handle_ids) != len(set(handle_ids)):
            raise ValueError("tool handle ids must be unique within a request")
        if self.mode == "programmatic" and self.program_ref is None:
            raise ValueError("programmatic mode requires a program ref")
        if self.mode == "direct" and self.program_ref is not None:
            raise ValueError("direct mode cannot carry a program ref")
        if (
            self.activation_requirements.required_plan_ref != self.plan_ref
            or self.activation_requirements.required_runtime_profile_ref
            != self.runtime_profile_ref
        ):
            raise ValueError(
                "activation requirements must bind the request plan and runtime profile"
            )
        allowed_effects = set(self.effect_ceiling.allowed_effect_classes)
        if any(handle.effect_class not in allowed_effects for handle in self.tool_handles):
            raise ValueError("a tool handle exceeds the request effect ceiling")
        return self


class ProgrammaticFailure(StrictControlPlaneModel):
    """Typed failure detail without provider-specific error semantics."""

    failure_code: NonEmptyStr
    stage: Literal["activation", "adapter", "tool", "observation", "cancel"]
    detail_ref: ContentRef | None = None
    retryable: bool = False


class ProgrammaticToolCallObservation(StrictControlPlaneModel):
    """One observed tool call and its bounded intermediate refs."""

    call_id: NonEmptyStr
    sequence: PositiveInt
    tool_handle_id: NonEmptyStr
    status: ProgrammaticToolCallStatus
    input_ref: ContentRef
    output_ref: ContentRef | None = None
    intermediate_value_refs: tuple[ContentRef, ...] = ()
    failure: ProgrammaticFailure | None = None
    started_at: datetime
    finished_at: datetime | None = None
    wall_time_ms: NonNegativeInt | None = None

    @field_validator("started_at", "finished_at")
    @classmethod
    def require_aware_call_time(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return _require_aware(value, "tool call time")

    @model_validator(mode="after")
    def validate_call(self) -> ProgrammaticToolCallObservation:
        if self.finished_at is not None and self.finished_at < self.started_at:
            raise ValueError("tool call finished_at must not precede started_at")
        if self.status == "succeeded":
            if self.output_ref is None or self.failure is not None:
                raise ValueError("successful tool calls require output and no failure")
        elif self.failure is None or self.output_ref is not None:
            raise ValueError(
                "failed or cancelled tool calls require failure and no output"
            )
        refs = [
            (ref.owner_repo, ref.object_id) for ref in self.intermediate_value_refs
        ]
        if len(refs) != len(set(refs)):
            raise ValueError("intermediate value refs must be unique per tool call")
        return self


class ProgrammaticEconomyObservation(StrictControlPlaneModel):
    """Observed economy counters; no counter is an execution budget."""

    availability: EconomyAvailability
    measurement_source: MeasurementSource | None = None
    input_tokens: NonNegativeInt | None = None
    cached_input_tokens: NonNegativeInt | None = None
    output_tokens: NonNegativeInt | None = None
    model_calls: NonNegativeInt | None = None
    turns: NonNegativeInt | None = None
    tool_schema_bytes: NonNegativeInt | None = None
    tool_schema_tokens: NonNegativeInt | None = None
    tool_calls: NonNegativeInt | None = None
    intermediate_values: NonNegativeInt | None = None
    wall_time_ms: NonNegativeInt | None = None
    rework_count: NonNegativeInt | None = None
    unavailable_reason: NonEmptyStr | None = None
    observed_at: datetime

    @field_validator("observed_at")
    @classmethod
    def require_aware_economy_time(cls, value: datetime) -> datetime:
        return _require_aware(value, "economy observation time")

    @model_validator(mode="after")
    def validate_economy(self) -> ProgrammaticEconomyObservation:
        measurements = (
            self.input_tokens,
            self.cached_input_tokens,
            self.output_tokens,
            self.model_calls,
            self.turns,
            self.tool_schema_bytes,
            self.tool_schema_tokens,
            self.tool_calls,
            self.intermediate_values,
            self.wall_time_ms,
            self.rework_count,
        )
        if self.availability == "unavailable":
            if any(value is not None for value in measurements):
                raise ValueError("unavailable economy cannot carry measurements")
            if self.measurement_source is not None or self.unavailable_reason is None:
                raise ValueError(
                    "unavailable economy requires a reason and no measurement source"
                )
            return self
        if self.measurement_source is None or not any(
            value is not None for value in measurements
        ):
            raise ValueError(
                "observed or partial economy requires a source and measurement"
            )
        if (
            self.cached_input_tokens is not None
            and self.input_tokens is not None
            and self.cached_input_tokens > self.input_tokens
        ):
            raise ValueError("cached input tokens cannot exceed input tokens")
        if self.unavailable_reason is not None:
            raise ValueError("available economy cannot carry an unavailable reason")
        return self


class ProgrammaticObservationDimension(StrictControlPlaneModel):
    """Availability receipt for one required observation dimension."""

    dimension: ObservationDimension
    availability: ObservationAvailability
    evidence_ref: ContentRef | None = None
    reason_code: NonEmptyStr | None = None

    @model_validator(mode="after")
    def validate_dimension(self) -> ProgrammaticObservationDimension:
        if self.availability == "observed":
            if self.evidence_ref is None or self.reason_code is not None:
                raise ValueError("observed dimensions require only an evidence ref")
        elif self.evidence_ref is not None or self.reason_code is None:
            raise ValueError(
                "unavailable dimensions require only a reason code"
            )
        return self


class ProgrammaticExecutionObservation(StrictControlPlaneModel):
    """Runtime record for one execution, including explicit missingness."""

    schema_version: Literal[
        "aoa_programmatic_tool_execution_v1"
    ] = PROGRAMMATIC_EXECUTION_SCHEMA_VERSION
    request_ref: ContentRef
    execution_id: NonEmptyStr
    correlation_id: NonEmptyStr
    adapter_id: NonEmptyStr
    status: ProgrammaticExecutionStatus
    started_at: datetime
    finished_at: datetime
    result_ref: ContentRef | None = None
    tool_calls: tuple[ProgrammaticToolCallObservation, ...] = ()
    intermediate_value_refs: tuple[ContentRef, ...] = ()
    economy: ProgrammaticEconomyObservation
    failure: ProgrammaticFailure | None = None
    dimension_observations: tuple[ProgrammaticObservationDimension, ...]
    provenance: ProvenanceRef

    @field_validator("started_at", "finished_at")
    @classmethod
    def require_aware_observation_time(cls, value: datetime) -> datetime:
        return _require_aware(value, "execution observation time")

    @model_validator(mode="after")
    def validate_observation(self) -> ProgrammaticExecutionObservation:
        if self.finished_at < self.started_at:
            raise ValueError("execution finished_at must not precede started_at")
        if self.status == "succeeded":
            if self.result_ref is None or self.failure is not None:
                raise ValueError("successful execution requires a result and no failure")
        elif self.status in {"failed", "cancelled"}:
            if self.failure is None or self.result_ref is not None:
                raise ValueError(
                    "failed or cancelled execution requires failure and no result"
                )
        elif self.failure is not None and self.result_ref is None:
            raise ValueError("partial execution failure must retain a result ref")

        call_ids = [call.call_id for call in self.tool_calls]
        sequences = [call.sequence for call in self.tool_calls]
        if len(call_ids) != len(set(call_ids)):
            raise ValueError("tool call ids must be unique")
        if sequences != list(range(1, len(sequences) + 1)):
            raise ValueError("tool call sequences must be contiguous and ordered")
        refs = [
            (ref.owner_repo, ref.object_id) for ref in self.intermediate_value_refs
        ]
        if len(refs) != len(set(refs)):
            raise ValueError("execution intermediate value refs must be unique")
        dimensions = [item.dimension for item in self.dimension_observations]
        if not dimensions or len(dimensions) != len(set(dimensions)):
            raise ValueError("execution must have unique dimension observations")
        if (
            self.economy.tool_calls is not None
            and self.economy.tool_calls != len(self.tool_calls)
        ):
            raise ValueError("economy tool_calls must match the observed call count")
        if (
            self.economy.intermediate_values is not None
            and self.economy.intermediate_values != len(self.intermediate_value_refs)
        ):
            raise ValueError(
                "economy intermediate_values must match the observed ref count"
            )
        return self


def programmatic_execution_request_digest(
    request: ProgrammaticExecutionRequest,
) -> Digest:
    """Return the canonical digest of one immutable request."""

    return canonical_digest(request)


def programmatic_execution_request_ref(
    request: ProgrammaticExecutionRequest,
) -> ContentRef:
    """Build the content ref that an observation must repeat exactly."""

    return ContentRef(
        object_id=f"programmatic-execution-request:{request.execution_id}",
        owner_repo=request.provenance.owner_repo,
        schema_version=PROGRAMMATIC_EXECUTION_SCHEMA_VERSION,
        digest=programmatic_execution_request_digest(request),
    )


def assert_programmatic_execution_admitted(
    request: ProgrammaticExecutionRequest,
) -> None:
    """Fail closed unless an explicit runtime admission is present."""

    if request.activation.state != "admitted":
        raise ControlPlaneContractError(
            "programmatic execution is not admitted; source defaults to off"
        )
    if request.activation.admission_ref is None or request.activation.admitted_at is None:
        raise ControlPlaneContractError(
            "programmatic execution admission is missing its exact evidence"
        )


def assert_programmatic_execution_observation(
    request: ProgrammaticExecutionRequest,
    observation: ProgrammaticExecutionObservation,
) -> None:
    """Validate observation identity, handles, ceilings, and missingness."""

    assert_programmatic_execution_admitted(request)
    if observation.request_ref != programmatic_execution_request_ref(request):
        raise ControlPlaneContractError(
            "execution observation does not bind the exact request digest"
        )
    if (
        observation.execution_id != request.execution_id
        or observation.correlation_id != request.correlation_id
        or observation.adapter_id != request.adapter_id
    ):
        raise ControlPlaneContractError(
            "execution observation is outside the request identity scope"
        )

    handles = {handle.handle_id for handle in request.tool_handles}
    unknown_handles = {
        call.tool_handle_id for call in observation.tool_calls
    } - handles
    if unknown_handles:
        raise ControlPlaneContractError(
            f"execution observation contains unknown tool handles: {sorted(unknown_handles)}"
        )
    max_tool_calls = request.effect_ceiling.max_tool_calls
    if max_tool_calls is not None and len(observation.tool_calls) > max_tool_calls:
        raise ControlPlaneContractError("execution exceeds the admitted tool-call ceiling")

    observed_dimensions = {
        item.dimension: item for item in observation.dimension_observations
    }
    required = set(request.observation_requirements.required_dimensions)
    missing = required - observed_dimensions.keys()
    if missing:
        raise ControlPlaneContractError(
            f"execution observation is missing dimensions: {sorted(missing)}"
        )
    if request.observation_requirements.missingness_policy == "reject_missing":
        unavailable = {
            dimension
            for dimension in required
            if observed_dimensions[dimension].availability != "observed"
        }
        if unavailable:
            raise ControlPlaneContractError(
                f"execution observation has rejected missing dimensions: {sorted(unavailable)}"
            )
    economy_dimension = observed_dimensions.get("economy")
    if economy_dimension is not None:
        if (
            economy_dimension.availability == "observed"
            and observation.economy.availability == "unavailable"
        ):
            raise ControlPlaneContractError(
                "economy dimension is observed but economy counters are unavailable"
            )
        if (
            economy_dimension.availability != "observed"
            and observation.economy.availability != "unavailable"
        ):
            raise ControlPlaneContractError(
                "economy counters are present while the economy dimension is unavailable"
            )
