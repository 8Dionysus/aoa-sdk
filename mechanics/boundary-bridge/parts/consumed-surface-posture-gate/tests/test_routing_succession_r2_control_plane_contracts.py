from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from aoa_sdk.contracts.control_plane import (
    ALLOWED_LIFECYCLE_TRANSITIONS,
    ABIRef,
    AgentRef,
    ApprovalDecision,
    ApprovalRequest,
    ApprovalRequirement,
    CancelCommand,
    CandidateExplanation,
    CapabilityRef,
    CheckpointPolicy,
    CloseoutBundleRef,
    CloseoutRequirement,
    ContentRef,
    ControlPlaneContractError,
    EvalRequirement,
    EvalVerdictRef,
    EvidenceBundleRef,
    EvidenceRequirement,
    ExecutionEvent,
    MemoryReceiptRef,
    PlanSnapshot,
    PlanStep,
    ProvenanceRef,
    RecoverCommand,
    ResolvedAgentProfile,
    RetentionRequirement,
    RetryPolicy,
    RollbackPolicy,
    RouteCandidate,
    RouteDecision,
    RouteExplanation,
    RouteIntent,
    RunOutcome,
    RunPlan,
    RunStatus,
    RuntimeProfile,
    ScenarioBinding,
    ScenarioRef,
    SessionHandle,
    StartCommand,
    assert_approvals_satisfied,
    assert_closeout_ready,
    assert_execution_event_chain,
    assert_explanation_matches_decision,
    assert_idempotent_replay,
    assert_plan_snapshot_digest,
    assert_run_plan_digest,
    assert_snapshot_current,
    assert_transition_allowed,
    canonical_digest,
    execution_event_digest,
)


NOW = datetime(2026, 7, 23, 18, 0, tzinfo=timezone.utc)
PART_ROOT = Path(__file__).resolve().parents[1]
DESIGN_PATH = PART_ROOT / "docs" / "routing-succession-r2-agent-os-contracts.md"
EVIDENCE_PATH = (
    PART_ROOT / "evidence" / "routing-succession-r2-agent-os-contracts.json"
)


def _digest(value: str) -> str:
    return f"sha256:{hashlib.sha256(value.encode()).hexdigest()}"


def _provenance(
    owner: str,
    artifact: str,
    *,
    source_ref: str = "0123456789abcdef",
) -> ProvenanceRef:
    return ProvenanceRef(
        owner_repo=owner,
        artifact_ref=artifact,
        source_ref=source_ref,
        artifact_digest=_digest(f"{owner}:{artifact}:{source_ref}"),
        schema_ref=f"{owner}:schemas/{artifact}.schema.json",
        schema_version=f"{artifact}_v1",
    )


def _content(object_id: str) -> ContentRef:
    return ContentRef(
        object_id=object_id,
        owner_repo="aoa-sdk",
        schema_version="aoa_control_plane_v1",
        digest=_digest(object_id),
    )


def _agent() -> AgentRef:
    return AgentRef(
        agent_id="agent:codex-primary",
        provenance=_provenance("aoa-agents", "generated/agent_catalog.json"),
    )


def _capability(name: str = "bounded-repo-change") -> CapabilityRef:
    return CapabilityRef(
        capability_id=f"capability:{name}",
        capability_kind="workflow",
        provenance=_provenance(
            "aoa-skills",
            "generated/capability_graph.json",
        ),
    )


def _scenario(name: str = "bounded-repo-change") -> ScenarioRef:
    return ScenarioRef(
        scenario_id=f"scenario:{name}",
        provenance=_provenance(
            "aoa-playbooks",
            "generated/playbook_activation_surfaces.min.json",
        ),
    )


def _approval_requirement(step_id: str = "mutate") -> ApprovalRequirement:
    return ApprovalRequirement(
        requirement_id=f"approval:{step_id}",
        approval_owner=_provenance(
            "abyss-stack",
            "Configs/agent-api/governed-execution-policy.yaml",
        ),
        operation=step_id,
        risk_class="repo_mutation",
        applies_to_step_ids=(step_id,),
        expires_after_seconds=3600,
    )


def _run_plan(case: str = "bounded") -> RunPlan:
    agent = _agent()
    capability = _capability(case)
    scenario = _scenario(case)
    binding = ScenarioBinding(
        binding_id=f"binding:{case}",
        correlation_id=f"correlation:{case}",
        scenario=scenario,
        decision_ref=_content(f"decision:{case}"),
        agent_refs=(agent,),
        capability_refs=(capability,),
        input_refs=(scenario.provenance, capability.provenance),
        expected_artifact_kinds=("runtime_result", "validation_receipt"),
        provenance=_provenance("aoa-sdk", f"bindings/{case}.json"),
    )
    runtime = RuntimeProfile(
        profile_id="runtime:abyss-stack-governed",
        runtime_owner="abyss-stack",
        adapter_id="abyss-stack-governed-v1",
        supported_plan_schema_versions=("aoa_control_plane_v1",),
        supported_event_schema_versions=("aoa_control_plane_v1",),
        supported_effect_classes=(
            "read_only",
            "repo_mutation",
            "runtime_mutation",
            "external",
        ),
        constraint_refs=(
            _provenance(
                "abyss-stack",
                "Configs/agent-api/governed-execution-policy.yaml",
            ),
        ),
        provenance=_provenance(
            "abyss-stack",
            "mechanics/governed-execution/parts/governed-runner",
        ),
    )
    routing_abi = ABIRef(
        abi_id="aoa-routing",
        abi_version="aoa_routing_thin_router_v1",
        owner_repo="aoa-routing",
        schema_ref="aoa-routing:schemas/router.schema.json",
        source_ref="7e2fe467ad26aa645b61849001a456dda4562ffc",
        artifact_digest=_digest("aoa-routing-abi"),
    )
    snapshot = PlanSnapshot(
        snapshot_id=f"snapshot:{case}",
        source_refs=(
            agent.provenance,
            capability.provenance,
            scenario.provenance,
            runtime.provenance,
        ),
        abi_refs=(routing_abi,),
        snapshot_digest=_digest("placeholder"),
    )
    snapshot = snapshot.model_copy(
        update={
            "snapshot_digest": canonical_digest(
                snapshot,
                exclude={"snapshot_digest"},
            )
        }
    )
    approval = _approval_requirement("mutate")
    if case == "multi-agent":
        steps = (
            PlanStep(
                step_id="summon",
                operation_kind="summon",
                effect_class="external",
                agent_refs=(agent,),
                capability_refs=(capability,),
                expected_output_kinds=("child_session_handle",),
            ),
            PlanStep(
                step_id="return",
                operation_kind="return",
                effect_class="read_only",
                depends_on=("summon",),
                agent_refs=(agent,),
                expected_output_kinds=("bounded_return_packet",),
            ),
            PlanStep(
                step_id="validate",
                operation_kind="validate",
                effect_class="read_only",
                depends_on=("return",),
                expected_output_kinds=("validation_receipt",),
            ),
            PlanStep(
                step_id="closeout",
                operation_kind="closeout",
                effect_class="read_only",
                depends_on=("validate",),
                expected_output_kinds=("closeout_bundle",),
            ),
        )
        approvals: tuple[ApprovalRequirement, ...] = ()
    else:
        steps = (
            PlanStep(
                step_id="inspect",
                operation_kind="inspect",
                effect_class="read_only",
                agent_refs=(agent,),
                capability_refs=(capability,),
                input_refs=(scenario.provenance,),
                expected_output_kinds=("inspection_packet",),
            ),
            PlanStep(
                step_id="mutate",
                operation_kind="mutate",
                effect_class="repo_mutation",
                depends_on=("inspect",),
                agent_refs=(agent,),
                capability_refs=(capability,),
                approval_requirement_ids=(approval.requirement_id,),
                expected_output_kinds=("change_artifact",),
            ),
            PlanStep(
                step_id="validate",
                operation_kind="validate",
                effect_class="read_only",
                depends_on=("mutate",),
                expected_output_kinds=("validation_receipt",),
            ),
            PlanStep(
                step_id="checkpoint",
                operation_kind="checkpoint",
                effect_class="read_only",
                depends_on=("validate",),
                expected_output_kinds=("checkpoint_receipt",),
            ),
            PlanStep(
                step_id="evaluate",
                operation_kind="evaluate",
                effect_class="external",
                depends_on=("validate",),
                expected_output_kinds=("eval_verdict_ref",),
            ),
            PlanStep(
                step_id="retain",
                operation_kind="retain",
                effect_class="external",
                depends_on=("checkpoint",),
                expected_output_kinds=("memory_receipt_ref",),
            ),
            PlanStep(
                step_id="closeout",
                operation_kind="closeout",
                effect_class="read_only",
                depends_on=("evaluate", "retain"),
                expected_output_kinds=("closeout_bundle",),
            ),
        )
        approvals = (approval,)

    plan = RunPlan(
        plan_id=f"plan:{case}",
        correlation_id=f"correlation:{case}",
        decision_ref=_content(f"decision:{case}"),
        scenario_binding=binding,
        runtime_profile=runtime,
        snapshot=snapshot,
        steps=steps,
        approval_requirements=approvals,
        checkpoint_policy=CheckpointPolicy(
            owner=_provenance("aoa-sdk", "checkpoint-policy-v1"),
            required_after_step_ids=(
                ("validate",) if case == "multi-agent" else ("validate", "checkpoint")
            ),
        ),
        retry_policy=RetryPolicy(
            max_attempts=3 if case == "degradation" else 1,
            retryable_failure_codes=(
                ("runtime_disconnect", "event_transport_unavailable")
                if case == "degradation"
                else ()
            ),
        ),
        rollback_policy=RollbackPolicy(
            required=case != "multi-agent",
            owner=_provenance("abyss-stack", "governed-rollback-policy"),
            trigger_codes=("post_change_validation_failure",),
            rollback_artifact_ref=(
                _provenance("abyss-stack", "rollback.status.json")
                if case != "multi-agent"
                else None
            ),
        ),
        evidence_requirements=(
            EvidenceRequirement(
                requirement_id="evidence:runtime",
                artifact_kind="runtime_result",
                producer_owner="abyss-stack",
                terminal_required=True,
            ),
            EvidenceRequirement(
                requirement_id="evidence:validation",
                artifact_kind="validation_receipt",
                producer_owner="abyss-stack",
                required_after_step_id="validate",
                terminal_required=True,
            ),
        ),
        eval_requirements=(
            EvalRequirement(
                requirement_id="eval:bounded-result",
                eval_owner_ref=_provenance("aoa-evals", "generated/eval_catalog.min.json"),
                eval_contract_ref=_provenance("aoa-evals", "evals/bounded-result"),
                required_evidence_ids=("evidence:runtime", "evidence:validation"),
            ),
        ),
        retention_requirements=(
            RetentionRequirement(
                requirement_id="retention:reviewed-closeout",
                memory_owner_ref=_provenance("aoa-memo", "generated/memory"),
                retention_contract_ref=_provenance(
                    "aoa-memo",
                    "mechanics/writeback/retention-contract",
                ),
            ),
        ),
        closeout_requirements=(
            CloseoutRequirement(
                requirement_id="closeout:evidence-chain",
                owner_ref=_provenance("aoa-sdk", "closeout-contract-v1"),
                required_ref_kinds=(
                    "runtime_result",
                    "validation_receipt",
                    "eval_verdict",
                    "memory_receipt",
                ),
            ),
        ),
        plan_digest=_digest("placeholder"),
        provenance=_provenance("aoa-sdk", f"plans/{case}.json"),
    )
    return plan.model_copy(
        update={"plan_digest": canonical_digest(plan, exclude={"plan_digest"})}
    )


def _session(plan: RunPlan) -> SessionHandle:
    return SessionHandle(
        session_id=f"session:{plan.plan_id}",
        correlation_id=plan.correlation_id,
        plan_ref=_content(plan.plan_id),
        plan_digest=plan.plan_digest,
        snapshot_digest=plan.snapshot.snapshot_digest,
        event_stream_id=f"stream:{plan.plan_id}",
        prepared_at=NOW,
        prepared_by=_provenance("aoa-sdk", "runner/session-handle"),
    )


def _approval(plan: RunPlan, session: SessionHandle) -> ApprovalDecision:
    requirement = plan.approval_requirements[0]
    return ApprovalDecision(
        decision_id="approval-decision:1",
        request_id="approval-request:1",
        requirement_id=requirement.requirement_id,
        session_id=session.session_id,
        correlation_id=session.correlation_id,
        plan_digest=plan.plan_digest,
        snapshot_digest=plan.snapshot.snapshot_digest,
        verdict="approved",
        approval_authority=requirement.approval_owner,
        decided_by=_provenance("operator", "identities/operator-1.json"),
        decided_at=NOW,
        reason="operator accepted the exact pinned plan",
    )


def _event(
    session: SessionHandle,
    *,
    event_id: str,
    sequence: int,
    previous_event_digest: str | None,
    state_before: str,
    state_after: str,
    trigger: str,
) -> ExecutionEvent:
    event = ExecutionEvent(
        event_id=event_id,
        event_stream_id=session.event_stream_id,
        session_id=session.session_id,
        correlation_id=session.correlation_id,
        sequence=sequence,
        previous_event_digest=previous_event_digest,
        event_digest=_digest("placeholder"),
        event_kind="state_transition",
        emitted_at=NOW + timedelta(seconds=sequence),
        emitted_by=_provenance("abyss-stack", "Logs/governed-runs/event-stream.jsonl"),
        state_before=state_before,
        state_after=state_after,
        trigger=trigger,
    )
    return event.model_copy(update={"event_digest": execution_event_digest(event)})


def test_core_contracts_round_trip_as_strict_json() -> None:
    plan = _run_plan()
    session = _session(plan)
    intent = RouteIntent(
        intent_id="intent:bounded",
        correlation_id=plan.correlation_id,
        objective="Make one bounded repository change and prove it",
        requested_by=_agent(),
        scenario=_scenario(),
        requested_capability_kinds=("workflow",),
        context_refs=(_scenario().provenance,),
        authored_at=NOW,
    )
    candidate = RouteCandidate(
        candidate_id="candidate:bounded",
        capability=_capability(),
        agent=_agent(),
        scenario=_scenario(),
        rank=0,
        compatibility="compatible",
        policy_posture="approval_required",
        reason_codes=("exact-capability-match",),
        evidence_refs=(_capability().provenance,),
    )
    decision = RouteDecision(
        decision_id="decision:bounded",
        correlation_id=plan.correlation_id,
        intent_ref=_content(intent.intent_id),
        status="resolved",
        candidates=(candidate,),
        selected_candidate_id=candidate.candidate_id,
        approval_requirements=plan.approval_requirements,
        resolver_version="aoa-route-resolver-v1",
        reason_codes=("single-compatible-candidate",),
        input_snapshot_digest=plan.snapshot.snapshot_digest,
        provenance=_provenance("aoa-sdk", "route-decisions/decision-bounded.json"),
    )
    explanation = RouteExplanation(
        explanation_id="explanation:bounded",
        correlation_id=plan.correlation_id,
        decision_ref=_content(decision.decision_id),
        decision_status=decision.status,
        candidate_explanations=(
            CandidateExplanation(
                candidate_id=candidate.candidate_id,
                disposition="selected",
                reason_codes=("single-compatible-candidate",),
                evidence_refs=candidate.evidence_refs,
            ),
        ),
        selected_candidate_id=candidate.candidate_id,
        provenance=_provenance("aoa-sdk", "route-explanations/explanation-bounded.json"),
    )
    profile = ResolvedAgentProfile(
        profile_id="resolved-agent:bounded",
        agent=_agent(),
        capability_refs=(_capability(),),
        constraint_refs=(_scenario().provenance,),
        projection_provenance=_provenance(
            "aoa-sdk",
            "resolved-agents/bounded.json",
        ),
    )
    approval_request = ApprovalRequest(
        request_id="approval-request:1",
        requirement_id=plan.approval_requirements[0].requirement_id,
        approval_authority=plan.approval_requirements[0].approval_owner,
        session_id=session.session_id,
        correlation_id=session.correlation_id,
        plan_digest=plan.plan_digest,
        snapshot_digest=plan.snapshot.snapshot_digest,
        requested_at=NOW,
        expires_at=NOW + timedelta(hours=1),
        request_provenance=_provenance(
            "aoa-sdk",
            "approval-requests/approval-request-1.json",
        ),
    )

    for model in (
        profile,
        intent,
        decision,
        explanation,
        plan,
        session,
        approval_request,
        _approval(plan, session),
    ):
        restored = type(model).model_validate_json(model.model_dump_json())
        assert restored == model
    assert_run_plan_digest(plan)
    assert_plan_snapshot_digest(plan.snapshot)
    assert_explanation_matches_decision(decision, explanation)

    with pytest.raises(ControlPlaneContractError, match="does not account"):
        assert_explanation_matches_decision(
            decision.model_copy(
                update={
                    "candidates": (
                        *decision.candidates,
                        candidate.model_copy(update={"candidate_id": "candidate:other"}),
                    )
                }
            ),
            explanation,
        )

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        RunPlan.model_validate({**plan.model_dump(mode="json"), "runtime_command": "rm -rf"})
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        PlanStep.model_validate(
            {
                **plan.steps[0].model_dump(mode="json"),
                "tool_args": ["hidden-runtime-instruction"],
            }
        )
    forbidden_candidate = candidate.model_copy(
        update={"policy_posture": "forbidden"}
    )
    with pytest.raises(ValidationError, match="forbidden candidate"):
        RouteDecision.model_validate(
            {
                **decision.model_dump(mode="python"),
                "candidates": (forbidden_candidate,),
            }
        )
    with pytest.raises(ValidationError, match="does not support the run plan schema"):
        RunPlan.model_validate(
            {
                **plan.model_dump(mode="python"),
                "runtime_profile": plan.runtime_profile.model_copy(
                    update={"supported_plan_schema_versions": ("future-plan-v2",)}
                ),
            }
        )


def test_all_three_golden_scenarios_use_one_contract_family() -> None:
    bounded = _run_plan("bounded")
    multi_agent = _run_plan("multi-agent")
    degradation = _run_plan("degradation")

    for plan in (bounded, multi_agent, degradation):
        assert RunPlan.model_validate_json(plan.model_dump_json()) == plan
        assert_run_plan_digest(plan)
        assert plan.runtime_profile.runtime_owner == "abyss-stack"
        assert plan.runtime_profile.adapter_protocol_version == "aoa_runtime_adapter_v1"

    assert {step.operation_kind for step in bounded.steps} >= {
        "mutate",
        "evaluate",
        "checkpoint",
        "retain",
        "closeout",
    }
    assert {step.operation_kind for step in multi_agent.steps} >= {
        "summon",
        "return",
        "validate",
        "closeout",
    }
    assert degradation.retry_policy.max_attempts == 3
    assert degradation.checkpoint_policy.required_on_recoverable_failure
    assert degradation.rollback_policy.required


def test_lifecycle_graph_is_closed_and_has_no_implicit_shortcuts() -> None:
    states = {
        "prepared",
        "awaiting_approval",
        "running",
        "paused",
        "recoverable_failure",
        "failed",
        "completed",
        "cancelled",
        "closed",
    }
    covered = {
        state
        for before, _trigger, after in ALLOWED_LIFECYCLE_TRANSITIONS
        for state in (before, after)
    }
    assert covered == states
    assert all(
        state == "closed"
        or any(before == state for before, _trigger, _after in ALLOWED_LIFECYCLE_TRANSITIONS)
        for state in states
    )
    assert ("prepared", "closeout", "closed") not in ALLOWED_LIFECYCLE_TRANSITIONS
    assert (
        "recoverable_failure",
        "recover",
        "running",
    ) not in ALLOWED_LIFECYCLE_TRANSITIONS

    assert_transition_allowed("running", "recoverable_failure", "runtime_interrupted")
    assert_transition_allowed("recoverable_failure", "paused", "recover")
    with pytest.raises(ControlPlaneContractError, match="invalid lifecycle transition"):
        assert_transition_allowed("recoverable_failure", "running", "resume")

    with pytest.raises(ValidationError, match="closed status must name"):
        RunStatus(
            session_id="session:1",
            correlation_id="correlation:1",
            state="closed",
            revision=2,
            updated_at=NOW,
            observed_by=_provenance("aoa-sdk", "runner/status/session-1.json"),
        )


def test_snapshot_and_approval_guards_fail_closed_on_drift_or_bypass() -> None:
    plan = _run_plan()
    session = _session(plan)
    observed_sources = {
        (source.owner_repo, source.artifact_ref): source.artifact_digest
        for source in plan.snapshot.source_refs
    }
    observed_abis = {
        (abi.owner_repo, abi.abi_id): (abi.abi_version, abi.artifact_digest)
        for abi in plan.snapshot.abi_refs
    }
    assert_snapshot_current(
        plan.snapshot,
        observed_sources=observed_sources,
        observed_abis=observed_abis,
    )
    with pytest.raises(ControlPlaneContractError, match="stale or spoofed"):
        assert_snapshot_current(
            plan.snapshot,
            observed_sources={
                **observed_sources,
                next(iter(observed_sources)): _digest("spoofed"),
            },
            observed_abis=observed_abis,
        )
    abi_key = next(iter(observed_abis))
    with pytest.raises(ControlPlaneContractError, match="stale or incompatible ABI"):
        assert_snapshot_current(
            plan.snapshot,
            observed_sources=observed_sources,
            observed_abis={**observed_abis, abi_key: ("aoa_routing_thin_router_v2", _digest("v2"))},
        )

    with pytest.raises(ControlPlaneContractError, match="missing approved decision"):
        assert_approvals_satisfied(plan, (), session=session, at=NOW)
    approval = _approval(plan, session)
    assert_approvals_satisfied(plan, (approval,), session=session, at=NOW)
    with pytest.raises(ControlPlaneContractError, match="approval scope mismatch"):
        assert_approvals_satisfied(
            plan,
            (approval.model_copy(update={"plan_digest": _digest("other-plan")}),),
            session=session,
            at=NOW,
        )
    with pytest.raises(ControlPlaneContractError, match="approval owner mismatch"):
        assert_approvals_satisfied(
            plan,
            (
                approval.model_copy(
                    update={
                        "approval_authority": _provenance(
                            "aoa-sdk",
                            "forged-approval-owner",
                        )
                    }
                ),
            ),
            session=session,
            at=NOW,
        )
    with pytest.raises(ControlPlaneContractError, match="approval expired"):
        assert_approvals_satisfied(
            plan,
            (approval,),
            session=session,
            at=NOW + timedelta(hours=2),
        )


def test_command_replay_is_idempotent_only_for_identical_payload() -> None:
    plan = _run_plan()
    session = _session(plan)
    command = StartCommand(
        command_id="command:start:1",
        idempotency_key="idempotency:start:1",
        session_id=session.session_id,
        correlation_id=session.correlation_id,
        plan_digest=plan.plan_digest,
        expected_revision=0,
        issued_at=NOW,
        issued_by=_agent().provenance,
        reason="start the exact approved plan",
    )
    assert_idempotent_replay(command, command.model_copy())
    with pytest.raises(ControlPlaneContractError, match="different command payload"):
        assert_idempotent_replay(
            command,
            command.model_copy(update={"reason": "reuse key for another effect"}),
        )
    with pytest.raises(ControlPlaneContractError, match="same replay scope"):
        assert_idempotent_replay(
            command,
            command.model_copy(update={"idempotency_key": "another-key"}),
        )

    for command_model in (
        CancelCommand(
            **{
                **command.model_dump(exclude={"command_kind"}),
                "command_kind": "cancel",
                "rollback_requested": True,
            }
        ),
        RecoverCommand(
            **{
                **command.model_dump(exclude={"command_kind"}),
                "command_kind": "recover",
                "recover_after_sequence": 4,
                "recovery_evidence_ref": _provenance(
                    "abyss-stack",
                    "Logs/governed-runs/recovery.json",
                ),
            }
        ),
    ):
        assert type(command_model).model_validate_json(command_model.model_dump_json()) == command_model


def test_event_chain_rejects_gap_reorder_substitution_and_invalid_transition() -> None:
    plan = _run_plan()
    session = _session(plan)
    started = _event(
        session,
        event_id="event:0",
        sequence=0,
        previous_event_digest=None,
        state_before="prepared",
        state_after="running",
        trigger="start",
    )
    paused = _event(
        session,
        event_id="event:1",
        sequence=1,
        previous_event_digest=started.event_digest,
        state_before="running",
        state_after="paused",
        trigger="pause",
    )
    assert_execution_event_chain((started, paused), session=session)
    assert_execution_event_chain((started, started, paused), session=session)

    with pytest.raises(ControlPlaneContractError, match="gap or reorder"):
        assert_execution_event_chain((paused, started), session=session)
    wrong_link = paused.model_copy(
        update={"previous_event_digest": _digest("wrong")}
    )
    wrong_link = wrong_link.model_copy(
        update={"event_digest": execution_event_digest(wrong_link)}
    )
    with pytest.raises(ControlPlaneContractError, match="does not link"):
        assert_execution_event_chain(
            (
                started,
                wrong_link,
            ),
            session=session,
        )
    substituted = started.model_copy(
        update={
            "emitted_at": NOW + timedelta(minutes=1),
        }
    )
    substituted = substituted.model_copy(
        update={"event_digest": execution_event_digest(substituted)}
    )
    with pytest.raises(ControlPlaneContractError, match="different content"):
        assert_execution_event_chain((started, substituted), session=session)
    with pytest.raises(ControlPlaneContractError, match="event digest mismatch"):
        assert_execution_event_chain(
            (
                started.model_copy(update={"event_digest": _digest("tampered")}),
            ),
            session=session,
        )
    with pytest.raises(ValidationError, match="invalid lifecycle transition"):
        ExecutionEvent(
            **{
                **started.model_dump(mode="python"),
                "event_id": "event:invalid",
                "state_before": "prepared",
                "state_after": "completed",
                "trigger": "runtime_completed",
            }
        )


def test_runtime_success_is_not_an_eval_or_memory_verdict() -> None:
    plan = _run_plan()
    session = _session(plan)
    outcome = RunOutcome(
        outcome_id="outcome:1",
        session_id=session.session_id,
        correlation_id=session.correlation_id,
        plan_digest=plan.plan_digest,
        execution_status="succeeded",
        terminal_state="completed",
        completed_at=NOW,
        runtime_result_ref=_provenance(
            "abyss-stack",
            "Logs/governed-runs/result.summary.json",
        ),
        evidence_bundle_refs=(
            EvidenceBundleRef(
                ref_id="evidence:runtime:1",
                provenance=_provenance(
                    "abyss-stack",
                    "Logs/governed-runs/evidence-bundle.json",
                ),
            ),
        ),
    )
    assert outcome.eval_verdict_refs == ()
    assert outcome.memory_receipt_refs == ()
    assert outcome.closeout_bundle_ref is None

    closeout = CloseoutBundleRef(
        ref_id="closeout:1",
        provenance=_provenance("aoa-sdk", "closeout/closeout-1.json"),
        satisfies_requirement_ids=("closeout:evidence-chain",),
    )
    with pytest.raises(ControlPlaneContractError, match="missing terminal evidence"):
        assert_closeout_ready(plan, session, outcome, closeout)

    complete_outcome = outcome.model_copy(
        update={
            "evidence_bundle_refs": (
                EvidenceBundleRef(
                    ref_id="evidence:complete:1",
                    provenance=_provenance(
                        "abyss-stack",
                        "Logs/governed-runs/evidence-complete.json",
                    ),
                    satisfies_requirement_ids=(
                        "evidence:runtime",
                        "evidence:validation",
                    ),
                ),
            ),
            "eval_verdict_refs": (
                EvalVerdictRef(
                    ref_id="eval:verdict:1",
                    provenance=_provenance(
                        "aoa-evals",
                        "verdicts/bounded-result.json",
                    ),
                    satisfies_requirement_ids=("eval:bounded-result",),
                ),
            ),
            "memory_receipt_refs": (
                MemoryReceiptRef(
                    ref_id="memory:receipt:complete",
                    provenance=_provenance(
                        "aoa-memo",
                        "receipts/reviewed-closeout.json",
                    ),
                    satisfies_requirement_ids=("retention:reviewed-closeout",),
                ),
            ),
            "closeout_bundle_ref": closeout,
        }
    )
    assert_closeout_ready(plan, session, complete_outcome, closeout)
    forged_eval = complete_outcome.eval_verdict_refs[0].model_copy(
        update={
            "provenance": _provenance(
                "aoa-sdk",
                "forged/eval-verdict.json",
            )
        }
    )
    with pytest.raises(ControlPlaneContractError, match="missing eval verdict"):
        assert_closeout_ready(
            plan,
            session,
            complete_outcome.model_copy(
                update={"eval_verdict_refs": (forged_eval,)}
            ),
            closeout,
        )

    closed = RunStatus(
        session_id=session.session_id,
        correlation_id=session.correlation_id,
        state="closed",
        revision=8,
        last_event_sequence=7,
        closeout_ref=closeout,
        updated_at=NOW,
        observed_by=_provenance("aoa-sdk", "runner/status/session-1.json"),
    )
    assert closed.closeout_ref == closeout

    memory_receipt = MemoryReceiptRef(
        ref_id="memory:receipt:1",
        provenance=_provenance("aoa-memo", "receipts/memory-1.json"),
    )
    assert memory_receipt.provenance.owner_repo == "aoa-memo"


def test_r2_machine_design_matches_typed_contract_and_stop_lines() -> None:
    evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    design = DESIGN_PATH.read_text(encoding="utf-8")

    assert evidence["scope"] == {
        "stage": "R2 Agent OS SDK contracts and lifecycle design",
        "current_canonical_routing_producer": "aoa-routing",
        "producer_migration_authorized": False,
        "runtime_execution_authorized": False,
        "behavioral_facades_active": False,
        "next_authorized_stage": "R3 disposable migration rehearsal after G2 validation",
    }
    assert evidence["contract_versions"] == {
        "control_plane": "aoa_control_plane_v1",
        "lifecycle": "aoa_run_lifecycle_v1",
        "runtime_adapter": "aoa_runtime_adapter_v1",
        "routing_abi_during_owner_succession": "aoa_routing_thin_router_v1",
    }
    assert {
        tuple(transition)
        for transition in evidence["lifecycle"]["transitions"]
    } == ALLOWED_LIFECYCLE_TRANSITIONS
    assert len(evidence["golden_scenarios"]) == 3
    assert all(
        not scenario["hidden_instructions_required"]
        for scenario in evidence["golden_scenarios"]
    )
    assert evidence["owner_boundaries"]["sdk_executes_models_or_tools"] is False
    assert evidence["owner_boundaries"]["runtime_success_is_eval_verdict"] is False
    assert evidence["run_plan_contract"]["runtime_commands_allowed_in_plan"] is False
    assert evidence["closeout_guard"] == {
        "exact_session_correlation_and_plan_scope": True,
        "terminal_evidence_requirement_ids_must_be_satisfied": True,
        "required_eval_verdict_ids_must_be_satisfied": True,
        "required_memory_receipt_ids_must_be_satisfied": True,
        "closeout_bundle_requirement_ids_must_be_satisfied": True,
        "requirement_owner_must_match_ref_provenance": True,
        "runtime_success_creates_missing_owner_refs": False,
    }
    assert evidence["gate_g2"]["does_not_authorize"][-1] == (
        "aoa-routing retirement or archive"
    )

    for marker in (
        "`aoa-routing` remains canonical",
        "`ControlPlaneProtocol`",
        "`AoARunnerProtocol`",
        "`RuntimeAdapterProtocol`",
        "There is no `recoverable_failure -> running` shortcut.",
        "G2 authorizes R3 disposable migration rehearsal only.",
    ):
        assert marker in design
