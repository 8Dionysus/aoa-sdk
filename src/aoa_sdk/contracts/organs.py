"""Protocol-independent contracts for the OS Abyss organ access fabric.

The models in this module describe desired access state, bounded discovery,
candidate activation intent, and result metadata. They do not discover organs
from repository or process presence, provision credentials, execute runtime
work, accept owner truth, or issue proof verdicts.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Any, Generic, Literal, TypeAlias, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .control_plane import Digest


ORGAN_CONTRACT_VERSION: Literal["aoa_organ_contract_v1"] = "aoa_organ_contract_v1"
ORGAN_REGISTRY_SOURCE_VERSION: Literal["aoa_organ_registry_source_v1"] = (
    "aoa_organ_registry_source_v1"
)
ORGAN_REGISTRY_PROJECTION_VERSION: Literal["aoa_organ_registry_projection_v1"] = (
    "aoa_organ_registry_projection_v1"
)
ORGAN_ACTIVATION_PLAN_VERSION: Literal["aoa_organ_activation_plan_v1"] = (
    "aoa_organ_activation_plan_v1"
)
ORGAN_RESULT_ENVELOPE_VERSION: Literal["aoa_organ_result_envelope_v1"] = (
    "aoa_organ_result_envelope_v1"
)
ORGAN_ADAPTER_PROTOCOL_VERSION: Literal["aoa_organ_adapter_v1"] = (
    "aoa_organ_adapter_v1"
)

Identifier = Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9._-]{1,127}$")]
NonEmptyStr = Annotated[str, Field(min_length=1)]
SecretFreeRef = Annotated[str, Field(min_length=3, max_length=512)]

RegistryState: TypeAlias = Literal[
    "declared",
    "package_candidate",
    "deploy_candidate",
    "shadow",
    "admitted",
    "suspended",
    "deprecated",
    "retired",
]
PolicyFamily: TypeAlias = Literal[
    "read",
    "candidate",
    "internal_effect",
    "external_effect",
]
EffectClass: TypeAlias = Literal[
    "observe",
    "derive",
    "validate",
    "prepare_candidate",
    "apply_runtime",
    "accept_source",
    "external_emit",
    "external_change",
]
PrimitiveKind: TypeAlias = Literal["tool", "resource", "resource_template", "prompt"]
FreshnessState: TypeAlias = Literal[
    "exact",
    "compatible_drift",
    "stale_readable",
    "blocked",
    "unknown",
    "rollback_required",
]
AxisState: TypeAlias = Literal["asserted", "not_asserted", "not_applicable"]
EvalStatus: TypeAlias = Literal[
    "not_run",
    "candidate",
    "passed",
    "failed",
    "expired",
]
MaturityAxis: TypeAlias = Literal[
    "declared",
    "owner_reviewed",
    "packaged",
    "exported",
    "deployed",
    "process_alive",
    "endpoint_ready",
    "registry_indexed",
    "consumer_registered",
    "schema_observed",
    "call_succeeded",
    "result_grounded",
    "freshness_satisfied",
    "owner_accepted",
    "cross_organ_proven",
    "rollback_proven",
]

POLICY_RANK: dict[PolicyFamily, int] = {
    "read": 0,
    "candidate": 1,
    "internal_effect": 2,
    "external_effect": 3,
}
EFFECT_POLICY: dict[EffectClass, PolicyFamily] = {
    "observe": "read",
    "derive": "read",
    "validate": "read",
    "prepare_candidate": "candidate",
    "apply_runtime": "internal_effect",
    "accept_source": "internal_effect",
    "external_emit": "external_effect",
    "external_change": "external_effect",
}
ACTIVATABLE_STATES = frozenset({"admitted"})
NON_DISCOVERABLE_STATES = frozenset(
    {"suspended", "deprecated", "retired"}
)


class StrictOrganModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class OrganOwners(StrictOrganModel):
    source_owner: NonEmptyStr
    access_owner: NonEmptyStr
    control_owner: Literal["aoa-sdk"] = "aoa-sdk"
    runtime_owner: NonEmptyStr
    proof_owner: NonEmptyStr
    acceptance_owner: NonEmptyStr


class QualifiedEvidenceRef(StrictOrganModel):
    owner: NonEmptyStr
    evidence_ref: SecretFreeRef
    revision: NonEmptyStr
    observed_at: datetime
    expires_at: datetime | None = None

    @field_validator("observed_at", "expires_at")
    @classmethod
    def require_aware_time(cls, value: datetime | None) -> datetime | None:
        return _aware_utc(value)

    @model_validator(mode="after")
    def validate_expiry(self) -> QualifiedEvidenceRef:
        if self.expires_at is not None and self.expires_at <= self.observed_at:
            raise ValueError("evidence expiry must be after its observation")
        return self


class RevisionIdentity(StrictOrganModel):
    revision: NonEmptyStr
    digest: Digest | None = None
    schema_digest: Digest | None = None


class OrganRevisions(StrictOrganModel):
    source: RevisionIdentity
    package: RevisionIdentity | None = None
    deploy: RevisionIdentity | None = None
    consumer_schema: RevisionIdentity | None = None


class FreshnessPolicy(StrictOrganModel):
    policy_id: Identifier
    max_age_seconds: Annotated[int, Field(gt=0)]
    stale_readable_seconds: Annotated[int, Field(ge=0)] = 0
    cache_scope: Literal["none", "request", "task", "agent", "workspace"]
    provider_watermark_required: bool = True


class CredentialContours(StrictOrganModel):
    read: Identifier
    candidate: Identifier | None = None
    internal_effect: Identifier | None = None
    external_effect: Identifier | None = None

    @model_validator(mode="after")
    def require_distinct_contours(self) -> CredentialContours:
        values = [
            value
            for value in (
                self.read,
                self.candidate,
                self.internal_effect,
                self.external_effect,
            )
            if value is not None
        ]
        if len(values) != len(set(values)):
            raise ValueError("credential contours must be distinct across policy families")
        return self

    def for_policy(self, policy_family: PolicyFamily) -> str | None:
        return getattr(self, policy_family)


class PrimitiveContract(StrictOrganModel):
    primitive_id: Identifier
    kind: PrimitiveKind
    effect_class: EffectClass
    policy_family: PolicyFamily
    input_schema_ref: SecretFreeRef | None = None
    output_schema_ref: SecretFreeRef
    approval_required: bool = False
    approval_owner: NonEmptyStr | None = None
    idempotency: Literal[
        "read_only",
        "idempotent",
        "idempotency_key_required",
        "non_idempotent",
    ]
    rollback_route: SecretFreeRef | None = None
    maximum_blast_radius: NonEmptyStr
    annotations_are_security_enforcement: Literal[False] = False

    @model_validator(mode="after")
    def validate_effect_policy(self) -> PrimitiveContract:
        expected = EFFECT_POLICY[self.effect_class]
        if self.policy_family != expected:
            raise ValueError(
                f"effect class {self.effect_class!r} requires policy family {expected!r}"
            )
        if self.policy_family == "read":
            if self.approval_required:
                raise ValueError("read primitives cannot require effect approval")
            if self.rollback_route is not None:
                raise ValueError("read primitives cannot claim a rollback route")
            if self.approval_owner is not None:
                raise ValueError("read primitives cannot claim an approval owner")
            if self.idempotency != "read_only":
                raise ValueError("read primitives must declare read_only idempotency")
        else:
            if self.kind != "tool":
                raise ValueError("effectful primitives must be tools")
            if self.rollback_route is None:
                raise ValueError("effectful primitives require a rollback route")
        if self.policy_family in {"internal_effect", "external_effect"}:
            if not self.approval_required or self.approval_owner is None:
                raise ValueError("effectful primitives require explicit approval")
        elif self.policy_family == "candidate":
            if self.approval_required or self.approval_owner is not None:
                raise ValueError(
                    "candidate preparation cannot claim effect approval authority"
                )
        return self


class CapabilityContract(StrictOrganModel):
    capability_id: Identifier
    summary: Annotated[str, Field(min_length=12, max_length=512)]
    policy_family: PolicyFamily
    credential_class: Identifier
    primitives: tuple[PrimitiveContract, ...]
    task_intent_terms: tuple[Identifier, ...] = ()
    owner_payload_schema_ref: SecretFreeRef
    eval_refs: tuple[SecretFreeRef, ...] = ()

    @model_validator(mode="after")
    def validate_primitives(self) -> CapabilityContract:
        if not self.primitives:
            raise ValueError("a capability must expose at least one primitive")
        ids = [primitive.primitive_id for primitive in self.primitives]
        if len(ids) != len(set(ids)):
            raise ValueError("primitive ids must be unique within a capability")
        if any(
            POLICY_RANK[primitive.policy_family] > POLICY_RANK[self.policy_family]
            for primitive in self.primitives
        ):
            raise ValueError("a primitive cannot exceed its capability policy ceiling")
        return self


class EndpointContract(StrictOrganModel):
    adapter_id: Identifier
    adapter_protocol_version: Literal["aoa_organ_adapter_v1"] = (
        ORGAN_ADAPTER_PROTOCOL_VERSION
    )
    connection_mode: Literal["direct_owner"] = "direct_owner"
    transport: Literal["stdio", "streamable-http", "owner-api", "none"]
    endpoint_ref: SecretFreeRef
    protocol_versions: tuple[NonEmptyStr, ...]
    server_schema_digest: Digest | None = None

    @model_validator(mode="after")
    def validate_protocols(self) -> EndpointContract:
        if not self.protocol_versions:
            raise ValueError("an endpoint must declare at least one protocol version")
        return self


class ConsumerCompatibility(StrictOrganModel):
    consumer_id: Identifier
    support_state: Literal["supported", "shadow", "blocked", "unknown"]
    protocol_versions: tuple[NonEmptyStr, ...] = ()
    observed_schema_digest: Digest | None = None
    evidence_ref: QualifiedEvidenceRef | None = None


class MaturityEvidence(StrictOrganModel):
    state: AxisState
    evidence: QualifiedEvidenceRef | None = None
    freshness_policy: NonEmptyStr | None = None

    @model_validator(mode="after")
    def validate_assertion(self) -> MaturityEvidence:
        if self.state == "asserted":
            if self.evidence is None or self.freshness_policy is None:
                raise ValueError(
                    "an asserted maturity axis needs owner evidence and freshness policy"
                )
        elif self.evidence is not None or self.freshness_policy is not None:
            raise ValueError(
                "a non-asserted maturity axis cannot carry assertion evidence"
            )
        return self


class OrganMaturityVector(StrictOrganModel):
    declared: MaturityEvidence
    owner_reviewed: MaturityEvidence
    packaged: MaturityEvidence
    exported: MaturityEvidence
    deployed: MaturityEvidence
    process_alive: MaturityEvidence
    endpoint_ready: MaturityEvidence
    registry_indexed: MaturityEvidence
    consumer_registered: MaturityEvidence
    schema_observed: MaturityEvidence
    call_succeeded: MaturityEvidence
    result_grounded: MaturityEvidence
    freshness_satisfied: MaturityEvidence
    owner_accepted: MaturityEvidence
    cross_organ_proven: MaturityEvidence
    rollback_proven: MaturityEvidence


class HandoffContract(StrictOrganModel):
    input_ref_kind: Identifier
    output_ref_kind: Identifier
    next_owner: NonEmptyStr
    stop_states: tuple[Identifier, ...]
    hidden_server_chaining_allowed: Literal[False] = False


class OrganRecord(StrictOrganModel):
    contract_version: Literal["aoa_organ_contract_v1"] = ORGAN_CONTRACT_VERSION
    organ_id: Identifier
    display_name: NonEmptyStr
    description: Annotated[str, Field(min_length=12, max_length=1024)]
    owners: OrganOwners
    registry_state: RegistryState
    authority_ceiling: PolicyFamily
    authentication_requirements: tuple[Identifier, ...]
    credential_contours: CredentialContours
    revisions: OrganRevisions
    freshness_policy: FreshnessPolicy
    freshness_state: FreshnessState = "unknown"
    freshness_evidence: QualifiedEvidenceRef | None = None
    eval_refs: tuple[SecretFreeRef, ...] = ()
    eval_status: EvalStatus = "not_run"
    eval_evidence: QualifiedEvidenceRef | None = None
    capabilities: tuple[CapabilityContract, ...]
    endpoint: EndpointContract | None = None
    consumer_compatibility: tuple[ConsumerCompatibility, ...] = ()
    maturity: OrganMaturityVector
    activation_preconditions: tuple[QualifiedEvidenceRef, ...] = ()
    rollback_route: SecretFreeRef
    support_route: SecretFreeRef
    handoff: HandoffContract

    @model_validator(mode="after")
    def validate_record(self) -> OrganRecord:
        ids = [capability.capability_id for capability in self.capabilities]
        if len(ids) != len(set(ids)):
            raise ValueError("capability ids must be unique within an organ")
        if any(
            POLICY_RANK[capability.policy_family] > POLICY_RANK[self.authority_ceiling]
            for capability in self.capabilities
        ):
            raise ValueError("a capability cannot exceed the organ authority ceiling")
        for capability in self.capabilities:
            expected_credential = self.credential_contours.for_policy(
                capability.policy_family
            )
            if expected_credential is None:
                raise ValueError(
                    f"capability {capability.capability_id!r} has no credential contour"
                )
            if capability.credential_class != expected_credential:
                raise ValueError(
                    f"capability {capability.capability_id!r} must use its "
                    f"{capability.policy_family!r} credential contour"
                )
        if self.freshness_state != "unknown" and self.freshness_evidence is None:
            raise ValueError("a claimed freshness state needs owner-qualified evidence")
        if self.registry_state == "admitted":
            if self.endpoint is None:
                raise ValueError("an admitted organ requires a direct owner endpoint")
            if self.revisions.package is None or self.revisions.deploy is None:
                raise ValueError("an admitted organ requires package and deploy identity")
            if not self.activation_preconditions:
                raise ValueError("an admitted organ requires activation preconditions")
            required_axes = (
                "declared",
                "owner_reviewed",
                "packaged",
                "exported",
                "deployed",
                "process_alive",
                "endpoint_ready",
                "registry_indexed",
                "consumer_registered",
                "schema_observed",
                "call_succeeded",
                "result_grounded",
                "freshness_satisfied",
                "owner_accepted",
                "rollback_proven",
            )
            missing_axes = [
                axis
                for axis in required_axes
                if getattr(self.maturity, axis).state != "asserted"
            ]
            if missing_axes:
                raise ValueError(
                    "an admitted organ requires asserted maturity axes: "
                    + ", ".join(missing_axes)
                )
            if self.freshness_state != "exact":
                raise ValueError("an admitted organ requires exact owner freshness")
            if self.eval_status != "passed" or self.eval_evidence is None:
                raise ValueError(
                    "an admitted organ requires passed eval status and evidence"
                )
            supported_consumers = [
                consumer
                for consumer in self.consumer_compatibility
                if consumer.support_state == "supported"
                and consumer.evidence_ref is not None
            ]
            if not supported_consumers:
                raise ValueError(
                    "an admitted organ requires an evidenced supported consumer"
                )
        return self


class OrganRegistrySource(StrictOrganModel):
    schema_version: Literal["aoa_organ_registry_source_v1"] = (
        ORGAN_REGISTRY_SOURCE_VERSION
    )
    registry_id: Identifier
    workspace_owner: NonEmptyStr
    authored_at: datetime
    expires_at: datetime
    default_admission: Literal["deny"] = "deny"
    contains_secrets: Literal[False] = False
    owner_decision_refs: tuple[SecretFreeRef, ...]
    records: tuple[OrganRecord, ...]

    @field_validator("authored_at", "expires_at")
    @classmethod
    def require_aware_time(cls, value: datetime) -> datetime:
        result = _aware_utc(value)
        assert result is not None
        return result

    @model_validator(mode="after")
    def validate_source(self) -> OrganRegistrySource:
        if self.expires_at <= self.authored_at:
            raise ValueError("registry expiry must be after authored_at")
        ids = [record.organ_id for record in self.records]
        if len(ids) != len(set(ids)):
            raise ValueError("organ ids must be unique in a registry source")
        if not self.owner_decision_refs:
            raise ValueError("a registry source requires owner decision refs")
        contour_owners: dict[str, tuple[str, PolicyFamily]] = {}
        for record in self.records:
            for policy_family in POLICY_RANK:
                credential_class = record.credential_contours.for_policy(policy_family)
                if credential_class is None:
                    continue
                previous = contour_owners.get(credential_class)
                current = (record.organ_id, policy_family)
                if previous is not None and previous != current:
                    raise ValueError(
                        f"credential contour {credential_class!r} is shared by "
                        f"{previous!r} and {current!r}"
                    )
                contour_owners[credential_class] = current
        return self


class CatalogCapability(StrictOrganModel):
    capability_id: Identifier
    summary: NonEmptyStr
    policy_family: PolicyFamily
    primitive_ids: tuple[Identifier, ...]
    primitive_namespaces: tuple[Identifier, ...]
    effect_classes: tuple[EffectClass, ...]
    task_intent_terms: tuple[Identifier, ...] = ()


class OrganProjectionEntry(StrictOrganModel):
    organ_id: Identifier
    display_name: NonEmptyStr
    description: NonEmptyStr
    registry_state: RegistryState
    discoverable: bool
    owners: OrganOwners
    authority_ceiling: PolicyFamily
    authentication_requirements: tuple[Identifier, ...]
    credential_classes: tuple[Identifier, ...]
    revisions: OrganRevisions
    freshness_policy: FreshnessPolicy
    freshness_state: FreshnessState
    freshness_evidence: QualifiedEvidenceRef | None = None
    eval_refs: tuple[SecretFreeRef, ...] = ()
    eval_status: EvalStatus = "not_run"
    eval_evidence: QualifiedEvidenceRef | None = None
    capabilities: tuple[CapabilityContract, ...]
    endpoint: EndpointContract | None = None
    consumer_compatibility: tuple[ConsumerCompatibility, ...] = ()
    maturity: OrganMaturityVector
    activation_preconditions: tuple[QualifiedEvidenceRef, ...] = ()
    rollback_route: SecretFreeRef
    support_route: SecretFreeRef
    handoff: HandoffContract


class OrganRegistryProjection(StrictOrganModel):
    schema_version: Literal["aoa_organ_registry_projection_v1"] = (
        ORGAN_REGISTRY_PROJECTION_VERSION
    )
    registry_id: Identifier
    workspace_owner: NonEmptyStr
    source_digest: Digest
    projection_digest: Digest
    compiled_at: datetime
    expires_at: datetime
    default_admission: Literal["deny"] = "deny"
    contains_secrets: Literal[False] = False
    entries: tuple[OrganProjectionEntry, ...]

    @field_validator("compiled_at", "expires_at")
    @classmethod
    def require_aware_time(cls, value: datetime) -> datetime:
        result = _aware_utc(value)
        assert result is not None
        return result


class CatalogEntry(StrictOrganModel):
    organ_id: Identifier
    display_name: NonEmptyStr
    registry_state: RegistryState
    authority_ceiling: PolicyFamily
    source_owner: NonEmptyStr
    access_owner: NonEmptyStr
    freshness_state: FreshnessState
    eval_status: EvalStatus
    capabilities: tuple[CatalogCapability, ...]


class CatalogResult(StrictOrganModel):
    registry_digest: Digest
    entries: tuple[CatalogEntry, ...]
    result_bytes: Annotated[int, Field(ge=0)]
    schema_bytes_loaded: Literal[0] = 0
    truncated: bool
    hidden_state_counts: dict[RegistryState, Annotated[int, Field(ge=0)]]


class ActivationRequest(StrictOrganModel):
    request_id: Identifier
    organ_id: Identifier
    capability_id: Identifier
    primitive_id: Identifier
    consumer_id: Identifier
    requested_policy_family: PolicyFamily
    authorized_policy_families: tuple[PolicyFamily, ...]
    credential_class: Identifier
    observed_server_schema_digest: Digest
    observed_consumer_schema_digest: Digest
    requested_at: datetime
    expires_at: datetime
    precondition_evidence: tuple[QualifiedEvidenceRef, ...]
    approval_ref: QualifiedEvidenceRef | None = None
    exact_effect_target: NonEmptyStr | None = None

    @field_validator("requested_at", "expires_at")
    @classmethod
    def require_aware_time(cls, value: datetime) -> datetime:
        result = _aware_utc(value)
        assert result is not None
        return result

    @model_validator(mode="after")
    def validate_request(self) -> ActivationRequest:
        if self.expires_at <= self.requested_at:
            raise ValueError("activation request expiry must follow requested_at")
        if self.requested_policy_family not in self.authorized_policy_families:
            raise ValueError("requested policy family is not in the explicit allowlist")
        if self.requested_policy_family in {"internal_effect", "external_effect"}:
            if self.approval_ref is None:
                raise ValueError("effect activation requires explicit approval evidence")
        if self.requested_policy_family == "external_effect" and not self.exact_effect_target:
            raise ValueError("external effect activation requires an exact target")
        return self


class OrganActivationPlan(StrictOrganModel):
    schema_version: Literal["aoa_organ_activation_plan_v1"] = (
        ORGAN_ACTIVATION_PLAN_VERSION
    )
    plan_id: Digest
    plan_kind: Literal["candidate_only"] = "candidate_only"
    execution_authorized: Literal[False] = False
    registry_digest: Digest
    organ_id: Identifier
    capability_id: Identifier
    primitive_id: Identifier
    owners: OrganOwners
    policy_family: PolicyFamily
    effect_class: EffectClass
    credential_class: Identifier
    endpoint: EndpointContract
    source_revision: RevisionIdentity
    package_revision: RevisionIdentity
    deploy_revision: RevisionIdentity
    server_schema_digest: Digest
    consumer_schema_digest: Digest
    consumer_id: Identifier
    precondition_evidence: tuple[QualifiedEvidenceRef, ...]
    approval_ref: QualifiedEvidenceRef | None = None
    exact_effect_target: NonEmptyStr | None = None
    expires_at: datetime
    rollback_route: SecretFreeRef

    @field_validator("expires_at")
    @classmethod
    def require_aware_time(cls, value: datetime) -> datetime:
        result = _aware_utc(value)
        assert result is not None
        return result


class CompatibilityObservation(StrictOrganModel):
    organ_id: Identifier
    registry_digest: Digest
    expected_deploy_revision: NonEmptyStr | None
    observed_deploy_revision: NonEmptyStr | None
    expected_server_schema_digest: Digest | None
    observed_server_schema_digest: Digest | None
    expected_consumer_schema_digest: Digest | None
    observed_consumer_schema_digest: Digest | None
    state: FreshnessState
    reason_codes: tuple[Identifier, ...]
    observed_at: datetime
    evidence_refs: tuple[QualifiedEvidenceRef, ...]

    @field_validator("observed_at")
    @classmethod
    def require_aware_time(cls, value: datetime) -> datetime:
        result = _aware_utc(value)
        assert result is not None
        return result


class OrganResultMetadata(StrictOrganModel):
    contract_version: Literal["aoa_organ_result_envelope_v1"] = (
        ORGAN_RESULT_ENVELOPE_VERSION
    )
    organ_id: Identifier
    capability_id: Identifier
    primitive_id: Identifier
    owners: OrganOwners
    authority_ceiling: PolicyFamily
    source_revision: NonEmptyStr
    deployed_revision: NonEmptyStr | None
    package_identity: RevisionIdentity | None
    server_schema_digest: Digest
    consumer_observed_digest: Digest
    provider_watermark: NonEmptyStr | None
    observed_at: datetime
    freshness_state: FreshnessState
    freshness_policy: FreshnessPolicy
    ttl_seconds: Annotated[int | None, Field(ge=0)] = None
    cache_scope: Literal["none", "request", "task", "agent", "workspace"]
    evidence_refs: tuple[QualifiedEvidenceRef, ...]
    effect_class: EffectClass
    applied_state: Literal["not_applied", "applied", "denied", "candidate_only"]
    warnings: tuple[NonEmptyStr, ...] = ()
    receipt_ref: QualifiedEvidenceRef | None = None
    trace_id: NonEmptyStr
    self_report_is_security_authority: Literal[False] = False

    @field_validator("observed_at")
    @classmethod
    def require_aware_time(cls, value: datetime) -> datetime:
        result = _aware_utc(value)
        assert result is not None
        return result

    @model_validator(mode="after")
    def validate_effect_state(self) -> OrganResultMetadata:
        if self.cache_scope != self.freshness_policy.cache_scope:
            raise ValueError("result cache scope must match its freshness policy")
        if self.effect_class in {"observe", "derive", "validate"}:
            if self.applied_state != "not_applied":
                raise ValueError("read and derived results cannot claim an applied effect")
        elif self.effect_class == "prepare_candidate":
            if self.applied_state not in {"candidate_only", "denied"}:
                raise ValueError(
                    "candidate results cannot claim a durable applied effect"
                )
        elif self.applied_state == "applied" and self.receipt_ref is None:
            raise ValueError("an applied effect requires an owner-qualified receipt")
        if (
            self.freshness_policy.provider_watermark_required
            and self.provider_watermark is None
        ):
            raise ValueError("the freshness policy requires a provider watermark")
        return self


OwnerPayloadT = TypeVar("OwnerPayloadT")


class OrganResultEnvelope(BaseModel, Generic[OwnerPayloadT]):
    """Minimal common metadata plus an owner-specific typed payload."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    metadata: OrganResultMetadata
    owner_payload_schema_ref: SecretFreeRef
    owner_payload: OwnerPayloadT


def _aware_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamps must be timezone-aware")
    return value.astimezone(timezone.utc)


def model_json_payload(model: BaseModel) -> dict[str, Any]:
    """Return a JSON-safe payload without weakening the concrete model type."""

    return model.model_dump(mode="json")
