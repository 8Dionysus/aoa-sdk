"""Contour-addressed OS Abyss organ registry contracts.

The v2 registry makes ``(organ_id, contour_id)`` the admission identity.  It
does not discover runtime state, refresh evidence, provision credentials, or
move owner authority into the SDK.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal, TypeAlias

from pydantic import Field, field_validator, model_validator

from .control_plane import Digest
from .organs import (
    CapabilityContract,
    ConsumerCompatibility,
    EndpointContract,
    EvalStatus,
    FreshnessPolicy,
    FreshnessState,
    HandoffContract,
    Identifier,
    MaturityEvidence,
    NonEmptyStr,
    OrganMaturityVector,
    OrganOwners,
    OrganRevisions,
    POLICY_RANK,
    PolicyFamily,
    QualifiedEvidenceRef,
    RegistryState,
    SecretFreeRef,
    StrictOrganModel,
)


ORGAN_CONTOUR_CONTRACT_VERSION: Literal["aoa_organ_contour_contract_v2"] = (
    "aoa_organ_contour_contract_v2"
)
ORGAN_REGISTRY_SOURCE_V2: Literal["aoa_organ_registry_source_v2"] = (
    "aoa_organ_registry_source_v2"
)
ORGAN_REGISTRY_PROJECTION_V2: Literal["aoa_organ_registry_projection_v2"] = (
    "aoa_organ_registry_projection_v2"
)
ORGAN_REGISTRY_RUNTIME_OVERLAY_V1: Literal[
    "aoa_organ_registry_runtime_overlay_v1"
] = "aoa_organ_registry_runtime_overlay_v1"
ORGAN_CONTOUR_SUPPLEMENT_V1: Literal["aoa_organ_contour_supplement_v1"] = (
    "aoa_organ_contour_supplement_v1"
)

AuthorityClass: TypeAlias = Literal[
    "read",
    "candidate",
    "proof_result",
    "internal_effect",
    "external_effect",
]
ContourCurrentness: TypeAlias = Literal[
    "current",
    "stale_readable",
    "blocked",
    "unknown",
]


class ContourRuntimeIdentity(StrictOrganModel):
    """Non-secret identities required to bind one deployed contour."""

    source_revision: NonEmptyStr
    source_tree_digest: Digest | None = None
    package_name: Identifier
    package_version: NonEmptyStr
    package_digest: Digest | None = None
    deployment_revision: NonEmptyStr | None = None
    deployment_manifest_ref: SecretFreeRef | None = None
    deployment_manifest_digest: Digest | None = None
    deployed_tree_digest: Digest | None = None
    process_ref: SecretFreeRef | None = None
    process_identity: NonEmptyStr | None = None
    dependency_graph_digest: Digest | None = None


class ContourLastGoodState(StrictOrganModel):
    """A separately evidenced rollback target, never an admission shortcut."""

    recorded_at: datetime
    expires_at: datetime
    protocol_version: NonEmptyStr
    endpoint_ref: SecretFreeRef
    credential_class: Identifier
    principal_id: Identifier
    server_schema_digest: Digest
    runtime_identity: ContourRuntimeIdentity
    evidence_refs: Annotated[tuple[QualifiedEvidenceRef, ...], Field(min_length=1)]
    rollback_executed: Literal[False] = False

    @field_validator("recorded_at", "expires_at")
    @classmethod
    def require_aware_time(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("contour last-good timestamps must be timezone-aware")
        return value

    @model_validator(mode="after")
    def validate_expiry(self) -> "ContourLastGoodState":
        if self.expires_at <= self.recorded_at:
            raise ValueError("contour last-good expiry must follow recording")
        return self


class OrganContourRecord(StrictOrganModel):
    """One independently credentialed and admitted organ access contour."""

    contour_id: Identifier
    registry_state: RegistryState
    authority_class: AuthorityClass
    policy_family: PolicyFamily
    credential_class: Identifier
    principal_id: Identifier
    allowlist: Annotated[tuple[NonEmptyStr, ...], Field(min_length=1)]
    capabilities: Annotated[tuple[CapabilityContract, ...], Field(min_length=1)]
    endpoint: EndpointContract | None = None
    runtime_identity: ContourRuntimeIdentity
    runtime_identity_evidence: tuple[QualifiedEvidenceRef, ...] = ()
    revisions: OrganRevisions
    freshness_policy: FreshnessPolicy
    freshness_state: FreshnessState = "unknown"
    freshness_evidence: QualifiedEvidenceRef | None = None
    owner_watermark: NonEmptyStr | None = None
    owner_watermark_evidence: QualifiedEvidenceRef | None = None
    eval_status: EvalStatus = "not_run"
    proof_refs: tuple[QualifiedEvidenceRef, ...] = ()
    acceptance_refs: tuple[QualifiedEvidenceRef, ...] = ()
    consumer_compatibility: tuple[ConsumerCompatibility, ...] = ()
    maturity: OrganMaturityVector
    activation_preconditions: tuple[QualifiedEvidenceRef, ...] = ()
    currentness: ContourCurrentness = "unknown"
    currentness_expires_at: datetime
    observation_route: SecretFreeRef
    rollback_route: SecretFreeRef
    last_good: ContourLastGoodState | None = None

    @field_validator("currentness_expires_at")
    @classmethod
    def require_aware_time(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("contour currentness expiry must be timezone-aware")
        return value

    @model_validator(mode="after")
    def validate_contour(self) -> "OrganContourRecord":
        if len(self.allowlist) != len(set(self.allowlist)):
            raise ValueError("contour allowlist entries must be unique")
        capability_ids = [item.capability_id for item in self.capabilities]
        if len(capability_ids) != len(set(capability_ids)):
            raise ValueError("capability ids must be unique within a contour")
        for capability in self.capabilities:
            if capability.policy_family != self.policy_family:
                raise ValueError("every contour capability must use its policy family")
            if capability.credential_class != self.credential_class:
                raise ValueError("every contour capability must use its credential class")
        exported_names = {
            primitive.mcp_name or primitive.primitive_id
            for capability in self.capabilities
            for primitive in capability.primitives
        }
        if set(self.allowlist) != exported_names:
            raise ValueError("contour allowlist must exactly match exported primitives")
        if self.authority_class != "proof_result":
            if self.authority_class != self.policy_family:
                raise ValueError("authority class must match policy family")
        elif self.policy_family != "read":
            raise ValueError("proof-result contours must remain read-policy surfaces")
        if self.freshness_state != "unknown" and self.freshness_evidence is None:
            raise ValueError("claimed contour freshness requires owner evidence")
        if (self.owner_watermark is None) != (self.owner_watermark_evidence is None):
            raise ValueError("owner watermark and evidence must appear together")
        if self.registry_state == "admitted":
            if self.endpoint is None:
                raise ValueError("an admitted contour requires an endpoint")
            if self.currentness != "current":
                raise ValueError("an admitted contour requires current evidence")
            if not self.activation_preconditions:
                raise ValueError("an admitted contour requires activation preconditions")
            if not self.proof_refs or not self.acceptance_refs:
                raise ValueError("an admitted contour requires proof and acceptance refs")
        if self.last_good is not None:
            if self.last_good.credential_class != self.credential_class:
                raise ValueError("last-good credential contour must not cross authority")
            if self.last_good.principal_id != self.principal_id:
                raise ValueError("last-good principal must match the contour")
        return self


class OrganRecordV2(StrictOrganModel):
    contract_version: Literal["aoa_organ_contour_contract_v2"] = (
        ORGAN_CONTOUR_CONTRACT_VERSION
    )
    organ_id: Identifier
    display_name: NonEmptyStr
    description: Annotated[str, Field(min_length=12, max_length=1024)]
    owners: OrganOwners
    authentication_requirements: tuple[Identifier, ...]
    support_route: SecretFreeRef
    handoff: HandoffContract
    contours: Annotated[tuple[OrganContourRecord, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def validate_contours(self) -> "OrganRecordV2":
        ids = [item.contour_id for item in self.contours]
        if len(ids) != len(set(ids)):
            raise ValueError("contour ids must be unique within an organ")
        return self


class OrganRegistrySourceV2(StrictOrganModel):
    schema_version: Literal["aoa_organ_registry_source_v2"] = ORGAN_REGISTRY_SOURCE_V2
    registry_id: Identifier
    workspace_owner: NonEmptyStr
    authored_at: datetime
    expires_at: datetime
    default_admission: Literal["deny"] = "deny"
    contains_secrets: Literal[False] = False
    owner_decision_refs: Annotated[tuple[SecretFreeRef, ...], Field(min_length=1)]
    records: tuple[OrganRecordV2, ...]

    @field_validator("authored_at", "expires_at")
    @classmethod
    def require_aware_time(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("registry timestamps must be timezone-aware")
        return value

    @model_validator(mode="after")
    def validate_source(self) -> "OrganRegistrySourceV2":
        if self.expires_at <= self.authored_at:
            raise ValueError("registry expiry must follow authored_at")
        organ_ids = [item.organ_id for item in self.records]
        if len(organ_ids) != len(set(organ_ids)):
            raise ValueError("organ ids must be unique in a registry source")
        credential_owners: dict[str, tuple[str, str]] = {}
        principal_owners: dict[str, tuple[str, str]] = {}
        for record in self.records:
            for contour in record.contours:
                identity = (record.organ_id, contour.contour_id)
                previous = credential_owners.get(contour.credential_class)
                if previous is not None and previous != identity:
                    raise ValueError(
                        f"credential class {contour.credential_class!r} is shared by "
                        f"{previous!r} and {identity!r}"
                    )
                credential_owners[contour.credential_class] = identity
                previous_principal = principal_owners.get(contour.principal_id)
                if previous_principal is not None and previous_principal != identity:
                    raise ValueError(
                        f"principal {contour.principal_id!r} is shared by "
                        f"{previous_principal!r} and {identity!r}"
                    )
                principal_owners[contour.principal_id] = identity
        return self


class ContourRuntimeOverlay(StrictOrganModel):
    """Explicit runtime binding; never an admission or evidence refresh."""

    organ_id: Identifier
    contour_id: Identifier
    principal_id: Identifier
    endpoint: EndpointContract | None = None
    runtime_identity: ContourRuntimeIdentity
    runtime_evidence_refs: Annotated[
        tuple[QualifiedEvidenceRef, ...], Field(min_length=1)
    ]
    observation_route: SecretFreeRef
    rollback_route: SecretFreeRef


class OrganRegistryRuntimeOverlay(StrictOrganModel):
    """Owner-reviewed exact runtime identities applied to a v2 shape migration."""

    schema_version: Literal["aoa_organ_registry_runtime_overlay_v1"] = (
        ORGAN_REGISTRY_RUNTIME_OVERLAY_V1
    )
    overlay_id: Identifier
    authored_at: datetime
    expires_at: datetime
    owner_decision_ref: SecretFreeRef
    contours: Annotated[tuple[ContourRuntimeOverlay, ...], Field(min_length=1)]
    admission_asserted: Literal[False] = False
    proof_asserted: Literal[False] = False
    acceptance_asserted: Literal[False] = False
    currentness_refreshed: Literal[False] = False
    contains_secrets: Literal[False] = False

    @field_validator("authored_at", "expires_at")
    @classmethod
    def require_aware_overlay_time(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("runtime overlay timestamps must be timezone-aware")
        return value

    @model_validator(mode="after")
    def validate_overlay(self) -> "OrganRegistryRuntimeOverlay":
        if self.expires_at <= self.authored_at:
            raise ValueError("runtime overlay expiry must follow authored_at")
        identities = [(item.organ_id, item.contour_id) for item in self.contours]
        if len(identities) != len(set(identities)):
            raise ValueError("runtime overlay contour identities must be unique")
        return self


class ContourSupplementEntry(StrictOrganModel):
    """One owner-declared contour shape, without admission state."""

    contour_id: Identifier
    authority_class: AuthorityClass
    policy_family: PolicyFamily
    credential_class: Identifier
    principal_id: Identifier
    capabilities: Annotated[tuple[CapabilityContract, ...], Field(min_length=1)]
    observation_route: SecretFreeRef
    rollback_route: SecretFreeRef

    @model_validator(mode="after")
    def validate_supplement_entry(self) -> "ContourSupplementEntry":
        if self.authority_class != "proof_result":
            if self.authority_class != self.policy_family:
                raise ValueError("supplement authority must match policy family")
        elif self.policy_family != "read":
            raise ValueError("proof-result supplement must remain read-policy")
        if any(item.policy_family != self.policy_family for item in self.capabilities):
            raise ValueError("supplement capabilities must use one policy family")
        if any(
            item.credential_class != self.credential_class
            for item in self.capabilities
        ):
            raise ValueError("supplement capabilities must use one credential")
        return self


class OrganContourSupplement(StrictOrganModel):
    """Owner evidence for adding contour shapes; forced to shadow on merge."""

    schema_version: Literal["aoa_organ_contour_supplement_v1"] = (
        ORGAN_CONTOUR_SUPPLEMENT_V1
    )
    supplement_id: Identifier
    organ_id: Identifier
    source_owner: NonEmptyStr
    source_evidence: QualifiedEvidenceRef
    owner_decision_ref: SecretFreeRef
    contours: Annotated[tuple[ContourSupplementEntry, ...], Field(min_length=1)]
    admission_asserted: Literal[False] = False
    proof_asserted: Literal[False] = False
    acceptance_asserted: Literal[False] = False
    runtime_identity_asserted: Literal[False] = False
    contains_secrets: Literal[False] = False

    @field_validator("contours")
    @classmethod
    def require_unique_supplement_contours(
        cls, value: tuple[ContourSupplementEntry, ...]
    ) -> tuple[ContourSupplementEntry, ...]:
        identities = [item.contour_id for item in value]
        if len(identities) != len(set(identities)):
            raise ValueError("supplement contour identities must be unique")
        return value


class OrganContourProjectionEntry(StrictOrganModel):
    organ_id: Identifier
    contour_id: Identifier
    display_name: NonEmptyStr
    description: NonEmptyStr
    owners: OrganOwners
    authentication_requirements: tuple[Identifier, ...]
    support_route: SecretFreeRef
    handoff: HandoffContract
    contour: OrganContourRecord
    discoverable: bool
    projection_index_evidence: MaturityEvidence


class OrganRegistryProjectionV2(StrictOrganModel):
    schema_version: Literal["aoa_organ_registry_projection_v2"] = (
        ORGAN_REGISTRY_PROJECTION_V2
    )
    registry_id: Identifier
    workspace_owner: NonEmptyStr
    source_digest: Digest
    projection_digest: Digest
    compiled_at: datetime
    expires_at: datetime
    default_admission: Literal["deny"] = "deny"
    contains_secrets: Literal[False] = False
    entries: tuple[OrganContourProjectionEntry, ...]

    @field_validator("compiled_at", "expires_at")
    @classmethod
    def require_aware_time(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("projection timestamps must be timezone-aware")
        return value


def authority_rank(authority: AuthorityClass) -> int:
    if authority == "proof_result":
        return POLICY_RANK["read"]
    return POLICY_RANK[authority]
