from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from aoa_sdk.contracts.control_plane import (
    ContentRef,
    ControlPlaneContractError,
    ProvenanceRef,
    canonical_digest,
)
from aoa_sdk.contracts.goal_lifecycle import (
    GoalLifecycleContext,
    GoalLifecycleDecision,
    GoalLifecycleExecutionReceipt,
    GoalLifecycleRequest,
    GoalLifecycleTransition,
    assert_goal_lifecycle_execution_scope,
    assert_goal_lifecycle_execution_receipt_scope,
    resolve_goal_lifecycle,
)


NOW = datetime(2026, 8, 25, 12, 0, tzinfo=timezone.utc)
VALID_UNTIL = NOW + timedelta(days=1)


def _digest(label: str) -> str:
    return "sha256:" + label.encode().hex().ljust(64, "0")[:64]


def _provenance(owner: str, artifact: str) -> ProvenanceRef:
    return ProvenanceRef(
        owner_repo=owner,
        artifact_ref=artifact,
        source_ref="goal-lifecycle-contract-test",
        artifact_digest=_digest(f"{owner}:{artifact}"),
        schema_ref="goal-lifecycle-contract-test",
        schema_version="v1",
    )


def _ref(object_id: str, owner: str = "codex-goal") -> ContentRef:
    return ContentRef(
        object_id=object_id,
        owner_repo=owner,
        schema_version="v1",
        digest=_digest(object_id),
    )


def _request(*, desired_state: str = "paused") -> GoalLifecycleRequest:
    evidence = _provenance("aoa-agents", "return/accepted-delegation")
    return GoalLifecycleRequest(
        request_id="goal-transition-request:test",
        correlation_id="goal-transition-correlation:test",
        idempotency_key="goal-transition-idempotency:test",
        goal_ref=_ref("goal:test"),
        observed_state="active",
        expected_state="active",
        desired_state=desired_state,
        transition_kind="delegation_yield",
        reason="responsibility moved to an accepted external holder",
        evidence_refs=(evidence,),
        current_holder_ref=_ref("holder:master"),
        return_owner_ref=_ref("holder:master"),
        requested_by=_provenance("codex-goal", "holder/master"),
        requested_at=NOW,
    )


def _context(request: GoalLifecycleRequest) -> GoalLifecycleContext:
    return GoalLifecycleContext(
        context_id="goal-lifecycle-context:test",
        correlation_id=request.correlation_id,
        goal_ref=request.goal_ref,
        observed_state=request.observed_state,
        dag_ref=_ref("dag:test", "aoa-skills"),
        ownership_ref=_ref("ownership:test", "aoa-agents"),
        current_holder_ref=request.current_holder_ref,
        return_owner_ref=request.return_owner_ref,
        allowed_transitions=(
            GoalLifecycleTransition(
                from_state="active",
                to_state=request.desired_state,
                transition_kind=request.transition_kind,
            ),
        ),
        evidence_refs=request.evidence_refs,
        observed_at=NOW,
        valid_until=VALID_UNTIL,
        observed_by=_provenance("aoa-agents", "context/goal-dag-ownership"),
    )


def test_goal_lifecycle_legitimacy_is_resolved_before_runtime_execution() -> None:
    request = _request()
    decision = resolve_goal_lifecycle(request, _context(request))

    assert decision.status == "accepted"
    assert decision.reason_codes == ("transition_legitimate",)
    assert decision.goal_ref == request.goal_ref
    assert decision.request_ref.digest.startswith("sha256:")
    assert decision.resolver_version == "aoa_goal_lifecycle_legitimacy_v1"


def test_goal_lifecycle_rejects_stale_owner_state_without_transport_choice() -> None:
    request = _request()
    stale_context = _context(request).model_copy(update={"observed_state": "paused"})

    decision = resolve_goal_lifecycle(request, stale_context)

    assert decision.status == "rejected"
    assert "observed_state_mismatch" in decision.reason_codes
    assert "expected_state_mismatch" in decision.reason_codes


def test_goal_lifecycle_rejects_owner_context_older_than_request() -> None:
    request = _request()
    stale_context = _context(request).model_copy(
        update={"observed_at": datetime(2026, 8, 25, 11, 59, tzinfo=timezone.utc)}
    )

    decision = resolve_goal_lifecycle(request, stale_context)

    assert decision.status == "rejected"
    assert decision.reason_codes == ("owner_context_stale_for_request",)


def test_goal_lifecycle_allows_empty_admitted_edges_to_resolve_as_rejection() -> None:
    request = _request()
    context = _context(request).model_copy(update={"allowed_transitions": ()})

    decision = resolve_goal_lifecycle(request, context)

    assert decision.status == "rejected"
    assert "transition_not_admitted_by_goal_dag" in decision.reason_codes


def test_runtime_scope_accepts_only_the_exact_semantic_decision() -> None:
    request = _request()
    decision = resolve_goal_lifecycle(request, _context(request))
    assert_goal_lifecycle_execution_scope(request, decision)

    with pytest.raises(ValueError, match="accepted Goal lifecycle decision"):
        assert_goal_lifecycle_execution_scope(
            request,
            decision.model_copy(update={"status": "rejected"}),
        )


def test_runtime_scope_rejects_an_expired_accepted_decision() -> None:
    request = _request()
    decision = resolve_goal_lifecycle(request, _context(request))

    with pytest.raises(ControlPlaneContractError, match="expired"):
        assert_goal_lifecycle_execution_scope(
            request,
            decision,
            now=VALID_UNTIL + timedelta(seconds=1),
        )


def _execution_receipt(
    request: GoalLifecycleRequest,
    decision: GoalLifecycleDecision,
    *,
    evidence_refs: tuple[ProvenanceRef, ...] | None = None,
) -> GoalLifecycleExecutionReceipt:
    decision_ref = ContentRef(
        object_id=decision.decision_id,
        owner_repo=decision.resolved_by.owner_repo,
        schema_version=decision.schema_version,
        digest=canonical_digest(decision),
    )
    return GoalLifecycleExecutionReceipt(
        execution_id="goal-lifecycle-execution:test",
        correlation_id=request.correlation_id,
        idempotency_key=request.idempotency_key,
        goal_ref=request.goal_ref,
        request_ref=decision.request_ref,
        decision_ref=decision_ref,
        observed_state=request.observed_state,
        desired_state=request.desired_state,
        resulting_state=request.desired_state,
        status="executed",
        evidence_refs=request.evidence_refs if evidence_refs is None else evidence_refs,
        produced_by=_provenance("abyss-stack", "goal-lifecycle-adapter"),
        executed_at=NOW,
        boundaries={"accepted": True, "executed": True},
    )


def test_execution_receipt_is_bound_to_the_exact_request_and_decision() -> None:
    request = _request()
    decision = resolve_goal_lifecycle(request, _context(request))
    receipt = _execution_receipt(request, decision)

    assert_goal_lifecycle_execution_receipt_scope(request, decision, receipt)

    with pytest.raises(ControlPlaneContractError, match="outside request/decision scope"):
        assert_goal_lifecycle_execution_receipt_scope(
            request,
            decision,
            receipt.model_copy(update={"correlation_id": "foreign-correlation"}),
        )


def test_successful_execution_receipt_requires_evidence() -> None:
    request = _request()
    decision = resolve_goal_lifecycle(request, _context(request))

    with pytest.raises(ValueError, match="must carry evidence"):
        _execution_receipt(request, decision, evidence_refs=())
