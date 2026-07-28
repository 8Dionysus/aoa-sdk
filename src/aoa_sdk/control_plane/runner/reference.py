"""Deterministic, non-executing runtime adapter for lifecycle verification."""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal, TypeAlias

from ...contracts.control_plane import (
    ABIRef,
    ApprovalDecision,
    ApprovalRequest,
    CancelCommand,
    CloseoutBundleRef,
    CommandReceipt,
    ContentRef,
    ControlPlaneContractError,
    EvalVerdictRef,
    EvidenceBundleRef,
    ExecutionEvent,
    MemoryReceiptRef,
    LifecycleTrigger,
    ObservedABIRef,
    ObservedSourceRef,
    PauseCommand,
    ProvenanceRef,
    RecoverCommand,
    ResumeCommand,
    RunOutcome,
    RunPlan,
    RunState,
    RunStatus,
    RuntimeCommand,
    RuntimeProfile,
    RuntimeSnapshotObservation,
    SessionHandle,
    StartCommand,
    assert_approval_decision_matches_request,
    assert_approvals_satisfied,
    assert_closeout_bundle_scope,
    assert_run_plan_digest,
    canonical_digest,
    command_digest,
    execution_event_digest,
)


REFERENCE_ADAPTER_VERSION = "aoa_reference_runtime_adapter_v1"
ReferenceEventKind: TypeAlias = Literal[
    "state_transition",
    "command_ack",
    "progress",
    "approval_requested",
    "approval_decision",
    "evidence_emitted",
    "outcome",
    "heartbeat",
]
ReferenceExecutionStatus: TypeAlias = Literal[
    "succeeded",
    "partial",
    "failed",
    "cancelled",
]
ReferenceTerminalState: TypeAlias = Literal["completed", "failed", "cancelled"]


class ReferenceAdapterError(ControlPlaneContractError):
    """The deterministic reference adapter rejected a lifecycle operation."""


class ReferenceAdapterUnavailable(ReferenceAdapterError):
    """The reference adapter is intentionally unavailable for a disconnect test."""


@dataclass
class _ReferenceSession:
    plan: RunPlan
    handle: SessionHandle
    status: RunStatus
    events: list[ExecutionEvent] = field(default_factory=list)
    commands: dict[str, tuple[RuntimeCommand, CommandReceipt]] = field(
        default_factory=dict
    )
    requests: dict[str, ApprovalRequest] = field(default_factory=dict)
    decisions: dict[str, ApprovalDecision] = field(default_factory=dict)
    request_generation: int = 0
    outcome: RunOutcome | None = None


class DeterministicReferenceAdapter:
    """A runtime-protocol witness that changes state but executes no plan step."""

    executes_plan_steps = False

    def __init__(
        self,
        *,
        profile: RuntimeProfile | None = None,
        clock: Callable[[], datetime] | None = None,
        observed_source_overrides: Mapping[tuple[str, str], str] | None = None,
        observed_abi_overrides: Mapping[tuple[str, str], tuple[str, str]] | None = None,
    ) -> None:
        self._profile = profile or reference_runtime_profile()
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._observed_source_overrides = dict(observed_source_overrides or {})
        self._observed_abi_overrides = dict(observed_abi_overrides or {})
        self._sessions: dict[str, _ReferenceSession] = {}
        self._available = True

    @property
    def profile(self) -> RuntimeProfile:
        return self._profile

    def set_available(self, available: bool) -> None:
        """Test-only availability switch; it never changes session state."""

        self._available = available

    def observe_snapshot(
        self,
        plan: RunPlan,
        session: SessionHandle,
    ) -> RuntimeSnapshotObservation:
        self._require_available()
        self._assert_plan_session(plan, session)
        observed_at = _aware(self._clock(), "observed_at")
        state = self._sessions.get(session.session_id)
        freshness_floor = (
            state.status.updated_at if state is not None else session.prepared_at
        )
        if observed_at < freshness_floor:
            observed_at = freshness_floor
        observation_token = hashlib.sha256(
            (f"{plan.snapshot.snapshot_digest}:{observed_at.isoformat()}").encode()
        ).hexdigest()
        source_refs = tuple(
            ObservedSourceRef(
                owner_repo=source.owner_repo,
                artifact_ref=source.artifact_ref,
                artifact_digest=self._observed_source_overrides.get(
                    (source.owner_repo, source.artifact_ref),
                    source.artifact_digest,
                ),
            )
            for source in plan.snapshot.source_refs
        )
        abi_refs = tuple(
            _observed_abi(
                abi,
                self._observed_abi_overrides.get((abi.owner_repo, abi.abi_id)),
            )
            for abi in plan.snapshot.abi_refs
        )
        observation = RuntimeSnapshotObservation(
            observation_id=(
                f"reference-observation:{session.session_id}:{observation_token}"
            ),
            session_id=session.session_id,
            correlation_id=session.correlation_id,
            plan_digest=plan.plan_digest,
            source_refs=source_refs,
            abi_refs=abi_refs,
            observed_at=observed_at,
            observed_by=self._profile.provenance,
        )
        return observation

    def dispatch(
        self,
        plan: RunPlan,
        session: SessionHandle,
        command: RuntimeCommand,
    ) -> CommandReceipt:
        self._require_available()
        self._assert_plan_session(plan, session)
        state = self._sessions.get(session.session_id)
        if state is None:
            if not isinstance(command, (StartCommand, CancelCommand)):
                raise ReferenceAdapterError(
                    "reference session must begin with start or cancel"
                )
            state = self._new_session(plan, session)
            self._sessions[session.session_id] = state
        elif state.plan != plan or state.handle != session:
            raise ReferenceAdapterError("reference session binding changed")

        previous = state.commands.get(command.idempotency_key)
        if previous is not None:
            prior_command, prior_receipt = previous
            if command_digest(prior_command) != command_digest(command):
                return CommandReceipt(
                    command_id=command.command_id,
                    idempotency_key=command.idempotency_key,
                    command_digest=command_digest(command),
                    session_id=session.session_id,
                    status="rejected",
                    resulting_revision=state.status.revision,
                    rejection_code="idempotency_payload_mismatch",
                    produced_by=self._profile.provenance,
                )
            return prior_receipt.model_copy(
                update={
                    "status": "duplicate",
                    "event_refs": (),
                    "rejection_code": None,
                }
            )

        rejection = self._command_rejection(state, command)
        if rejection is not None:
            return CommandReceipt(
                command_id=command.command_id,
                idempotency_key=command.idempotency_key,
                command_digest=command_digest(command),
                session_id=session.session_id,
                status="rejected",
                resulting_revision=state.status.revision,
                rejection_code=rejection,
                produced_by=self._profile.provenance,
            )

        first_event = len(state.events)
        self._apply_command(state, command)
        self._emit(
            state,
            event_kind="command_ack",
            emitted_at=command.issued_at,
            command_id=command.command_id,
            idempotency_key=command.idempotency_key,
        )
        event_refs = tuple(_event_ref(event) for event in state.events[first_event:])
        receipt = CommandReceipt(
            command_id=command.command_id,
            idempotency_key=command.idempotency_key,
            command_digest=command_digest(command),
            session_id=session.session_id,
            status="applied",
            resulting_revision=state.status.revision,
            event_refs=event_refs,
            produced_by=self._profile.provenance,
        )
        state.commands[command.idempotency_key] = (command, receipt)
        return receipt

    def approval_requests(
        self,
        session: SessionHandle,
    ) -> Iterable[ApprovalRequest]:
        self._require_available()
        state = self._state(session)
        return tuple(
            state.requests[requirement.requirement_id]
            for requirement in state.plan.approval_requirements
            if requirement.requirement_id in state.requests
        )

    def approval_decisions(
        self,
        session: SessionHandle,
    ) -> Iterable[ApprovalDecision]:
        self._require_available()
        state = self._state(session)
        return tuple(
            state.decisions[requirement.requirement_id]
            for requirement in state.plan.approval_requirements
            if requirement.requirement_id in state.decisions
        )

    def command_receipts(
        self,
        session: SessionHandle,
    ) -> Iterable[CommandReceipt]:
        self._require_available()
        state = self._state(session)
        return tuple(receipt for _, receipt in state.commands.values())

    def renew_approvals(
        self,
        plan: RunPlan,
        session: SessionHandle,
        *,
        requested_at: datetime,
    ) -> Iterable[ApprovalRequest]:
        self._require_available()
        state = self._state(session)
        if state.plan != plan:
            raise ReferenceAdapterError("approval renewal plan changed")
        if state.status.state not in {"awaiting_approval", "paused"}:
            raise ReferenceAdapterError(
                "approval renewal requires awaiting_approval or paused"
            )
        renewable = tuple(
            requirement
            for requirement in plan.approval_requirements
            if requirement.renewable
        )
        if not renewable:
            raise ReferenceAdapterError("plan has no renewable approvals")
        self._make_requests(
            state,
            requirements=renewable,
            requested_at=_aware(requested_at, "requested_at"),
        )
        return self.approval_requests(session)

    def apply_approval(
        self,
        plan: RunPlan,
        session: SessionHandle,
        approval: ApprovalDecision,
    ) -> RunStatus:
        self._require_available()
        state = self._state(session)
        if state.plan != plan:
            raise ReferenceAdapterError("approval plan changed")
        existing = next(
            (
                decision
                for decision in state.decisions.values()
                if decision.decision_id == approval.decision_id
            ),
            None,
        )
        if existing is not None:
            if existing != approval:
                raise ReferenceAdapterError(
                    "approval decision id was replayed with different content"
                )
            return state.status
        if state.status.state not in {"awaiting_approval", "paused"}:
            raise ReferenceAdapterError(
                f"approval is invalid while session is {state.status.state}"
            )
        requirement = next(
            (
                item
                for item in plan.approval_requirements
                if item.requirement_id == approval.requirement_id
            ),
            None,
        )
        request = state.requests.get(approval.requirement_id)
        if requirement is None or request is None:
            raise ReferenceAdapterError("approval has no current request")
        assert_approval_decision_matches_request(requirement, request, approval)
        if approval.requirement_id in state.decisions:
            raise ReferenceAdapterError(
                "current approval request already has a decision"
            )
        state.decisions[approval.requirement_id] = approval
        self._emit(
            state,
            event_kind="approval_decision",
            emitted_at=approval.decided_at,
            approval_decision_ref=_model_ref(
                approval.decision_id,
                approval,
                approval.approval_authority.owner_repo,
            ),
        )
        if state.status.state == "paused":
            return state.status
        if approval.verdict == "rejected":
            self._transition(
                state,
                state_after="cancelled",
                trigger="approval_rejected",
                at=approval.decided_at,
            )
            self._record_outcome(
                state,
                execution_status="cancelled",
                at=approval.decided_at,
            )
        elif approval.verdict == "expired":
            self._transition(
                state,
                state_after="paused",
                trigger="approval_expired",
                at=approval.decided_at,
            )
        else:
            pending = tuple(
                item.requirement_id
                for item in plan.approval_requirements
                if (
                    item.requirement_id not in state.decisions
                    or state.decisions[item.requirement_id].verdict != "approved"
                )
            )
            if pending:
                state.status = state.status.model_copy(
                    update={
                        "pending_approval_ids": pending,
                        "revision": state.status.revision + 1,
                        "updated_at": approval.decided_at,
                    }
                )
            else:
                assert_approvals_satisfied(
                    plan,
                    state.decisions.values(),
                    session=session,
                    at=approval.decided_at,
                )
                self._transition(
                    state,
                    state_after="running",
                    trigger="approval_granted",
                    at=approval.decided_at,
                )
        return state.status

    def status(self, session: SessionHandle) -> RunStatus:
        self._require_available()
        return self._state(session).status

    def events(
        self,
        session: SessionHandle,
        *,
        after_sequence: int,
    ) -> Iterable[ExecutionEvent]:
        self._require_available()
        state = self._state(session)
        return tuple(event for event in state.events if event.sequence > after_sequence)

    def outcome(self, session: SessionHandle) -> RunOutcome | None:
        self._require_available()
        return self._state(session).outcome

    def closeout(
        self,
        plan: RunPlan,
        session: SessionHandle,
        outcome: RunOutcome,
        bundle: CloseoutBundleRef,
    ) -> RunStatus:
        self._require_available()
        state = self._state(session)
        if state.plan != plan or state.outcome != outcome:
            raise ReferenceAdapterError("closeout plan or outcome changed")
        if state.status.state == "closed":
            if state.status.closeout_ref != bundle:
                raise ReferenceAdapterError(
                    "closed session cannot accept another closeout bundle"
                )
            return state.status
        if state.status.state not in {"failed", "completed", "cancelled"}:
            raise ReferenceAdapterError("closeout requires an execution-terminal state")
        assert_closeout_bundle_scope(plan, session, outcome, bundle)
        self._transition(
            state,
            state_after="closed",
            trigger="closeout",
            at=_aware(self._clock(), "closeout time"),
            closeout_ref=bundle,
        )
        return state.status

    def advance(
        self,
        session: SessionHandle,
        *,
        trigger: Literal[
            "runtime_interrupted",
            "runtime_completed",
            "runtime_failed",
        ],
        at: datetime | None = None,
        failure_codes: tuple[str, ...] = (),
        execution_status: ReferenceExecutionStatus | None = None,
        evidence_bundle_refs: tuple[EvidenceBundleRef, ...] = (),
        eval_verdict_refs: tuple[EvalVerdictRef, ...] = (),
        memory_receipt_refs: tuple[MemoryReceiptRef, ...] = (),
    ) -> RunStatus:
        """Test-only runtime transition; it records references and executes nothing."""

        self._require_available()
        state = self._state(session)
        at = _aware(at or self._clock(), "advance time")
        if trigger == "runtime_interrupted":
            if not failure_codes:
                raise ReferenceAdapterError(
                    "runtime interruption requires a failure code"
                )
            recovery_cursor = state.status.last_event_sequence
            self._transition(
                state,
                state_after="recoverable_failure",
                trigger=trigger,
                at=at,
                failure_code=failure_codes[0],
                recover_from_event_sequence=recovery_cursor,
            )
        elif trigger == "runtime_completed":
            if execution_status not in {None, "succeeded"}:
                raise ReferenceAdapterError(
                    "runtime_completed requires succeeded execution status"
                )
            self._transition(
                state,
                state_after="completed",
                trigger=trigger,
                at=at,
            )
            self._record_outcome(
                state,
                execution_status="succeeded",
                at=at,
                evidence_bundle_refs=evidence_bundle_refs,
                eval_verdict_refs=eval_verdict_refs,
                memory_receipt_refs=memory_receipt_refs,
            )
        elif trigger == "runtime_failed":
            if execution_status not in {"partial", "failed"} or not failure_codes:
                raise ReferenceAdapterError(
                    "runtime_failed requires partial/failed status and failure codes"
                )
            self._transition(
                state,
                state_after="failed",
                trigger=trigger,
                at=at,
                failure_code=failure_codes[0],
            )
            self._record_outcome(
                state,
                execution_status=execution_status,
                at=at,
                failure_codes=failure_codes,
                evidence_bundle_refs=evidence_bundle_refs,
                eval_verdict_refs=eval_verdict_refs,
                memory_receipt_refs=memory_receipt_refs,
            )
        else:
            raise ReferenceAdapterError(
                f"unsupported reference runtime trigger: {trigger}"
            )
        return state.status

    def emit_progress(
        self,
        session: SessionHandle,
        *,
        at: datetime | None = None,
        payload_ref: ProvenanceRef | None = None,
    ) -> ExecutionEvent:
        """Emit a non-effect progress observation for event-chain tests."""

        self._require_available()
        state = self._state(session)
        return self._emit(
            state,
            event_kind="progress",
            emitted_at=_aware(at or self._clock(), "progress time"),
            payload_ref=payload_ref,
        )

    def _new_session(
        self,
        plan: RunPlan,
        session: SessionHandle,
    ) -> _ReferenceSession:
        return _ReferenceSession(
            plan=plan,
            handle=session,
            status=RunStatus(
                session_id=session.session_id,
                correlation_id=session.correlation_id,
                state="prepared",
                revision=0,
                updated_at=session.prepared_at,
                observed_by=self._profile.provenance,
            ),
        )

    def _apply_command(
        self,
        state: _ReferenceSession,
        command: RuntimeCommand,
    ) -> None:
        at = command.issued_at
        if isinstance(command, StartCommand):
            if state.plan.approval_requirements:
                self._make_requests(
                    state,
                    requirements=state.plan.approval_requirements,
                    requested_at=at,
                )
                self._transition(
                    state,
                    state_after="awaiting_approval",
                    trigger="approval_required",
                    at=at,
                    pending_approval_ids=tuple(
                        item.requirement_id for item in state.plan.approval_requirements
                    ),
                )
            else:
                self._transition(
                    state,
                    state_after="running",
                    trigger="start",
                    at=at,
                )
        elif isinstance(command, PauseCommand):
            self._transition(
                state,
                state_after="paused",
                trigger="pause",
                at=at,
            )
        elif isinstance(command, ResumeCommand):
            if command.resume_after_sequence != state.status.last_event_sequence:
                raise ReferenceAdapterError("resume cursor mismatch")
            if state.plan.approval_requirements:
                assert_approvals_satisfied(
                    state.plan,
                    state.decisions.values(),
                    session=state.handle,
                    at=at,
                )
            self._transition(
                state,
                state_after="running",
                trigger="resume",
                at=at,
            )
        elif isinstance(command, RecoverCommand):
            if (
                command.recover_after_sequence
                != state.status.recover_from_event_sequence
            ):
                raise ReferenceAdapterError("recover cursor mismatch")
            self._transition(
                state,
                state_after="paused",
                trigger="recover",
                at=at,
            )
        elif isinstance(command, CancelCommand):
            self._transition(
                state,
                state_after="cancelled",
                trigger="cancel",
                at=at,
            )
            self._record_outcome(
                state,
                execution_status="cancelled",
                at=at,
            )
        else:
            raise ReferenceAdapterError(
                f"unsupported command type: {type(command).__name__}"
            )

    def _command_rejection(
        self,
        state: _ReferenceSession,
        command: RuntimeCommand,
    ) -> str | None:
        if (
            command.session_id != state.handle.session_id
            or command.correlation_id != state.handle.correlation_id
            or command.plan_digest != state.plan.plan_digest
        ):
            return "command_scope_mismatch"
        if command.expected_revision != state.status.revision:
            return "stale_expected_revision"
        allowed: tuple[str, ...]
        if isinstance(command, StartCommand):
            allowed = ("prepared",)
        elif isinstance(command, PauseCommand):
            allowed = ("running",)
        elif isinstance(command, ResumeCommand):
            allowed = ("paused",)
        elif isinstance(command, RecoverCommand):
            allowed = ("recoverable_failure",)
        elif isinstance(command, CancelCommand):
            allowed = (
                "prepared",
                "awaiting_approval",
                "running",
                "paused",
                "recoverable_failure",
            )
        else:
            return "unsupported_command"
        if state.status.state not in allowed:
            return f"invalid_state:{state.status.state}"
        return None

    def _make_requests(
        self,
        state: _ReferenceSession,
        *,
        requirements: Iterable,
        requested_at: datetime,
    ) -> None:
        state.request_generation += 1
        for requirement in requirements:
            request = ApprovalRequest(
                request_id=(
                    f"approval-request:{state.handle.session_id}:"
                    f"{requirement.requirement_id}:{state.request_generation}"
                ),
                requirement_id=requirement.requirement_id,
                approval_authority=requirement.approval_owner,
                session_id=state.handle.session_id,
                correlation_id=state.handle.correlation_id,
                plan_digest=state.plan.plan_digest,
                snapshot_digest=state.plan.snapshot.snapshot_digest,
                requested_at=requested_at,
                expires_at=(
                    requested_at + timedelta(seconds=requirement.expires_after_seconds)
                    if requirement.expires_after_seconds is not None
                    else None
                ),
                request_provenance=self._profile.provenance,
            )
            state.requests[requirement.requirement_id] = request
            state.decisions.pop(requirement.requirement_id, None)
            self._emit(
                state,
                event_kind="approval_requested",
                emitted_at=requested_at,
                approval_request_ref=_model_ref(
                    request.request_id,
                    request,
                    self._profile.runtime_owner,
                ),
            )

    def _record_outcome(
        self,
        state: _ReferenceSession,
        *,
        execution_status: ReferenceExecutionStatus,
        at: datetime,
        failure_codes: tuple[str, ...] = (),
        evidence_bundle_refs: tuple[EvidenceBundleRef, ...] = (),
        eval_verdict_refs: tuple[EvalVerdictRef, ...] = (),
        memory_receipt_refs: tuple[MemoryReceiptRef, ...] = (),
    ) -> RunOutcome:
        if state.outcome is not None:
            raise ReferenceAdapterError("reference session already has an outcome")
        terminal_for_status: dict[
            ReferenceExecutionStatus,
            ReferenceTerminalState,
        ] = {
            "succeeded": "completed",
            "partial": "failed",
            "failed": "failed",
            "cancelled": "cancelled",
        }
        outcome = RunOutcome(
            outcome_id=f"reference-outcome:{state.handle.session_id}",
            session_id=state.handle.session_id,
            correlation_id=state.handle.correlation_id,
            plan_digest=state.plan.plan_digest,
            execution_status=execution_status,
            terminal_state=terminal_for_status[execution_status],
            completed_at=at,
            runtime_result_ref=ProvenanceRef(
                owner_repo=self._profile.runtime_owner,
                artifact_ref=(
                    f"reference-runtime-results/{state.handle.session_id}.json"
                ),
                source_ref=REFERENCE_ADAPTER_VERSION,
                artifact_digest=f"sha256:{hashlib.sha256(state.handle.session_id.encode()).hexdigest()}",
                schema_ref="src/aoa_sdk/contracts/control_plane.py#RunOutcome",
                schema_version="aoa_control_plane_v1",
            ),
            evidence_bundle_refs=evidence_bundle_refs,
            eval_verdict_refs=eval_verdict_refs,
            memory_receipt_refs=memory_receipt_refs,
            failure_codes=failure_codes,
        )
        state.outcome = outcome
        self._emit(
            state,
            event_kind="outcome",
            emitted_at=at,
            outcome_ref=_model_ref(
                outcome.outcome_id,
                outcome,
                self._profile.runtime_owner,
            ),
        )
        return outcome

    def _transition(
        self,
        state: _ReferenceSession,
        *,
        state_after: RunState,
        trigger: LifecycleTrigger,
        at: datetime,
        pending_approval_ids: tuple[str, ...] = (),
        failure_code: str | None = None,
        recover_from_event_sequence: int | None = None,
        closeout_ref: CloseoutBundleRef | None = None,
    ) -> None:
        state_before = state.status.state
        self._emit(
            state,
            event_kind="state_transition",
            emitted_at=at,
            state_before=state_before,
            state_after=state_after,
            trigger=trigger,
        )
        state.status = state.status.model_copy(
            update={
                "state": state_after,
                "revision": state.status.revision + 1,
                "pending_approval_ids": pending_approval_ids,
                "failure_code": failure_code,
                "recover_from_event_sequence": recover_from_event_sequence,
                "closeout_ref": closeout_ref,
                "updated_at": at,
            }
        )

    def _emit(
        self,
        state: _ReferenceSession,
        *,
        event_kind: ReferenceEventKind,
        emitted_at: datetime,
        state_before: RunState | None = None,
        state_after: RunState | None = None,
        trigger: LifecycleTrigger | None = None,
        command_id: str | None = None,
        idempotency_key: str | None = None,
        payload_ref: ProvenanceRef | None = None,
        approval_request_ref: ContentRef | None = None,
        approval_decision_ref: ContentRef | None = None,
        outcome_ref: ContentRef | None = None,
    ) -> ExecutionEvent:
        emitted_at = _aware(emitted_at, "event emitted_at")
        if state.events and emitted_at < state.events[-1].emitted_at:
            raise ReferenceAdapterError("reference event time cannot move backwards")
        sequence = len(state.events)
        event = ExecutionEvent(
            event_id=f"reference-event:{state.handle.session_id}:{sequence}",
            event_stream_id=state.handle.event_stream_id,
            session_id=state.handle.session_id,
            correlation_id=state.handle.correlation_id,
            sequence=sequence,
            previous_event_digest=(
                state.events[-1].event_digest if state.events else None
            ),
            event_digest="sha256:" + "0" * 64,
            event_kind=event_kind,
            emitted_at=emitted_at,
            emitted_by=self._profile.provenance,
            state_before=state_before,
            state_after=state_after,
            trigger=trigger,
            command_id=command_id,
            idempotency_key=idempotency_key,
            payload_ref=payload_ref,
            approval_request_ref=approval_request_ref,
            approval_decision_ref=approval_decision_ref,
            outcome_ref=outcome_ref,
        )
        event = event.model_copy(update={"event_digest": execution_event_digest(event)})
        state.events.append(event)
        state.status = state.status.model_copy(
            update={
                "last_event_sequence": event.sequence,
                "updated_at": emitted_at,
            }
        )
        return event

    def _state(self, session: SessionHandle) -> _ReferenceSession:
        state = self._sessions.get(session.session_id)
        if state is None:
            raise ReferenceAdapterError(
                f"unknown reference session: {session.session_id}"
            )
        if state.handle != session:
            raise ReferenceAdapterError("reference session handle changed")
        return state

    def _assert_plan_session(
        self,
        plan: RunPlan,
        session: SessionHandle,
    ) -> None:
        assert_run_plan_digest(plan)
        if plan.runtime_profile != self._profile:
            raise ReferenceAdapterError("plan does not bind this reference profile")
        if (
            session.correlation_id != plan.correlation_id
            or session.plan_digest != plan.plan_digest
            or session.snapshot_digest != plan.snapshot.snapshot_digest
        ):
            raise ReferenceAdapterError("session does not bind the exact plan")

    def _require_available(self) -> None:
        if not self._available:
            raise ReferenceAdapterUnavailable(
                "deterministic reference adapter is unavailable"
            )


def reference_runtime_profile() -> RuntimeProfile:
    """Return the exact SDK-owned no-execution reference profile."""

    provenance = default_reference_adapter_provenance()
    return RuntimeProfile(
        profile_id="runtime-profile:aoa-sdk-reference-v1",
        runtime_owner="aoa-sdk",
        adapter_id=REFERENCE_ADAPTER_VERSION,
        supported_plan_schema_versions=("aoa_control_plane_v1",),
        supported_event_schema_versions=("aoa_control_plane_v1",),
        supported_effect_classes=(
            "read_only",
            "repo_mutation",
            "runtime_mutation",
            "external",
        ),
        provenance=provenance,
    )


def default_reference_adapter_provenance() -> ProvenanceRef:
    source_file = Path(__file__)
    module_digest = hashlib.sha256(source_file.read_bytes()).hexdigest()
    return ProvenanceRef(
        owner_repo="aoa-sdk",
        artifact_ref="src/aoa_sdk/control_plane/runner/reference.py",
        source_ref=f"{REFERENCE_ADAPTER_VERSION}@sha256:{module_digest}",
        artifact_digest=f"sha256:{module_digest}",
        schema_ref="src/aoa_sdk/contracts/control_plane.py",
        schema_version="aoa_control_plane_v1",
    )


def _observed_abi(
    abi: ABIRef,
    override: tuple[str, str] | None,
) -> ObservedABIRef:
    version, digest = override or (abi.abi_version, abi.artifact_digest)
    return ObservedABIRef(
        owner_repo=abi.owner_repo,
        abi_id=abi.abi_id,
        abi_version=version,
        artifact_digest=digest,
    )


def _model_ref(object_id: str, model, owner_repo: str) -> ContentRef:
    return ContentRef(
        object_id=object_id,
        owner_repo=owner_repo,
        schema_version=model.schema_version,
        digest=canonical_digest(model),
    )


def _event_ref(event: ExecutionEvent) -> ContentRef:
    return ContentRef(
        object_id=event.event_id,
        owner_repo=event.emitted_by.owner_repo,
        schema_version=event.schema_version,
        digest=event.event_digest,
    )


def _aware(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ReferenceAdapterError(f"{field_name} must be timezone-aware")
    return value.astimezone(timezone.utc)
