from __future__ import annotations

from aoa_sdk import AoASDK
from aoa_sdk.a2a.rebase import QuestPassport, RemoteTaskResult, SummonIntent


def test_sdk_exposes_a2a_rebase_bridge(workspace_root) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    passport = QuestPassport(
        difficulty="d1_patch",
        risk="r2_contract",
        control_mode="codex_supervised",
        delegate_tier="executor",
        route_anchor="bounded_plan",
        expected_artifacts=["verification_result"],
    )
    intent = SummonIntent(
        desired_role="reviewer",
        expected_outputs=["verification_result"],
        reviewed_artifact_path="/tmp/reviewed.md",
    )

    request_payload = sdk.a2a.build_summon_request(
        passport,
        intent,
        checkpoint_note_ref="aoa-sdk/.aoa/session-growth/current/example/checkpoint-note.json",
    )
    decision = sdk.a2a.assess_summon(passport, intent)
    target = sdk.a2a.build_codex_local_target("reviewer")
    remote_task = RemoteTaskResult(
        task_id="task-child-1",
        state="failed",
        agent_id="reviewer",
        endpoint="codex://local/reviewer",
        returned_artifacts=["verification_result"],
    )
    return_plan = sdk.a2a.build_return_plan(
        remote_task,
        decision,
        checkpoint_note_ref="aoa-sdk/.aoa/session-growth/current/example/checkpoint-note.json",
    )
    result_payload = sdk.a2a.build_summon_result(
        decision,
        codex_local_target=target,
        return_plan=return_plan,
    )

    assert request_payload["expected_outputs"] == ["verification_result"]
    assert (
        request_payload["summon_request"]["reviewed_artifact_path"]
        == "/tmp/reviewed.md"
    )
    assert decision.lane == "codex_local_reviewed"
    assert target.workspace_root == str(workspace_root.resolve())
    assert result_payload["codex_local_target"]["config_path"].endswith(
        "/.codex/agents/reviewer.toml"
    )
    assert result_payload["return_plan"]["reentry_mode"] == "checkpoint_relaunch"
    assert result_payload["owner_publication_plan"] == []
