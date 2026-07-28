from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from aoa_sdk.contracts.control_plane import (
    ApprovalDecision,
    CandidateExplanation,
    CloseoutBundleRef,
    ContentRef,
    EvalVerdictRef,
    EvidenceBundleRef,
    ExecutionEvent,
    MemoryReceiptRef,
    ProvenanceRef,
    RecoverCommand,
    ResumeCommand,
    RouteDecision,
    RouteExplanation,
    RouteIntent,
    ScenarioBinding,
    StartCommand,
    candidate_explanation_disposition,
    canonical_digest,
    execution_event_digest,
)
from aoa_sdk.contracts.evidence_chain import CheckpointReceiptRef
from aoa_sdk.control_plane.evidence_chain import (
    EvidenceChainError,
    EvidenceChainRepository,
    assemble_evidence_chain,
    assert_evidence_chain_complete,
)
from aoa_sdk.control_plane.planning import (
    compile_run_plan,
    load_plan_compilation_snapshot,
)
from aoa_sdk.control_plane.runner import (
    AoARunner,
    AoARunnerError,
    DeterministicReferenceAdapter,
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
NOW = datetime(2026, 7, 26, 21, 0, tzinfo=timezone.utc)
ZERO_DIGEST = "sha256:" + "0" * 64


@dataclass
class MutableClock:
    value: datetime

    def __call__(self) -> datetime:
        return self.value


def _provenance(owner: str, artifact_ref: str) -> ProvenanceRef:
    return ProvenanceRef(
        owner_repo=owner,
        artifact_ref=artifact_ref,
        source_ref="fixture-source-ref",
        artifact_digest=ZERO_DIGEST,
        schema_ref="schemas/fixture.schema.json",
        schema_version="fixture-v1",
    )


def _route_chain(*, recovery: bool = False):
    payload = json.loads(INPUTS_PATH.read_text(encoding="utf-8"))
    base_decision = RouteDecision.model_validate(payload["decision"])
    binding = ScenarioBinding.model_validate(payload["scenario_binding"])
    intent = RouteIntent(
        intent_id=base_decision.intent_ref.object_id,
        correlation_id=base_decision.correlation_id,
        objective="Complete one bounded change through an owner-safe evidence chain",
        requested_by=binding.agent_refs[0],
        scenario=binding.scenario,
        requested_capability_kinds=(
            base_decision.candidates[0].capability.capability_kind,
        ),
        context_refs=binding.input_refs,
        authored_at=NOW,
        provenance=_provenance(
            base_decision.intent_ref.owner_repo,
            "intents/bounded-change.json",
        ),
    )
    decision = base_decision.model_copy(
        update={
            "intent_ref": ContentRef(
                object_id=intent.intent_id,
                owner_repo=intent.provenance.owner_repo,
                schema_version=intent.schema_version,
                digest=canonical_digest(intent),
            )
        }
    )
    decision_ref = ContentRef(
        object_id=decision.decision_id,
        owner_repo=decision.provenance.owner_repo,
        schema_version=decision.schema_version,
        digest=canonical_digest(decision),
    )
    explanation = RouteExplanation(
        explanation_id=f"explanation:{decision.decision_id}",
        correlation_id=decision.correlation_id,
        decision_ref=decision_ref,
        decision_status=decision.status,
        candidate_explanations=tuple(
            CandidateExplanation(
                candidate_id=item.candidate_id,
                disposition=candidate_explanation_disposition(
                    item,
                    selected_candidate_id=decision.selected_candidate_id,
                ),
                reason_codes=item.reason_codes,
                evidence_refs=item.evidence_refs,
            )
            for item in decision.candidates
        ),
        selected_candidate_id=decision.selected_candidate_id,
        ambiguity_codes=tuple(
            item for item in decision.reason_codes if item.startswith("ambiguous_")
        ),
        provenance=_provenance(
            "aoa-sdk",
            "route-explanations/bounded-change.json",
        ),
    )
    binding = binding.model_copy(update={"decision_ref": decision_ref})
    plan = compile_run_plan(
        decision,
        binding,
        reference_runtime_profile(),
        load_plan_compilation_snapshot(),
    )
    if recovery:
        updated = plan.model_copy(
            update={
                "retry_policy": plan.retry_policy.model_copy(
                    update={
                        "max_attempts": 2,
                        "retryable_failure_codes": ("fixture-runtime-interruption",),
                    }
                ),
                "plan_digest": ZERO_DIGEST,
            }
        )
        plan = updated.model_copy(
            update={
                "plan_digest": canonical_digest(
                    updated,
                    exclude={"plan_digest"},
                )
            }
        )
    return intent, decision, explanation, plan


def _owner_refs(plan):
    eval_refs = tuple(
        EvalVerdictRef(
            ref_id=f"eval-verdict:{item.requirement_id}",
            provenance=_provenance(
                item.eval_owner_ref.owner_repo,
                f"verdicts/{item.requirement_id}.json",
            ),
            satisfies_requirement_ids=(item.requirement_id,),
        )
        for item in plan.eval_requirements
    )
    memory_refs = tuple(
        MemoryReceiptRef(
            ref_id=f"memory-receipt:{item.requirement_id}",
            provenance=_provenance(
                item.memory_owner_ref.owner_repo,
                f"receipts/{item.requirement_id}.json",
            ),
            satisfies_requirement_ids=(item.requirement_id,),
        )
        for item in plan.retention_requirements
    )
    checkpoint_refs = (
        CheckpointReceiptRef(
            ref_id="checkpoint-receipt:bounded-change",
            provenance=_provenance(
                plan.checkpoint_policy.owner.owner_repo,
                "checkpoints/bounded-change-reviewed.json",
            ),
            review_status="reviewed",
            covered_step_ids=plan.checkpoint_policy.required_after_step_ids,
        ),
    )
    owners = {item.owner_ref.owner_repo for item in plan.closeout_requirements}
    assert len(owners) == 1
    closeout_ref = CloseoutBundleRef(
        ref_id="closeout-receipt:bounded-change",
        provenance=_provenance(
            next(iter(owners)),
            "closeout/bounded-change.json",
        ),
        satisfies_requirement_ids=tuple(
            item.requirement_id for item in plan.closeout_requirements
        ),
    )
    return eval_refs, memory_refs, checkpoint_refs, closeout_ref


def _terminal_run(*, recovery: bool = False):
    intent, decision, explanation, plan = _route_chain(recovery=recovery)
    clock = MutableClock(NOW)
    runner = AoARunner(clock=clock, id_factory=lambda: "evidence-chain")
    adapter = DeterministicReferenceAdapter(clock=clock)
    session = runner.prepare(plan)
    start = StartCommand(
        command_id="command:start",
        idempotency_key="idempotency:start",
        session_id=session.session_id,
        correlation_id=session.correlation_id,
        plan_digest=session.plan_digest,
        expected_revision=0,
        issued_at=NOW + timedelta(seconds=1),
        issued_by=_provenance("fixture-caller", "commands/start.json"),
        reason="start the unified evidence-chain proof",
    )
    assert runner.start(session, adapter, start).state == "awaiting_approval"
    request = runner.approval_requests(session)[0]
    decision_record = ApprovalDecision(
        decision_id="approval-decision:bounded-change",
        request_id=request.request_id,
        requirement_id=request.requirement_id,
        session_id=session.session_id,
        correlation_id=session.correlation_id,
        plan_digest=session.plan_digest,
        snapshot_digest=session.snapshot_digest,
        verdict="approved",
        approval_authority=request.approval_authority,
        decided_by=_provenance("fixture-operator", "operators/reviewer.json"),
        decided_at=NOW + timedelta(seconds=2),
        reason="approve the deterministic reference execution",
    )
    assert runner.approve(session, decision_record).state == "running"
    evidence_refs = tuple(
        EvidenceBundleRef(
            ref_id=f"runtime-evidence:{item.requirement_id}",
            provenance=_provenance(
                item.producer_owner,
                f"runtime-evidence/{item.requirement_id}.json",
            ),
            satisfies_requirement_ids=(item.requirement_id,),
        )
        for item in plan.evidence_requirements
        if item.terminal_required
    )
    completed_at = NOW + timedelta(seconds=3)
    if recovery:
        adapter.advance(
            session,
            trigger="runtime_interrupted",
            at=NOW + timedelta(seconds=3),
            failure_codes=("fixture-runtime-interruption",),
        )
        assert runner.sync(session, adapter).state == "recoverable_failure"
        interrupted = runner.status(session)
        assert interrupted.recover_from_event_sequence is not None
        recover = RecoverCommand(
            command_id="command:recover",
            idempotency_key="idempotency:recover",
            session_id=session.session_id,
            correlation_id=session.correlation_id,
            plan_digest=session.plan_digest,
            expected_revision=interrupted.revision,
            issued_at=NOW + timedelta(seconds=4),
            issued_by=_provenance("fixture-caller", "commands/recover.json"),
            reason="recover the evidence-chain fixture",
            recover_after_sequence=interrupted.recover_from_event_sequence,
            recovery_evidence_ref=_provenance(
                plan.runtime_profile.runtime_owner,
                "runtime/recovery-evidence.json",
            ),
        )
        assert runner.recover(session, adapter, recover).state == "paused"
        paused = runner.status(session)
        resume = ResumeCommand(
            command_id="command:resume",
            idempotency_key="idempotency:resume",
            session_id=session.session_id,
            correlation_id=session.correlation_id,
            plan_digest=session.plan_digest,
            expected_revision=paused.revision,
            issued_at=NOW + timedelta(seconds=5),
            issued_by=_provenance("fixture-caller", "commands/resume.json"),
            reason="resume the recovered evidence-chain fixture",
            resume_after_sequence=paused.last_event_sequence,
        )
        assert runner.resume(session, adapter, resume).state == "running"
        completed_at = NOW + timedelta(seconds=6)
    adapter.advance(
        session,
        trigger="runtime_completed",
        at=completed_at,
        evidence_bundle_refs=evidence_refs,
    )
    assert runner.sync(session, adapter).state == "completed"
    outcome = runner.outcome(session)
    assert outcome is not None
    clock.value = completed_at + timedelta(seconds=3)
    return (
        intent,
        decision,
        explanation,
        plan,
        runner,
        adapter,
        session,
        outcome,
    )


def _assemble_complete(terminal, *, assembled_at: datetime):
    (
        intent,
        decision,
        explanation,
        plan,
        runner,
        _adapter,
        session,
        outcome,
    ) = terminal
    eval_refs, memory_refs, checkpoint_refs, closeout_ref = _owner_refs(plan)
    return assemble_evidence_chain(
        intent=intent,
        decision=decision,
        explanation=explanation,
        plan=plan,
        session=session,
        events=runner.events(session),
        runtime_outcome=outcome,
        eval_verdict_refs=eval_refs,
        memory_receipt_refs=memory_refs,
        checkpoint_receipt_refs=checkpoint_refs,
        closeout_bundle_ref=closeout_ref,
        assembled_at=assembled_at,
        assembled_by=_provenance(
            "aoa-sdk",
            "src/aoa_sdk/control_plane/evidence_chain.py",
        ),
    )


def test_c5_contracts_remain_available_through_public_models() -> None:
    from aoa_sdk.models import (
        CheckpointReceiptRef as PublicCheckpointReceiptRef,
        EvidenceChain as PublicEvidenceChain,
        EvidenceChainIndex as PublicEvidenceChainIndex,
        EvidenceChainIndexEntry as PublicEvidenceChainIndexEntry,
    )

    from aoa_sdk.contracts.evidence_chain import (
        EvidenceChain,
        EvidenceChainIndex,
        EvidenceChainIndexEntry,
    )

    assert PublicCheckpointReceiptRef is CheckpointReceiptRef
    assert PublicEvidenceChain is EvidenceChain
    assert PublicEvidenceChainIndex is EvidenceChainIndex
    assert PublicEvidenceChainIndexEntry is EvidenceChainIndexEntry


def test_partial_chain_advances_to_complete_and_resolves_by_both_ids(
    tmp_path: Path,
) -> None:
    terminal = _terminal_run()
    (
        intent,
        decision,
        explanation,
        plan,
        runner,
        _adapter,
        session,
        outcome,
    ) = terminal
    partial = assemble_evidence_chain(
        intent=intent,
        decision=decision,
        explanation=explanation,
        plan=plan,
        session=session,
        events=runner.events(session),
        runtime_outcome=outcome,
        assembled_at=NOW + timedelta(seconds=4),
        assembled_by=_provenance(
            "aoa-sdk",
            "src/aoa_sdk/control_plane/evidence_chain.py",
        ),
    )
    assert partial.disposition == "partial"
    assert any(item.startswith("eval:") for item in partial.missing_required_refs)
    assert any(item.startswith("checkpoint:") for item in partial.missing_required_refs)
    with pytest.raises(EvidenceChainError, match="partial"):
        assert_evidence_chain_complete(partial)

    repository = EvidenceChainRepository(tmp_path / "chain-store")
    assert repository.record(partial).revision == 1
    assert repository.resolve_session(session) == partial

    complete = _assemble_complete(
        terminal,
        assembled_at=NOW + timedelta(seconds=5),
    )
    assert complete.disposition == "complete"
    assert complete.missing_required_refs == ()
    assert repository.record(complete).revision == 2
    assert repository.resolve_session(session) == complete
    assert complete.closeout_bundle_ref is not None
    assert repository.resolve_closeout(complete.closeout_bundle_ref) == complete
    assert len(list((tmp_path / "chain-store" / "objects").iterdir())) == 2


def test_runner_closes_only_with_the_complete_external_owner_chain() -> None:
    terminal = _terminal_run()
    (
        _intent,
        _decision,
        _explanation,
        _plan,
        runner,
        _adapter,
        session,
        outcome,
    ) = terminal
    complete = _assemble_complete(
        terminal,
        assembled_at=NOW + timedelta(seconds=5),
    )

    status = runner.closeout(session, outcome, complete)
    assert status.state == "closed"
    assert status.closeout_ref == complete.closeout_bundle_ref
    assert runner.closeout(session, outcome, complete) == status


def test_chain_allows_only_command_ack_after_exact_runtime_outcome() -> None:
    terminal = _terminal_run()
    complete = _assemble_complete(
        terminal,
        assembled_at=NOW + timedelta(seconds=5),
    )
    prior = complete.events[-1]
    acknowledgement = ExecutionEvent(
        event_id=f"{prior.event_id}:command-ack",
        event_stream_id=prior.event_stream_id,
        session_id=prior.session_id,
        correlation_id=prior.correlation_id,
        sequence=prior.sequence + 1,
        previous_event_digest=prior.event_digest,
        event_digest=ZERO_DIGEST,
        event_kind="command_ack",
        emitted_at=prior.emitted_at,
        emitted_by=prior.emitted_by,
        command_id="command:terminal-dispatch",
        idempotency_key="idempotency:terminal-dispatch",
    )
    acknowledgement = acknowledgement.model_copy(
        update={"event_digest": execution_event_digest(acknowledgement)}
    )
    with_ack = assemble_evidence_chain(
        intent=complete.intent,
        decision=complete.decision,
        explanation=complete.explanation,
        plan=complete.plan,
        session=complete.session,
        events=(*complete.events, acknowledgement),
        runtime_outcome=complete.runtime_outcome,
        eval_verdict_refs=complete.eval_verdict_refs,
        memory_receipt_refs=complete.memory_receipt_refs,
        checkpoint_receipt_refs=complete.checkpoint_receipt_refs,
        closeout_bundle_ref=complete.closeout_bundle_ref,
        assembled_at=complete.assembled_at,
        assembled_by=complete.assembled_by,
    )
    assert assert_evidence_chain_complete(with_ack) == complete.closeout_bundle_ref

    post_outcome_transition = acknowledgement.model_copy(
        update={
            "event_id": f"{prior.event_id}:transition",
            "event_digest": ZERO_DIGEST,
            "event_kind": "state_transition",
            "state_before": "completed",
            "state_after": "closed",
            "trigger": "closeout",
            "command_id": None,
            "idempotency_key": None,
        }
    )
    post_outcome_transition = post_outcome_transition.model_copy(
        update={"event_digest": execution_event_digest(post_outcome_transition)}
    )
    with pytest.raises(EvidenceChainError, match="only command acknowledgement"):
        assemble_evidence_chain(
            intent=complete.intent,
            decision=complete.decision,
            explanation=complete.explanation,
            plan=complete.plan,
            session=complete.session,
            events=(*complete.events, post_outcome_transition),
            runtime_outcome=complete.runtime_outcome,
            eval_verdict_refs=complete.eval_verdict_refs,
            memory_receipt_refs=complete.memory_receipt_refs,
            checkpoint_receipt_refs=complete.checkpoint_receipt_refs,
            closeout_bundle_ref=complete.closeout_bundle_ref,
            assembled_at=complete.assembled_at,
            assembled_by=complete.assembled_by,
        )


def test_chain_rejects_runtime_synthesized_eval_and_wrong_eval_owner() -> None:
    terminal = _terminal_run()
    (
        intent,
        decision,
        explanation,
        plan,
        runner,
        _adapter,
        session,
        outcome,
    ) = terminal
    eval_refs, memory_refs, checkpoint_refs, closeout_ref = _owner_refs(plan)
    synthesized = outcome.model_copy(update={"eval_verdict_refs": eval_refs})
    with pytest.raises(EvidenceChainError, match="must not synthesize"):
        assemble_evidence_chain(
            intent=intent,
            decision=decision,
            explanation=explanation,
            plan=plan,
            session=session,
            events=runner.events(session),
            runtime_outcome=synthesized,
            assembled_at=NOW + timedelta(seconds=5),
            assembled_by=_provenance(
                "aoa-sdk",
                "src/aoa_sdk/control_plane/evidence_chain.py",
            ),
        )

    wrong_owner = eval_refs[0].model_copy(
        update={
            "provenance": eval_refs[0].provenance.model_copy(
                update={"owner_repo": "abyss-stack"}
            )
        }
    )
    with pytest.raises(EvidenceChainError, match="owner differs"):
        assemble_evidence_chain(
            intent=intent,
            decision=decision,
            explanation=explanation,
            plan=plan,
            session=session,
            events=runner.events(session),
            runtime_outcome=outcome,
            eval_verdict_refs=(wrong_owner, *eval_refs[1:]),
            memory_receipt_refs=memory_refs,
            checkpoint_receipt_refs=checkpoint_refs,
            closeout_bundle_ref=closeout_ref,
            assembled_at=NOW + timedelta(seconds=5),
            assembled_by=_provenance(
                "aoa-sdk",
                "src/aoa_sdk/control_plane/evidence_chain.py",
            ),
        )


def test_runner_rejects_partial_chain_without_dispatching_closeout() -> None:
    terminal = _terminal_run()
    (
        intent,
        decision,
        explanation,
        plan,
        runner,
        _adapter,
        session,
        outcome,
    ) = terminal
    partial = assemble_evidence_chain(
        intent=intent,
        decision=decision,
        explanation=explanation,
        plan=plan,
        session=session,
        events=runner.events(session),
        runtime_outcome=outcome,
        assembled_at=NOW + timedelta(seconds=4),
        assembled_by=_provenance(
            "aoa-sdk",
            "src/aoa_sdk/control_plane/evidence_chain.py",
        ),
    )

    with pytest.raises(AoARunnerError, match="partial"):
        runner.closeout(session, outcome, partial)
    assert runner.status(session).state == "completed"


def test_chain_rejects_premature_closeout_and_wrong_checkpoint_owner() -> None:
    terminal = _terminal_run()
    (
        intent,
        decision,
        explanation,
        plan,
        runner,
        _adapter,
        session,
        outcome,
    ) = terminal
    _eval_refs, _memory_refs, checkpoint_refs, closeout_ref = _owner_refs(plan)
    with pytest.raises(EvidenceChainError, match="cannot precede"):
        assemble_evidence_chain(
            intent=intent,
            decision=decision,
            explanation=explanation,
            plan=plan,
            session=session,
            events=runner.events(session),
            runtime_outcome=outcome,
            closeout_bundle_ref=closeout_ref,
            assembled_at=NOW + timedelta(seconds=5),
            assembled_by=_provenance(
                "aoa-sdk",
                "src/aoa_sdk/control_plane/evidence_chain.py",
            ),
        )

    wrong_checkpoint = checkpoint_refs[0].model_copy(
        update={
            "provenance": checkpoint_refs[0].provenance.model_copy(
                update={"owner_repo": "aoa-sdk"}
            )
        }
    )
    with pytest.raises(EvidenceChainError, match="checkpoint receipt owner"):
        assemble_evidence_chain(
            intent=intent,
            decision=decision,
            explanation=explanation,
            plan=plan,
            session=session,
            events=runner.events(session),
            runtime_outcome=outcome,
            checkpoint_receipt_refs=(wrong_checkpoint,),
            assembled_at=NOW + timedelta(seconds=5),
            assembled_by=_provenance(
                "aoa-sdk",
                "src/aoa_sdk/control_plane/evidence_chain.py",
            ),
        )


def test_repository_rejects_tampered_object_and_complete_replacement(
    tmp_path: Path,
) -> None:
    terminal = _terminal_run()
    complete = _assemble_complete(
        terminal,
        assembled_at=NOW + timedelta(seconds=5),
    )
    repository = EvidenceChainRepository(tmp_path / "chain-store")
    entry = repository.record(complete)
    replacement = complete.model_copy(
        update={
            "assembled_at": complete.assembled_at + timedelta(seconds=1),
            "chain_digest": ZERO_DIGEST,
        }
    )
    replacement = replacement.model_copy(
        update={
            "chain_digest": canonical_digest(
                replacement,
                exclude={"chain_digest"},
            )
        }
    )
    with pytest.raises(EvidenceChainError, match="complete.*immutable"):
        repository.record(replacement)

    object_path = tmp_path / "chain-store" / entry.object_ref
    payload = json.loads(object_path.read_text(encoding="utf-8"))
    payload["correlation_id"] = "correlation:tampered"
    object_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(EvidenceChainError, match="unavailable or invalid"):
        repository.resolve_session(complete.session)


def test_recovery_chain_requires_explicit_pause_and_failure_checkpoints() -> None:
    terminal = _terminal_run(recovery=True)
    (
        intent,
        decision,
        explanation,
        plan,
        runner,
        _adapter,
        session,
        outcome,
    ) = terminal
    eval_refs, memory_refs, checkpoint_refs, closeout_ref = _owner_refs(plan)
    partial = assemble_evidence_chain(
        intent=intent,
        decision=decision,
        explanation=explanation,
        plan=plan,
        session=session,
        events=runner.events(session),
        runtime_outcome=outcome,
        eval_verdict_refs=eval_refs,
        memory_receipt_refs=memory_refs,
        checkpoint_receipt_refs=checkpoint_refs,
        assembled_at=NOW + timedelta(seconds=10),
        assembled_by=_provenance(
            "aoa-sdk",
            "src/aoa_sdk/control_plane/evidence_chain.py",
        ),
    )
    assert "checkpoint:pause" in partial.missing_required_refs
    assert "checkpoint:recoverable-failure" in partial.missing_required_refs

    reviewed_recovery = checkpoint_refs[0].model_copy(
        update={
            "covers_pause": True,
            "covers_recoverable_failure": True,
        }
    )
    complete = assemble_evidence_chain(
        intent=intent,
        decision=decision,
        explanation=explanation,
        plan=plan,
        session=session,
        events=runner.events(session),
        runtime_outcome=outcome,
        eval_verdict_refs=eval_refs,
        memory_receipt_refs=memory_refs,
        checkpoint_receipt_refs=(reviewed_recovery,),
        closeout_bundle_ref=closeout_ref,
        assembled_at=NOW + timedelta(seconds=11),
        assembled_by=_provenance(
            "aoa-sdk",
            "src/aoa_sdk/control_plane/evidence_chain.py",
        ),
    )
    assert complete.disposition == "complete"
