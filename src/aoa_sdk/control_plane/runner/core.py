"""Validated lifecycle client over an explicit runtime adapter."""

from __future__ import annotations

import hashlib
import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from ...contracts.control_plane import (
    ApprovalDecision,
    ApprovalRequest,
    CancelCommand,
    CloseoutBundleRef,
    CommandReceipt,
    ContentRef,
    ControlPlaneContractError,
    ExecutionEvent,
    PauseCommand,
    ProvenanceRef,
    RecoverCommand,
    ResumeCommand,
    RunOutcome,
    RunPlan,
    RunStatus,
    RuntimeAdapterProtocol,
    RuntimeCommand,
    SessionHandle,
    StartCommand,
    assert_approval_decision_matches_request,
    assert_closeout_ready,
    assert_execution_event_chain,
    assert_run_plan_digest,
    assert_runtime_snapshot_observation,
    canonical_digest,
    command_digest,
    deduplicate_execution_events,
)
from ...contracts.evidence_chain import EvidenceChain
from ..evidence_chain import (
    EvidenceChainError,
    assert_evidence_chain_complete,
)


AOA_RUNNER_VERSION = "aoa_control_plane_runner_v1"


class AoARunnerError(ControlPlaneContractError):
    """A lifecycle action could not be admitted or reconciled."""


class RunnerSessionNotFound(AoARunnerError):
    """The supplied handle is not registered in this Runner."""


class RunnerCommandRejected(AoARunnerError):
    """The runtime adapter returned an explicit rejected command receipt."""


@dataclass
class _SessionRecord:
    plan: RunPlan
    session: SessionHandle
    status: RunStatus
    adapter: RuntimeAdapterProtocol | None = None
    events: list[ExecutionEvent] = field(default_factory=list)
    receipts: list[CommandReceipt] = field(default_factory=list)


class AoARunner:
    """Stateful control-plane client that delegates every runtime transition."""

    def __init__(
        self,
        *,
        clock: Callable[[], datetime] | None = None,
        id_factory: Callable[[], str] | None = None,
        provenance: ProvenanceRef | None = None,
    ) -> None:
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._id_factory = id_factory or (lambda: uuid.uuid4().hex)
        self._provenance = provenance or default_runner_provenance()
        self._sessions: dict[str, _SessionRecord] = {}

    def prepare(self, plan: RunPlan) -> SessionHandle:
        """Validate and register one immutable plan without selecting a runtime."""

        assert_run_plan_digest(plan)
        token = self._id_factory()
        prepared_at = _aware(self._clock(), "prepared_at")
        session = SessionHandle(
            session_id=f"aoa-session:{token}",
            correlation_id=plan.correlation_id,
            plan_ref=ContentRef(
                object_id=plan.plan_id,
                owner_repo=plan.provenance.owner_repo,
                schema_version=plan.schema_version,
                digest=plan.plan_digest,
            ),
            plan_digest=plan.plan_digest,
            snapshot_digest=plan.snapshot.snapshot_digest,
            event_stream_id=f"aoa-execution-events:{token}",
            prepared_at=prepared_at,
            prepared_by=self._provenance,
        )
        if session.session_id in self._sessions:
            raise AoARunnerError(f"session id collision: {session.session_id}")
        status = RunStatus(
            session_id=session.session_id,
            correlation_id=session.correlation_id,
            state="prepared",
            revision=0,
            updated_at=prepared_at,
            observed_by=self._provenance,
        )
        self._sessions[session.session_id] = _SessionRecord(
            plan=plan,
            session=session,
            status=status,
        )
        return session

    def restore(
        self,
        plan: RunPlan,
        session: SessionHandle,
        adapter: RuntimeAdapterProtocol,
    ) -> RunStatus:
        """Rebuild a verified local observation from a durable handle and adapter."""

        assert_run_plan_digest(plan)
        _assert_session_matches_plan(session, plan)
        existing = self._sessions.get(session.session_id)
        if existing is not None:
            if existing.plan != plan or existing.session != session:
                raise AoARunnerError(
                    f"session id {session.session_id!r} is already bound differently"
                )
            self._bind_adapter(existing, adapter)
            return self.sync(session, adapter)
        prepared_status = RunStatus(
            session_id=session.session_id,
            correlation_id=session.correlation_id,
            state="prepared",
            revision=0,
            updated_at=session.prepared_at,
            observed_by=session.prepared_by,
        )
        record = _SessionRecord(
            plan=plan,
            session=session,
            status=prepared_status,
            adapter=adapter,
        )
        self._assert_adapter(record, adapter)
        self._observe_snapshot(record, adapter)
        self._sessions[session.session_id] = record
        try:
            status = self._reconcile(record, adapter)
            self._reconcile_receipts(record, adapter)
            self._validate_current_approvals(record)
            self._validate_outcome(record)
            return status
        except Exception:
            self._sessions.pop(session.session_id, None)
            raise

    def start(
        self,
        session: SessionHandle,
        adapter: RuntimeAdapterProtocol,
        command: StartCommand,
    ) -> RunStatus:
        record = self._record(session)
        self._bind_adapter(record, adapter)
        replayed = self._verified_replay_status(record, command)
        if replayed is not None:
            return replayed
        self._observe_snapshot(record, adapter)
        return self._dispatch(record, adapter, command)

    def pause(
        self,
        session: SessionHandle,
        adapter: RuntimeAdapterProtocol,
        command: PauseCommand,
    ) -> RunStatus:
        record = self._record(session)
        self._bind_adapter(record, adapter)
        return self._dispatch(record, adapter, command)

    def approve(
        self,
        session: SessionHandle,
        approval: ApprovalDecision,
    ) -> RunStatus:
        record = self._record(session)
        adapter = self._bound_adapter(record)
        requests = {
            request.requirement_id: request
            for request in self._validated_approval_requests(record)
        }
        requirements = {
            requirement.requirement_id: requirement
            for requirement in record.plan.approval_requirements
        }
        requirement = requirements.get(approval.requirement_id)
        request = requests.get(approval.requirement_id)
        if requirement is None or request is None:
            raise AoARunnerError(
                f"no current approval request for {approval.requirement_id!r}"
            )
        assert_approval_decision_matches_request(requirement, request, approval)
        previous = record.status
        with _verified_read_model_update(record):
            adapter.apply_approval(record.plan, record.session, approval)
            status = self._reconcile(record, adapter)
            self._reconcile_receipts(record, adapter)
            decisions = self._validate_current_approvals(record)
            self._validate_outcome(record)
            if not any(
                decision.decision_id == approval.decision_id and decision == approval
                for decision in decisions
            ):
                raise AoARunnerError(
                    f"adapter did not retain approval decision {approval.decision_id!r}"
                )
            if status == previous and approval not in decisions:
                raise AoARunnerError("duplicate approval was not retained exactly")
        return status

    def renew_approvals(
        self,
        session: SessionHandle,
        *,
        requested_at: datetime,
    ) -> tuple[ApprovalRequest, ...]:
        record = self._record(session)
        if record.status.state not in {"awaiting_approval", "paused"}:
            raise AoARunnerError(
                "approval renewal is only valid while awaiting approval or paused"
            )
        adapter = self._bound_adapter(record)
        requested_at = _aware(requested_at, "requested_at")
        with _verified_read_model_update(record):
            adapter.renew_approvals(
                record.plan,
                record.session,
                requested_at=requested_at,
            )
            self._reconcile(record, adapter)
            self._reconcile_receipts(record, adapter)
            requests = self._validated_approval_requests(record)
            self._validate_current_approvals(record)
            self._validate_outcome(record)
        return requests

    def resume(
        self,
        session: SessionHandle,
        adapter: RuntimeAdapterProtocol,
        command: ResumeCommand,
    ) -> RunStatus:
        record = self._record(session)
        self._bind_adapter(record, adapter)
        replayed = self._verified_replay_status(record, command)
        if replayed is not None:
            return replayed
        self._observe_snapshot(record, adapter)
        self._validate_current_approvals(record, at=command.issued_at)
        return self._dispatch(record, adapter, command)

    def cancel(
        self,
        session: SessionHandle,
        adapter: RuntimeAdapterProtocol,
        command: CancelCommand,
    ) -> RunStatus:
        record = self._record(session)
        self._bind_adapter(record, adapter)
        return self._dispatch(record, adapter, command)

    def recover(
        self,
        session: SessionHandle,
        adapter: RuntimeAdapterProtocol,
        command: RecoverCommand,
    ) -> RunStatus:
        record = self._record(session)
        self._bind_adapter(record, adapter)
        replayed = self._verified_replay_status(record, command)
        if replayed is not None:
            return replayed
        self._assert_retry_allowed(record)
        self._observe_snapshot(record, adapter)
        return self._dispatch(record, adapter, command)

    def sync(
        self,
        session: SessionHandle,
        adapter: RuntimeAdapterProtocol,
    ) -> RunStatus:
        record = self._record(session)
        self._bind_adapter(record, adapter)
        with _verified_read_model_update(record):
            status = self._reconcile(record, adapter)
            self._reconcile_receipts(record, adapter)
            self._validate_current_approvals(record)
            self._validate_outcome(record)
        return status

    def status(self, session: SessionHandle) -> RunStatus:
        return self._record(session).status

    def approval_requests(
        self,
        session: SessionHandle,
    ) -> tuple[ApprovalRequest, ...]:
        return self._validated_approval_requests(self._record(session))

    def approval_decisions(
        self,
        session: SessionHandle,
    ) -> tuple[ApprovalDecision, ...]:
        return self._validate_current_approvals(self._record(session))

    def events(self, session: SessionHandle) -> tuple[ExecutionEvent, ...]:
        return tuple(self._record(session).events)

    def command_receipts(
        self,
        session: SessionHandle,
    ) -> tuple[CommandReceipt, ...]:
        return tuple(self._record(session).receipts)

    def outcome(self, session: SessionHandle) -> RunOutcome | None:
        return self._validate_outcome(self._record(session))

    def closeout(
        self,
        session: SessionHandle,
        outcome: RunOutcome,
        bundle: CloseoutBundleRef | EvidenceChain,
    ) -> RunStatus:
        record = self._record(session)
        adapter = self._bound_adapter(record)
        observed_outcome = self._validate_outcome(record)
        if observed_outcome is None or observed_outcome != outcome:
            raise AoARunnerError(
                "closeout outcome does not match the runtime-owned outcome"
            )
        closeout_bundle = self._admitted_closeout_bundle(
            record,
            outcome,
            bundle,
        )
        if record.status.state == "closed":
            if record.status.closeout_ref != closeout_bundle:
                raise AoARunnerError(
                    "session is already closed with a different bundle"
                )
            return record.status
        if record.status.state != outcome.terminal_state:
            raise AoARunnerError(
                "closeout outcome does not match the current terminal state"
            )
        with _verified_read_model_update(record):
            adapter.closeout(
                record.plan,
                record.session,
                outcome,
                closeout_bundle,
            )
            status = self._reconcile(record, adapter)
            self._reconcile_receipts(record, adapter)
            self._validate_current_approvals(record)
            current_outcome = self._validate_outcome(record)
            if current_outcome != outcome:
                raise AoARunnerError(
                    "adapter changed the runtime-owned outcome during closeout"
                )
            if status.state != "closed" or status.closeout_ref != closeout_bundle:
                raise AoARunnerError("adapter did not close with the admitted bundle")
        return status

    @staticmethod
    def _admitted_closeout_bundle(
        record: _SessionRecord,
        outcome: RunOutcome,
        bundle: CloseoutBundleRef | EvidenceChain,
    ) -> CloseoutBundleRef:
        if isinstance(bundle, CloseoutBundleRef):
            assert_closeout_ready(
                record.plan,
                record.session,
                outcome,
                bundle,
            )
            return bundle
        try:
            closeout_bundle = assert_evidence_chain_complete(bundle)
        except EvidenceChainError as exc:
            raise AoARunnerError(str(exc)) from exc
        verified_events = tuple(record.events)
        events_match = bundle.events == verified_events
        if record.status.state == "closed":
            events_match = (
                verified_events[: len(bundle.events)] == bundle.events
                and len(verified_events) == len(bundle.events) + 1
                and verified_events[-1].event_kind == "state_transition"
                and verified_events[-1].trigger == "closeout"
                and verified_events[-1].state_after == "closed"
            )
        if (
            bundle.plan != record.plan
            or bundle.session != record.session
            or not events_match
            or bundle.runtime_outcome != outcome
        ):
            raise AoARunnerError(
                "evidence chain differs from the verified Runner read model"
            )
        return closeout_bundle

    def _record(self, session: SessionHandle) -> _SessionRecord:
        record = self._sessions.get(session.session_id)
        if record is None:
            raise RunnerSessionNotFound(
                f"session {session.session_id!r} is not registered"
            )
        if record.session != session:
            raise AoARunnerError("session handle does not match the registered handle")
        _assert_session_matches_plan(session, record.plan)
        return record

    def _bind_adapter(
        self,
        record: _SessionRecord,
        adapter: RuntimeAdapterProtocol,
    ) -> None:
        self._assert_adapter(record, adapter)
        if record.adapter is not None and record.adapter.profile != adapter.profile:
            raise AoARunnerError("session adapter profile cannot change")
        record.adapter = adapter

    def _assert_adapter(
        self,
        record: _SessionRecord,
        adapter: RuntimeAdapterProtocol,
    ) -> None:
        if adapter.profile != record.plan.runtime_profile:
            raise AoARunnerError(
                "runtime adapter profile does not exactly match the run plan"
            )

    def _bound_adapter(self, record: _SessionRecord) -> RuntimeAdapterProtocol:
        if record.adapter is None:
            raise AoARunnerError("session has no explicitly bound runtime adapter")
        return record.adapter

    def _observe_snapshot(
        self,
        record: _SessionRecord,
        adapter: RuntimeAdapterProtocol,
    ) -> None:
        observation = adapter.observe_snapshot(record.plan, record.session)
        if observation.observed_by != adapter.profile.provenance:
            raise AoARunnerError(
                "runtime snapshot observation is not bound to the adapter profile"
            )
        if observation.observed_at < record.status.updated_at:
            raise AoARunnerError(
                "runtime snapshot observation predates the verified lifecycle state"
            )
        assert_runtime_snapshot_observation(
            record.plan,
            record.session,
            observation,
        )

    def _dispatch(
        self,
        record: _SessionRecord,
        adapter: RuntimeAdapterProtocol,
        command: RuntimeCommand,
    ) -> RunStatus:
        replayed = self._verified_replay_status(record, command)
        if replayed is not None:
            return replayed
        _assert_command_scope(record, command)
        receipt = adapter.dispatch(record.plan, record.session, command)
        with _verified_read_model_update(record):
            previous_status = record.status
            status, new_events = self._reconcile_with_events(
                record,
                adapter,
                commit=False,
            )
            _assert_receipt(
                receipt,
                command=command,
                status=status,
                previous_status=previous_status,
                new_events=new_events,
                runtime_provenance=adapter.profile.provenance,
            )
            record.events.extend(new_events)
            record.status = status
            record.receipts.append(receipt)
            self._reconcile_receipts(record, adapter)
            self._validate_current_approvals(record)
            self._validate_outcome(record)
        if receipt.status == "rejected":
            raise RunnerCommandRejected(
                f"runtime command rejected: {receipt.rejection_code}"
            )
        return status

    def _verified_replay_status(
        self,
        record: _SessionRecord,
        command: RuntimeCommand,
    ) -> RunStatus | None:
        matching_receipts = [
            receipt
            for receipt in record.receipts
            if receipt.idempotency_key == command.idempotency_key
        ]
        if not matching_receipts:
            return None
        if len(matching_receipts) != 1:
            raise AoARunnerError("duplicate idempotency receipts are ambiguous")
        receipt = matching_receipts[0]
        if (
            receipt.command_id != command.command_id
            or receipt.command_digest != command_digest(command)
        ):
            raise AoARunnerError(
                "idempotency key was reused with different command content"
            )
        if receipt.status == "rejected":
            raise RunnerCommandRejected(
                f"runtime command rejected: {receipt.rejection_code}"
            )
        return record.status

    def _assert_retry_allowed(self, record: _SessionRecord) -> None:
        status = record.status
        if status.state != "recoverable_failure" or status.failure_code is None:
            raise AoARunnerError(
                "bounded recovery requires a current recoverable failure"
            )
        policy = record.plan.retry_policy
        if status.failure_code not in policy.retryable_failure_codes:
            raise AoARunnerError(
                f"failure code {status.failure_code!r} is not retryable by the plan"
            )
        prior_recoveries = sum(
            event.event_kind == "state_transition" and event.trigger == "recover"
            for event in record.events
        )
        next_attempt = prior_recoveries + 2
        if next_attempt > policy.max_attempts:
            raise AoARunnerError(
                f"retry attempt {next_attempt} exceeds max_attempts "
                f"{policy.max_attempts}"
            )

    def _reconcile(
        self,
        record: _SessionRecord,
        adapter: RuntimeAdapterProtocol,
    ) -> RunStatus:
        status, _ = self._reconcile_with_events(record, adapter)
        return status

    def _reconcile_with_events(
        self,
        record: _SessionRecord,
        adapter: RuntimeAdapterProtocol,
        *,
        commit: bool = True,
    ) -> tuple[RunStatus, tuple[ExecutionEvent, ...]]:
        previous_status = record.status
        previous_digest = record.events[-1].event_digest if record.events else None
        supplied_events = tuple(
            adapter.events(
                record.session,
                after_sequence=previous_status.last_event_sequence,
            )
        )
        normalized = deduplicate_execution_events(supplied_events)
        retained_event_ids = {event.event_id for event in record.events}
        reused_event_ids = sorted(
            event.event_id
            for event in normalized
            if event.event_id in retained_event_ids
        )
        if reused_event_ids:
            raise AoARunnerError(
                f"runtime reused event ids across reconciled slices: {reused_event_ids}"
            )
        assert_execution_event_chain(
            normalized,
            session=record.session,
            after_sequence=previous_status.last_event_sequence,
            previous_digest=previous_digest,
        )
        status = adapter.status(record.session)
        _assert_status_and_events(
            previous_status,
            status,
            normalized,
            runtime_provenance=adapter.profile.provenance,
        )
        if commit:
            record.events.extend(normalized)
            record.status = status
        return status, normalized

    def _validated_approval_requests(
        self,
        record: _SessionRecord,
    ) -> tuple[ApprovalRequest, ...]:
        adapter = self._bound_adapter(record)
        requests = tuple(adapter.approval_requests(record.session))
        requirements = {
            requirement.requirement_id: requirement
            for requirement in record.plan.approval_requirements
        }
        seen: set[str] = set()
        for request in requests:
            if request.requirement_id in seen:
                raise AoARunnerError(
                    f"duplicate current approval request for {request.requirement_id}"
                )
            seen.add(request.requirement_id)
            requirement = requirements.get(request.requirement_id)
            if requirement is None:
                raise AoARunnerError(
                    f"adapter requested unknown approval {request.requirement_id}"
                )
            if (
                request.session_id != record.session.session_id
                or request.correlation_id != record.session.correlation_id
                or request.plan_digest != record.plan.plan_digest
                or request.snapshot_digest != record.plan.snapshot.snapshot_digest
                or request.approval_authority != requirement.approval_owner
                or request.request_provenance != adapter.profile.provenance
            ):
                raise AoARunnerError(
                    f"approval request scope mismatch for {request.requirement_id}"
                )
            expected_ref = _approval_request_ref(request)
            matching_events = [
                event
                for event in record.events
                if event.approval_request_ref == expected_ref
            ]
            if len(matching_events) != 1:
                raise AoARunnerError(
                    f"approval request {request.request_id!r} lacks one exact event"
                )
        if record.status.state == "awaiting_approval":
            if set(record.status.pending_approval_ids) != set(seen):
                raise AoARunnerError(
                    "pending approval status does not match current requests"
                )
        return requests

    def _validate_current_approvals(
        self,
        record: _SessionRecord,
        *,
        at: datetime | None = None,
    ) -> tuple[ApprovalDecision, ...]:
        if record.adapter is None:
            return ()
        requests = {
            request.requirement_id: request
            for request in self._validated_approval_requests(record)
        }
        requirements = {
            requirement.requirement_id: requirement
            for requirement in record.plan.approval_requirements
        }
        decisions = tuple(record.adapter.approval_decisions(record.session))
        seen: set[str] = set()
        for decision in decisions:
            if decision.requirement_id in seen:
                raise AoARunnerError(
                    f"duplicate current approval decision for {decision.requirement_id}"
                )
            seen.add(decision.requirement_id)
            requirement = requirements.get(decision.requirement_id)
            request = requests.get(decision.requirement_id)
            if requirement is None or request is None:
                raise AoARunnerError(
                    f"approval decision has no current request: {decision.requirement_id}"
                )
            assert_approval_decision_matches_request(
                requirement,
                request,
                decision,
            )
            expected_ref = _approval_decision_ref(decision)
            matching_events = [
                event
                for event in record.events
                if event.approval_decision_ref == expected_ref
            ]
            if len(matching_events) != 1:
                raise AoARunnerError(
                    f"approval decision {decision.decision_id!r} lacks one exact event"
                )
        if at is not None and record.plan.approval_requirements:
            from ...contracts.control_plane import assert_approvals_satisfied

            assert_approvals_satisfied(
                record.plan,
                decisions,
                session=record.session,
                at=_aware(at, "approval check time"),
            )
        return decisions

    def _reconcile_receipts(
        self,
        record: _SessionRecord,
        adapter: RuntimeAdapterProtocol,
    ) -> None:
        receipts = tuple(adapter.command_receipts(record.session))
        keys: set[str] = set()
        event_by_ref = {_ref_key(_event_ref(event)): event for event in record.events}
        claimed_event_refs: set[tuple[str, str, str, str]] = set()
        previous_slice_end = -1
        previous_resulting_revision = -1
        durable_by_key: dict[str, CommandReceipt] = {}
        for receipt in receipts:
            if receipt.idempotency_key in keys:
                raise AoARunnerError(
                    f"duplicate adapter receipt key: {receipt.idempotency_key}"
                )
            keys.add(receipt.idempotency_key)
            if (
                receipt.session_id != record.session.session_id
                or receipt.produced_by != adapter.profile.provenance
                or receipt.status != "applied"
            ):
                raise AoARunnerError("durable runtime receipt is not authoritative")
            if not receipt.event_refs:
                raise AoARunnerError("durable runtime receipt has no event slice")
            ref_keys = tuple(_ref_key(ref) for ref in receipt.event_refs)
            if len(ref_keys) != len(set(ref_keys)):
                raise AoARunnerError("durable runtime receipt repeats an event ref")
            if claimed_event_refs.intersection(ref_keys):
                raise AoARunnerError("durable runtime receipts overlap event slices")
            try:
                events = tuple(event_by_ref[key] for key in ref_keys)
            except KeyError as exc:
                raise AoARunnerError(
                    "durable runtime receipt references an unverified event"
                ) from exc
            sequences = tuple(event.sequence for event in events)
            if sequences != tuple(range(sequences[0], sequences[-1] + 1)):
                raise AoARunnerError(
                    "durable runtime receipt event slice is not contiguous and ordered"
                )
            if sequences[0] <= previous_slice_end:
                raise AoARunnerError(
                    "durable receipt event slices are not strictly ordered"
                )
            if receipt.resulting_revision < previous_resulting_revision:
                raise AoARunnerError("durable receipt revisions moved backwards")
            acknowledgements = [
                event
                for event in events
                if event.event_kind == "command_ack"
                and event.command_id == receipt.command_id
                and event.idempotency_key == receipt.idempotency_key
            ]
            if len(acknowledgements) != 1 or acknowledgements[0] != events[-1]:
                raise AoARunnerError(
                    "durable runtime receipt lacks one terminal exact acknowledgement"
                )
            if receipt.resulting_revision > record.status.revision:
                raise AoARunnerError(
                    "durable runtime receipt revision exceeds runtime status"
                )
            claimed_event_refs.update(ref_keys)
            previous_slice_end = sequences[-1]
            previous_resulting_revision = receipt.resulting_revision
            durable_by_key[receipt.idempotency_key] = receipt
        acknowledged_commands = {
            (event.command_id, event.idempotency_key)
            for event in record.events
            if event.event_kind == "command_ack"
        }
        receipted_commands = {
            (receipt.command_id, receipt.idempotency_key) for receipt in receipts
        }
        if acknowledged_commands != receipted_commands:
            raise AoARunnerError(
                "runtime command acknowledgements and durable receipts do not match"
            )
        local_keys: set[str] = set()
        rejected_receipts: list[CommandReceipt] = []
        for local_receipt in record.receipts:
            if local_receipt.idempotency_key in local_keys:
                raise AoARunnerError(
                    "duplicate local idempotency receipts are ambiguous"
                )
            local_keys.add(local_receipt.idempotency_key)
            durable_receipt = durable_by_key.get(local_receipt.idempotency_key)
            if local_receipt.status == "rejected":
                if (
                    local_receipt.session_id != record.session.session_id
                    or local_receipt.produced_by != adapter.profile.provenance
                ):
                    raise AoARunnerError(
                        "local rejected receipt is outside the runtime scope"
                    )
                if durable_receipt is not None:
                    raise AoARunnerError(
                        "a rejected command key also has a durable applied receipt"
                    )
                rejected_receipts.append(local_receipt)
                continue
            if durable_receipt is None:
                raise AoARunnerError(
                    "local applied or duplicate receipt is absent from durable state"
                )
            if local_receipt.status == "applied":
                if local_receipt != durable_receipt:
                    raise AoARunnerError(
                        "local applied receipt differs from durable runtime state"
                    )
            elif (
                local_receipt.command_id != durable_receipt.command_id
                or local_receipt.command_digest != durable_receipt.command_digest
                or local_receipt.session_id != durable_receipt.session_id
                or local_receipt.produced_by != durable_receipt.produced_by
            ):
                raise AoARunnerError(
                    "local duplicate receipt does not bind the durable command"
                )
        record.receipts[:] = [*receipts, *rejected_receipts]

    def _validate_outcome(self, record: _SessionRecord) -> RunOutcome | None:
        if record.adapter is None:
            return None
        outcome = record.adapter.outcome(record.session)
        if outcome is None:
            if any(event.event_kind == "outcome" for event in record.events):
                raise AoARunnerError(
                    "runtime event chain names an outcome that the adapter omitted"
                )
            if record.status.state in {"failed", "completed", "cancelled", "closed"}:
                raise AoARunnerError("terminal runtime state has no RunOutcome")
            return None
        if (
            outcome.session_id != record.session.session_id
            or outcome.correlation_id != record.session.correlation_id
            or outcome.plan_digest != record.plan.plan_digest
            or outcome.runtime_result_ref.owner_repo
            != record.plan.runtime_profile.runtime_owner
        ):
            raise AoARunnerError("runtime outcome is outside the session scope")
        expected_state = (
            record.status.state
            if record.status.state != "closed"
            else outcome.terminal_state
        )
        if outcome.terminal_state != expected_state:
            raise AoARunnerError("runtime outcome does not match terminal status")
        expected_ref = _outcome_ref(outcome)
        matching_events = [
            event for event in record.events if event.outcome_ref == expected_ref
        ]
        if len(matching_events) != 1:
            raise AoARunnerError(
                f"runtime outcome {outcome.outcome_id!r} lacks one exact event"
            )
        return outcome


def default_runner_provenance() -> ProvenanceRef:
    source_file = Path(__file__)
    module_digest = hashlib.sha256(source_file.read_bytes()).hexdigest()
    return ProvenanceRef(
        owner_repo="aoa-sdk",
        artifact_ref="src/aoa_sdk/control_plane/runner/core.py",
        source_ref=f"{AOA_RUNNER_VERSION}@sha256:{module_digest}",
        artifact_digest=f"sha256:{module_digest}",
        schema_ref="src/aoa_sdk/contracts/control_plane.py",
        schema_version="aoa_control_plane_v1",
    )


def _assert_session_matches_plan(session: SessionHandle, plan: RunPlan) -> None:
    expected_ref = ContentRef(
        object_id=plan.plan_id,
        owner_repo=plan.provenance.owner_repo,
        schema_version=plan.schema_version,
        digest=plan.plan_digest,
    )
    if (
        session.correlation_id != plan.correlation_id
        or session.plan_ref != expected_ref
        or session.plan_digest != plan.plan_digest
        or session.snapshot_digest != plan.snapshot.snapshot_digest
    ):
        raise AoARunnerError("session handle does not match the exact run plan")


def _assert_command_scope(
    record: _SessionRecord,
    command: RuntimeCommand,
) -> None:
    status = record.status
    if (
        command.session_id != record.session.session_id
        or command.correlation_id != record.session.correlation_id
        or command.plan_digest != record.plan.plan_digest
    ):
        raise AoARunnerError("runtime command is outside the session and plan scope")
    if command.expected_revision != status.revision:
        raise AoARunnerError(
            f"runtime command expected revision {command.expected_revision}, "
            f"current revision is {status.revision}"
        )
    allowed_states: tuple[str, ...]
    if isinstance(command, StartCommand):
        allowed_states = ("prepared",)
    elif isinstance(command, PauseCommand):
        allowed_states = ("running",)
    elif isinstance(command, ResumeCommand):
        allowed_states = ("paused",)
        if command.resume_after_sequence != status.last_event_sequence:
            raise AoARunnerError("resume command does not pin the current event cursor")
    elif isinstance(command, RecoverCommand):
        allowed_states = ("recoverable_failure",)
        if command.recover_after_sequence != status.recover_from_event_sequence:
            raise AoARunnerError(
                "recover command does not pin the interruption recovery cursor"
            )
        if (
            command.recovery_evidence_ref.owner_repo
            != record.plan.runtime_profile.runtime_owner
        ):
            raise AoARunnerError(
                "recovery evidence does not come from the runtime owner"
            )
    elif isinstance(command, CancelCommand):
        allowed_states = (
            "prepared",
            "awaiting_approval",
            "running",
            "paused",
            "recoverable_failure",
        )
    else:
        raise AoARunnerError(f"unsupported runtime command: {type(command).__name__}")
    if status.state not in allowed_states:
        raise AoARunnerError(
            f"{command.command_kind} is invalid while session is {status.state}"
        )


def _assert_receipt(
    receipt: CommandReceipt,
    *,
    command: RuntimeCommand,
    status: RunStatus,
    previous_status: RunStatus,
    new_events: tuple[ExecutionEvent, ...],
    runtime_provenance: ProvenanceRef,
) -> None:
    if (
        receipt.command_id != command.command_id
        or receipt.idempotency_key != command.idempotency_key
        or receipt.command_digest != command_digest(command)
        or receipt.session_id != command.session_id
        or receipt.resulting_revision != status.revision
        or receipt.produced_by != runtime_provenance
    ):
        raise AoARunnerError("runtime command receipt scope or digest mismatch")
    if receipt.status == "duplicate":
        if new_events or status != previous_status:
            raise AoARunnerError("duplicate command created a new effect or status")
        return
    if receipt.status == "applied":
        acknowledgements = [
            event
            for event in new_events
            if event.event_kind == "command_ack"
            and event.command_id == command.command_id
            and event.idempotency_key == command.idempotency_key
        ]
        if len(acknowledgements) != 1:
            raise AoARunnerError("applied command lacks one exact acknowledgement")
        if not new_events or acknowledgements[0] != new_events[-1]:
            raise AoARunnerError(
                "applied command acknowledgement must terminate its event slice"
            )
        expected_refs = tuple(_event_ref(event) for event in new_events)
        if receipt.event_refs != expected_refs:
            raise AoARunnerError(
                "command receipt does not bind the exact emitted event slice"
            )
    elif new_events or status != previous_status:
        raise AoARunnerError("rejected command changed runtime state or events")


def _assert_status_and_events(
    previous: RunStatus,
    current: RunStatus,
    events: tuple[ExecutionEvent, ...],
    *,
    runtime_provenance: ProvenanceRef,
) -> None:
    if (
        current.session_id != previous.session_id
        or current.correlation_id != previous.correlation_id
        or current.observed_by != runtime_provenance
    ):
        raise AoARunnerError("runtime status is outside the session or owner scope")
    expected_last_sequence = (
        events[-1].sequence if events else previous.last_event_sequence
    )
    if current.last_event_sequence != expected_last_sequence:
        raise AoARunnerError("runtime status does not name the verified event cursor")
    if current.updated_at < previous.updated_at:
        raise AoARunnerError("runtime status time moved backwards")
    state = previous.state
    previous_time = previous.updated_at
    for event in events:
        if event.emitted_by != runtime_provenance:
            raise AoARunnerError(
                f"event {event.event_id!r} is not emitted by the runtime owner"
            )
        if event.emitted_at < previous_time:
            raise AoARunnerError("runtime event time moved backwards")
        previous_time = event.emitted_at
        if event.event_kind == "state_transition":
            if event.state_before != state:
                raise AoARunnerError(
                    f"event {event.event_id!r} does not continue lifecycle state"
                )
            if event.state_after is None:
                raise AoARunnerError("state transition lacks resulting state")
            state = event.state_after
    if current.updated_at < previous_time:
        raise AoARunnerError("runtime status time predates the latest verified event")
    if state != current.state:
        raise AoARunnerError("runtime status state is not derived from event history")
    changed = (
        current.state != previous.state
        or current.pending_approval_ids != previous.pending_approval_ids
        or current.failure_code != previous.failure_code
        or current.recover_from_event_sequence != previous.recover_from_event_sequence
        or current.closeout_ref != previous.closeout_ref
    )
    if not events:
        if current != previous:
            raise AoARunnerError("runtime status changed without an event")
    elif changed and current.revision <= previous.revision:
        raise AoARunnerError("runtime status mutation did not advance revision")
    elif current.revision < previous.revision:
        raise AoARunnerError("runtime status revision moved backwards")


def _event_ref(event: ExecutionEvent) -> ContentRef:
    return ContentRef(
        object_id=event.event_id,
        owner_repo=event.emitted_by.owner_repo,
        schema_version=event.schema_version,
        digest=event.event_digest,
    )


def _approval_request_ref(request: ApprovalRequest) -> ContentRef:
    return ContentRef(
        object_id=request.request_id,
        owner_repo=request.request_provenance.owner_repo,
        schema_version=request.schema_version,
        digest=canonical_digest(request),
    )


def _approval_decision_ref(decision: ApprovalDecision) -> ContentRef:
    return ContentRef(
        object_id=decision.decision_id,
        owner_repo=decision.approval_authority.owner_repo,
        schema_version=decision.schema_version,
        digest=canonical_digest(decision),
    )


def _outcome_ref(outcome: RunOutcome) -> ContentRef:
    return ContentRef(
        object_id=outcome.outcome_id,
        owner_repo=outcome.runtime_result_ref.owner_repo,
        schema_version=outcome.schema_version,
        digest=canonical_digest(outcome),
    )


def _ref_key(ref: ContentRef) -> tuple[str, str, str, str]:
    return (
        ref.object_id,
        ref.owner_repo,
        ref.schema_version,
        ref.digest,
    )


def _aware(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise AoARunnerError(f"{field_name} must be timezone-aware")
    return value.astimezone(timezone.utc)


@contextmanager
def _verified_read_model_update(record: _SessionRecord) -> Iterator[None]:
    """Rollback every local projection when one runtime view fails validation."""

    previous_status = record.status
    previous_events = tuple(record.events)
    previous_receipts = tuple(record.receipts)
    try:
        yield
    except Exception:
        record.status = previous_status
        record.events[:] = previous_events
        record.receipts[:] = previous_receipts
        raise
