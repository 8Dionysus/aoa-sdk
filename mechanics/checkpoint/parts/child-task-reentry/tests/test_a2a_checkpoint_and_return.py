from aoa_sdk.a2a.rebase import (
    QuestPassport,
    RemoteTaskResult,
    SummonIntent,
    assess_summon,
    build_checkpoint_evidence_bundle,
    build_checkpoint_evidence_handoff_plan,
    build_summon_request_payload,
    build_return_plan,
    build_transition_decision_payload,
)


def test_self_agent_requires_checkpoint_stack() -> None:
    passport = QuestPassport(
        difficulty="d1_patch",
        risk="r1_repo_local",
        control_mode="codex_supervised",
        delegate_tier="executor",
        route_anchor="bounded_plan",
        expected_artifacts=["work_result"],
        self_agent=True,
    )
    intent = SummonIntent(
        desired_role="coder",
        expected_outputs=["work_result"],
    )

    decision = assess_summon(passport, intent)

    assert decision.allowed is False
    assert decision.checkpoint_required is True
    assert "missing_self_agent_checkpoint" in decision.reason_codes


def test_return_plan_prefers_checkpoint_relaunch_when_checkpoint_exists() -> None:
    passport = QuestPassport(
        difficulty="d1_patch",
        risk="r1_repo_local",
        control_mode="codex_supervised",
        delegate_tier="executor",
        route_anchor="bounded_plan",
        expected_artifacts=["verification_result"],
    )
    intent = SummonIntent(
        desired_role="reviewer", expected_outputs=["verification_result"]
    )
    decision = assess_summon(passport, intent)
    result = RemoteTaskResult(
        task_id="task-child-1",
        state="failed",
        agent_id="reviewer",
        endpoint="codex://local/reviewer",
        returned_artifacts=["verification_result"],
    )

    return_plan = build_return_plan(
        result,
        decision,
        checkpoint_note_ref="aoa-sdk/.aoa/session-growth/current/example/checkpoint-note.json",
        codex_trace_ref="codex:thread:example",
    )
    payload = build_transition_decision_payload(return_plan)

    assert return_plan is not None
    assert return_plan.reentry_mode == "checkpoint_relaunch"
    assert return_plan.anchor_artifact == "bounded_plan"
    assert payload["decision"] == "return"
    assert payload["checkpoint_note_ref"] is not None
    assert payload["next_hop"] == "workflow.operations.checkpoint-closeout"


def test_checkpoint_handoff_preserves_evidence_without_execution_claim() -> None:
    plan = build_checkpoint_evidence_handoff_plan(
        session_ref="session:example",
        reviewed_artifact_path="/srv/notes/reviewed.md",
        checkpoint_note_ref="aoa-sdk/.aoa/session-growth/current/example/checkpoint-note.json",
        codex_trace_ref="codex:thread:example",
        surviving_checkpoint_clusters=["cluster:return"],
    )
    bundle = build_checkpoint_evidence_bundle(plan)

    assert bundle["mode"] == "reviewed-evidence-handoff"
    assert bundle["capability_candidates"] == [
        "workflow.operations.checkpoint-closeout"
    ]
    assert bundle["capability_execution_claimed"] is False
    assert "execution_order" not in bundle


def test_summon_request_override_updates_nested_audit_refs() -> None:
    passport = QuestPassport(
        difficulty="d1_patch",
        risk="r1_repo_local",
        control_mode="codex_supervised",
        delegate_tier="executor",
        route_anchor="bounded_plan",
        expected_artifacts=["verification_result"],
    )
    intent = SummonIntent(
        desired_role="reviewer",
        expected_outputs=["verification_result"],
        audit_refs=["audit:original"],
    )

    payload = build_summon_request_payload(
        passport,
        intent,
        audit_refs=["audit:override"],
    )

    assert payload["audit_refs"] == ["audit:override"]
    assert payload["summon_request"]["audit_refs"] == ["audit:override"]
