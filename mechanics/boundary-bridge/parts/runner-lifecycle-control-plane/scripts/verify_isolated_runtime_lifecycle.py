#!/usr/bin/env python3
"""Exercise the public Runner lifecycle with the non-executing reference adapter."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from aoa_sdk.contracts.control_plane import canonical_digest
from aoa_sdk.control_plane.runner import (
    AoARunner,
    DeterministicReferenceAdapter,
    ReferenceAdapterUnavailable,
)
from aoa_sdk.models import (
    ApprovalDecision,
    CloseoutBundleRef,
    EvalVerdictRef,
    EvidenceBundleRef,
    MemoryReceiptRef,
    PauseCommand,
    ProvenanceRef,
    RecoverCommand,
    ResumeCommand,
    RunPlan,
    StartCommand,
)


NOW = datetime(2026, 7, 26, 20, 0, tzinfo=timezone.utc)


@dataclass
class MutableClock:
    value: datetime

    def __call__(self) -> datetime:
        return self.value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--chain",
        required=True,
        type=Path,
        help="JSON object containing a typed run_plan field.",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Session-local JSON receipt path.",
    )
    return parser.parse_args()


def digest(value: str) -> str:
    return f"sha256:{hashlib.sha256(value.encode()).hexdigest()}"


def provenance(owner: str, artifact_ref: str) -> ProvenanceRef:
    return ProvenanceRef(
        owner_repo=owner,
        artifact_ref=artifact_ref,
        source_ref="T1-G11-isolated-runtime",
        artifact_digest=digest(f"{owner}:{artifact_ref}"),
        schema_ref="aoa_control_plane_v1",
        schema_version="aoa_control_plane_v1",
    )


def recovery_plan(base_plan: RunPlan) -> RunPlan:
    retry_policy = base_plan.retry_policy.model_copy(
        update={
            "max_attempts": 2,
            "retryable_failure_codes": ("reference_disconnect",),
        }
    )
    candidate = base_plan.model_copy(
        update={
            "retry_policy": retry_policy,
            "plan_digest": digest("pending-recovery-plan"),
        }
    )
    return candidate.model_copy(
        update={
            "plan_digest": canonical_digest(candidate, exclude={"plan_digest"}),
        }
    )


def start_command(
    runner: AoARunner,
    session: Any,
    *,
    at: datetime,
) -> StartCommand:
    return StartCommand(
        command_id="command:T1-isolated:start",
        idempotency_key="idempotency:T1-isolated:start",
        session_id=session.session_id,
        correlation_id=session.correlation_id,
        plan_digest=session.plan_digest,
        expected_revision=runner.status(session).revision,
        issued_at=at,
        issued_by=provenance("T1-isolated-consumer", "commands/start"),
        reason="begin the non-executing isolated lifecycle",
    )


def approval_decision(
    runner: AoARunner,
    session: Any,
    *,
    at: datetime,
) -> ApprovalDecision:
    decided_requirement_ids = {
        item.requirement_id for item in runner.approval_decisions(session)
    }
    request = next(
        item
        for item in runner.approval_requests(session)
        if item.requirement_id not in decided_requirement_ids
    )
    return ApprovalDecision(
        decision_id=f"decision:T1-isolated:{request.requirement_id}",
        request_id=request.request_id,
        requirement_id=request.requirement_id,
        session_id=session.session_id,
        correlation_id=session.correlation_id,
        plan_digest=session.plan_digest,
        snapshot_digest=session.snapshot_digest,
        verdict="approved",
        approval_authority=request.approval_authority,
        decided_by=provenance(
            request.approval_authority.owner_repo,
            f"reviewed-decisions/{request.requirement_id}",
        ),
        decided_at=at,
        reason="bounded T1 reference-adapter lifecycle approval",
    )


def pause_command(
    runner: AoARunner,
    session: Any,
    *,
    at: datetime,
) -> PauseCommand:
    revision = runner.status(session).revision
    return PauseCommand(
        command_id=f"command:T1-isolated:pause:{revision}",
        idempotency_key=f"idempotency:T1-isolated:pause:{revision}",
        session_id=session.session_id,
        correlation_id=session.correlation_id,
        plan_digest=session.plan_digest,
        expected_revision=revision,
        issued_at=at,
        issued_by=provenance("T1-isolated-consumer", "commands/pause"),
        reason="pause the exact isolated lifecycle",
    )


def resume_command(
    runner: AoARunner,
    session: Any,
    *,
    at: datetime,
) -> ResumeCommand:
    status = runner.status(session)
    return ResumeCommand(
        command_id=f"command:T1-isolated:resume:{status.revision}",
        idempotency_key=f"idempotency:T1-isolated:resume:{status.revision}",
        session_id=session.session_id,
        correlation_id=session.correlation_id,
        plan_digest=session.plan_digest,
        expected_revision=status.revision,
        issued_at=at,
        issued_by=provenance("T1-isolated-consumer", "commands/resume"),
        reason="resume from the exact verified event cursor",
        resume_after_sequence=status.last_event_sequence,
    )


def recover_command(
    runner: AoARunner,
    session: Any,
    runtime_owner: str,
    *,
    at: datetime,
) -> RecoverCommand:
    status = runner.status(session)
    if status.recover_from_event_sequence is None:
        raise AssertionError("recoverable failure did not retain an event cursor")
    return RecoverCommand(
        command_id=f"command:T1-isolated:recover:{status.revision}",
        idempotency_key=f"idempotency:T1-isolated:recover:{status.revision}",
        session_id=session.session_id,
        correlation_id=session.correlation_id,
        plan_digest=session.plan_digest,
        expected_revision=status.revision,
        issued_at=at,
        issued_by=provenance("T1-isolated-consumer", "commands/recover"),
        reason="recover to an inspectable paused state",
        recover_after_sequence=status.recover_from_event_sequence,
        recovery_evidence_ref=provenance(
            runtime_owner,
            "reference-runtime/T1-isolated-recovery",
        ),
    )


def terminal_refs(
    plan: RunPlan,
) -> tuple[
    tuple[EvidenceBundleRef, ...],
    tuple[EvalVerdictRef, ...],
    tuple[MemoryReceiptRef, ...],
]:
    evidence = tuple(
        EvidenceBundleRef(
            ref_id=f"evidence-ref:{requirement.requirement_id}",
            provenance=provenance(
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
            provenance=provenance(
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
            provenance=provenance(
                requirement.memory_owner_ref.owner_repo,
                f"reference-memory/{requirement.requirement_id}",
            ),
            satisfies_requirement_ids=(requirement.requirement_id,),
        )
        for requirement in plan.retention_requirements
        if requirement.receipt_required_for_closeout
    )
    return evidence, evals, memory


def closeout_bundle(plan: RunPlan) -> CloseoutBundleRef:
    owners = {
        requirement.owner_ref.owner_repo
        for requirement in plan.closeout_requirements
    }
    if len(owners) != 1:
        raise AssertionError("the isolated plan needs one exact closeout owner")
    owner = next(iter(owners))
    return CloseoutBundleRef(
        ref_id=f"closeout-ref:{plan.plan_id}:T1-isolated",
        provenance=provenance(owner, f"reference-closeout/{plan.plan_id}"),
        satisfies_requirement_ids=tuple(
            requirement.requirement_id
            for requirement in plan.closeout_requirements
        ),
    )


def main() -> int:
    args = parse_args()
    chain_bytes = args.chain.read_bytes()
    chain = json.loads(chain_bytes)
    base_plan = RunPlan.model_validate(chain["run_plan"])
    plan = recovery_plan(base_plan)
    clock = MutableClock(NOW)
    runner = AoARunner(clock=clock, id_factory=lambda: "T1-isolated-primary")
    adapter = DeterministicReferenceAdapter(
        profile=plan.runtime_profile,
        clock=clock,
    )
    session = runner.prepare(plan)

    clock.value = NOW + timedelta(seconds=1)
    start = start_command(runner, session, at=clock.value)
    started = runner.start(session, adapter, start)
    start_event_count = len(runner.events(session))
    duplicate_start = runner.start(session, adapter, start)
    if duplicate_start != started or len(runner.events(session)) != start_event_count:
        raise AssertionError("duplicate start changed the verified lifecycle")

    for offset in range(2, 2 + len(plan.approval_requirements)):
        clock.value = NOW + timedelta(seconds=offset)
        runner.approve(
            session,
            approval_decision(runner, session, at=clock.value),
        )
    if runner.status(session).state != "running":
        raise AssertionError("approved session did not enter running")

    clock.value += timedelta(seconds=1)
    pause = pause_command(runner, session, at=clock.value)
    paused = runner.pause(session, adapter, pause)
    pause_event_count = len(runner.events(session))
    duplicate_pause = runner.pause(session, adapter, pause)
    if duplicate_pause != paused or len(runner.events(session)) != pause_event_count:
        raise AssertionError("duplicate pause changed the verified lifecycle")

    clock.value += timedelta(seconds=1)
    resumed = runner.resume(
        session,
        adapter,
        resume_command(runner, session, at=clock.value),
    )
    if resumed.state != "running":
        raise AssertionError("paused session did not resume")

    clock.value += timedelta(seconds=1)
    adapter.advance(
        session,
        trigger="runtime_interrupted",
        failure_codes=("reference_disconnect",),
        at=clock.value,
    )
    adapter.set_available(False)
    state_before_disconnect_sync = runner.status(session)
    try:
        runner.sync(session, adapter)
    except ReferenceAdapterUnavailable:
        pass
    else:
        raise AssertionError("unavailable adapter did not surface service failure")
    if runner.status(session) != state_before_disconnect_sync:
        raise AssertionError("failed sync changed verified local state")
    adapter.set_available(True)
    if runner.sync(session, adapter).state != "recoverable_failure":
        raise AssertionError("interruption did not reconcile to recoverable failure")

    clock.value += timedelta(seconds=1)
    recovered = runner.recover(
        session,
        adapter,
        recover_command(
            runner,
            session,
            plan.runtime_profile.runtime_owner,
            at=clock.value,
        ),
    )
    if recovered.state != "paused":
        raise AssertionError("recovery did not stop at the inspectable pause")

    clock.value += timedelta(seconds=1)
    if runner.resume(
        session,
        adapter,
        resume_command(runner, session, at=clock.value),
    ).state != "running":
        raise AssertionError("recovered session did not resume")

    for _ in range(64):
        clock.value += timedelta(seconds=1)
        adapter.emit_progress(session, at=clock.value)
    if runner.sync(session, adapter).state != "running":
        raise AssertionError("long lifecycle progress changed running state")

    restored_runner = AoARunner(
        clock=clock,
        id_factory=lambda: "unused-after-restore",
    )
    restored_status = restored_runner.restore(plan, session, adapter)
    if restored_status != runner.status(session):
        raise AssertionError("SessionHandle restore changed the verified status")
    if restored_runner.events(session) != runner.events(session):
        raise AssertionError("SessionHandle restore changed the verified event chain")
    if restored_runner.command_receipts(session) != runner.command_receipts(session):
        raise AssertionError("SessionHandle restore changed command receipts")

    evidence, evals, memory = terminal_refs(plan)
    clock.value += timedelta(seconds=1)
    adapter.advance(
        session,
        trigger="runtime_completed",
        at=clock.value,
        evidence_bundle_refs=evidence,
        eval_verdict_refs=evals,
        memory_receipt_refs=memory,
    )
    if restored_runner.sync(session, adapter).state != "completed":
        raise AssertionError("runtime completion did not reconcile")
    outcome = restored_runner.outcome(session)
    if outcome is None:
        raise AssertionError("completed runtime did not expose a typed outcome")

    clock.value += timedelta(seconds=1)
    closed = restored_runner.closeout(
        session,
        outcome,
        closeout_bundle(plan),
    )
    if closed.state != "closed":
        raise AssertionError("complete isolated lifecycle did not close")

    events = restored_runner.events(session)
    receipts = restored_runner.command_receipts(session)
    receipt = {
        "schema_version": "aoa_sdk_g11_isolated_runtime_trial_v1",
        "terminal_state": closed.state,
        "execution_status": outcome.execution_status,
        "base_plan_id": base_plan.plan_id,
        "base_plan_digest": base_plan.plan_digest,
        "test_plan_digest": plan.plan_digest,
        "test_plan_variation": {
            "field": "retry_policy",
            "max_attempts": plan.retry_policy.max_attempts,
            "retryable_failure_codes": list(
                plan.retry_policy.retryable_failure_codes
            ),
            "compiler_output_claimed": False,
        },
        "session": session.model_dump(mode="json"),
        "final_status": closed.model_dump(mode="json"),
        "outcome": outcome.model_dump(mode="json"),
        "observations": {
            "duplicate_start_no_new_event": True,
            "duplicate_pause_no_new_event": True,
            "pause_resume_completed": True,
            "service_failure_preserved_verified_state": True,
            "interruption_reconciled": True,
            "recovery_stopped_at_pause": True,
            "recovered_session_resumed": True,
            "progress_event_count": 64,
            "session_handle_restore_exact": True,
            "event_count": len(events),
            "command_receipt_count": len(receipts),
            "event_sequences_contiguous": [
                event.sequence for event in events
            ] == list(range(len(events))),
            "reference_adapter_executes_plan_steps": adapter.executes_plan_steps,
        },
        "source": {
            "chain_file_sha256": hashlib.sha256(chain_bytes).hexdigest(),
            "interpreter": sys.executable,
            "interpreter_realpath": str(Path(sys.executable).resolve()),
        },
        "actual_effects": [
            "in_memory_lifecycle_state",
            "non_executing_reference_adapter",
            "session_local_output_write",
        ],
        "claim_limit": (
            "This receipt verifies isolated AoARunner lifecycle semantics with "
            "the deterministic non-executing reference adapter. It does not "
            "execute plan steps, invoke a model or tool, prove production "
            "runtime behavior, create an eval verdict, or establish benefit."
        ),
    }
    args.output.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
