from __future__ import annotations

import json

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
        capability_refs=["workflow.operations.delegation"],
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
    checkpoint_plan = sdk.a2a.build_checkpoint_evidence_handoff_plan(
        session_ref="session:example",
        reviewed_artifact_path="/tmp/reviewed.md",
        return_plan=return_plan,
    )
    owner_handoff = sdk.a2a.build_owner_evidence_handoff(
        owner_ref="repo:aoa-playbooks",
        candidate_kind="checkpoint-owner-followthrough",
        reason="owner review is required",
        evidence_refs=["/tmp/reviewed.md"],
        capability_ref="workflow.operations.checkpoint-closeout",
    )
    result_payload = sdk.a2a.build_summon_result(
        decision,
        codex_local_target=target,
        return_plan=return_plan,
        checkpoint_handoff_plan=checkpoint_plan,
        owner_handoffs=[owner_handoff],
    )

    assert request_payload["expected_outputs"] == ["verification_result"]
    assert "secondary_tier" in request_payload["quest_passport"]
    assert "fallback_tier" not in request_payload["quest_passport"]
    assert (
        request_payload["summon_request"]["reviewed_artifact_path"]
        == "/tmp/reviewed.md"
    )
    assert decision.lane == "codex_local_reviewed"
    assert target.workspace_root == str(workspace_root.resolve())
    assert (
        "aoa-agents/generated/codex_agents/projection_manifest.json"
        in target.projection_chain
    )
    assert result_payload["codex_local_target"]["config_path"].endswith(
        "/.codex/agents/reviewer.toml"
    )
    assert result_payload["return_plan"]["reentry_mode"] == "checkpoint_relaunch"
    assert result_payload["return_plan"]["next_hop"] == (
        "workflow.operations.checkpoint-closeout"
    )
    assert result_payload["capability_execution_claimed"] is False
    assert result_payload["owner_handoffs"] == [
        {
            "owner_ref": "repo:aoa-playbooks",
            "candidate_kind": "checkpoint-owner-followthrough",
            "reason": "owner review is required",
            "evidence_refs": ["/tmp/reviewed.md"],
            "capability_ref": "workflow.operations.checkpoint-closeout",
            "review_required": True,
        }
    ]


def test_sdk_prefers_aoa_agents_projection_manifest_for_local_target(
    workspace_root,
) -> None:
    manifest_path = (
        workspace_root
        / "aoa-agents"
        / "generated"
        / "codex_agents"
        / "projection_manifest.json"
    )
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    for entry in payload["generated_agents"]:
        if entry["name"] == "coder":
            entry["sandbox_mode"] = "read-only"
            entry["mcp_affinity"] = ["aoa_workspace", "aoa_stats"]
            entry["nickname_candidates"] = ["Weld", "Join", "Fit"]
            entry["config_path"] = "agents/coder.custom.toml"
            break
    manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    target = sdk.a2a.build_codex_local_target("coder")

    assert target.sandbox_mode == "read-only"
    assert target.mcp_servers == ["aoa_workspace", "aoa_stats"]
    assert target.nickname_candidates == ["Weld", "Join", "Fit"]
    assert target.config_path.endswith("/.codex/agents/coder.custom.toml")
