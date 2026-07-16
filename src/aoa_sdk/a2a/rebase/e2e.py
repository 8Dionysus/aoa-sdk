from __future__ import annotations

from .checkpoint import (
    build_checkpoint_evidence_bundle,
    build_checkpoint_evidence_handoff_plan,
)
from .closeout import (
    build_owner_evidence_handoff,
    build_reviewed_return_handoff,
    build_runtime_return_closeout_receipt,
)
from .codex import build_codex_local_target
from .contracts import build_summon_request_payload, build_summon_result_payload
from .memo import build_memo_export_plan
from .models import QuestPassport, RemoteTaskResult, SummonIntent
from .passports import assess_summon
from .returning import build_return_plan, build_transition_decision_payload
from .utils import to_jsonable


FIXTURE_ID = "a2a-summon-return-checkpoint-e2e"
SESSION_REF = "session:a2a-return-checkpoint-e2e"
CHECKPOINT_NOTE_REF = (
    "aoa-sdk/.aoa/session-growth/current/"
    "a2a-return-checkpoint/checkpoint-note.json"
)
CODEX_TRACE_REF = "codex:thread:a2a-return-checkpoint"
REVIEWED_ARTIFACT_PATH = "/srv/notes/a2a-reviewed-child-return.md"
OBSERVED_AT = "2026-07-15T00:00:00.000Z"


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
        capability_refs=[
            "workflow.operations.delegation",
            "workflow.operations.checkpoint-closeout",
        ],
        expected_outputs=["verification_result", "bounded_plan"],
        parent_task_id="parent:a2a-return-checkpoint",
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
        task_id="task-a2a-return-child",
        state="failed",
        agent_id="reviewer",
        endpoint="codex://local/reviewer",
        returned_artifacts=["verification_result", "bounded_plan", "transition_decision"],
        context_id="ctx-a2a-return-checkpoint",
        parent_task_id="parent:a2a-return-checkpoint",
        artifact_refs=[
            "/srv/artifacts/a2a-return-checkpoint/verification_result.json",
            "/srv/artifacts/a2a-return-checkpoint/bounded_plan.md",
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

    checkpoint_handoff_plan = build_checkpoint_evidence_handoff_plan(
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
    owner_handoffs = [
        build_owner_evidence_handoff(
            owner_ref="repo:abyss-stack",
            candidate_kind="runtime-return-receipt",
            reason="runtime owner must decide whether to admit the reviewed return receipt",
            evidence_refs=[REVIEWED_ARTIFACT_PATH, *remote_task.artifact_refs],
        ),
        build_owner_evidence_handoff(
            owner_ref="repo:aoa-evals",
            candidate_kind="child-return-eval",
            reason="eval owner must verify the returned artifacts before any proof claim",
            evidence_refs=[REVIEWED_ARTIFACT_PATH, *remote_task.artifact_refs],
        ),
        build_owner_evidence_handoff(
            owner_ref="repo:aoa-memo",
            candidate_kind="reviewed-writeback-candidate",
            reason="memo owner must decide whether the reviewed return is durable memory",
            evidence_refs=[REVIEWED_ARTIFACT_PATH],
        ),
        build_owner_evidence_handoff(
            owner_ref="repo:aoa-playbooks",
            candidate_kind="checkpoint-owner-followthrough",
            reason="the owner playbook may compose reviewed checkpoint follow-through",
            evidence_refs=[REVIEWED_ARTIFACT_PATH, CHECKPOINT_NOTE_REF],
            capability_ref="workflow.operations.checkpoint-closeout",
        ),
    ]
    reviewed_return_handoff = build_reviewed_return_handoff(
        remote_task,
        decision,
        session_ref=SESSION_REF,
        reviewed_artifact_path=REVIEWED_ARTIFACT_PATH,
        owner_handoffs=owner_handoffs,
        audit_refs=[
            REVIEWED_ARTIFACT_PATH,
            "repo:aoa-sdk/mechanics/checkpoint/parts/child-task-reentry/examples/summon_return_checkpoint_e2e.fixture.json",
        ],
        memo_export_plan=memo_export_plan,
        return_plan=return_plan,
        checkpoint_handoff_plan=checkpoint_handoff_plan,
        codex_target=codex_target,
    )
    runtime_return_closeout_receipt = build_runtime_return_closeout_receipt(
        remote_task,
        decision,
        session_ref=SESSION_REF,
        reviewed_artifact_path=REVIEWED_ARTIFACT_PATH,
        return_plan=return_plan,
        checkpoint_handoff_plan=checkpoint_handoff_plan,
        codex_target=codex_target,
        observed_at=observed_at,
    )
    summon_result = build_summon_result_payload(
        decision,
        codex_local_target=codex_target,
        return_plan=return_plan,
        checkpoint_handoff_plan=checkpoint_handoff_plan,
        memo_export_plan=memo_export_plan,
        owner_handoffs=owner_handoffs,
    )

    return {
        "fixture_id": FIXTURE_ID,
        "schema_version": 2,
        "fixture_kind": "a2a_summon_return_checkpoint_e2e",
        "dry_run": True,
        "live_automation": False,
        "capability_execution_claimed": False,
        "playbook_id": "AOA-P-0031",
        "eval_anchor": "aoa-a2a-summon-return-checkpoint",
        "owner_refs": {
            "delegation_capability": "workflow.operations.delegation",
            "checkpoint_capability": "workflow.operations.checkpoint-closeout",
            "sdk_contract": "repo:aoa-sdk/mechanics/checkpoint/parts/child-task-reentry/schemas/summon-request-v4.schema.json",
            "sdk_helper": "repo:aoa-sdk/mechanics/checkpoint/parts/child-task-reentry/docs/summon-return-checkpoint.md",
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
        "checkpoint_handoff_plan": to_jsonable(checkpoint_handoff_plan),
        "checkpoint_evidence_bundle": build_checkpoint_evidence_bundle(
            checkpoint_handoff_plan,
            owner_handoffs=owner_handoffs,
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
                "checkpoint_handoff_plan",
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
        "owner_handoffs": [to_jsonable(item) for item in owner_handoffs],
        "reviewed_return_handoff": reviewed_return_handoff,
        "runtime_return_closeout_receipt": runtime_return_closeout_receipt,
        "runtime_closeout_dry_run_receipt_contract": {
            "artifact_kind": "aoa.runtime-a2a-return-closeout-dry-run",
            "dry_run": True,
            "live_automation": False,
            "exported_by": "scripts/aoa-a2a-return-closeout-dry-run",
            "source_payload": "reviewed_return_handoff",
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
