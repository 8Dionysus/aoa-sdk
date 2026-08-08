"""Protocol-independent owner task contracts.

These contracts describe durable handles for owner-run work.  They do not
define MCP methods, execute an organ tool, or grant authority from possession
of a task identifier.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal, TypeAlias

from pydantic import Field, field_validator, model_validator

from .control_plane import Digest
from .organs import Identifier, NonEmptyStr, SecretFreeRef, StrictOrganModel


TASK_RECORD_VERSION: Literal["aoa_owner_task_v1"] = "aoa_owner_task_v1"
TASK_AUDIT_VERSION: Literal["aoa_owner_task_audit_v1"] = "aoa_owner_task_audit_v1"
TASK_STORE_STATUS_VERSION: Literal["aoa_owner_task_store_status_v1"] = (
    "aoa_owner_task_store_status_v1"
)

TaskStatus: TypeAlias = Literal[
    "working",
    "input_required",
    "completed",
    "failed",
    "cancelled",
    "expired",
]
TaskCancellationOutcome: TypeAlias = Literal[
    "not_requested",
    "pending",
    "accepted",
    "too_late",
    "rejected",
]
TASK_STATUSES: tuple[TaskStatus, ...] = (
    "working",
    "input_required",
    "completed",
    "failed",
    "cancelled",
    "expired",
)
TERMINAL_TASK_STATUSES = frozenset({"completed", "failed", "cancelled", "expired"})


class TaskInputRequest(StrictOrganModel):
    request_key: Identifier
    prompt_ref: SecretFreeRef
    input_schema_ref: SecretFreeRef
    input_schema_digest: Digest
    requested_at: datetime
    expires_at: datetime

    @field_validator("requested_at", "expires_at")
    @classmethod
    def require_aware_time(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("task input timestamps must be timezone-aware")
        return value

    @model_validator(mode="after")
    def validate_expiry(self) -> "TaskInputRequest":
        if self.expires_at <= self.requested_at:
            raise ValueError("task input expiry must follow request")
        return self


class AcceptedTaskInput(StrictOrganModel):
    request_key: Identifier
    input_key: Identifier
    input_digest: Digest
    accepted_at: datetime

    @field_validator("accepted_at")
    @classmethod
    def require_aware_time(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("accepted task input timestamp must be timezone-aware")
        return value


class OwnerTaskRecord(StrictOrganModel):
    schema_version: Literal["aoa_owner_task_v1"] = TASK_RECORD_VERSION
    task_id: Annotated[str, Field(min_length=43, max_length=128)]
    principal_id: Identifier
    organ_id: Identifier
    contour_id: Identifier
    tool_name: NonEmptyStr
    arguments_digest: Digest
    owner_run_ref: SecretFreeRef
    idempotency_key: Identifier
    status: TaskStatus
    revision: Annotated[int, Field(ge=1)]
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    poll_interval_ms: Annotated[int, Field(ge=100, le=3_600_000)]
    outstanding_inputs: tuple[TaskInputRequest, ...] = ()
    accepted_inputs: tuple[AcceptedTaskInput, ...] = ()
    cancellation_requested_at: datetime | None = None
    cancellation_outcome: TaskCancellationOutcome = "not_requested"
    result_ref: SecretFreeRef | None = None
    result_digest: Digest | None = None
    error_ref: SecretFreeRef | None = None
    error_digest: Digest | None = None
    evidence_refs: tuple[SecretFreeRef, ...] = ()
    audit_refs: tuple[SecretFreeRef, ...] = ()
    authority_escalation_allowed: Literal[False] = False
    task_id_is_authorization: Literal[False] = False

    @field_validator(
        "created_at", "updated_at", "expires_at", "cancellation_requested_at"
    )
    @classmethod
    def require_aware_time(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("task timestamps must be timezone-aware")
        return value

    @model_validator(mode="after")
    def validate_record(self) -> "OwnerTaskRecord":
        if self.expires_at <= self.created_at or self.updated_at < self.created_at:
            raise ValueError("task expiry must follow creation and updates cannot predate it")
        if self.status == "expired":
            if self.updated_at < self.expires_at:
                raise ValueError("expired task must be persisted at or after its TTL")
        elif self.updated_at >= self.expires_at:
            raise ValueError("non-expired task updates must precede its TTL")
        request_keys = [item.request_key for item in self.outstanding_inputs]
        if len(request_keys) != len(set(request_keys)):
            raise ValueError("outstanding input request keys must be unique")
        input_keys = [item.input_key for item in self.accepted_inputs]
        if len(input_keys) != len(set(input_keys)):
            raise ValueError("accepted input keys must be unique")
        if self.status == "input_required" and not self.outstanding_inputs:
            raise ValueError("input_required tasks need an outstanding request")
        if self.status != "input_required" and self.outstanding_inputs:
            raise ValueError("only input_required tasks may expose outstanding input")
        if (self.result_ref is None) != (self.result_digest is None):
            raise ValueError("task result ref and digest must appear together")
        if (self.error_ref is None) != (self.error_digest is None):
            raise ValueError("task error ref and digest must appear together")
        if self.status == "completed" and self.result_ref is None:
            raise ValueError("completed tasks require a result reference")
        if self.status == "failed" and self.error_ref is None:
            raise ValueError("failed tasks require an error reference")
        if self.status not in {"completed", "failed"} and any(
            value is not None
            for value in (self.result_ref, self.result_digest, self.error_ref, self.error_digest)
        ):
            raise ValueError("only completed or failed tasks may carry terminal payload refs")
        if self.cancellation_outcome == "not_requested":
            if self.cancellation_requested_at is not None:
                raise ValueError("unrequested cancellation cannot have a timestamp")
        elif self.cancellation_requested_at is None:
            raise ValueError("cancellation outcome requires its request timestamp")
        if self.status == "cancelled" and self.cancellation_outcome != "accepted":
            raise ValueError("cancelled task requires accepted cancellation")
        return self


class TaskAuditReceipt(StrictOrganModel):
    schema_version: Literal["aoa_owner_task_audit_v1"] = TASK_AUDIT_VERSION
    audit_id: Digest
    task_id_digest: Digest
    principal_id: Identifier
    organ_id: Identifier
    contour_id: Identifier
    action: Literal[
        "create",
        "get",
        "apply_input",
        "request_cancel",
        "complete",
        "fail",
        "expire",
    ]
    prior_revision: Annotated[int, Field(ge=0)]
    resulting_revision: Annotated[int, Field(ge=1)]
    occurred_at: datetime
    outcome: Literal["applied", "idempotent", "denied"]
    reason_codes: tuple[Identifier, ...] = ()
    record_digest: Digest
    owner_execution_performed_by_sdk: Literal[False] = False
    authority_granted_by_task_id: Literal[False] = False

    @field_validator("occurred_at")
    @classmethod
    def require_aware_time(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("task audit timestamp must be timezone-aware")
        return value


class TaskMutationResult(StrictOrganModel):
    record: OwnerTaskRecord
    audit: TaskAuditReceipt


class TaskStoreQuotaStatus(StrictOrganModel):
    maximum_active_tasks: Annotated[int, Field(ge=1)]
    maximum_active_tasks_per_principal: Annotated[int, Field(ge=1)]
    active_tasks: Annotated[int, Field(ge=0)]
    maximum_observed_active_per_principal: Annotated[int, Field(ge=0)]
    global_remaining: Annotated[int, Field(ge=0)]


class TaskStoreStatus(StrictOrganModel):
    """Aggregate private operational state without task or principal enumeration."""

    schema_version: Literal["aoa_owner_task_store_status_v1"] = (
        TASK_STORE_STATUS_VERSION
    )
    observed_at: datetime
    record_count: Annotated[int, Field(ge=0)]
    active_count: Annotated[int, Field(ge=0)]
    status_counts: dict[TaskStatus, Annotated[int, Field(ge=0)]]
    outstanding_input_count: Annotated[int, Field(ge=0)]
    pending_cancellation_count: Annotated[int, Field(ge=0)]
    expired_unpersisted_count: Annotated[int, Field(ge=0)]
    orphan_candidate_count: Annotated[int, Field(ge=0)]
    orphan_after_seconds: Annotated[int, Field(ge=60)]
    orphan_candidate_basis: Literal[
        "pending_cancellation_without_terminal_transition"
    ] = "pending_cancellation_without_terminal_transition"
    oldest_active_updated_at: datetime | None = None
    next_expiry_at: datetime | None = None
    quota: TaskStoreQuotaStatus
    contains_task_identifiers: Literal[False] = False
    contains_principal_identifiers: Literal[False] = False
    owner_execution_inferred: Literal[False] = False
    admission_inferred: Literal[False] = False

    @field_validator("observed_at", "oldest_active_updated_at", "next_expiry_at")
    @classmethod
    def require_aware_status_time(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("task store status timestamps must be timezone-aware")
        return value

    @model_validator(mode="after")
    def validate_counts(self) -> "TaskStoreStatus":
        expected = set(TASK_STATUSES)
        if set(self.status_counts) != expected:
            raise ValueError("task store status must carry every task state")
        if sum(self.status_counts.values()) != self.record_count:
            raise ValueError("task status counts must equal the record count")
        if self.quota.active_tasks != self.active_count:
            raise ValueError("task quota and active counts must agree")
        return self
