"""Owner-bounded, resumable organ-admission transaction contracts.

The SDK addresses and validates externally issued evidence.  It does not run
owner validators, compute central proof, issue owner/operator acceptance,
mutate the private registry, or activate an effect.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .control_plane import Digest
from .organs import (
    CapabilityContract,
    Identifier,
    MaturityAxis,
    NonEmptyStr,
    OrganOwners,
    PolicyFamily,
    RegistryState,
    SecretFreeRef,
)


ADMISSION_REQUEST_VERSION: Literal["aoa_organ_admission_request_v1"] = (
    "aoa_organ_admission_request_v1"
)
ADMISSION_EVIDENCE_VERSION: Literal["aoa_organ_admission_evidence_v1"] = (
    "aoa_organ_admission_evidence_v1"
)
ADMISSION_RUN_VERSION: Literal["aoa_organ_admission_run_v1"] = (
    "aoa_organ_admission_run_v1"
)
ADMISSION_CANDIDATE_VERSION: Literal["aoa_organ_admission_candidate_v1"] = (
    "aoa_organ_admission_candidate_v1"
)
ADMISSION_DECISION_VERSION: Literal["aoa_organ_admission_decision_v1"] = (
    "aoa_organ_admission_decision_v1"
)
ADMISSION_AUTHORIZATION_VERSION: Literal[
    "aoa_organ_admission_authorization_v1"
] = "aoa_organ_admission_authorization_v1"
ADMISSION_BASELINE_AUDIT_VERSION: Literal[
    "aoa_organ_admission_baseline_audit_v1"
] = "aoa_organ_admission_baseline_audit_v1"

AdmissionStage: TypeAlias = Literal[
    "owner_source",
    "reviewed_revision",
    "package",
    "deploy_manifest",
    "deployed_bytes",
    "process_identity",
    "endpoint",
    "observed_schema",
    "auth_contour",
    "consumer_registration",
    "authenticated_canary",
    "owner_grounding_freshness",
    "central_proof",
    "owner_result_acceptance",
    "rollback_proof",
]
AdmissionEvidenceOutcome: TypeAlias = Literal["passed", "blocked", "rejected"]
AdmissionRunState: TypeAlias = Literal[
    "collecting",
    "ready_for_candidate",
    "blocked",
    "rejected",
]
AdmissionPreviewAction: TypeAlias = Literal[
    "add_capability",
    "replace_capability",
    "refresh_admission",
]
AdmissionDecisionKind: TypeAlias = Literal["owner", "operator"]
AdmissionDecisionValue: TypeAlias = Literal["accepted", "rejected"]
AdmissionBaselineStatus: TypeAlias = Literal[
    "current",
    "refresh_required",
    "capability_absent",
    "not_admitted",
]
AdmissionAxisState: TypeAlias = Literal["current", "missing", "expired"]


class StrictAdmissionModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class AdmissionTarget(StrictAdmissionModel):
    organ_id: Identifier
    capability_id: Identifier
    primitive_ids: Annotated[tuple[Identifier, ...], Field(min_length=1)]
    policy_family: PolicyFamily
    credential_class: Identifier

    @model_validator(mode="after")
    def validate_primitives(self) -> AdmissionTarget:
        if len(self.primitive_ids) != len(set(self.primitive_ids)):
            raise ValueError("admission target primitive ids must be unique")
        return self


class OwnerValidatorBinding(StrictAdmissionModel):
    owner: NonEmptyStr
    validator_ref: SecretFreeRef
    validator_revision: NonEmptyStr
    validator_schema_digest: Digest


class RegistryComparisonAnchor(StrictAdmissionModel):
    registry_id: Identifier
    registry_digest: Digest
    entry_digest: Digest
    entry_state: RegistryState
    observed_at: datetime
    expires_at: datetime

    @field_validator("observed_at", "expires_at")
    @classmethod
    def require_aware_time(cls, value: datetime) -> datetime:
        return _aware_utc(value)

    @model_validator(mode="after")
    def validate_expiry(self) -> RegistryComparisonAnchor:
        if self.expires_at <= self.observed_at:
            raise ValueError("registry comparison expiry must follow observation")
        return self


class AdmissionAxisAudit(StrictAdmissionModel):
    axis: MaturityAxis
    state: AdmissionAxisState
    owner: NonEmptyStr | None = None
    evidence_ref: SecretFreeRef | None = None
    revision: NonEmptyStr | None = None
    observed_at: datetime | None = None
    expires_at: datetime | None = None

    @field_validator("observed_at", "expires_at")
    @classmethod
    def require_aware_optional_time(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        return _aware_utc(value) if value is not None else None


class OrganAdmissionBaselineAudit(StrictAdmissionModel):
    schema_version: Literal["aoa_organ_admission_baseline_audit_v1"] = (
        ADMISSION_BASELINE_AUDIT_VERSION
    )
    audit_id: Digest
    registry_id: Identifier
    registry_digest: Digest
    entry_digest: Digest
    organ_id: Identifier
    capability_id: Identifier
    registry_state: RegistryState
    status: AdmissionBaselineStatus
    evaluated_at: datetime
    projection_expires_at: datetime
    capability_present: bool
    axis_audits: tuple[AdmissionAxisAudit, ...]
    reason_codes: tuple[Identifier, ...]
    admission_current: bool
    owner_validators_executed_by_sdk: Literal[False] = False
    central_proof_computed_by_sdk: Literal[False] = False
    owner_acceptance_inferred_by_sdk: Literal[False] = False
    registry_mutated_by_sdk: Literal[False] = False

    @field_validator("evaluated_at", "projection_expires_at")
    @classmethod
    def require_aware_time(cls, value: datetime) -> datetime:
        return _aware_utc(value)


class OrganAdmissionRequest(StrictAdmissionModel):
    schema_version: Literal["aoa_organ_admission_request_v1"] = (
        ADMISSION_REQUEST_VERSION
    )
    request_id: Identifier
    requested_by: NonEmptyStr
    operator_owner: NonEmptyStr
    consumer_owner: NonEmptyStr
    owners: OrganOwners
    target: AdmissionTarget
    proposed_capability: CapabilityContract
    current_registry: RegistryComparisonAnchor
    owner_validator_bindings: Annotated[
        tuple[OwnerValidatorBinding, ...], Field(min_length=1)
    ]
    requested_at: datetime
    expires_at: datetime
    default_admission: Literal["deny"] = "deny"
    contains_secrets: Literal[False] = False
    automatic_registry_update_allowed: Literal[False] = False
    automatic_effect_activation_allowed: Literal[False] = False
    central_proof_may_be_issued_by_sdk: Literal[False] = False
    owner_acceptance_may_be_issued_by_sdk: Literal[False] = False

    @field_validator("requested_at", "expires_at")
    @classmethod
    def require_aware_time(cls, value: datetime) -> datetime:
        return _aware_utc(value)

    @model_validator(mode="after")
    def validate_request(self) -> OrganAdmissionRequest:
        if self.expires_at <= self.requested_at:
            raise ValueError("admission request expiry must follow request time")
        if self.current_registry.observed_at > self.requested_at:
            raise ValueError("registry comparison cannot postdate the request")
        if self.current_registry.expires_at < self.expires_at:
            raise ValueError("admission request cannot outlive its registry anchor")
        if self.requested_by not in {
            self.owners.source_owner,
            self.owners.access_owner,
            self.consumer_owner,
            self.operator_owner,
        }:
            raise ValueError("admission request must come from an owner or operator")
        capability = self.proposed_capability
        if capability.capability_id != self.target.capability_id:
            raise ValueError("proposed capability does not match admission target")
        if capability.policy_family != self.target.policy_family:
            raise ValueError("proposed capability policy does not match target")
        if capability.credential_class != self.target.credential_class:
            raise ValueError("proposed capability credential does not match target")
        if tuple(item.primitive_id for item in capability.primitives) != (
            self.target.primitive_ids
        ):
            raise ValueError("proposed primitive order and ids must match the target")
        allowed_validator_owners = {
            self.owners.source_owner,
            self.owners.access_owner,
            self.owners.runtime_owner,
            self.owners.proof_owner,
            self.owners.acceptance_owner,
            self.consumer_owner,
            self.operator_owner,
        }
        if any(
            binding.owner not in allowed_validator_owners
            for binding in self.owner_validator_bindings
        ):
            raise ValueError("validator binding must belong to a named owner")
        if len(self.owner_validator_bindings) != len(
            {
                (item.owner, item.validator_ref, item.validator_revision)
                for item in self.owner_validator_bindings
            }
        ):
            raise ValueError("owner validator bindings must be unique")
        return self


class AdmissionEvidenceStatement(StrictAdmissionModel):
    schema_version: Literal["aoa_organ_admission_evidence_v1"] = (
        ADMISSION_EVIDENCE_VERSION
    )
    run_id: Digest
    previous_snapshot_digest: Digest
    stage: AdmissionStage
    issuer: NonEmptyStr
    owner: NonEmptyStr
    target: AdmissionTarget
    subject_ref: SecretFreeRef
    subject_revision: NonEmptyStr
    subject_digest: Digest
    subject_schema_ref: SecretFreeRef
    subject_schema_digest: Digest
    evidence_ref: SecretFreeRef
    evidence_revision: NonEmptyStr
    evidence_digest: Digest
    validator: OwnerValidatorBinding
    validation_receipt_ref: SecretFreeRef
    validation_receipt_digest: Digest
    observed_at: datetime
    expires_at: datetime
    outcome: AdmissionEvidenceOutcome
    reason_codes: tuple[Identifier, ...] = ()
    contains_secrets: Literal[False] = False
    owner_native_validation_claimed: Literal[True] = True

    @field_validator("observed_at", "expires_at")
    @classmethod
    def require_aware_time(cls, value: datetime) -> datetime:
        return _aware_utc(value)

    @model_validator(mode="after")
    def validate_evidence(self) -> AdmissionEvidenceStatement:
        if self.expires_at <= self.observed_at:
            raise ValueError("admission evidence expiry must follow observation")
        if self.issuer != self.owner:
            raise ValueError("admission evidence issuer must be its named owner")
        if self.validator.owner != self.owner:
            raise ValueError("admission evidence validator must belong to its owner")
        if self.outcome == "passed" and self.reason_codes:
            raise ValueError("passed admission evidence cannot carry stop reasons")
        if self.outcome != "passed" and not self.reason_codes:
            raise ValueError("blocked or rejected evidence requires reason codes")
        return self


class AdmissionEvidenceReceipt(AdmissionEvidenceStatement):
    evidence_id: Digest


class OrganAdmissionRun(StrictAdmissionModel):
    schema_version: Literal["aoa_organ_admission_run_v1"] = ADMISSION_RUN_VERSION
    run_id: Digest
    request_digest: Digest
    request: OrganAdmissionRequest
    evidence: tuple[AdmissionEvidenceReceipt, ...]
    snapshot_digest: Digest
    state: AdmissionRunState
    next_stage: AdmissionStage | None
    next_owner: NonEmptyStr | None
    stop_reason_codes: tuple[Identifier, ...] = ()
    owner_validators_executed_by_sdk: Literal[False] = False
    central_proof_computed_by_sdk: Literal[False] = False
    owner_acceptance_inferred_by_sdk: Literal[False] = False
    registry_mutated_by_sdk: Literal[False] = False
    effect_activation_authorized: Literal[False] = False


class RegistryTransitionPreview(StrictAdmissionModel):
    registry_id: Identifier
    base_registry_digest: Digest
    base_entry_digest: Digest
    organ_id: Identifier
    capability_id: Identifier
    from_state: RegistryState
    proposed_state: Literal["admitted"] = "admitted"
    action: AdmissionPreviewAction
    registry_mutation_performed: Literal[False] = False
    compare_and_swap_required: Literal[True] = True


class OrganAdmissionCandidate(StrictAdmissionModel):
    schema_version: Literal["aoa_organ_admission_candidate_v1"] = (
        ADMISSION_CANDIDATE_VERSION
    )
    candidate_id: Digest
    run_id: Digest
    run_snapshot_digest: Digest
    request_digest: Digest
    target: AdmissionTarget
    owners: OrganOwners
    consumer_owner: NonEmptyStr
    operator_owner: NonEmptyStr
    evidence_ids: tuple[Digest, ...]
    preview: RegistryTransitionPreview
    created_at: datetime
    expires_at: datetime
    owner_decision_required: Literal[True] = True
    operator_decision_required: Literal[True] = True
    registry_update_authorized: Literal[False] = False
    registry_mutation_performed: Literal[False] = False
    effect_activation_authorized: Literal[False] = False

    @field_validator("created_at", "expires_at")
    @classmethod
    def require_aware_time(cls, value: datetime) -> datetime:
        return _aware_utc(value)


class AdmissionDecisionStatement(StrictAdmissionModel):
    schema_version: Literal["aoa_organ_admission_decision_v1"] = (
        ADMISSION_DECISION_VERSION
    )
    candidate_id: Digest
    decision_kind: AdmissionDecisionKind
    issuer: NonEmptyStr
    decision: AdmissionDecisionValue
    decision_ref: SecretFreeRef
    decision_artifact_digest: Digest
    decided_at: datetime
    expires_at: datetime
    reason_codes: tuple[Identifier, ...] = ()
    contains_secrets: Literal[False] = False
    registry_mutation_performed: Literal[False] = False

    @field_validator("decided_at", "expires_at")
    @classmethod
    def require_aware_time(cls, value: datetime) -> datetime:
        return _aware_utc(value)

    @model_validator(mode="after")
    def validate_decision(self) -> AdmissionDecisionStatement:
        if self.expires_at <= self.decided_at:
            raise ValueError("admission decision expiry must follow decision time")
        if self.decision == "accepted" and self.reason_codes:
            raise ValueError("accepted admission decision cannot carry stop reasons")
        if self.decision == "rejected" and not self.reason_codes:
            raise ValueError("rejected admission decision requires reason codes")
        return self


class AdmissionDecisionReceipt(AdmissionDecisionStatement):
    decision_id: Digest


class OrganAdmissionAuthorization(StrictAdmissionModel):
    schema_version: Literal["aoa_organ_admission_authorization_v1"] = (
        ADMISSION_AUTHORIZATION_VERSION
    )
    authorization_id: Digest
    candidate_id: Digest
    owner_decision_id: Digest
    operator_decision_id: Digest
    target: AdmissionTarget
    target_record_digest: Digest
    base_registry_digest: Digest
    base_entry_digest: Digest
    authorized_at: datetime
    expires_at: datetime
    registry_update_authorized: Literal[True] = True
    registry_mutation_performed: Literal[False] = False
    compare_and_swap_required: Literal[True] = True
    post_update_projection_verification_required: Literal[True] = True
    effect_activation_authorized: Literal[False] = False
    central_proof_computed_by_sdk: Literal[False] = False
    owner_acceptance_inferred_by_sdk: Literal[False] = False

    @field_validator("authorized_at", "expires_at")
    @classmethod
    def require_aware_time(cls, value: datetime) -> datetime:
        return _aware_utc(value)


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamps must be timezone-aware")
    return value.astimezone(timezone.utc)
