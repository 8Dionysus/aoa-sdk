from __future__ import annotations

from pathlib import Path

from jsonschema import Draft202012Validator

from aoa_sdk import AoASDK
from aoa_sdk.a2a.rebase import QuestPassport, RemoteTaskResult, SummonIntent


def find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "pyproject.toml").is_file() and (
            candidate / "src" / "aoa_sdk"
        ).is_dir():
            return candidate
    raise RuntimeError(f"could not find aoa-sdk repo root from {start}")


REPO_ROOT = find_repo_root(Path(__file__).resolve())
SCHEMA_ROOT = (
    REPO_ROOT / "mechanics" / "checkpoint" / "parts" / "child-task-reentry" / "schemas"
)


def test_sdk_owned_child_task_schemas_validate_bounded_packets(monkeypatch) -> None:
    monkeypatch.setenv("AOA_SDK_REPO_PATH_AOA_SDK", str(REPO_ROOT))
    sdk = AoASDK.from_workspace(REPO_ROOT)
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
        capability_refs=["workflow.operations.delegation"],
        expected_outputs=["verification_result"],
        reviewed_artifact_path="/srv/notes/reviewed.md",
    )
    request_payload = sdk.a2a.build_summon_request(
        passport,
        intent,
        checkpoint_note_ref="aoa-sdk/.aoa/session-growth/current/example/checkpoint-note.json",
        codex_trace_ref="codex:thread:example",
    )
    decision = sdk.a2a.assess_summon(passport, intent)
    result = RemoteTaskResult(
        task_id="task-child-1",
        state="failed",
        agent_id="reviewer",
        endpoint="codex://local/reviewer",
        returned_artifacts=["verification_result"],
    )
    return_plan = sdk.a2a.build_return_plan(
        result,
        decision,
        checkpoint_note_ref="aoa-sdk/.aoa/session-growth/current/example/checkpoint-note.json",
    )
    checkpoint_plan = sdk.a2a.build_checkpoint_evidence_handoff_plan(
        session_ref="session:example",
        reviewed_artifact_path="/srv/notes/reviewed.md",
        return_plan=return_plan,
    )
    owner_handoff = sdk.a2a.build_owner_evidence_handoff(
        owner_ref="repo:aoa-playbooks",
        candidate_kind="checkpoint-owner-followthrough",
        reason="the owner decides whether to execute the checkpoint workflow",
        evidence_refs=["/srv/notes/reviewed.md"],
        capability_ref="workflow.operations.checkpoint-closeout",
    )
    result_payload = sdk.a2a.build_summon_result(
        decision,
        return_plan=return_plan,
        checkpoint_handoff_plan=checkpoint_plan,
        owner_handoffs=[owner_handoff],
    )

    assert sdk.a2a.summon_request_schema_path() == (
        SCHEMA_ROOT / "summon-request-v4.schema.json"
    )
    assert sdk.a2a.summon_result_schema_path() == (
        SCHEMA_ROOT / "summon-result-v4.schema.json"
    )
    assert list(Draft202012Validator(request_schema).iter_errors(request_payload)) == []
    assert list(Draft202012Validator(result_schema).iter_errors(result_payload)) == []
    assert request_payload["summon_request"]["capability_refs"] == [
        "workflow.operations.delegation"
    ]
    assert result_payload["capability_execution_claimed"] is False
    assert result_payload["owner_handoffs"][0]["review_required"] is True


def test_result_schema_rejects_an_execution_claim() -> None:
    schema = AoASDK.from_workspace(REPO_ROOT).a2a._load_schema(
        SCHEMA_ROOT / "summon-result-v4.schema.json"
    )
    payload = {
        "allowed": True,
        "lane": "codex_local_leaf",
        "execution_surface": "codex_local",
        "cohort_pattern": "solo",
        "closeout_required": True,
        "capability_execution_claimed": True,
        "checkpoint_handoff_plan": None,
        "owner_handoffs": [],
    }

    errors = list(Draft202012Validator(schema).iter_errors(payload))

    assert any(error.validator == "const" for error in errors)
