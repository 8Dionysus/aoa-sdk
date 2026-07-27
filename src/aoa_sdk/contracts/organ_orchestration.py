"""Typed contracts for explicit cross-organ OS Abyss orchestration.

The contract family records a host-visible chain from owner-qualified KAG
evidence through a memo candidate and bounded eval pressure to an explicit
owner acceptance decision.  It does not call MCP tools, write durable memory,
compute proof, infer acceptance, or execute owner effects.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Literal, TypeAlias

from pydantic import ConfigDict, Field, BaseModel, field_validator, model_validator

from .control_plane import Digest
from .organs import (
    EffectClass,
    FreshnessState,
    Identifier,
    NonEmptyStr,
    PolicyFamily,
    QualifiedEvidenceRef,
    SecretFreeRef,
)


ORCHESTRATION_REQUEST_VERSION: Literal[
    "aoa_cross_organ_orchestration_request_v1"
] = "aoa_cross_organ_orchestration_request_v1"
ORCHESTRATION_RUN_VERSION: Literal["aoa_cross_organ_orchestration_run_v1"] = (
    "aoa_cross_organ_orchestration_run_v1"
)
ORCHESTRATION_STAGE_VERSION: Literal["aoa_cross_organ_stage_v1"] = (
    "aoa_cross_organ_stage_v1"
)
ORCHESTRATION_RECEIPT_VERSION: Literal["aoa_host_stage_receipt_v1"] = (
    "aoa_host_stage_receipt_v1"
)

StageKind: TypeAlias = Literal[
    "kag_evidence",
    "memo_candidate",
    "eval_request",
    "eval_result",
    "owner_acceptance",
]
ArtifactRefKind: TypeAlias = Literal[
    "orchestration_intent",
    "kag_evidence",
    "memo_candidate",
    "eval_request",
    "eval_result",
    "owner_acceptance",
]
TransitionState: TypeAlias = Literal[
    "proceed",
    "stopped",
    "denied",
    "accepted_terminal",
    "rejected_terminal",
]
ReceiptOutcome: TypeAlias = Literal[
    "observed",
    "candidate_created",
    "request_created",
    "validated",
    "accepted",
    "rejected",
    "stopped",
    "denied",
]
AppliedState: TypeAlias = Literal[
    "not_applied",
    "candidate_only",
    "applied",
    "denied",
]
OrchestrationRunState: TypeAlias = Literal[
    "awaiting_kag_evidence",
    "awaiting_memo_candidate",
    "awaiting_eval_request",
    "awaiting_eval_result",
    "awaiting_owner_acceptance",
    "accepted",
    "rejected",
    "stopped",
    "denied",
]


class StrictOrchestrationModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class OrchestrationOwners(StrictOrchestrationModel):
    evidence_owner: NonEmptyStr
    memory_owner: NonEmptyStr
    proof_owner: NonEmptyStr
    acceptance_owner: NonEmptyStr
    control_owner: Literal["aoa-sdk"] = "aoa-sdk"
    runtime_owner: NonEmptyStr


class SchemaIdentity(StrictOrchestrationModel):
    owner: NonEmptyStr
    schema_ref: SecretFreeRef
    schema_digest: Digest
    source_revision: NonEmptyStr
    schema_version: NonEmptyStr


class TypedArtifactRef(StrictOrchestrationModel):
    ref_kind: ArtifactRefKind
    owner: NonEmptyStr
    artifact_ref: SecretFreeRef
    artifact_digest: Digest
    source_revision: NonEmptyStr
    schema_identity: SchemaIdentity
    authority_ceiling: PolicyFamily
    created_at: datetime
    expires_at: datetime | None = None

    @field_validator("created_at", "expires_at")
    @classmethod
    def require_aware_time(cls, value: datetime | None) -> datetime | None:
        return _aware_utc(value)

    @model_validator(mode="after")
    def validate_identity(self) -> TypedArtifactRef:
        if self.schema_identity.owner != self.owner:
            raise ValueError("artifact and schema owner must match")
        if self.expires_at is not None and self.expires_at <= self.created_at:
            raise ValueError("artifact expiry must follow creation")
        return self


class StageSchemaContract(StrictOrchestrationModel):
    stage_kind: StageKind
    owner: NonEmptyStr
    input_ref_kind: ArtifactRefKind
    output_ref_kind: ArtifactRefKind
    output_schema: SchemaIdentity
    authority_ceiling: PolicyFamily
    effect_class: EffectClass
    next_owner: NonEmptyStr | None

    @model_validator(mode="after")
    def validate_schema_owner(self) -> StageSchemaContract:
        if self.output_schema.owner != self.owner:
            raise ValueError("stage output schema must belong to the stage owner")
        return self


class CrossOrganOrchestrationRequest(StrictOrchestrationModel):
    schema_version: Literal["aoa_cross_organ_orchestration_request_v1"] = (
        ORCHESTRATION_REQUEST_VERSION
    )
    request_id: Identifier
    intent: Annotated[str, Field(min_length=12, max_length=2048)]
    requested_by: NonEmptyStr
    host_id: Identifier
    owners: OrchestrationOwners
    root_input: TypedArtifactRef
    stage_contracts: tuple[StageSchemaContract, ...]
    evidence_refs: Annotated[tuple[QualifiedEvidenceRef, ...], Field(min_length=1)]
    created_at: datetime
    expires_at: datetime
    hidden_shared_context_allowed: Literal[False] = False
    hidden_server_chaining_allowed: Literal[False] = False
    automatic_candidate_promotion_allowed: Literal[False] = False
    automatic_acceptance_allowed: Literal[False] = False
    model_confidence_is_acceptance_authority: Literal[False] = False
    host_visible_receipts_required: Literal[True] = True

    @field_validator("created_at", "expires_at")
    @classmethod
    def require_aware_time(cls, value: datetime) -> datetime:
        result = _aware_utc(value)
        assert result is not None
        return result

    @model_validator(mode="after")
    def validate_chain_contract(self) -> CrossOrganOrchestrationRequest:
        if self.expires_at <= self.created_at:
            raise ValueError("orchestration expiry must follow creation")
        if self.root_input.ref_kind != "orchestration_intent":
            raise ValueError("root input must be an orchestration_intent")
        if self.root_input.created_at > self.created_at:
            raise ValueError("root input cannot be created after the request")
        if (
            self.root_input.expires_at is not None
            and self.root_input.expires_at <= self.created_at
        ):
            raise ValueError("root input is expired when the request is created")

        expected = (
            (
                "kag_evidence",
                self.owners.evidence_owner,
                "orchestration_intent",
                "kag_evidence",
                "read",
                "observe",
                self.owners.memory_owner,
            ),
            (
                "memo_candidate",
                self.owners.memory_owner,
                "kag_evidence",
                "memo_candidate",
                "candidate",
                "prepare_candidate",
                self.owners.proof_owner,
            ),
            (
                "eval_request",
                self.owners.proof_owner,
                "memo_candidate",
                "eval_request",
                "candidate",
                "prepare_candidate",
                self.owners.proof_owner,
            ),
            (
                "eval_result",
                self.owners.proof_owner,
                "eval_request",
                "eval_result",
                "read",
                "validate",
                self.owners.acceptance_owner,
            ),
            (
                "owner_acceptance",
                self.owners.acceptance_owner,
                "eval_result",
                "owner_acceptance",
                "internal_effect",
                "accept_source",
                None,
            ),
        )
        observed = tuple(
            (
                item.stage_kind,
                item.owner,
                item.input_ref_kind,
                item.output_ref_kind,
                item.authority_ceiling,
                item.effect_class,
                item.next_owner,
            )
            for item in self.stage_contracts
        )
        if observed != expected:
            raise ValueError(
                "stage contracts must pin the exact KAG -> memo -> eval -> "
                "owner-acceptance chain"
            )
        return self


class HostVisibleStageReceipt(StrictOrchestrationModel):
    schema_version: Literal["aoa_host_stage_receipt_v1"] = (
        ORCHESTRATION_RECEIPT_VERSION
    )
    receipt_id: Identifier
    receipt_ref: SecretFreeRef
    receipt_digest: Digest
    host_id: Identifier
    run_id: Digest
    stage_kind: StageKind
    previous_snapshot_digest: Digest
    input_artifact_digest: Digest
    output_artifact_digest: Digest
    issued_at: datetime
    outcome: ReceiptOutcome
    owner_receipt_refs: tuple[TypedArtifactRef, ...] = ()

    @field_validator("issued_at")
    @classmethod
    def require_aware_time(cls, value: datetime) -> datetime:
        result = _aware_utc(value)
        assert result is not None
        return result


class CrossOrganStageObservation(StrictOrchestrationModel):
    stage_kind: StageKind
    stage_owner: NonEmptyStr
    source_revision: NonEmptyStr
    input_ref: TypedArtifactRef
    output_ref: TypedArtifactRef
    input_schema_identity: SchemaIdentity
    output_schema_identity: SchemaIdentity
    evidence_refs: Annotated[tuple[QualifiedEvidenceRef, ...], Field(min_length=1)]
    freshness_state: FreshnessState
    observed_at: datetime
    expires_at: datetime
    authority_ceiling: PolicyFamily
    effect_class: EffectClass
    applied_state: AppliedState
    receipt: HostVisibleStageReceipt
    next_owner: NonEmptyStr | None
    transition_state: TransitionState
    stop_reason_codes: tuple[Identifier, ...] = ()
    review_ref: QualifiedEvidenceRef | None = None
    acceptance_decision: Literal["accepted", "rejected"] | None = None
    mcp_tools_executed_by_sdk: Literal[False] = False
    model_confidence_is_acceptance_authority: Literal[False] = False

    @field_validator("observed_at", "expires_at")
    @classmethod
    def require_aware_time(cls, value: datetime) -> datetime:
        result = _aware_utc(value)
        assert result is not None
        return result

    @model_validator(mode="after")
    def validate_observation(self) -> CrossOrganStageObservation:
        if self.expires_at <= self.observed_at:
            raise ValueError("stage expiry must follow observation")
        if self.stage_owner != self.output_ref.owner:
            raise ValueError("stage owner must own the output artifact")
        if self.source_revision != self.output_ref.source_revision:
            raise ValueError("stage source revision must match the output artifact")
        if self.input_schema_identity != self.input_ref.schema_identity:
            raise ValueError("input schema identity must match the input artifact")
        if self.output_schema_identity != self.output_ref.schema_identity:
            raise ValueError("output schema identity must match the output artifact")
        if self.authority_ceiling != self.output_ref.authority_ceiling:
            raise ValueError(
                "stage authority ceiling must match the output artifact"
            )
        if self.receipt.stage_kind != self.stage_kind:
            raise ValueError("receipt stage kind does not match the observation")
        if self.receipt.input_artifact_digest != self.input_ref.artifact_digest:
            raise ValueError("receipt does not bind the input artifact")
        if self.receipt.output_artifact_digest != self.output_ref.artifact_digest:
            raise ValueError("receipt does not bind the output artifact")

        terminal = self.transition_state in {
            "stopped",
            "denied",
            "accepted_terminal",
            "rejected_terminal",
        }
        if terminal and self.next_owner is not None:
            raise ValueError("a terminal transition cannot name a next owner")
        if not terminal and self.next_owner is None:
            raise ValueError("a proceeding transition requires a next owner")
        if self.transition_state in {"stopped", "denied", "rejected_terminal"}:
            if not self.stop_reason_codes:
                raise ValueError("a non-success transition requires stop reason codes")
        elif self.stop_reason_codes:
            raise ValueError("a successful transition cannot carry stop reason codes")

        if self.freshness_state not in {"exact", "compatible_drift"}:
            if self.transition_state not in {"stopped", "denied"}:
                raise ValueError("stale or blocked evidence must stop or deny the chain")
        if self.transition_state == "accepted_terminal":
            if self.freshness_state != "exact":
                raise ValueError("owner acceptance requires exact freshness")
            if self.acceptance_decision != "accepted":
                raise ValueError("accepted terminal state needs an accepted decision")
        elif self.transition_state == "rejected_terminal":
            if self.acceptance_decision != "rejected":
                raise ValueError("rejected terminal state needs a rejected decision")
        elif self.acceptance_decision is not None:
            raise ValueError("only the terminal owner stage can decide acceptance")

        if self.effect_class in {"observe", "derive", "validate"}:
            if self.applied_state != "not_applied":
                raise ValueError("read or validation stages cannot claim an effect")
        elif self.effect_class == "prepare_candidate":
            if self.applied_state not in {"candidate_only", "denied"}:
                raise ValueError("candidate stages cannot claim a durable effect")
        elif self.effect_class == "accept_source":
            expected = (
                "applied"
                if self.transition_state == "accepted_terminal"
                else "denied"
            )
            if self.applied_state != expected:
                raise ValueError("owner acceptance effect state is inconsistent")
        else:
            raise ValueError("cross-organ orchestration forbids runtime/external effects")
        return self


class CrossOrganStage(StrictOrchestrationModel):
    schema_version: Literal["aoa_cross_organ_stage_v1"] = (
        ORCHESTRATION_STAGE_VERSION
    )
    sequence: Annotated[int, Field(ge=0, le=4)]
    previous_stage_digest: Digest | None
    stage_digest: Digest
    observation: CrossOrganStageObservation


class CrossOrganOrchestrationRun(StrictOrchestrationModel):
    schema_version: Literal["aoa_cross_organ_orchestration_run_v1"] = (
        ORCHESTRATION_RUN_VERSION
    )
    run_id: Digest
    request_digest: Digest
    request: CrossOrganOrchestrationRequest
    stages: tuple[CrossOrganStage, ...]
    snapshot_digest: Digest
    state: OrchestrationRunState
    next_stage_kind: StageKind | None
    next_owner: NonEmptyStr | None
    stop_reason_codes: tuple[Identifier, ...] = ()
    owner_tools_executed_by_sdk: Literal[False] = False
    proof_computed_by_sdk: Literal[False] = False
    durable_memory_written_by_sdk: Literal[False] = False
    acceptance_inferred_by_sdk: Literal[False] = False
    runtime_execution_authorized: Literal[False] = False


def _aware_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamps must be timezone-aware")
    return value.astimezone(timezone.utc)
