from __future__ import annotations

from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from aoa_sdk import AoASDK
from aoa_sdk.a2a.rebase import QuestPassport, RemoteTaskResult, SummonIntent


LIVE_WORKSPACE_ROOT = Path(__file__).resolve().parents[1]


def test_sdk_a2a_bridge_validates_against_live_aoa_summon_contract() -> None:
    sdk = _live_sdk_or_skip()
    request_schema = sdk.a2a.summon_request_schema()
    result_schema = sdk.a2a.summon_result_schema()

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
        reviewed_artifact_path="/srv/notes/reviewed.md",
    )
    request_payload = sdk.a2a.build_summon_request(
        passport,
        intent,
        checkpoint_note_ref="aoa-sdk/.aoa/session-growth/current/example/checkpoint-note.json",
        codex_trace_ref="aoa-sdk/.aoa/skill-runtime-sessions/example-trace.json",
    )
    decision = sdk.a2a.assess_summon(passport, intent)
    target = sdk.a2a.build_codex_local_target("reviewer", workspace_root="/srv")
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
        owner_publication_plan=[],
    )

    assert sdk.a2a.summon_request_schema_path().name == "summon-request-v3.schema.json"
    assert sdk.a2a.summon_result_schema_path().name == "summon-result-v3.schema.json"
    assert sdk.a2a.summon_request_schema_path().exists()
    assert sdk.a2a.summon_result_schema_path().exists()

    request_errors = sorted(
        Draft202012Validator(request_schema).iter_errors(request_payload),
        key=lambda error: list(error.absolute_path),
    )
    result_errors = sorted(
        Draft202012Validator(result_schema).iter_errors(result_payload),
        key=lambda error: list(error.absolute_path),
    )

    assert request_errors == []
    assert result_errors == []
    assert result_payload["lane"] == "codex_local_reviewed"
    assert result_payload["return_plan"]["reentry_mode"] == "checkpoint_relaunch"
    assert (
        "aoa-agents/generated/codex_agents/projection_manifest.json"
        in target.projection_chain
    )


def _live_sdk_or_skip() -> AoASDK:
    if not LIVE_WORKSPACE_ROOT.exists():
        pytest.skip("live aoa-sdk workspace checkout is unavailable")

    sdk = AoASDK.from_workspace(LIVE_WORKSPACE_ROOT)
    if not sdk.workspace.has_repo("aoa-skills"):
        pytest.skip("live aoa-skills checkout is unavailable")

    if not sdk.a2a.summon_request_schema_path().exists():
        pytest.skip("live aoa-summon request schema is unavailable")
    if not sdk.a2a.summon_result_schema_path().exists():
        pytest.skip("live aoa-summon result schema is unavailable")

    return sdk
