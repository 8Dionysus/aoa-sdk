from aoa_sdk.a2a.rebase import (
    QuestPassport,
    RemoteTaskResult,
    SummonIntent,
    assess_summon,
    build_codex_local_target,
    build_memo_export_plan,
    build_reviewed_closeout_request,
    build_return_plan,
    build_runtime_wave_closeout_receipt,
    plan_owner_publications,
)


def test_codex_local_target_uses_project_level_paths() -> None:
    target = build_codex_local_target("coder", workspace_root="/srv")

    assert target.config_path == "/srv/.codex/agents/coder.toml"
    assert target.install_surface == "/srv/.codex/agents"
    assert target.workspace_marker == "/srv/AOA_WORKSPACE_ROOT"
    assert target.mcp_servers == ["aoa_workspace"]
    assert (
        "aoa-agents/generated/codex_agents/projection_manifest.json"
        in target.projection_chain
    )


def test_closeout_request_and_runtime_receipt_keep_canonical_mapping() -> None:
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
    target = build_codex_local_target("reviewer", workspace_root="/srv")
    result = RemoteTaskResult(
        task_id="task-child-1",
        state="failed",
        agent_id="reviewer",
        endpoint="codex://local/reviewer",
        returned_artifacts=["verification_result"],
        artifact_refs=["/srv/artifacts/verification_result.json"],
    )
    return_plan = build_return_plan(
        result,
        decision,
        checkpoint_note_ref="aoa-sdk/.aoa/session-growth/current/example/checkpoint-note.json",
    )
    memo_plan = build_memo_export_plan(
        result,
        reviewed_artifact_path="/srv/notes/reviewed.md",
        return_plan=return_plan,
        checkpoint_note_ref="aoa-sdk/.aoa/session-growth/current/example/checkpoint-note.json",
    )
    publication_plan = plan_owner_publications(
        runtime_receipt_paths=["/srv/receipts/runtime_wave_closeout_receipt.json"],
        memo_receipt_paths=["/srv/receipts/memo_writeback_receipt.json"],
    )
    request = build_reviewed_closeout_request(
        result,
        decision,
        session_ref="session:example",
        reviewed_artifact_path="/srv/notes/reviewed.md",
        publication_plan=publication_plan,
        return_plan=return_plan,
        memo_export_plan=memo_plan,
        codex_target=target,
    )
    receipt = build_runtime_wave_closeout_receipt(
        result,
        decision,
        session_ref="session:example",
        reviewed_artifact_path="/srv/notes/reviewed.md",
        return_plan=return_plan,
        codex_target=target,
    )

    assert request["batches"][0]["publisher"] == "abyss-stack.runtime-wave-closeouts"
    assert receipt["event_kind"] == "runtime_wave_closeout_receipt"
    assert receipt["payload"]["execution_surface"] == "codex_local"
    assert receipt["payload"]["return_reentry_mode"] == "checkpoint_relaunch"
    assert receipt["payload"]["codex_config_path"] == "/srv/.codex/agents/reviewer.toml"
    assert request["memo_export_plan"]["contains_raw_trace"] is False
