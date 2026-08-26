"""Runtime-neutral Goal lifecycle request, legitimacy, and execution contracts.

The semantic owner supplies the current Goal/DAG/ownership context and resolves
whether a requested transition is legitimate.  A runtime adapter receives only
that typed request plus the accepted decision; it never invents responsibility,
selects a Goal, or interprets a transport response as semantic acceptance.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal, Protocol

from pydantic import field_validator, model_validator

from .control_plane import (
    ContentRef,
    ControlPlaneContractError,
    NonEmptyStr,
    ProvenanceRef,
    StrictControlPlaneModel,
    canonical_digest,
)


GOAL_LIFECYCLE_SCHEMA_VERSION: Literal["aoa_goal_lifecycle_v1"] = (
    "aoa_goal_lifecycle_v1"
)
GOAL_LIFECYCLE_RESOLVER_VERSION = "aoa_goal_lifecycle_legitimacy_v1"

GoalLifecycleStage = Literal[
    "requested",
    "accepted",
    "executed",
    "delivered",
    "semantically_accepted",
    "closed",
]
GoalLifecycleDecisionStatus = Literal["accepted", "rejected"]
GoalLifecycleExecutionStatus = Literal["executed", "replayed", "rejected"]


def _require_aware(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value


class GoalLifecycleTransition(StrictControlPlaneModel):
    """One owner-admitted edge in the current Goal lifecycle graph."""

    from_state: NonEmptyStr
    to_state: NonEmptyStr
    transition_kind: NonEmptyStr


class GoalLifecycleRequest(StrictControlPlaneModel):
    """A single instance request to change one owner-bound Goal state."""

    schema_version: Literal["aoa_goal_lifecycle_v1"] = GOAL_LIFECYCLE_SCHEMA_VERSION
    request_id: NonEmptyStr
    correlation_id: NonEmptyStr
    idempotency_key: NonEmptyStr
    goal_ref: ContentRef
    observed_state: NonEmptyStr
    expected_state: NonEmptyStr
    desired_state: NonEmptyStr
    transition_kind: NonEmptyStr
    reason: NonEmptyStr
    evidence_refs: tuple[ProvenanceRef, ...]
    current_holder_ref: ContentRef
    return_owner_ref: ContentRef
    requested_by: ProvenanceRef
    requested_at: datetime

    @field_validator("requested_at")
    @classmethod
    def require_aware_requested_at(cls, value: datetime) -> datetime:
        return _require_aware(value, "requested_at")

    @field_validator("evidence_refs")
    @classmethod
    def require_evidence(
        cls, value: tuple[ProvenanceRef, ...]
    ) -> tuple[ProvenanceRef, ...]:
        if not value:
            raise ValueError("a Goal lifecycle request must carry evidence refs")
        return value


class GoalLifecycleContext(StrictControlPlaneModel):
    """The semantic owner's current Goal, DAG, and ownership read model."""

    schema_version: Literal["aoa_goal_lifecycle_v1"] = GOAL_LIFECYCLE_SCHEMA_VERSION
    context_id: NonEmptyStr
    correlation_id: NonEmptyStr
    goal_ref: ContentRef
    observed_state: NonEmptyStr
    dag_ref: ContentRef
    ownership_ref: ContentRef
    current_holder_ref: ContentRef
    return_owner_ref: ContentRef
    allowed_transitions: tuple[GoalLifecycleTransition, ...]
    evidence_refs: tuple[ProvenanceRef, ...]
    observed_at: datetime
    valid_until: datetime
    observed_by: ProvenanceRef

    @field_validator("observed_at")
    @classmethod
    def require_aware_observed_at(cls, value: datetime) -> datetime:
        return _require_aware(value, "observed_at")

    @field_validator("valid_until")
    @classmethod
    def require_aware_valid_until(cls, value: datetime) -> datetime:
        return _require_aware(value, "valid_until")

    @field_validator("allowed_transitions")
    @classmethod
    def require_allowed_transitions(
        cls, value: tuple[GoalLifecycleTransition, ...]
    ) -> tuple[GoalLifecycleTransition, ...]:
        if len(set(value)) != len(value):
            raise ValueError("Goal lifecycle transitions must be unique")
        return value

    @model_validator(mode="after")
    def validate_context_freshness(self) -> "GoalLifecycleContext":
        if self.valid_until < self.observed_at:
            raise ValueError("Goal lifecycle context validity cannot precede observation")
        return self


class GoalLifecycleDecision(StrictControlPlaneModel):
    """Semantic-owner legitimacy result consumed by a runtime adapter."""

    schema_version: Literal["aoa_goal_lifecycle_v1"] = GOAL_LIFECYCLE_SCHEMA_VERSION
    decision_id: NonEmptyStr
    correlation_id: NonEmptyStr
    idempotency_key: NonEmptyStr
    goal_ref: ContentRef
    request_ref: ContentRef
    context_ref: ContentRef
    status: GoalLifecycleDecisionStatus
    observed_state: NonEmptyStr
    desired_state: NonEmptyStr
    transition_kind: NonEmptyStr
    reason_codes: tuple[NonEmptyStr, ...]
    evidence_refs: tuple[ProvenanceRef, ...]
    resolved_by: ProvenanceRef
    resolver_version: NonEmptyStr
    decided_at: datetime
    valid_until: datetime

    @field_validator("decided_at")
    @classmethod
    def require_aware_decided_at(cls, value: datetime) -> datetime:
        return _require_aware(value, "decided_at")

    @field_validator("valid_until")
    @classmethod
    def require_aware_decision_valid_until(cls, value: datetime) -> datetime:
        return _require_aware(value, "valid_until")

    @model_validator(mode="after")
    def validate_decision(self) -> "GoalLifecycleDecision":
        if not self.reason_codes:
            raise ValueError("a Goal lifecycle decision must name reason codes")
        if self.status == "accepted" and not self.evidence_refs:
            raise ValueError("an accepted Goal lifecycle decision needs evidence")
        if self.valid_until < self.decided_at:
            raise ValueError("Goal lifecycle decision validity cannot precede decision")
        return self


class GoalLifecycleBoundaryClaims(StrictControlPlaneModel):
    """Separate lifecycle claims carried by one stage-specific receipt."""

    requested: Literal[True] = True
    accepted: bool
    executed: bool
    delivered: bool = False
    semantically_accepted: bool = False
    closed: bool = False

    @model_validator(mode="after")
    def validate_order(self) -> "GoalLifecycleBoundaryClaims":
        if self.accepted and not self.requested:
            raise ValueError("accepted cannot precede requested")
        if self.executed and not self.accepted:
            raise ValueError("executed cannot precede accepted")
        if self.delivered and not self.executed:
            raise ValueError("delivered cannot precede executed")
        if self.semantically_accepted and not self.delivered:
            raise ValueError("semantic acceptance cannot precede delivery")
        if self.closed and not self.semantically_accepted:
            raise ValueError("closure cannot precede semantic acceptance")
        return self


class GoalLifecycleExecutionReceipt(StrictControlPlaneModel):
    """Runtime-only execution result after authoritative Goal re-read."""

    schema_version: Literal["aoa_goal_lifecycle_v1"] = GOAL_LIFECYCLE_SCHEMA_VERSION
    execution_id: NonEmptyStr
    stage: Literal["executed"] = "executed"
    correlation_id: NonEmptyStr
    idempotency_key: NonEmptyStr
    goal_ref: ContentRef
    request_ref: ContentRef
    decision_ref: ContentRef
    observed_state: NonEmptyStr
    desired_state: NonEmptyStr
    resulting_state: NonEmptyStr
    status: GoalLifecycleExecutionStatus
    evidence_refs: tuple[ProvenanceRef, ...]
    produced_by: ProvenanceRef
    executed_at: datetime
    boundaries: GoalLifecycleBoundaryClaims

    @field_validator("executed_at")
    @classmethod
    def require_aware_executed_at(cls, value: datetime) -> datetime:
        return _require_aware(value, "executed_at")

    @model_validator(mode="after")
    def validate_execution(self) -> "GoalLifecycleExecutionReceipt":
        if self.status in {"executed", "replayed"}:
            if self.resulting_state != self.desired_state:
                raise ValueError(
                    "a successful Goal lifecycle execution must confirm desired state"
                )
            if not self.boundaries.accepted or not self.boundaries.executed:
                raise ValueError(
                    "a successful Goal lifecycle execution must carry accepted/executed claims"
                )
            if not self.evidence_refs:
                raise ValueError(
                    "a successful Goal lifecycle execution must carry evidence"
                )
        if self.status == "rejected" and self.boundaries.executed:
            raise ValueError("a rejected execution cannot claim execution")
        return self


class GoalLifecycleAdapterProtocol(Protocol):
    """Runtime adapter boundary for an already accepted semantic request."""

    def execute_goal_transition(
        self,
        request: GoalLifecycleRequest,
        decision: GoalLifecycleDecision,
    ) -> GoalLifecycleExecutionReceipt:
        """Apply and authoritatively confirm one accepted Goal transition."""


def _content_ref(
    *, object_id: str, owner_repo: str, schema_version: str, value: StrictControlPlaneModel
) -> ContentRef:
    return ContentRef(
        object_id=object_id,
        owner_repo=owner_repo,
        schema_version=schema_version,
        digest=canonical_digest(value),
    )


def _request_ref(request: GoalLifecycleRequest) -> ContentRef:
    return _content_ref(
        object_id=request.request_id,
        owner_repo=request.requested_by.owner_repo,
        schema_version=request.schema_version,
        value=request,
    )


def _decision_ref(decision: GoalLifecycleDecision) -> ContentRef:
    return _content_ref(
        object_id=decision.decision_id,
        owner_repo=decision.resolved_by.owner_repo,
        schema_version=decision.schema_version,
        value=decision,
    )


def resolve_goal_lifecycle(
    request: GoalLifecycleRequest,
    context: GoalLifecycleContext,
) -> GoalLifecycleDecision:
    """Resolve legitimacy from owner state without selecting or invoking a runtime."""

    reasons: list[str] = []
    if context.observed_at < request.requested_at:
        reasons.append("owner_context_stale_for_request")
    if context.valid_until < request.requested_at:
        reasons.append("owner_context_expired_for_request")
    if request.correlation_id != context.correlation_id:
        reasons.append("correlation_mismatch")
    if request.goal_ref != context.goal_ref:
        reasons.append("goal_ref_mismatch")
    if request.observed_state != context.observed_state:
        reasons.append("observed_state_mismatch")
    if request.expected_state != context.observed_state:
        reasons.append("expected_state_mismatch")
    if request.current_holder_ref != context.current_holder_ref:
        reasons.append("current_holder_mismatch")
    if request.return_owner_ref != context.return_owner_ref:
        reasons.append("return_owner_mismatch")
    edge = GoalLifecycleTransition(
        from_state=request.expected_state,
        to_state=request.desired_state,
        transition_kind=request.transition_kind,
    )
    if edge not in context.allowed_transitions:
        reasons.append("transition_not_admitted_by_goal_dag")
    missing_evidence = [
        ref for ref in request.evidence_refs if ref not in context.evidence_refs
    ]
    if missing_evidence:
        reasons.append("evidence_not_present_in_owner_context")

    request_ref = _request_ref(request)
    context_ref = _content_ref(
        object_id=context.context_id,
        owner_repo=context.observed_by.owner_repo,
        schema_version=context.schema_version,
        value=context,
    )
    status: GoalLifecycleDecisionStatus = "accepted" if not reasons else "rejected"
    reason_codes = tuple(reasons) if reasons else ("transition_legitimate",)
    return GoalLifecycleDecision(
        decision_id=f"goal-lifecycle-decision:{request_ref.digest.removeprefix('sha256:')}",
        correlation_id=request.correlation_id,
        idempotency_key=request.idempotency_key,
        goal_ref=request.goal_ref,
        request_ref=request_ref,
        context_ref=context_ref,
        status=status,
        observed_state=request.observed_state,
        desired_state=request.desired_state,
        transition_kind=request.transition_kind,
        reason_codes=reason_codes,
        evidence_refs=request.evidence_refs,
        resolved_by=context.observed_by,
        resolver_version=GOAL_LIFECYCLE_RESOLVER_VERSION,
        decided_at=context.observed_at,
        valid_until=context.valid_until,
    )


def assert_goal_lifecycle_execution_scope(
    request: GoalLifecycleRequest,
    decision: GoalLifecycleDecision,
    *,
    now: datetime | None = None,
) -> None:
    """Fail closed when an adapter receives an unrelated decision."""

    expected_request_ref = _request_ref(request)
    if decision.status != "accepted":
        raise ControlPlaneContractError(
            "runtime adapters may execute only an accepted Goal lifecycle decision"
        )
    if (
        decision.request_ref != expected_request_ref
        or decision.correlation_id != request.correlation_id
        or decision.idempotency_key != request.idempotency_key
        or decision.goal_ref != request.goal_ref
    ):
        raise ControlPlaneContractError("Goal lifecycle decision is outside request scope")
    if (
        decision.observed_state != request.observed_state
        or decision.desired_state != request.desired_state
        or decision.transition_kind != request.transition_kind
    ):
        raise ControlPlaneContractError("Goal lifecycle decision does not match request")
    check_at = now if now is not None else datetime.now(UTC)
    _require_aware(check_at, "now")
    if check_at > decision.valid_until:
        raise ControlPlaneContractError(
            "Goal lifecycle decision has expired before execution"
        )


def assert_goal_lifecycle_execution_receipt_scope(
    request: GoalLifecycleRequest,
    decision: GoalLifecycleDecision,
    receipt: GoalLifecycleExecutionReceipt,
) -> None:
    """Bind a runtime receipt to the exact accepted request and decision."""

    assert_goal_lifecycle_execution_scope(request, decision)
    expected_decision_ref = _decision_ref(decision)
    if (
        receipt.correlation_id != request.correlation_id
        or receipt.idempotency_key != request.idempotency_key
        or receipt.goal_ref != request.goal_ref
        or receipt.request_ref != decision.request_ref
        or receipt.decision_ref != expected_decision_ref
        or receipt.observed_state != request.observed_state
        or receipt.desired_state != request.desired_state
    ):
        raise ControlPlaneContractError(
            "Goal lifecycle execution receipt is outside request/decision scope"
        )
