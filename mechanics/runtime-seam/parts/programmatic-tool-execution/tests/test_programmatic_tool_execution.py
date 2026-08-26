from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

import pytest

from aoa_sdk.contracts.control_plane import ContentRef, ProvenanceRef
from aoa_sdk.contracts.programmatic_execution import (
    ProgrammaticActivation,
    ProgrammaticActivationRequirements,
    ProgrammaticEconomyObservation,
    ProgrammaticEffectCeiling,
    ProgrammaticExecutionObservation,
    ProgrammaticExecutionRequest,
    ProgrammaticObservationDimension,
    ProgrammaticObservationRequirements,
    ProgrammaticToolCallObservation,
    ProgrammaticToolHandle,
    assert_programmatic_execution_observation,
    programmatic_execution_request_digest,
    programmatic_execution_request_ref,
)


NOW = datetime(2026, 8, 26, 15, 30, tzinfo=timezone.utc)


def _digest(value: str) -> str:
    return f"sha256:{hashlib.sha256(value.encode()).hexdigest()}"


def _provenance(artifact: str = "fixture.json") -> ProvenanceRef:
    return ProvenanceRef(
        owner_repo="fixture-owner",
        artifact_ref=artifact,
        source_ref="fixture-source",
        artifact_digest=_digest(artifact),
        schema_ref="fixture.schema.json",
        schema_version="fixture_v1",
    )


def _ref(object_id: str) -> ContentRef:
    return ContentRef(
        object_id=object_id,
        owner_repo="fixture-owner",
        schema_version="fixture_v1",
        digest=_digest(object_id),
    )


def _handle() -> ProgrammaticToolHandle:
    return ProgrammaticToolHandle(
        handle_id="tool-handle:read",
        tool_id="read_file",
        input_schema_ref=_ref("schema:read-input"),
        output_schema_ref=_ref("schema:read-output"),
        effect_class="read_only",
        provenance=_provenance("tool.json"),
    )


def _request(
    *,
    activation: ProgrammaticActivation | None = None,
    observation_requirements: ProgrammaticObservationRequirements | None = None,
    mode: str = "programmatic",
    effect_ceiling: ProgrammaticEffectCeiling | None = None,
) -> ProgrammaticExecutionRequest:
    plan_ref = _ref("plan")
    profile_ref = _ref("runtime-profile")
    return ProgrammaticExecutionRequest(
        execution_id="execution:fixture",
        correlation_id="correlation:fixture",
        adapter_id="fixture-adapter",
        mode=mode,
        plan_ref=plan_ref,
        runtime_profile_ref=profile_ref,
        input_ref=_ref("input"),
        program_ref=_ref("program") if mode == "programmatic" else None,
        tool_handles=(_handle(),),
        effect_ceiling=effect_ceiling
        or ProgrammaticEffectCeiling(sandbox_id="sandbox:fixture"),
        activation_requirements=ProgrammaticActivationRequirements(
            required_plan_ref=plan_ref,
            required_runtime_profile_ref=profile_ref,
        ),
        activation=activation or ProgrammaticActivation(),
        observation_requirements=observation_requirements
        or ProgrammaticObservationRequirements(),
        requested_at=NOW,
        provenance=_provenance("request.json"),
    )


def _admitted_request(
    *,
    observation_requirements: ProgrammaticObservationRequirements | None = None,
) -> ProgrammaticExecutionRequest:
    return _request(
        activation=ProgrammaticActivation(
            state="admitted",
            admission_ref=_ref("admission"),
            admitted_at=NOW,
        ),
        observation_requirements=observation_requirements,
    )


def _economy(*, unavailable: bool = False) -> ProgrammaticEconomyObservation:
    if unavailable:
        return ProgrammaticEconomyObservation(
            availability="unavailable",
            unavailable_reason="provider_usage_not_exposed",
            observed_at=NOW + timedelta(seconds=1),
        )
    return ProgrammaticEconomyObservation(
        availability="observed",
        measurement_source="runtime",
        input_tokens=10,
        cached_input_tokens=2,
        output_tokens=4,
        model_calls=1,
        turns=1,
        tool_schema_bytes=128,
        tool_schema_tokens=32,
        tool_calls=1,
        intermediate_values=1,
        wall_time_ms=5,
        rework_count=0,
        observed_at=NOW + timedelta(seconds=1),
    )


def _dimensions(*, economy_available: bool = True) -> tuple[ProgrammaticObservationDimension, ...]:
    dimensions: list[ProgrammaticObservationDimension] = []
    for dimension in (
        "execution",
        "tool_calls",
        "intermediate_values",
        "failures",
        "wall_time",
        "rework",
    ):
        dimensions.append(
            ProgrammaticObservationDimension(
                dimension=dimension,
                availability="observed",
                evidence_ref=_ref(f"evidence:{dimension}"),
            )
        )
    dimensions.append(
        ProgrammaticObservationDimension(
            dimension="economy",
            availability="observed" if economy_available else "unavailable",
            evidence_ref=_ref("evidence:economy") if economy_available else None,
            reason_code=None if economy_available else "provider_usage_not_exposed",
        )
    )
    return tuple(dimensions)


def _observation(
    request: ProgrammaticExecutionRequest,
    *,
    economy_available: bool = True,
) -> ProgrammaticExecutionObservation:
    call = ProgrammaticToolCallObservation(
        call_id="call:read",
        sequence=1,
        tool_handle_id="tool-handle:read",
        status="succeeded",
        input_ref=_ref("call-input"),
        output_ref=_ref("call-output"),
        intermediate_value_refs=(_ref("intermediate:read"),),
        started_at=NOW,
        finished_at=NOW + timedelta(milliseconds=5),
        wall_time_ms=5,
    )
    return ProgrammaticExecutionObservation(
        request_ref=programmatic_execution_request_ref(request),
        execution_id=request.execution_id,
        correlation_id=request.correlation_id,
        adapter_id=request.adapter_id,
        status="succeeded",
        started_at=NOW,
        finished_at=NOW + timedelta(seconds=1),
        result_ref=_ref("result"),
        tool_calls=(call,),
        intermediate_value_refs=(_ref("intermediate:read"),),
        economy=_economy(unavailable=not economy_available),
        dimension_observations=_dimensions(economy_available=economy_available),
        provenance=_provenance("observation.json"),
    )


def test_request_is_default_off_and_has_no_token_budget() -> None:
    request = _request()

    assert request.activation.state == "not_admitted"
    assert request.activation_requirements.default_enabled is False
    assert "token_budget" not in request.model_dump_json()
    assert programmatic_execution_request_digest(request).startswith("sha256:")


@pytest.mark.parametrize("mode", ["direct", "programmatic"])
def test_direct_and_programmatic_modes_share_the_same_contract(mode: str) -> None:
    request = _request(mode=mode)

    assert request.mode == mode
    assert (request.program_ref is not None) is (mode == "programmatic")


def test_mode_and_effect_ceiling_are_fail_closed() -> None:
    with pytest.raises(ValueError, match="programmatic mode requires a program ref"):
        request = _request(mode="programmatic")
        ProgrammaticExecutionRequest.model_validate(
            request.model_dump(mode="python") | {"program_ref": None}
        )

    with pytest.raises(ValueError, match="exceeds the request effect ceiling"):
        _request(
            effect_ceiling=ProgrammaticEffectCeiling(
                allowed_effect_classes=("runtime_mutation",),
                sandbox_id="sandbox:fixture",
            )
        )


def test_activation_requires_explicit_evidence() -> None:
    with pytest.raises(ValueError, match="requires an admission ref and time"):
        ProgrammaticActivation(state="admitted")

    with pytest.raises(ValueError, match="cannot carry admission evidence"):
        ProgrammaticActivation(state="not_admitted", admission_ref=_ref("admission"))


def test_observation_binds_exact_request_and_handles() -> None:
    request = _admitted_request()
    observation = _observation(request)

    assert_programmatic_execution_observation(request, observation)

    wrong_request = observation.model_copy(update={"request_ref": _ref("other-request")})
    with pytest.raises(ValueError, match="exact request digest"):
        assert_programmatic_execution_observation(request, wrong_request)


def test_missing_economy_can_be_explicitly_retained() -> None:
    requirements = ProgrammaticObservationRequirements(
        missingness_policy="explicit_unavailable"
    )
    request = _admitted_request(observation_requirements=requirements)
    observation = _observation(request, economy_available=False)

    assert_programmatic_execution_observation(request, observation)


def test_rejected_missing_dimension_and_bad_economy_fail_closed() -> None:
    request = _admitted_request()
    observation = _observation(request).model_copy(
        update={
            "dimension_observations": _dimensions(economy_available=False),
        }
    )
    with pytest.raises(ValueError, match="rejected missing dimensions"):
        assert_programmatic_execution_observation(request, observation)

    with pytest.raises(ValueError, match="cached input tokens"):
        ProgrammaticEconomyObservation(
            availability="observed",
            measurement_source="provider",
            input_tokens=1,
            cached_input_tokens=2,
            observed_at=NOW,
        )
