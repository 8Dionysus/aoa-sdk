from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from aoa_sdk import AoASDK
from aoa_sdk.contracts.control_plane import (
    ApprovalDecision,
    AoARunnerProtocol,
    CancelCommand,
    CloseoutBundleRef,
    CommandReceipt,
    ControlPlaneContractError,
    EvalVerdictRef,
    EvidenceBundleRef,
    MemoryReceiptRef,
    PauseCommand,
    ProvenanceRef,
    RecoverCommand,
    ResumeCommand,
    RouteDecision,
    RunPlan,
    RuntimeAdapterProtocol,
    ScenarioBinding,
    StartCommand,
    canonical_digest,
    command_digest,
    execution_event_digest,
)
from aoa_sdk.control_plane.planning import (
    compile_run_plan,
    load_plan_compilation_snapshot,
)
from aoa_sdk.control_plane.runner import (
    AoARunner,
    AoARunnerError,
    DeterministicReferenceAdapter,
    ReferenceAdapterUnavailable,
    reference_runtime_profile,
)


REPO_ROOT = Path(__file__).resolve().parents[5]
INPUTS_PATH = (
    REPO_ROOT
    / "mechanics"
    / "boundary-bridge"
    / "parts"
    / "plan-compilation-control-plane"
    / "examples"
    / "installed-wheel-smoke.inputs.json"
)
GOLDEN_PLAN_PATHS = (
    "bounded-preview-pruned.run-plan.json",
    "a2a-eval-only.run-plan.json",
    "runtime-proof-without-reground.run-plan.json",
)
NOW = datetime(2026, 7, 26, 18, 0, tzinfo=timezone.utc)


@dataclass
class MutableClock:
    value: datetime

    def __call__(self) -> datetime:
        return self.value


class OutOfOrderAdapter(DeterministicReferenceAdapter):
    def events(
        self,
        session,
        *,
        after_sequence: int,
    ):
        return tuple(
            reversed(
                tuple(
                    super().events(
                        session,
                        after_sequence=after_sequence,
                    )
                )
            )
        )


class InvalidDigestAdapter(DeterministicReferenceAdapter):
    def events(
        self,
        session,
        *,
        after_sequence: int,
    ):
        events = tuple(
            super().events(
                session,
                after_sequence=after_sequence,
            )
        )
        if not events:
            return events
        return (
            events[0].model_copy(update={"event_digest": _digest("tampered")}),
            *events[1:],
        )


class InvalidReceiptAdapter(DeterministicReferenceAdapter):
    def dispatch(self, plan, session, command):
        receipt = super().dispatch(plan, session, command)
        return receipt.model_copy(
            update={"command_digest": _digest("wrong-command")}
        )


class InvalidRestoredReceiptAdapter(DeterministicReferenceAdapter):
    tamper_receipts = False

    def command_receipts(self, session):
        receipts = tuple(super().command_receipts(session))
        if not self.tamper_receipts:
            return receipts
        return (
            receipts[0].model_copy(update={"event_refs": ()}),
            *receipts[1:],
        )


class InvalidApprovalDecisionReadAdapter(DeterministicReferenceAdapter):
    def approval_decisions(self, session):
        decisions = tuple(super().approval_decisions(session))
        return tuple(
            decision.model_copy(update={"reason": "tampered durable decision"})
            for decision in decisions
        )


class StaleObservationAdapter(DeterministicReferenceAdapter):
    def observe_snapshot(self, plan, session):
        observation = super().observe_snapshot(plan, session)
        return observation.model_copy(
            update={"observed_at": session.prepared_at - timedelta(seconds=1)}
        )


class RejectPauseAdapter(DeterministicReferenceAdapter):
    def dispatch(self, plan, session, command):
        if isinstance(command, PauseCommand):
            status = self.status(session)
            return CommandReceipt(
                command_id=command.command_id,
                idempotency_key=command.idempotency_key,
                command_digest=command_digest(command),
                session_id=session.session_id,
                status="rejected",
                resulting_revision=status.revision,
                rejection_code="reference_pause_denied",
                produced_by=self.profile.provenance,
            )
        return super().dispatch(plan, session, command)


class InvalidOutcomeReadAdapter(DeterministicReferenceAdapter):
    def outcome(self, session):
        outcome = super().outcome(session)
        if outcome is None:
            return None
        return outcome.model_copy(
            update={
                "runtime_result_ref": outcome.runtime_result_ref.model_copy(
                    update={"artifact_ref": "tampered-runtime-result"}
                )
            }
        )


class InvalidPostCloseoutOutcomeReadAdapter(DeterministicReferenceAdapter):
    def outcome(self, session):
        outcome = super().outcome(session)
        if outcome is None or super().status(session).state != "closed":
            return outcome
        return outcome.model_copy(
            update={
                "runtime_result_ref": outcome.runtime_result_ref.model_copy(
                    update={"artifact_ref": "tampered-after-closeout"}
                )
            }
        )


class DisconnectAfterApplyAdapter(DeterministicReferenceAdapter):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.dispatch_count = 0
        self.disconnect_after_apply = True

    def dispatch(self, plan, session, command):
        self.dispatch_count += 1
        receipt = super().dispatch(plan, session, command)
        if self.disconnect_after_apply:
            self.disconnect_after_apply = False
            raise ReferenceAdapterUnavailable("disconnected after durable command ack")
        return receipt


class MissingDurableReceiptAdapter(DeterministicReferenceAdapter):
    def command_receipts(self, session):
        super().command_receipts(session)
        return ()


class ReorderedDurableReceiptAdapter(DeterministicReferenceAdapter):
    reverse_receipts = False

    def command_receipts(self, session):
        receipts = tuple(super().command_receipts(session))
        if self.reverse_receipts:
            return tuple(reversed(receipts))
        return receipts


class StaleStatusTimestampAdapter(DeterministicReferenceAdapter):
    def status(self, session):
        status = super().status(session)
        if status.last_event_sequence < 0:
            return status
        return status.model_copy(
            update={"updated_at": status.updated_at - timedelta(microseconds=1)}
        )


class ReusedEventIdAdapter(DeterministicReferenceAdapter):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.retained_event_id: str | None = None
        self.reuse_next_event_id = False

    def events(self, session, *, after_sequence: int):
        events = tuple(super().events(session, after_sequence=after_sequence))
        if self.retained_event_id is None and events:
            self.retained_event_id = events[0].event_id
        if not self.reuse_next_event_id or not events:
            return events
        self.reuse_next_event_id = False
        reused = events[0].model_copy(
            update={
                "event_id": self.retained_event_id,
                "event_digest": _digest("pending-reused-event"),
            }
        )
        reused = reused.model_copy(
            update={"event_digest": execution_event_digest(reused)}
        )
        return (reused, *events[1:])


def _plan(
    *,
    renewable: bool = False,
    expiry_seconds: int | None = None,
    max_attempts: int | None = None,
    retryable_failure_codes: tuple[str, ...] | None = None,
) -> RunPlan:
    payload = json.loads(INPUTS_PATH.read_text(encoding="utf-8"))
    plan = compile_run_plan(
        RouteDecision.model_validate(payload["decision"]),
        ScenarioBinding.model_validate(payload["scenario_binding"]),
        reference_runtime_profile(),
        load_plan_compilation_snapshot(),
    )
    if (
        not renewable
        and expiry_seconds is None
        and max_attempts is None
        and retryable_failure_codes is None
    ):
        return plan
    requirement = plan.approval_requirements[0].model_copy(
        update={
            "renewable": renewable,
            "expires_after_seconds": expiry_seconds,
        }
    )
    retry_policy = plan.retry_policy.model_copy(
        update={
            "max_attempts": (
                max_attempts
                if max_attempts is not None
                else plan.retry_policy.max_attempts
            ),
            "retryable_failure_codes": (
                retryable_failure_codes
                if retryable_failure_codes is not None
                else plan.retry_policy.retryable_failure_codes
            ),
        }
    )
    updated = plan.model_copy(
        update={
            "approval_requirements": (requirement,),
            "retry_policy": retry_policy,
            "plan_digest": _digest("placeholder"),
        }
    )
    return updated.model_copy(
        update={"plan_digest": canonical_digest(updated, exclude={"plan_digest"})}
    )


def _runner(clock: MutableClock) -> AoARunner:
    return AoARunner(clock=clock, id_factory=lambda: "fixture")


def _start(runner: AoARunner, session, *, at: datetime) -> StartCommand:
    return StartCommand(
        command_id="command:start",
        idempotency_key="idempotency:start",
        session_id=session.session_id,
        correlation_id=session.correlation_id,
        plan_digest=session.plan_digest,
        expected_revision=runner.status(session).revision,
        issued_at=at,
        issued_by=_provenance("fixture-caller", "commands/start"),
        reason="begin the exact reference lifecycle",
    )


def _approve(
    runner: AoARunner,
    session,
    *,
    verdict: str = "approved",
    at: datetime,
) -> ApprovalDecision:
    request = runner.approval_requests(session)[0]
    return ApprovalDecision(
        decision_id=f"decision:{request.request_id}:{verdict}",
        request_id=request.request_id,
        requirement_id=request.requirement_id,
        session_id=session.session_id,
        correlation_id=session.correlation_id,
        plan_digest=session.plan_digest,
        snapshot_digest=session.snapshot_digest,
        verdict=verdict,
        approval_authority=request.approval_authority,
        decided_by=_provenance("fixture-operator", "identities/operator"),
        decided_at=at,
        reason=f"fixture {verdict} decision",
    )


def _pause(runner: AoARunner, session, *, at: datetime) -> PauseCommand:
    return PauseCommand(
        command_id=f"command:pause:{runner.status(session).revision}",
        idempotency_key=f"idempotency:pause:{runner.status(session).revision}",
        session_id=session.session_id,
        correlation_id=session.correlation_id,
        plan_digest=session.plan_digest,
        expected_revision=runner.status(session).revision,
        issued_at=at,
        issued_by=_provenance("fixture-caller", "commands/pause"),
        reason="pause the reference lifecycle",
    )


def _resume(runner: AoARunner, session, *, at: datetime) -> ResumeCommand:
    status = runner.status(session)
    return ResumeCommand(
        command_id=f"command:resume:{status.revision}",
        idempotency_key=f"idempotency:resume:{status.revision}",
        session_id=session.session_id,
        correlation_id=session.correlation_id,
        plan_digest=session.plan_digest,
        expected_revision=status.revision,
        issued_at=at,
        issued_by=_provenance("fixture-caller", "commands/resume"),
        reason="resume the exact verified cursor",
        resume_after_sequence=status.last_event_sequence,
    )


def _recover(runner: AoARunner, session, *, at: datetime) -> RecoverCommand:
    status = runner.status(session)
    assert status.recover_from_event_sequence is not None
    return RecoverCommand(
        command_id=f"command:recover:{status.revision}",
        idempotency_key=f"idempotency:recover:{status.revision}",
        session_id=session.session_id,
        correlation_id=session.correlation_id,
        plan_digest=session.plan_digest,
        expected_revision=status.revision,
        issued_at=at,
        issued_by=_provenance("fixture-caller", "commands/recover"),
        reason="recover to an inspectable paused state",
        recover_after_sequence=status.recover_from_event_sequence,
        recovery_evidence_ref=_provenance(
            "aoa-sdk",
            "reference-runtime/recovery-evidence",
        ),
    )


def _cancel(runner: AoARunner, session, *, at: datetime) -> CancelCommand:
    status = runner.status(session)
    return CancelCommand(
        command_id=f"command:cancel:{status.revision}",
        idempotency_key=f"idempotency:cancel:{status.revision}",
        session_id=session.session_id,
        correlation_id=session.correlation_id,
        plan_digest=session.plan_digest,
        expected_revision=status.revision,
        issued_at=at,
        issued_by=_provenance("fixture-caller", "commands/cancel"),
        reason="cancel the reference lifecycle",
    )


def _completed_refs(plan: RunPlan):
    evidence = tuple(
        EvidenceBundleRef(
            ref_id=f"evidence-ref:{requirement.requirement_id}",
            provenance=_provenance(
                requirement.producer_owner,
                f"reference-evidence/{requirement.requirement_id}",
            ),
            satisfies_requirement_ids=(requirement.requirement_id,),
        )
        for requirement in plan.evidence_requirements
        if requirement.terminal_required
    )
    evals = tuple(
        EvalVerdictRef(
            ref_id=f"eval-ref:{requirement.requirement_id}",
            provenance=_provenance(
                requirement.eval_owner_ref.owner_repo,
                f"reference-evals/{requirement.requirement_id}",
            ),
            satisfies_requirement_ids=(requirement.requirement_id,),
        )
        for requirement in plan.eval_requirements
        if requirement.verdict_required_for_closeout
    )
    memory = tuple(
        MemoryReceiptRef(
            ref_id=f"memory-ref:{requirement.requirement_id}",
            provenance=_provenance(
                requirement.memory_owner_ref.owner_repo,
                f"reference-memory/{requirement.requirement_id}",
            ),
            satisfies_requirement_ids=(requirement.requirement_id,),
        )
        for requirement in plan.retention_requirements
        if requirement.receipt_required_for_closeout
    )
    return evidence, evals, memory


def _closeout_bundle(plan: RunPlan) -> CloseoutBundleRef:
    owners = {
        requirement.owner_ref.owner_repo
        for requirement in plan.closeout_requirements
    }
    assert len(owners) == 1
    owner = next(iter(owners))
    return CloseoutBundleRef(
        ref_id=f"closeout-ref:{plan.plan_id}",
        provenance=_provenance(owner, f"reference-closeout/{plan.plan_id}"),
        satisfies_requirement_ids=tuple(
            requirement.requirement_id
            for requirement in plan.closeout_requirements
        ),
    )


def _running_session(*, clock: MutableClock | None = None):
    clock = clock or MutableClock(NOW)
    plan = _plan()
    runner = _runner(clock)
    adapter = DeterministicReferenceAdapter(clock=clock)
    session = runner.prepare(plan)
    runner.start(session, adapter, _start(runner, session, at=NOW + timedelta(seconds=1)))
    decision = _approve(
        runner,
        session,
        at=NOW + timedelta(seconds=2),
    )
    runner.approve(session, decision)
    assert runner.status(session).state == "running"
    return clock, plan, runner, adapter, session, decision


def test_aoa_sdk_exposes_a_lazy_runner_without_selecting_an_adapter() -> None:
    sdk = AoASDK.from_workspace(REPO_ROOT)
    assert isinstance(sdk.runner, AoARunner)
    assert isinstance(sdk.runner, AoARunnerProtocol)
    assert isinstance(DeterministicReferenceAdapter(), RuntimeAdapterProtocol)


def test_normal_completion_and_evidence_complete_closeout() -> None:
    clock, plan, runner, adapter, session, _ = _running_session()
    evidence, evals, memory = _completed_refs(plan)
    adapter.advance(
        session,
        trigger="runtime_completed",
        at=NOW + timedelta(seconds=3),
        evidence_bundle_refs=evidence,
        eval_verdict_refs=evals,
        memory_receipt_refs=memory,
    )
    assert runner.sync(session, adapter).state == "completed"
    outcome = runner.outcome(session)
    assert outcome is not None
    clock.value = NOW + timedelta(seconds=4)
    bundle = _closeout_bundle(plan)
    status = runner.closeout(session, outcome, bundle)
    assert status.state == "closed"
    assert runner.closeout(session, outcome, bundle) == status
    with pytest.raises(AoARunnerError, match="different bundle"):
        runner.closeout(
            session,
            outcome,
            bundle.model_copy(update={"ref_id": "closeout-ref:different"}),
        )
    assert adapter.executes_plan_steps is False
    assert [event.sequence for event in runner.events(session)] == list(
        range(len(runner.events(session)))
    )


@pytest.mark.parametrize("file_name", GOLDEN_PLAN_PATHS)
def test_all_c2_golden_plans_complete_through_one_runner_contract(
    file_name: str,
) -> None:
    plan = RunPlan.model_validate_json(
        (INPUTS_PATH.parent / file_name).read_text(encoding="utf-8")
    )
    clock = MutableClock(NOW)
    runner = _runner(clock)
    adapter = DeterministicReferenceAdapter(
        profile=plan.runtime_profile,
        clock=clock,
    )
    session = runner.prepare(plan)
    runner.start(
        session,
        adapter,
        _start(runner, session, at=NOW + timedelta(seconds=1)),
    )
    runner.approve(
        session,
        _approve(runner, session, at=NOW + timedelta(seconds=2)),
    )
    evidence, evals, memory = _completed_refs(plan)
    adapter.advance(
        session,
        trigger="runtime_completed",
        at=NOW + timedelta(seconds=3),
        evidence_bundle_refs=evidence,
        eval_verdict_refs=evals,
        memory_receipt_refs=memory,
    )
    assert runner.sync(session, adapter).state == "completed"
    outcome = runner.outcome(session)
    assert outcome is not None
    clock.value = NOW + timedelta(seconds=4)
    assert runner.closeout(
        session,
        outcome,
        _closeout_bundle(plan),
    ).state == "closed"


def test_rejected_approval_cancels_before_running() -> None:
    clock = MutableClock(NOW)
    plan = _plan()
    runner = _runner(clock)
    adapter = DeterministicReferenceAdapter(clock=clock)
    session = runner.prepare(plan)
    runner.start(session, adapter, _start(runner, session, at=NOW + timedelta(seconds=1)))
    status = runner.approve(
        session,
        _approve(
            runner,
            session,
            verdict="rejected",
            at=NOW + timedelta(seconds=2),
        ),
    )
    assert status.state == "cancelled"
    assert runner.outcome(session).execution_status == "cancelled"


def test_explicit_cancel_returns_a_typed_terminal_outcome() -> None:
    clock = MutableClock(NOW)
    plan = _plan()
    runner = _runner(clock)
    adapter = DeterministicReferenceAdapter(clock=clock)
    session = runner.prepare(plan)
    status = runner.cancel(
        session,
        adapter,
        _cancel(runner, session, at=NOW + timedelta(seconds=1)),
    )
    outcome = runner.outcome(session)
    assert status.state == "cancelled"
    assert outcome is not None
    assert outcome.execution_status == "cancelled"


def test_expired_approval_pauses_and_renewal_precedes_resume() -> None:
    clock = MutableClock(NOW)
    plan = _plan(renewable=True, expiry_seconds=10)
    runner = _runner(clock)
    adapter = DeterministicReferenceAdapter(clock=clock)
    session = runner.prepare(plan)
    runner.start(session, adapter, _start(runner, session, at=NOW + timedelta(seconds=1)))
    status = runner.approve(
        session,
        _approve(
            runner,
            session,
            verdict="expired",
            at=NOW + timedelta(seconds=12),
        ),
    )
    assert status.state == "paused"
    renewed = runner.renew_approvals(
        session,
        requested_at=NOW + timedelta(seconds=13),
    )
    assert renewed[0].request_id.endswith(":2")
    runner.approve(
        session,
        _approve(
            runner,
            session,
            at=NOW + timedelta(seconds=14),
        ),
    )
    status = runner.resume(
        session,
        adapter,
        _resume(runner, session, at=NOW + timedelta(seconds=15)),
    )
    assert status.state == "running"


def test_approval_window_rejects_early_expiry_and_expiry_boundary_approval() -> None:
    clock = MutableClock(NOW)
    plan = _plan(renewable=True, expiry_seconds=10)
    runner = _runner(clock)
    adapter = DeterministicReferenceAdapter(clock=clock)
    session = runner.prepare(plan)
    runner.start(
        session,
        adapter,
        _start(runner, session, at=NOW + timedelta(seconds=1)),
    )
    with pytest.raises(ControlPlaneContractError, match="expiry is outside"):
        runner.approve(
            session,
            _approve(
                runner,
                session,
                verdict="expired",
                at=NOW + timedelta(seconds=10),
            ),
        )
    with pytest.raises(ControlPlaneContractError, match="exceeded request window"):
        runner.approve(
            session,
            _approve(
                runner,
                session,
                at=NOW + timedelta(seconds=11),
            ),
        )
    assert runner.approve(
        session,
        _approve(runner, session, at=NOW + timedelta(seconds=10)),
    ).state == "running"
    runner.pause(
        session,
        adapter,
        _pause(runner, session, at=NOW + timedelta(seconds=11)),
    )
    with pytest.raises(ControlPlaneContractError, match="approval expired"):
        runner.resume(
            session,
            adapter,
            _resume(runner, session, at=NOW + timedelta(seconds=20)),
        )


def test_pause_resume_and_duplicate_commands_are_idempotent() -> None:
    _, _, runner, adapter, session, _ = _running_session()
    pause = _pause(runner, session, at=NOW + timedelta(seconds=3))
    paused = runner.pause(session, adapter, pause)
    event_count = len(runner.events(session))
    receipt_count = len(runner.command_receipts(session))
    assert runner.pause(session, adapter, pause) == paused
    assert len(runner.events(session)) == event_count
    assert len(runner.command_receipts(session)) == receipt_count
    resumed = runner.resume(
        session,
        adapter,
        _resume(runner, session, at=NOW + timedelta(seconds=4)),
    )
    assert resumed.state == "running"


def test_rejected_command_replay_returns_the_same_rejection_without_effect() -> None:
    clock = MutableClock(NOW)
    plan = _plan()
    runner = _runner(clock)
    adapter = RejectPauseAdapter(clock=clock)
    session = runner.prepare(plan)
    runner.start(
        session,
        adapter,
        _start(runner, session, at=NOW + timedelta(seconds=1)),
    )
    runner.approve(
        session,
        _approve(runner, session, at=NOW + timedelta(seconds=2)),
    )
    command = _pause(runner, session, at=NOW + timedelta(seconds=3))
    with pytest.raises(AoARunnerError, match="reference_pause_denied"):
        runner.pause(session, adapter, command)
    event_count = len(runner.events(session))
    receipt_count = len(runner.command_receipts(session))
    with pytest.raises(AoARunnerError, match="reference_pause_denied"):
        runner.pause(session, adapter, command)
    assert len(runner.events(session)) == event_count
    assert len(runner.command_receipts(session)) == receipt_count


def test_duplicate_start_and_approval_create_no_new_effect() -> None:
    clock = MutableClock(NOW)
    plan = _plan()
    runner = _runner(clock)
    adapter = DeterministicReferenceAdapter(clock=clock)
    session = runner.prepare(plan)
    command = _start(runner, session, at=NOW + timedelta(seconds=1))
    first = runner.start(session, adapter, command)
    event_count = len(runner.events(session))
    assert runner.start(session, adapter, command) == first
    assert len(runner.events(session)) == event_count
    approval = _approve(runner, session, at=NOW + timedelta(seconds=2))
    approved = runner.approve(session, approval)
    event_count = len(runner.events(session))
    assert runner.approve(session, approval) == approved
    assert len(runner.events(session)) == event_count


def test_partial_failure_returns_typed_terminal_outcome() -> None:
    _, plan, runner, adapter, session, _ = _running_session()
    evidence, _, _ = _completed_refs(plan)
    adapter.advance(
        session,
        trigger="runtime_failed",
        execution_status="partial",
        failure_codes=("partial_reference_failure",),
        at=NOW + timedelta(seconds=3),
        evidence_bundle_refs=evidence,
    )
    status = runner.sync(session, adapter)
    outcome = runner.outcome(session)
    assert status.state == "failed"
    assert outcome is not None
    assert outcome.execution_status == "partial"
    assert outcome.failure_codes == ("partial_reference_failure",)


def test_runtime_outcome_must_match_its_exact_event_reference() -> None:
    clock = MutableClock(NOW)
    plan = _plan()
    runner = _runner(clock)
    adapter = InvalidOutcomeReadAdapter(clock=clock)
    session = runner.prepare(plan)
    runner.start(
        session,
        adapter,
        _start(runner, session, at=NOW + timedelta(seconds=1)),
    )
    runner.approve(
        session,
        _approve(runner, session, at=NOW + timedelta(seconds=2)),
    )
    verified_status = runner.status(session)
    verified_events = runner.events(session)
    adapter.advance(
        session,
        trigger="runtime_completed",
        at=NOW + timedelta(seconds=3),
    )
    with pytest.raises(AoARunnerError, match="lacks one exact event"):
        runner.sync(session, adapter)
    assert runner.status(session) == verified_status
    assert runner.events(session) == verified_events


def test_disconnect_before_ack_is_replayable_without_state_change() -> None:
    clock = MutableClock(NOW)
    plan = _plan()
    runner = _runner(clock)
    adapter = DeterministicReferenceAdapter(clock=clock)
    session = runner.prepare(plan)
    command = _start(runner, session, at=NOW + timedelta(seconds=1))
    adapter.set_available(False)
    with pytest.raises(ReferenceAdapterUnavailable):
        runner.start(session, adapter, command)
    assert runner.status(session).state == "prepared"
    assert runner.command_receipts(session) == ()
    adapter.set_available(True)
    assert runner.start(session, adapter, command).state == "awaiting_approval"


def test_sync_imports_durable_receipt_after_disconnect_after_ack() -> None:
    clock = MutableClock(NOW)
    plan = _plan()
    runner = _runner(clock)
    adapter = DisconnectAfterApplyAdapter(clock=clock)
    session = runner.prepare(plan)
    command = _start(runner, session, at=NOW + timedelta(seconds=1))
    with pytest.raises(
        ReferenceAdapterUnavailable,
        match="after durable command ack",
    ):
        runner.start(session, adapter, command)
    assert runner.status(session).state == "prepared"
    assert runner.events(session) == ()
    assert runner.command_receipts(session) == ()

    assert runner.sync(session, adapter).state == "awaiting_approval"
    receipts = runner.command_receipts(session)
    assert len(receipts) == 1
    assert receipts[0].status == "applied"
    assert runner.start(session, adapter, command).state == "awaiting_approval"
    assert adapter.dispatch_count == 1


def test_disconnect_after_ack_reconciles_to_recoverable_failure() -> None:
    _, _, runner, adapter, session, _ = _running_session()
    adapter.advance(
        session,
        trigger="runtime_interrupted",
        failure_codes=("reference_disconnect",),
        at=NOW + timedelta(seconds=3),
    )
    adapter.set_available(False)
    with pytest.raises(ReferenceAdapterUnavailable):
        runner.sync(session, adapter)
    assert runner.status(session).state == "running"
    adapter.set_available(True)
    assert runner.sync(session, adapter).state == "recoverable_failure"


def test_recovery_requires_pause_before_resume_and_can_closeout() -> None:
    clock = MutableClock(NOW)
    plan = _plan(
        max_attempts=2,
        retryable_failure_codes=("reference_disconnect",),
    )
    runner = _runner(clock)
    adapter = DeterministicReferenceAdapter(clock=clock)
    session = runner.prepare(plan)
    runner.start(
        session,
        adapter,
        _start(runner, session, at=NOW + timedelta(seconds=1)),
    )
    runner.approve(
        session,
        _approve(runner, session, at=NOW + timedelta(seconds=2)),
    )
    adapter.advance(
        session,
        trigger="runtime_interrupted",
        failure_codes=("reference_disconnect",),
        at=NOW + timedelta(seconds=3),
    )
    assert runner.sync(session, adapter).state == "recoverable_failure"
    assert runner.recover(
        session,
        adapter,
        _recover(runner, session, at=NOW + timedelta(seconds=4)),
    ).state == "paused"
    assert runner.resume(
        session,
        adapter,
        _resume(runner, session, at=NOW + timedelta(seconds=5)),
    ).state == "running"
    evidence, evals, memory = _completed_refs(plan)
    adapter.advance(
        session,
        trigger="runtime_completed",
        at=NOW + timedelta(seconds=6),
        evidence_bundle_refs=evidence,
        eval_verdict_refs=evals,
        memory_receipt_refs=memory,
    )
    runner.sync(session, adapter)
    outcome = runner.outcome(session)
    assert outcome is not None
    clock.value = NOW + timedelta(seconds=7)
    assert runner.closeout(
        session,
        outcome,
        _closeout_bundle(plan),
    ).state == "closed"


def test_recovery_enforces_retryable_codes_and_attempt_bound() -> None:
    plan = _plan(
        max_attempts=2,
        retryable_failure_codes=("retryable_disconnect",),
    )

    clock = MutableClock(NOW)
    runner = _runner(clock)
    adapter = DeterministicReferenceAdapter(clock=clock)
    session = runner.prepare(plan)
    runner.start(
        session,
        adapter,
        _start(runner, session, at=NOW + timedelta(seconds=1)),
    )
    runner.approve(
        session,
        _approve(runner, session, at=NOW + timedelta(seconds=2)),
    )
    adapter.advance(
        session,
        trigger="runtime_interrupted",
        failure_codes=("not_retryable",),
        at=NOW + timedelta(seconds=3),
    )
    runner.sync(session, adapter)
    with pytest.raises(AoARunnerError, match="is not retryable"):
        runner.recover(
            session,
            adapter,
            _recover(runner, session, at=NOW + timedelta(seconds=4)),
        )

    clock = MutableClock(NOW)
    runner = _runner(clock)
    adapter = DeterministicReferenceAdapter(clock=clock)
    session = runner.prepare(plan)
    runner.start(
        session,
        adapter,
        _start(runner, session, at=NOW + timedelta(seconds=1)),
    )
    runner.approve(
        session,
        _approve(runner, session, at=NOW + timedelta(seconds=2)),
    )
    adapter.advance(
        session,
        trigger="runtime_interrupted",
        failure_codes=("retryable_disconnect",),
        at=NOW + timedelta(seconds=3),
    )
    runner.sync(session, adapter)
    recover = _recover(runner, session, at=NOW + timedelta(seconds=4))
    with pytest.raises(AoARunnerError, match="recovery evidence"):
        runner.recover(
            session,
            adapter,
            recover.model_copy(
                update={
                    "recovery_evidence_ref": _provenance(
                        "foreign-runtime",
                        "recovery-evidence",
                    )
                }
            ),
        )
    assert runner.recover(session, adapter, recover).state == "paused"
    assert runner.recover(session, adapter, recover).state == "paused"
    runner.resume(
        session,
        adapter,
        _resume(runner, session, at=NOW + timedelta(seconds=5)),
    )
    adapter.advance(
        session,
        trigger="runtime_interrupted",
        failure_codes=("retryable_disconnect",),
        at=NOW + timedelta(seconds=6),
    )
    runner.sync(session, adapter)
    with pytest.raises(AoARunnerError, match="exceeds max_attempts"):
        runner.recover(
            session,
            adapter,
            _recover(runner, session, at=NOW + timedelta(seconds=7)),
        )


def test_restore_rebuilds_verified_state_and_idempotency_ledger() -> None:
    clock, plan, runner, adapter, session, _ = _running_session()
    restored = AoARunner(clock=clock, id_factory=lambda: "unused")
    status = restored.restore(plan, session, adapter)
    assert status == runner.status(session)
    assert restored.events(session) == runner.events(session)
    start = _start_for_revision_zero(session)
    event_count = len(restored.events(session))
    assert restored.start(session, adapter, start) == status
    assert len(restored.events(session)) == event_count


def test_restore_rejects_a_receipt_without_its_verified_event_slice() -> None:
    clock = MutableClock(NOW)
    plan = _plan()
    runner = _runner(clock)
    adapter = InvalidRestoredReceiptAdapter(clock=clock)
    session = runner.prepare(plan)
    runner.start(
        session,
        adapter,
        _start(runner, session, at=NOW + timedelta(seconds=1)),
    )
    adapter.tamper_receipts = True
    restored = AoARunner(clock=clock, id_factory=lambda: "unused")
    with pytest.raises(AoARunnerError, match="has no event slice"):
        restored.restore(plan, session, adapter)


def test_restore_rejects_reordered_durable_receipt_slices() -> None:
    clock = MutableClock(NOW)
    plan = _plan()
    runner = _runner(clock)
    adapter = ReorderedDurableReceiptAdapter(clock=clock)
    session = runner.prepare(plan)
    runner.start(
        session,
        adapter,
        _start(runner, session, at=NOW + timedelta(seconds=1)),
    )
    runner.approve(
        session,
        _approve(runner, session, at=NOW + timedelta(seconds=2)),
    )
    runner.pause(
        session,
        adapter,
        _pause(runner, session, at=NOW + timedelta(seconds=3)),
    )
    adapter.reverse_receipts = True
    restored = AoARunner(clock=clock, id_factory=lambda: "unused")
    with pytest.raises(AoARunnerError, match="not strictly ordered"):
        restored.restore(plan, session, adapter)


def test_approval_decision_must_match_its_exact_event_reference() -> None:
    clock = MutableClock(NOW)
    plan = _plan()
    runner = _runner(clock)
    adapter = InvalidApprovalDecisionReadAdapter(clock=clock)
    session = runner.prepare(plan)
    runner.start(
        session,
        adapter,
        _start(runner, session, at=NOW + timedelta(seconds=1)),
    )
    verified_status = runner.status(session)
    verified_events = runner.events(session)
    verified_receipts = runner.command_receipts(session)
    with pytest.raises(AoARunnerError, match="lacks one exact event"):
        runner.approve(
            session,
            _approve(runner, session, at=NOW + timedelta(seconds=2)),
        )
    assert runner.status(session) == verified_status
    assert runner.events(session) == verified_events
    assert runner.command_receipts(session) == verified_receipts


def test_snapshot_drift_blocks_before_dispatch() -> None:
    clock = MutableClock(NOW)
    plan = _plan()
    source = plan.snapshot.source_refs[0]
    adapter = DeterministicReferenceAdapter(
        clock=clock,
        observed_source_overrides={
            (source.owner_repo, source.artifact_ref): _digest("stale")
        },
    )
    runner = _runner(clock)
    session = runner.prepare(plan)
    with pytest.raises(ControlPlaneContractError, match="stale or spoofed"):
        runner.start(
            session,
            adapter,
            _start(runner, session, at=NOW + timedelta(seconds=1)),
        )
    assert runner.status(session).state == "prepared"


def test_stale_runtime_observation_blocks_before_dispatch() -> None:
    clock = MutableClock(NOW)
    plan = _plan()
    adapter = StaleObservationAdapter(clock=clock)
    runner = _runner(clock)
    session = runner.prepare(plan)
    with pytest.raises(AoARunnerError, match="predates"):
        runner.start(
            session,
            adapter,
            _start(runner, session, at=NOW + timedelta(seconds=1)),
        )
    assert runner.status(session).state == "prepared"


def test_status_timestamp_cannot_precede_the_latest_event() -> None:
    clock = MutableClock(NOW)
    plan = _plan()
    adapter = StaleStatusTimestampAdapter(clock=clock)
    runner = _runner(clock)
    session = runner.prepare(plan)
    with pytest.raises(AoARunnerError, match="predates the latest verified event"):
        runner.start(
            session,
            adapter,
            _start(runner, session, at=NOW + timedelta(seconds=1)),
        )
    assert runner.status(session).state == "prepared"
    assert runner.events(session) == ()
    assert runner.command_receipts(session) == ()


def test_event_id_cannot_be_reused_across_reconciled_slices() -> None:
    clock = MutableClock(NOW)
    plan = _plan()
    adapter = ReusedEventIdAdapter(clock=clock)
    runner = _runner(clock)
    session = runner.prepare(plan)
    runner.start(
        session,
        adapter,
        _start(runner, session, at=NOW + timedelta(seconds=1)),
    )
    runner.approve(
        session,
        _approve(runner, session, at=NOW + timedelta(seconds=2)),
    )
    verified_status = runner.status(session)
    verified_events = runner.events(session)
    adapter.reuse_next_event_id = True
    adapter.emit_progress(session, at=NOW + timedelta(seconds=3))
    with pytest.raises(AoARunnerError, match="reused event ids"):
        runner.sync(session, adapter)
    assert runner.status(session) == verified_status
    assert runner.events(session) == verified_events


@pytest.mark.parametrize(
    "adapter_type,error",
    [
        (OutOfOrderAdapter, "event sequence gap or reorder"),
        (InvalidDigestAdapter, "event digest mismatch"),
    ],
)
def test_out_of_order_or_invalid_runtime_event_fails_closed(
    adapter_type,
    error: str,
) -> None:
    clock = MutableClock(NOW)
    plan = _plan()
    adapter = adapter_type(clock=clock)
    runner = _runner(clock)
    session = runner.prepare(plan)
    with pytest.raises(ControlPlaneContractError, match=error):
        runner.start(
            session,
            adapter,
            _start(runner, session, at=NOW + timedelta(seconds=1)),
        )
    assert runner.status(session).state == "prepared"


def test_invalid_receipt_does_not_enter_the_verified_local_ledger() -> None:
    clock = MutableClock(NOW)
    plan = _plan()
    adapter = InvalidReceiptAdapter(clock=clock)
    runner = _runner(clock)
    session = runner.prepare(plan)
    with pytest.raises(AoARunnerError, match="receipt scope or digest"):
        runner.start(
            session,
            adapter,
            _start(runner, session, at=NOW + timedelta(seconds=1)),
        )
    assert runner.status(session).state == "prepared"
    assert runner.events(session) == ()
    assert runner.command_receipts(session) == ()


def test_command_ack_without_a_durable_receipt_fails_closed() -> None:
    clock = MutableClock(NOW)
    plan = _plan()
    adapter = MissingDurableReceiptAdapter(clock=clock)
    runner = _runner(clock)
    session = runner.prepare(plan)
    with pytest.raises(
        AoARunnerError,
        match="acknowledgements and durable receipts do not match",
    ):
        runner.start(
            session,
            adapter,
            _start(runner, session, at=NOW + timedelta(seconds=1)),
        )
    assert runner.status(session).state == "prepared"
    assert runner.events(session) == ()
    assert runner.command_receipts(session) == ()


def test_closeout_rejects_missing_owner_evidence() -> None:
    clock, plan, runner, adapter, session, _ = _running_session()
    adapter.advance(
        session,
        trigger="runtime_completed",
        at=NOW + timedelta(seconds=3),
    )
    runner.sync(session, adapter)
    outcome = runner.outcome(session)
    assert outcome is not None
    clock.value = NOW + timedelta(seconds=4)
    with pytest.raises(ControlPlaneContractError, match="terminal evidence"):
        runner.closeout(session, outcome, _closeout_bundle(plan))


def test_closeout_revalidates_the_exact_runtime_outcome_atomically() -> None:
    clock = MutableClock(NOW)
    plan = _plan()
    runner = _runner(clock)
    adapter = InvalidPostCloseoutOutcomeReadAdapter(clock=clock)
    session = runner.prepare(plan)
    runner.start(
        session,
        adapter,
        _start(runner, session, at=NOW + timedelta(seconds=1)),
    )
    runner.approve(
        session,
        _approve(runner, session, at=NOW + timedelta(seconds=2)),
    )
    evidence, evals, memory = _completed_refs(plan)
    adapter.advance(
        session,
        trigger="runtime_completed",
        at=NOW + timedelta(seconds=3),
        evidence_bundle_refs=evidence,
        eval_verdict_refs=evals,
        memory_receipt_refs=memory,
    )
    runner.sync(session, adapter)
    outcome = runner.outcome(session)
    assert outcome is not None
    verified_status = runner.status(session)
    verified_events = runner.events(session)
    clock.value = NOW + timedelta(seconds=4)
    with pytest.raises(AoARunnerError, match="lacks one exact event"):
        runner.closeout(session, outcome, _closeout_bundle(plan))
    assert runner.status(session) == verified_status
    assert runner.events(session) == verified_events


def test_idempotency_key_with_changed_payload_is_rejected() -> None:
    _, _, runner, adapter, session, _ = _running_session()
    pause = _pause(runner, session, at=NOW + timedelta(seconds=3))
    runner.pause(session, adapter, pause)
    replay = pause.model_copy(update={"reason": "different payload"})
    with pytest.raises(AoARunnerError, match="different command content"):
        runner.pause(session, adapter, replay)


def _start_for_revision_zero(session) -> StartCommand:
    return StartCommand(
        command_id="command:start",
        idempotency_key="idempotency:start",
        session_id=session.session_id,
        correlation_id=session.correlation_id,
        plan_digest=session.plan_digest,
        expected_revision=0,
        issued_at=NOW + timedelta(seconds=1),
        issued_by=_provenance("fixture-caller", "commands/start"),
        reason="begin the exact reference lifecycle",
    )


def _provenance(owner: str, artifact_ref: str) -> ProvenanceRef:
    return ProvenanceRef(
        owner_repo=owner,
        artifact_ref=artifact_ref,
        source_ref="fixture-source-ref",
        artifact_digest=_digest(f"{owner}:{artifact_ref}"),
        schema_ref="schemas/fixture.schema.json",
        schema_version="fixture-v1",
    )


def _digest(value: str) -> str:
    import hashlib

    return f"sha256:{hashlib.sha256(value.encode()).hexdigest()}"
