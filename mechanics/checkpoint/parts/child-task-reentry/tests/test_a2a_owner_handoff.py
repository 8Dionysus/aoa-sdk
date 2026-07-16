from __future__ import annotations

import pytest

from aoa_sdk.a2a.api import A2AAPI
from aoa_sdk.a2a.rebase import (
    QuestPassport,
    RemoteTaskResult,
    SummonIntent,
    assess_summon,
    build_codex_local_target,
    build_owner_evidence_handoff,
    build_reviewed_return_handoff,
    build_return_plan,
    build_runtime_return_closeout_receipt,
)


def _return_context():
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
        capability_refs=["workflow.operations.delegation"],
        expected_outputs=["verification_result"],
    )
    decision = assess_summon(passport, intent)
    remote_task = RemoteTaskResult(
        task_id="task-child-1",
        state="failed",
        agent_id="reviewer",
        endpoint="codex://local/reviewer",
        returned_artifacts=["verification_result"],
        artifact_refs=["/srv/artifacts/verification_result.json"],
    )
    return_plan = build_return_plan(
        remote_task,
        decision,
        checkpoint_note_ref="aoa-sdk/.aoa/session-growth/current/example/checkpoint-note.json",
    )
    return decision, remote_task, return_plan


def test_reviewed_return_builds_owner_candidates_without_publication() -> None:
    decision, remote_task, return_plan = _return_context()
    target = build_codex_local_target("reviewer", workspace_root="/srv/AbyssOS")
    handoff = build_owner_evidence_handoff(
        owner_ref="repo:aoa-playbooks",
        candidate_kind="checkpoint-owner-followthrough",
        reason="the owner decides whether to execute its workflow",
        evidence_refs=["/srv/notes/reviewed.md", "/srv/notes/reviewed.md"],
        capability_ref="workflow.operations.checkpoint-closeout",
    )
    reviewed = build_reviewed_return_handoff(
        remote_task,
        decision,
        session_ref="session:example",
        reviewed_artifact_path="/srv/notes/reviewed.md",
        owner_handoffs=[handoff],
        return_plan=return_plan,
        codex_target=target,
    )
    receipt = build_runtime_return_closeout_receipt(
        remote_task,
        decision,
        session_ref="session:example",
        reviewed_artifact_path="/srv/notes/reviewed.md",
        return_plan=return_plan,
        codex_target=target,
        observed_at="2026-07-15T00:00:00Z",
    )

    assert reviewed["request_kind"] == "a2a_return_evidence_handoff"
    assert reviewed["capability_execution_claimed"] is False
    assert reviewed["owner_handoffs"][0]["evidence_refs"] == [
        "/srv/notes/reviewed.md"
    ]
    assert "batches" not in reviewed
    assert "owner_publication_plan" not in reviewed
    assert receipt["payload"]["capability_execution_claimed"] is False
    assert receipt["payload"]["return_reentry_mode"] == "checkpoint_relaunch"


def test_owner_handoff_requires_explicit_owner_evidence() -> None:
    with pytest.raises(ValueError, match="at least one evidence ref"):
        build_owner_evidence_handoff(
            owner_ref="repo:aoa-playbooks",
            candidate_kind="checkpoint-owner-followthrough",
            reason="owner review is required",
            evidence_refs=[],
        )


def test_retired_runtime_wave_alias_is_absent() -> None:
    assert not hasattr(A2AAPI, "build_runtime_wave_closeout_receipt")
