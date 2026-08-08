"""Protocol-independent incremental admission-keeper contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal, TypeAlias

from pydantic import Field, field_validator, model_validator

from .control_plane import Digest
from .organs import Identifier, NonEmptyStr, QualifiedEvidenceRef, SecretFreeRef, StrictOrganModel


KEEPER_SPEC_VERSION: Literal["aoa_admission_keeper_spec_v1"] = (
    "aoa_admission_keeper_spec_v1"
)
KEEPER_NODE_VERSION: Literal["aoa_admission_keeper_node_v1"] = (
    "aoa_admission_keeper_node_v1"
)
KEEPER_STATE_VERSION: Literal["aoa_admission_keeper_state_v1"] = (
    "aoa_admission_keeper_state_v1"
)
KEEPER_PLAN_VERSION: Literal["aoa_admission_keeper_plan_v1"] = (
    "aoa_admission_keeper_plan_v1"
)
KEEPER_CYCLE_VERSION: Literal["aoa_admission_keeper_cycle_v1"] = (
    "aoa_admission_keeper_cycle_v1"
)

KeeperStage: TypeAlias = Literal[
    "owner_source",
    "package",
    "deployment",
    "process",
    "endpoint",
    "credential",
    "schema",
    "authenticated_canary",
    "owner_grounding",
    "central_proof",
    "owner_acceptance",
    "rollback",
    "registry_admission",
    "consumer_observation",
]
KeeperNodeOutcome: TypeAlias = Literal["passed", "blocked", "rejected", "revoked"]
KeeperRefreshAction: TypeAlias = Literal["reuse", "refresh", "blocked"]
KeeperCurrentness: TypeAlias = Literal[
    "live",
    "observed",
    "verified",
    "admitted",
    "stale_readable",
    "candidate",
    "blocked",
    "last_good",
]


class KeeperStageSpec(StrictOrganModel):
    stage: KeeperStage
    owner: NonEmptyStr
    validator_ref: SecretFreeRef
    validator_revision: NonEmptyStr
    validator_schema_digest: Digest
    subject_digest: Digest
    dependency_stages: tuple[KeeperStage, ...] = ()
    maximum_age_seconds: Annotated[int, Field(gt=0)]
    cost_weight: Annotated[int, Field(ge=1, le=10_000)] = 1
    automatic_execution_allowed: bool = True

    @model_validator(mode="after")
    def guard_stronger_owner_stages(self) -> "KeeperStageSpec":
        if self.stage in {"central_proof", "owner_acceptance", "registry_admission"}:
            if self.automatic_execution_allowed:
                raise ValueError(
                    f"{self.stage} cannot be automatically issued by the keeper"
                )
        return self


class AdmissionKeeperSpec(StrictOrganModel):
    schema_version: Literal["aoa_admission_keeper_spec_v1"] = KEEPER_SPEC_VERSION
    spec_id: Digest
    organ_id: Identifier
    contour_id: Identifier
    transaction_ref: SecretFreeRef
    registry_anchor_digest: Digest
    target_record_digest: Digest
    authored_at: datetime
    expires_at: datetime
    stages: Annotated[tuple[KeeperStageSpec, ...], Field(min_length=1)]

    @field_validator("authored_at", "expires_at")
    @classmethod
    def require_aware_time(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("keeper spec timestamps must be timezone-aware")
        return value

    @model_validator(mode="after")
    def validate_graph(self) -> "AdmissionKeeperSpec":
        if self.expires_at <= self.authored_at:
            raise ValueError("keeper spec expiry must follow authored_at")
        seen: set[str] = set()
        for stage in self.stages:
            if stage.stage in seen:
                raise ValueError("keeper stages must be unique")
            missing = set(stage.dependency_stages) - seen
            if missing:
                raise ValueError(
                    f"keeper stage {stage.stage!r} has non-prior dependencies: {sorted(missing)}"
                )
            seen.add(stage.stage)
        return self


class AdmissionEvidenceNodeStatement(StrictOrganModel):
    schema_version: Literal["aoa_admission_keeper_node_v1"] = KEEPER_NODE_VERSION
    spec_id: Digest
    organ_id: Identifier
    contour_id: Identifier
    stage: KeeperStage
    stage_spec_digest: Digest
    dependency_node_ids: tuple[Digest, ...]
    owner: NonEmptyStr
    subject_digest: Digest
    receipt: QualifiedEvidenceRef
    observed_at: datetime
    expires_at: datetime
    outcome: KeeperNodeOutcome
    reason_codes: tuple[Identifier, ...] = ()
    contains_secrets: Literal[False] = False
    acceptance_inferred: Literal[False] = False
    proof_verdict_inferred: Literal[False] = False
    registry_mutation_performed: Literal[False] = False

    @field_validator("observed_at", "expires_at")
    @classmethod
    def require_aware_time(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("keeper evidence timestamps must be timezone-aware")
        return value

    @model_validator(mode="after")
    def validate_node(self) -> "AdmissionEvidenceNodeStatement":
        if self.expires_at <= self.observed_at:
            raise ValueError("keeper evidence expiry must follow observation")
        if self.receipt.owner != self.owner:
            raise ValueError("keeper evidence receipt must belong to its stage owner")
        if self.receipt.expires_at is not None and self.expires_at > self.receipt.expires_at:
            raise ValueError("keeper node cannot outlive its owner receipt")
        if self.outcome == "passed" and self.reason_codes:
            raise ValueError("passed keeper evidence cannot carry stop reasons")
        if self.outcome != "passed" and not self.reason_codes:
            raise ValueError("non-passing keeper evidence requires reason codes")
        return self


class AdmissionEvidenceNode(AdmissionEvidenceNodeStatement):
    node_id: Digest


class AdmissionKeeperStageState(StrictOrganModel):
    stage: KeeperStage
    node_id: Digest | None = None
    outcome: KeeperNodeOutcome | None = None
    expires_at: datetime | None = None
    current: bool = False
    reason_codes: tuple[Identifier, ...] = ()

    @field_validator("expires_at")
    @classmethod
    def require_aware_time(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("keeper stage expiry must be timezone-aware")
        return value


class AdmissionKeeperState(StrictOrganModel):
    schema_version: Literal["aoa_admission_keeper_state_v1"] = KEEPER_STATE_VERSION
    state_id: Digest
    revision: Annotated[int, Field(ge=1)]
    spec_id: Digest
    organ_id: Identifier
    contour_id: Identifier
    transaction_ref: SecretFreeRef
    updated_at: datetime
    stages: tuple[AdmissionKeeperStageState, ...]
    currentness: tuple[KeeperCurrentness, ...]
    admission_current: bool
    last_good_state_ref: SecretFreeRef | None = None
    last_good_state_digest: Digest | None = None
    blocker_codes: tuple[Identifier, ...] = ()
    next_safe_stage: KeeperStage | None = None
    immutable_evidence_only: Literal[True] = True
    timestamps_extended_in_place: Literal[False] = False
    owner_acceptance_issued_by_keeper: Literal[False] = False
    proof_verdict_issued_by_keeper: Literal[False] = False

    @field_validator("updated_at")
    @classmethod
    def require_aware_time(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("keeper state timestamp must be timezone-aware")
        return value

    @model_validator(mode="after")
    def validate_last_good(self) -> "AdmissionKeeperState":
        if (self.last_good_state_ref is None) != (self.last_good_state_digest is None):
            raise ValueError("last-good ref and digest must appear together")
        return self


class KeeperRefreshStep(StrictOrganModel):
    stage: KeeperStage
    action: KeeperRefreshAction
    owner: NonEmptyStr
    prior_node_id: Digest | None = None
    dependency_node_ids: tuple[Digest, ...] = ()
    reason_codes: tuple[Identifier, ...] = ()
    cost_weight: Annotated[int, Field(ge=0)]


class AdmissionKeeperRefreshPlan(StrictOrganModel):
    schema_version: Literal["aoa_admission_keeper_plan_v1"] = KEEPER_PLAN_VERSION
    plan_id: Digest
    spec_id: Digest
    prior_state_id: Digest | None = None
    organ_id: Identifier
    contour_id: Identifier
    planned_at: datetime
    refresh_before: datetime
    steps: tuple[KeeperRefreshStep, ...]
    full_refresh_cost: Annotated[int, Field(ge=0)]
    planned_refresh_cost: Annotated[int, Field(ge=0)]
    reused_stage_count: Annotated[int, Field(ge=0)]
    refreshed_stage_count: Annotated[int, Field(ge=0)]
    blocked_stage_count: Annotated[int, Field(ge=0)]
    registry_mutation_authorized: Literal[False] = False

    @field_validator("planned_at", "refresh_before")
    @classmethod
    def require_aware_time(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("keeper plan timestamps must be timezone-aware")
        return value


class AdmissionKeeperCycle(StrictOrganModel):
    schema_version: Literal["aoa_admission_keeper_cycle_v1"] = KEEPER_CYCLE_VERSION
    cycle_id: Digest
    generated_at: datetime
    organ_id: Identifier
    contour_id: Identifier
    transaction_ref: SecretFreeRef
    imported_node_ids: tuple[Digest, ...]
    plan: AdmissionKeeperRefreshPlan
    state: AdmissionKeeperState
    owner_tools_executed_by_sdk: Literal[False] = False
    registry_mutation_performed: Literal[False] = False
    acceptance_inferred: Literal[False] = False
    proof_verdict_inferred: Literal[False] = False

    @field_validator("generated_at")
    @classmethod
    def require_aware_cycle_time(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("keeper cycle timestamp must be timezone-aware")
        return value
