from __future__ import annotations

from .checkpoint import build_checkpoint_bridge_plan, build_checkpoint_context_bundle
from .closeout import (
    build_reviewed_closeout_request,
    build_runtime_wave_closeout_receipt,
    plan_owner_publications,
)
from .codex import build_codex_local_target
from .contracts import build_summon_request_payload, build_summon_result_payload
from .memo import build_memo_export_plan
from .models import QuestPassport, RemoteTaskResult, SummonIntent
from .passports import assess_summon
from .returning import build_return_plan, build_transition_decision_payload
from .utils import to_jsonable


FIXTURE_ID = "wave5-a2a-summon-return-checkpoint-e2e"
SESSION_REF = "session:wave5-a2a-return-checkpoint-e2e"
CHECKPOINT_NOTE_REF = (
    "aoa-sdk/.aoa/session-growth/current/"
    "wave5-a2a-return-checkpoint/checkpoint-note.json"
)
CODEX_TRACE_REF = (
    "aoa-sdk/.aoa/skill-runtime-sessions/"
    "wave5-a2a-return-checkpoint/codex-trace.json"
)
REVIEWED_ARTIFACT_PATH = "/srv/notes/wave5-a2a-reviewed-child-return.md"
OBSERVED_AT = "2026-04-14T00:00:00.000Z"


def build_summon_return_checkpoint_fixture(
    *,
    observed_at: str = OBSERVED_AT,
) -> dict:
    passport = QuestPassport(
        difficulty="d2_slice",
        risk="r2_contract",
        control_mode="codex_supervised",
        delegate_tier="executor",
        route_anchor="AOA-P-0031:a2a-summon-return-checkpoint",
        expected_artifacts=["verification_result", "bounded_plan"],
    )
    intent = SummonIntent(
        desired_role="reviewer",
        skill_refs=["aoa-summon", "aoa-checkpoint-closeout-bridge"],
        expected_outputs=["verification_result", "bounded_plan"],
        parent_task_id="parent:wave5-a2a-return-checkpoint",
        session_ref=SESSION_REF,
        reviewed_artifact_path=REVIEWED_ARTIFACT_PATH,
        audit_refs=[
            "repo:aoa-playbooks/playbooks/a2a-summon-return-checkpoint/PLAYBOOK.md",
            "repo:aoa-evals/examples/artifact_to_verdict_hook.a2a-summon-return-checkpoint.example.json",
        ],
        playbook_ref="AOA-P-0031",
    )
    summon_request = build_summon_request_payload(
        passport,
        intent,
        checkpoint_note_ref=CHECKPOINT_NOTE_REF,
        codex_trace_ref=CODEX_TRACE_REF,
        reviewed_artifact_path=REVIEWED_ARTIFACT_PATH,
    )
    decision = assess_summon(passport, intent)
    codex_target = build_codex_local_target("reviewer", workspace_root="/srv/AbyssOS")
    remote_task = RemoteTaskResult(
        task_id="task-wave5-a2a-return-child",
        state="failed",
        agent_id="reviewer",
        endpoint="codex://local/reviewer",
        returned_artifacts=["verification_result", "bounded_plan", "transition_decision"],
        context_id="ctx-wave5-a2a-return-checkpoint",
        parent_task_id="parent:wave5-a2a-return-checkpoint",
        artifact_refs=[
            "/srv/artifacts/wave5-a2a/verification_result.json",
            "/srv/artifacts/wave5-a2a/bounded_plan.md",
        ],
    )
    return_plan = build_return_plan(
        remote_task,
        decision,
        checkpoint_note_ref=CHECKPOINT_NOTE_REF,
        codex_trace_ref=CODEX_TRACE_REF,
    )
    if return_plan is None:  # pragma: no cover - fixture state is intentionally terminal
        raise ValueError("expected fixture child task to require a return plan")

    checkpoint_bridge_plan = build_checkpoint_bridge_plan(
        session_ref=SESSION_REF,
        reviewed_artifact_path=REVIEWED_ARTIFACT_PATH,
        checkpoint_note_ref=CHECKPOINT_NOTE_REF,
        codex_trace_ref=CODEX_TRACE_REF,
        surviving_checkpoint_clusters=[
            "cluster:return-anchor",
            "cluster:child-result-review",
        ],
        return_plan=return_plan,
    )
    memo_export_plan = build_memo_export_plan(
        remote_task,
        reviewed_artifact_path=REVIEWED_ARTIFACT_PATH,
        return_plan=return_plan,
        checkpoint_note_ref=CHECKPOINT_NOTE_REF,
    )
    publication_plan = plan_owner_publications(
        runtime_receipt_paths=[
            "/srv/receipts/wave5-a2a/runtime_wave_closeout_receipt.json"
        ],
        eval_receipt_paths=[
            "/srv/receipts/wave5-a2a/a2a_return_eval_packet.json"
        ],
        playbook_receipt_paths=[
            "/srv/receipts/wave5-a2a/playbook_review_harvest_receipt.json"
        ],
        memo_receipt_paths=[
            "/srv/receipts/wave5-a2a/memo_writeback_receipt.json"
        ],
    )
    reviewed_closeout_request = build_reviewed_closeout_request(
        remote_task,
        decision,
        session_ref=SESSION_REF,
        reviewed_artifact_path=REVIEWED_ARTIFACT_PATH,
        publication_plan=publication_plan,
        audit_refs=[
            REVIEWED_ARTIFACT_PATH,
            "repo:aoa-sdk/examples/a2a/summon_return_checkpoint_e2e.fixture.json",
        ],
        memo_export_plan=memo_export_plan,
        return_plan=return_plan,
        checkpoint_bridge_plan=checkpoint_bridge_plan,
        codex_target=codex_target,
    )
    runtime_wave_closeout_receipt = build_runtime_wave_closeout_receipt(
        remote_task,
        decision,
        session_ref=SESSION_REF,
        reviewed_artifact_path=REVIEWED_ARTIFACT_PATH,
        return_plan=return_plan,
        checkpoint_bridge_plan=checkpoint_bridge_plan,
        codex_target=codex_target,
        observed_at=observed_at,
    )
    summon_result = build_summon_result_payload(
        decision,
        codex_local_target=codex_target,
        return_plan=return_plan,
        checkpoint_bridge_plan=checkpoint_bridge_plan,
        memo_export_plan=memo_export_plan,
        owner_publication_plan=publication_plan,
    )

    return {
        "fixture_id": FIXTURE_ID,
        "schema_version": 1,
        "fixture_kind": "a2a_summon_return_checkpoint_e2e",
        "dry_run": True,
        "live_automation": False,
        "playbook_id": "AOA-P-0031",
        "eval_anchor": "aoa-a2a-summon-return-checkpoint",
        "owner_refs": {
            "summon_contract": "repo:aoa-skills/skills/aoa-summon/SKILL.md",
            "sdk_helper": "repo:aoa-sdk/docs/A2A_WAVE5_CODEX_RETURN_CHECKPOINT.md",
            "playbook": "repo:aoa-playbooks/playbooks/a2a-summon-return-checkpoint/PLAYBOOK.md",
            "eval_hook": "repo:aoa-evals/examples/artifact_to_verdict_hook.a2a-summon-return-checkpoint.example.json",
            "memo_writeback": "repo:aoa-memo/docs/A2A_CHILD_RETURN_WRITEBACK.md",
            "runtime_dry_run": "repo:abyss-stack/docs/A2A_RETURN_DRY_RUN.md",
            "routing_reentry": "repo:aoa-routing/generated/return_navigation_hints.min.json",
        },
        "summon_request": summon_request,
        "summon_result": summon_result,
        "summon_decision": to_jsonable(decision),
        "codex_local_target": to_jsonable(codex_target),
        "child_task_result": {
            "reviewed": True,
            "review_status": "reviewed",
            "reviewed_artifact_path": REVIEWED_ARTIFACT_PATH,
            "remote_task": to_jsonable(remote_task),
        },
        "return_plan": to_jsonable(return_plan),
        "transition_decision": build_transition_decision_payload(return_plan),
        "checkpoint_bridge_plan": to_jsonable(checkpoint_bridge_plan),
        "checkpoint_context_bundle": build_checkpoint_context_bundle(
            checkpoint_bridge_plan,
            owner_publication_plan=publication_plan,
        ),
        "a2a_return_eval_packet": {
            "hook_id": "aoa-p-0031-a2a-summon-return-checkpoint-hook",
            "playbook_id": "AOA-P-0031",
            "eval_anchor": "aoa-a2a-summon-return-checkpoint",
            "artifact_inputs": [
                "summon_request",
                "summon_decision",
                "codex_local_target",
                "child_task_result",
                "return_plan",
                "checkpoint_bridge_plan",
                "memo_writeback_ref",
                "runtime_closeout_dry_run_receipt",
            ],
            "review_required": True,
            "verdict_shape": "mixed",
        },
        "memo_writeback_candidate": {
            "memo_writeback_ref": "repo:aoa-memo/docs/A2A_CHILD_RETURN_WRITEBACK.md",
            "memo_export_plan": to_jsonable(memo_export_plan),
            "contains_raw_trace": memo_export_plan.contains_raw_trace,
        },
        "owner_publication_plan": [to_jsonable(plan) for plan in publication_plan],
        "reviewed_closeout_request": reviewed_closeout_request,
        "runtime_wave_closeout_receipt": runtime_wave_closeout_receipt,
        "runtime_closeout_dry_run_receipt_contract": {
            "artifact_kind": "aoa.runtime-a2a-return-closeout-dry-run",
            "dry_run": True,
            "live_automation": False,
            "exported_by": "scripts/aoa-a2a-return-closeout-dry-run",
            "source_payload": "reviewed_closeout_request",
        },
        "routing_reentry": {
            "entry_id": "AOA-P-0031",
            "return_reason": "checkpoint_continuity_needed",
            "surface_ref": "repo:aoa-routing/generated/return_navigation_hints.min.json",
            "primary_action": {
                "verb": "inspect",
                "target_repo": "aoa-playbooks",
                "target_surface": "generated/playbook_registry.min.json",
                "match_field": "id",
                "target_value": "AOA-P-0031",
            },
        },
    }
