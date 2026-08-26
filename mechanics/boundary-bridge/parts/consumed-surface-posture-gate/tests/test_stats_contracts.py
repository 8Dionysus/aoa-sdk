from __future__ import annotations

import pytest
from pydantic import ValidationError

from aoa_sdk.models import (
    ContentRef,
    INFERENCE_ECONOMY_AUTHORITY_CEILING,
    INFERENCE_ECONOMY_LIFECYCLE_PATHS,
    INFERENCE_ECONOMY_METRIC_PATHS,
    InferenceEconomyObservationRequirement,
    ProvenanceRef,
)


def content_ref(*, owner_repo: str = "aoa-stats") -> ContentRef:
    return ContentRef(
        object_id="inference-economy-observation",
        owner_repo=owner_repo,
        schema_version="aoa_stats_inference_economy_observation_v1",
        digest="sha256:" + "a" * 64,
    )


def provenance() -> ProvenanceRef:
    return ProvenanceRef(
        owner_repo="aoa-sdk",
        artifact_ref="contracts/stats.py",
        source_ref="aoa-sdk:contracts/stats.py",
        artifact_digest="sha256:" + "b" * 64,
        schema_ref="aoa_sdk_inference_economy_requirement_v1",
        schema_version="aoa_sdk_inference_economy_requirement_v1",
    )


def requirement(**updates: object) -> InferenceEconomyObservationRequirement:
    payload: dict[str, object] = {
        "requirement_id": "inference-economy:request-1",
        "correlation_id": "correlation:inference-economy:1",
        "contract_ref": content_ref(),
        "requested_by": provenance(),
        "reason": "Collect comparable execution-economy observations.",
    }
    payload.update(updates)
    return InferenceEconomyObservationRequirement.model_validate(payload)


def test_requirement_defaults_to_full_baseline_gated_observation() -> None:
    request = requirement()

    assert request.metric_paths == INFERENCE_ECONOMY_METRIC_PATHS
    assert request.lifecycle_paths == INFERENCE_ECONOMY_LIFECYCLE_PATHS
    assert request.default_off is True
    assert request.baseline_required is True
    assert request.activation_allowed is False
    assert request.authority_ceiling == INFERENCE_ECONOMY_AUTHORITY_CEILING
    assert request.model_config["extra"] == "forbid"


def test_requirement_can_narrow_observation_without_selecting_a_provider() -> None:
    request = requirement(
        metric_paths=["tokens.input", "tokens.output"],
        lifecycle_paths=["runtime_outcome"],
    )

    assert request.metric_paths == ("tokens.input", "tokens.output")
    assert request.lifecycle_paths == ("runtime_outcome",)


def test_requirement_rejects_foreign_contract_duplicate_paths_and_activation() -> None:
    with pytest.raises(ValidationError, match="owned by aoa-stats"):
        requirement(contract_ref=content_ref(owner_repo="aoa-models"))

    with pytest.raises(ValidationError, match="metric paths must be unique"):
        requirement(metric_paths=["tokens.input", "tokens.input"])

    with pytest.raises(ValidationError):
        requirement(activation_allowed=True)
