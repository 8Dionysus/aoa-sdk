"""Provider-neutral progressive tool-exposure contracts.

This module deliberately stops at a deterministic, candidate-only disclosure
plan.  It records the exact capability contour, schema identity, freshness,
effect ceiling, approval/rollback references, and rendered visibility budget
without authorizing a runtime invocation or claiming owner acceptance.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Annotated, Literal, TypeAlias

from pydantic import Field, field_validator, model_validator

from .control_plane import Digest
from .organs import (
    EFFECT_POLICY,
    POLICY_RANK,
    CapabilityContract,
    EffectClass,
    OrganOwners,
    PolicyFamily,
    PrimitiveContract,
    QualifiedEvidenceRef,
    RevisionIdentity,
    SecretFreeRef,
    StrictOrganModel,
)


ORGAN_EXPOSURE_CONTRACT_VERSION: Literal["aoa_organ_exposure_v1"] = (
    "aoa_organ_exposure_v1"
)
ORGAN_EXPOSURE_PLAN_VERSION: Literal["aoa_organ_exposure_plan_v1"] = (
    "aoa_organ_exposure_plan_v1"
)
ORGAN_EXPOSURE_SNAPSHOT_VERSION: Literal["aoa_organ_exposure_snapshot_v1"] = (
    "aoa_organ_exposure_snapshot_v1"
)
BASELINE_EVIDENCE_OWNER = "d0-baseline"
BASELINE_EVIDENCE_REF = "receipt://d0/baseline-ready"
BASELINE_EVIDENCE_REVISION_PREFIX = "baseline-"

ExposureFreshnessState: TypeAlias = Literal[
    "fresh",
    "stale",
    "expired",
    "unknown",
    "missing",
    "partial",
    "estimated",
    "provider_reported",
]
ExposureCountPosture: TypeAlias = Literal[
    "measured",
    "provider_reported",
    "estimated",
    "partial",
    "unknown",
    "missing",
]
ExposurePlanState: TypeAlias = Literal["blocked", "candidate"]
ExposureDecision: TypeAlias = Literal["allowed", "denied"]
NonEmptyExposureText = Annotated[str, Field(min_length=1, max_length=512)]


def _aware_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamps must be timezone-aware")
    return value.astimezone(timezone.utc)


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def exposure_digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


class ExposureFreshness(StrictOrganModel):
    """Freshness and TTL for the exact source contour used by disclosure."""

    state: ExposureFreshnessState
    source_ref: SecretFreeRef
    source_digest: Digest
    observed_at: datetime
    expires_at: datetime | None = None
    ttl_seconds: Annotated[int | None, Field(ge=0)] = None
    provider_watermark: NonEmptyExposureText | None = None
    reason_codes: tuple[NonEmptyExposureText, ...] = ()

    @field_validator("observed_at", "expires_at")
    @classmethod
    def require_aware_time(cls, value: datetime | None) -> datetime | None:
        return _aware_utc(value)

    @model_validator(mode="after")
    def validate_freshness(self) -> ExposureFreshness:
        if self.expires_at is not None and self.expires_at <= self.observed_at:
            raise ValueError("exposure freshness expiry must follow observation")
        if self.state in {"fresh", "provider_reported"} and self.expires_at is None:
            raise ValueError("usable exposure freshness requires an expiry")
        if self.state != "fresh" and not self.reason_codes:
            raise ValueError("non-fresh exposure state requires reason codes")
        return self


class ExposureCapabilityBinding(StrictOrganModel):
    """Owner-qualified identity for one capability contour."""

    organ_id: NonEmptyExposureText
    capability_id: NonEmptyExposureText
    qualified_capability_id: NonEmptyExposureText
    owners: OrganOwners
    capability_digest: Digest
    schema_digest: Digest
    source_revision: RevisionIdentity
    freshness: ExposureFreshness
    effect_ceiling: PolicyFamily
    approval_ref: QualifiedEvidenceRef | None = None
    rollback_route: SecretFreeRef

    @model_validator(mode="after")
    def validate_identity(self) -> ExposureCapabilityBinding:
        expected = (
            f"{self.owners.source_owner}:{self.organ_id}:{self.capability_id}"
        )
        if self.qualified_capability_id != expected:
            raise ValueError("qualified capability id is not owner-qualified")
        return self


class VisibleTool(StrictOrganModel):
    """One exact tool visible to a model after explicit disclosure."""

    tool_id: NonEmptyExposureText
    capability_id: NonEmptyExposureText
    primitive_id: NonEmptyExposureText
    mcp_name: NonEmptyExposureText
    effect_class: EffectClass
    policy_family: PolicyFamily
    input_schema_ref: SecretFreeRef | None = None
    output_schema_ref: SecretFreeRef
    schema_digest: Digest
    effect_ceiling: PolicyFamily

    @model_validator(mode="after")
    def validate_tool(self) -> VisibleTool:
        if self.tool_id != f"{self.capability_id}.{self.primitive_id}":
            raise ValueError("visible tool id must bind capability and primitive")
        if self.policy_family != EFFECT_POLICY[self.effect_class]:
            raise ValueError("visible tool effect and policy family do not match")
        if POLICY_RANK[self.policy_family] > POLICY_RANK[self.effect_ceiling]:
            raise ValueError("visible tool exceeds the capability effect ceiling")
        return self


class RenderedExposureSnapshot(StrictOrganModel):
    """Deterministic model-visible tool-set and visibility accounting."""

    schema_version: Literal["aoa_organ_exposure_snapshot_v1"] = (
        ORGAN_EXPOSURE_SNAPSHOT_VERSION
    )
    snapshot_id: Digest
    source_digest: Digest
    tools: tuple[VisibleTool, ...] = ()
    visible_tool_ids: tuple[NonEmptyExposureText, ...] = ()
    rendered_schema_digest: Digest
    rendered_bytes: Annotated[int, Field(ge=0)]
    rendered_tokens: Annotated[int, Field(ge=0)] | None = None
    token_count_posture: ExposureCountPosture = "unknown"
    token_count_method: NonEmptyExposureText | None = None
    observed_at: datetime
    expires_at: datetime | None = None
    refusal_reasons: tuple[NonEmptyExposureText, ...] = ()

    @field_validator("observed_at", "expires_at")
    @classmethod
    def require_aware_time(cls, value: datetime | None) -> datetime | None:
        return _aware_utc(value)

    @model_validator(mode="after")
    def validate_snapshot(self) -> RenderedExposureSnapshot:
        if self.visible_tool_ids != tuple(tool.tool_id for tool in self.tools):
            raise ValueError("visible tool ids must preserve rendered tool order")
        serialized_tools = [tool.model_dump(mode="json") for tool in self.tools]
        if self.rendered_bytes != len(_canonical_json_bytes(serialized_tools)):
            raise ValueError("rendered byte accounting does not match visible tools")
        if self.rendered_schema_digest != exposure_digest(serialized_tools):
            raise ValueError("rendered schema digest does not match visible tools")
        if self.snapshot_id != exposure_digest(
            {
                key: value
                for key, value in self.model_dump(mode="json").items()
                if key != "snapshot_id"
            }
        ):
            raise ValueError("exposure snapshot id is not content addressed")
        if self.rendered_tokens is None:
            if self.token_count_posture not in {"unknown", "missing", "partial"}:
                raise ValueError("token count posture requires a token count")
        elif self.token_count_posture in {"unknown", "missing"}:
            raise ValueError("known token count cannot have unknown posture")
        if self.token_count_posture in {"measured", "provider_reported", "estimated"}:
            if not self.token_count_method:
                raise ValueError("counted tokens require a counting method")
        if self.expires_at is not None and self.expires_at <= self.observed_at:
            raise ValueError("exposure snapshot expiry must follow observation")
        return self


class ExposureSelectionRequest(StrictOrganModel):
    """Explicit request for schema reveal; it is not an activation approval."""

    schema_version: Literal["aoa_organ_exposure_v1"] = ORGAN_EXPOSURE_CONTRACT_VERSION
    request_id: NonEmptyExposureText
    organ_id: NonEmptyExposureText
    capability_id: NonEmptyExposureText
    selected_primitive_ids: tuple[NonEmptyExposureText, ...] = ()
    requested_policy_family: PolicyFamily = "read"
    requested_at: datetime
    expires_at: datetime
    baseline_ready: bool = False
    baseline_evidence: QualifiedEvidenceRef | None = None
    reveal_schemas: bool = False
    selection_reason: NonEmptyExposureText | None = None
    approval_ref: QualifiedEvidenceRef | None = None

    @field_validator("requested_at", "expires_at")
    @classmethod
    def require_aware_time(cls, value: datetime) -> datetime:
        result = _aware_utc(value)
        assert result is not None
        return result

    @model_validator(mode="after")
    def validate_request(self) -> ExposureSelectionRequest:
        if self.expires_at <= self.requested_at:
            raise ValueError("exposure request expiry must follow requested_at")
        if len(set(self.selected_primitive_ids)) != len(self.selected_primitive_ids):
            raise ValueError("selected primitive ids must be unique and ordered")
        if self.baseline_ready and self.baseline_evidence is None:
            raise ValueError("baseline-ready disclosure requires baseline evidence")
        if self.approval_ref is not None and self.approval_ref.observed_at > self.requested_at:
            raise ValueError("approval evidence cannot be from the future")
        return self


class ProgressiveExposurePlan(StrictOrganModel):
    """Candidate-only disclosure plan consumed by a stronger runtime owner."""

    schema_version: Literal["aoa_organ_exposure_plan_v1"] = ORGAN_EXPOSURE_PLAN_VERSION
    plan_id: Digest
    plan_state: ExposurePlanState
    execution_authorized: Literal[False] = False
    activation_authorized: Literal[False] = False
    feature_enabled: bool = False
    baseline_ready: bool = False
    request_id: NonEmptyExposureText
    capability: ExposureCapabilityBinding
    requested_policy_family: PolicyFamily
    requested_primitive_ids: tuple[NonEmptyExposureText, ...] = ()
    visible_tools: tuple[VisibleTool, ...] = ()
    rendered_snapshot: RenderedExposureSnapshot
    approval_ref: QualifiedEvidenceRef | None = None
    rollback_route: SecretFreeRef
    requested_at: datetime
    expires_at: datetime
    expansion_reasons: tuple[NonEmptyExposureText, ...] = ()
    refusal_reasons: tuple[NonEmptyExposureText, ...] = ()
    claim_limit: Literal[
        "This candidate records deterministic disclosure identity and visibility accounting only. It does not authorize activation, execute a tool, prove runtime reachability, establish owner acceptance, or issue central proof."
    ] = (
        "This candidate records deterministic disclosure identity and visibility accounting only. It does not authorize activation, execute a tool, prove runtime reachability, establish owner acceptance, or issue central proof."
    )

    @field_validator("requested_at", "expires_at")
    @classmethod
    def require_aware_time(cls, value: datetime) -> datetime:
        result = _aware_utc(value)
        assert result is not None
        return result

    @model_validator(mode="after")
    def validate_plan(self) -> ProgressiveExposurePlan:
        if self.expires_at <= self.requested_at:
            raise ValueError("exposure plan expiry must follow requested_at")
        if self.visible_tools != self.rendered_snapshot.tools:
            raise ValueError("plan visible tools must match rendered snapshot")
        if len(set(self.requested_primitive_ids)) != len(self.requested_primitive_ids):
            raise ValueError("plan requested primitive ids must be unique and ordered")
        if self.visible_tools:
            if any(
                tool.capability_id != self.capability.capability_id
                for tool in self.visible_tools
            ):
                raise ValueError("plan visible tools must bind the selected capability")
            visible_primitives = tuple(tool.primitive_id for tool in self.visible_tools)
            if visible_primitives != self.requested_primitive_ids:
                raise ValueError(
                    "plan visible tools must preserve the requested primitive selection"
                )
        if self.plan_state == "blocked":
            if self.visible_tools or self.rendered_snapshot.rendered_bytes != 2:
                raise ValueError("blocked disclosure cannot reveal tools or schemas")
            if not self.refusal_reasons:
                raise ValueError("blocked disclosure requires refusal reasons")
        if self.plan_state == "candidate" and not self.expansion_reasons:
            raise ValueError("candidate disclosure requires expansion reasons")
        if self.activation_authorized or self.execution_authorized:
            raise ValueError("progressive exposure plans are candidate-only")
        unsigned = {
            key: value
            for key, value in self.model_dump(mode="json").items()
            if key not in {"plan_id", "claim_limit"}
        }
        if self.plan_id != exposure_digest(unsigned):
            raise ValueError("exposure plan id is not content addressed")
        return self


class ExposureAuthorizationCandidate(StrictOrganModel):
    """Typed handoff from disclosure to the external activation authority."""

    schema_version: Literal["aoa_organ_exposure_plan_v1"] = ORGAN_EXPOSURE_PLAN_VERSION
    plan_id: Digest
    request_id: NonEmptyExposureText
    activation_authorized: Literal[False] = False
    execution_authorized: Literal[False] = False
    authorization_state: Literal["blocked", "external_owner_required"]
    rendered_snapshot_id: Digest
    visible_tool_ids: tuple[NonEmptyExposureText, ...]
    visible_bytes: Annotated[int, Field(ge=0)]
    visible_tokens: Annotated[int, Field(ge=0)] | None = None
    reason_codes: tuple[NonEmptyExposureText, ...]
    approval_ref: QualifiedEvidenceRef | None = None
    rollback_route: SecretFreeRef


def exposure_tool_from_primitive(
    capability: CapabilityContract,
    primitive: PrimitiveContract,
    *,
    schema_digest: Digest,
) -> VisibleTool:
    """Build one deterministic visible tool descriptor from owner source."""

    return VisibleTool(
        tool_id=f"{capability.capability_id}.{primitive.primitive_id}",
        capability_id=capability.capability_id,
        primitive_id=primitive.primitive_id,
        mcp_name=primitive.mcp_name or primitive.primitive_id,
        effect_class=primitive.effect_class,
        policy_family=primitive.policy_family,
        input_schema_ref=primitive.input_schema_ref,
        output_schema_ref=primitive.output_schema_ref,
        schema_digest=schema_digest,
        effect_ceiling=capability.policy_family,
    )
