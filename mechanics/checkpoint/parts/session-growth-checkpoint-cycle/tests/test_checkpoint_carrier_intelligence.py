from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from typer.testing import CliRunner

from aoa_sdk import AoASDK
from aoa_sdk.checkpoints.carrier_indexes import (
    build_checkpoint_carrier_candidate_intelligence_index,
)
from aoa_sdk.checkpoints.carrier_intelligence import (
    build_carrier_intelligence_from_candidate_report,
)
from aoa_sdk.cli.main import app
from aoa_sdk.models import (
    ActionSignature,
    CandidateIntelligenceReport,
    ExistingWrapperFit,
    RepetitionCluster,
    WrapperReadiness,
)


@pytest.fixture(autouse=True)
def _explicit_runtime_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AOA_SESSION_ID", "runtime-carrier-intelligence-tests")


def _signature(
    *,
    signature_id: str,
    action: str,
    object_ref: str,
    wrapper_family: str,
    owner_pressure: list[str],
    evidence_refs: list[str],
    family: str = "command_execution",
) -> ActionSignature:
    return ActionSignature(
        signature_id=signature_id,
        family=family,
        action=action,
        object=object_ref,
        trigger="repeated ecosystem route pressure",
        inputs=evidence_refs,
        steps=["inspect owner route", "preserve candidate evidence", "defer owner verdict"],
        outputs=["carrier candidate route evidence"],
        verification=["same action shape recurs with the same owner boundary"],
        failure_modes=["carrier resemblance treated as acceptance"],
        stop_lines=["no_owner_verdict", "no_single_event_promotion"],
        owner_pressure=owner_pressure,
        evidence_refs=evidence_refs,
        wrapper_family_hint=wrapper_family,  # type: ignore[arg-type]
    )


def _cluster(signature: ActionSignature, *, repeat_count: int) -> RepetitionCluster:
    return RepetitionCluster(
        cluster_id=f"repetition:{signature.signature_id}",
        signature_id=signature.signature_id,
        repeat_count=repeat_count,
        cross_session_count=1 if repeat_count > 1 else 0,
        trigger_stability="high" if repeat_count >= 3 else "medium",
        step_stability="high",
        verification_stability="high",
        owner_clarity="high" if signature.owner_pressure else "low",
        action_event_ids=[],
        runtime_session_ids=["runtime:synthetic"] if repeat_count > 1 else [],
        evidence_refs=list(signature.evidence_refs),
        existing_wrapper_fit=ExistingWrapperFit(
            wrapper_family=signature.wrapper_family_hint,
            fit_status="strong",
            existing_surface_ref=signature.evidence_refs[0] if signature.evidence_refs else None,
            fit_reason="synthetic repeated carrier evidence",
            evidence_refs=list(signature.evidence_refs),
        ),
        wrapper_readiness=WrapperReadiness(
            proposed_wrapper_family=signature.wrapper_family_hint,
            draftability="reviewable" if repeat_count >= 2 else "observe",
            reasons=[f"repeat_count={repeat_count}"],
            stop_lines=["no_single_event_promotion"],
        ),
    )


def _report(signatures: list[ActionSignature], *, repeated: bool = True) -> CandidateIntelligenceReport:
    return CandidateIntelligenceReport(
        repo_root="/srv/AbyssOS/aoa-sdk",
        repo_label="aoa-sdk",
        generated_at=datetime(2026, 6, 4, tzinfo=UTC),
        source="checkpoint_note",
        action_signatures=signatures,
        repetition_clusters=[
            _cluster(signature, repeat_count=3 if repeated else 1)
            for signature in signatures
        ],
    )


def _candidate_by_action(report, action: str):  # type: ignore[no-untyped-def]
    return next(candidate for candidate in report.carrier_candidates if candidate.action == action)


def _write_legacy_checkpoint_entry(note_dir: Path, *, observed_at: str) -> None:
    note_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "session_ref": "session:legacy-carrier-intelligence",
        "runtime_session_id": "runtime-legacy-carrier-intelligence",
        "runtime_session_created_at": "2026-04-10T13:55:00Z",
        "repo_root": str(note_dir.parents[3].resolve()),
        "repo_label": "aoa-sdk",
        "history_entry": {
            "checkpoint_kind": "manual",
            "observed_at": observed_at,
            "report_ref": str(note_dir / "legacy-report.json"),
            "intent_text": "legacy recurring workflow candidate",
            "checkpoint_should_capture": True,
            "blocked_by": [],
            "candidate_clusters": [
                {
                    "candidate_id": "candidate:route:aoa-playbooks-playbook-registry-min",
                    "candidate_kind": "route",
                    "owner_hint": "aoa-playbooks",
                    "display_name": "Recurring route candidate",
                    "source_surface_ref": "aoa-playbooks.playbook_registry.min",
                    "evidence_refs": [
                        "aoa-playbooks.playbook_registry.min",
                        "aoa-techniques.technique_promotion_readiness.min",
                    ],
                    "confidence": "medium",
                    "session_end_targets": ["harvest", "progression", "upgrade"],
                    "progression_axis_signals": [],
                    "next_owner_moves": [
                        "carry the candidate through reviewed session closeout before moving candidates or stats"
                    ],
                }
            ],
            "manual_review_requested": False,
        },
    }
    with (note_dir / "checkpoint-note.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=True) + "\n")


def test_carrier_intelligence_classifies_non_sdk_mechanics_and_owner_scope() -> None:
    signatures = [
        _signature(
            signature_id="action-signature:memo-writeback",
            action="return_writeback_target",
            object_ref="mechanics/writeback/OWNER_MAP.md",
            wrapper_family="memo",
            owner_pressure=["aoa-memo"],
            evidence_refs=["aoa-memo:mechanics/writeback/README.md"],
            family="context_memory",
        ),
        _signature(
            signature_id="action-signature:center-mechanic",
            action="route_method_growth_owner_split",
            object_ref="mechanics/method-growth/README.md",
            wrapper_family="owner_local",
            owner_pressure=["Agents-of-Abyss"],
            evidence_refs=["Agents-of-Abyss:mechanics/README.md"],
            family="owner_routing",
        ),
        _signature(
            signature_id="action-signature:cross-repo-route",
            action="route_scenario_handoff",
            object_ref="playbook technique handoff",
            wrapper_family="playbook",
            owner_pressure=["aoa-playbooks", "aoa-techniques"],
            evidence_refs=[
                "aoa-playbooks:mechanics/scenario-composition/README.md",
                "aoa-techniques:mechanics/method-growth/README.md",
            ],
        ),
        _signature(
            signature_id="action-signature:sdk-local-mutation",
            action="record_commit_mutation",
            object_ref="aoa-sdk checkpoint mutation",
            wrapper_family="sdk_mechanic",
            owner_pressure=["aoa-sdk"],
            evidence_refs=[
                "context:aoa-sdk",
                "mutation_surface:code",
                "aoa-sdk:mechanics/checkpoint/README.md",
            ],
        ),
    ]

    report = build_carrier_intelligence_from_candidate_report(
        candidate_report=_report(signatures),
        sample_limit=2,
    )

    memo = _candidate_by_action(report, "return_writeback_target")
    center = _candidate_by_action(report, "route_method_growth_owner_split")
    cross_repo = _candidate_by_action(report, "route_scenario_handoff")
    sdk_local = _candidate_by_action(report, "record_commit_mutation")

    assert memo.carrier_kind == "mechanic"
    assert memo.owner_scope == "owner_repo"
    assert memo.owner_scope != "sdk_local"
    assert center.owner_scope == "center"
    assert cross_repo.owner_scope == "cross_repo"
    assert cross_repo.cross_repo_pressure is True
    assert sdk_local.owner_scope == "sdk_local"
    assert "no_sdk_local_as_head_pattern" in sdk_local.stop_lines
    assert len(report.sample_audit) == 2
    assert report.sample_audit[0].verdict == "unreviewed"


def test_carrier_intelligence_distinguishes_tool_mcp_hook_and_blocks_execution() -> None:
    signatures = [
        _signature(
            signature_id="action-signature:live-publisher-tool",
            action="publish_live_receipts",
            object_ref="mechanics/publication-receipts/parts/live-publisher/scripts/publish_live_receipts.py",
            wrapper_family="unknown",
            owner_pressure=["aoa-evals"],
            evidence_refs=[
                "aoa-evals:mechanics/publication-receipts/parts/live-publisher/scripts/publish_live_receipts.py"
            ],
        ),
        _signature(
            signature_id="action-signature:mcp-access-plane",
            action="expose_mcp_access_plane",
            object_ref="docs/architecture/AOA_EVALS_MCP_CONTRACT.md",
            wrapper_family="unknown",
            owner_pressure=["aoa-evals", "abyss-stack"],
            evidence_refs=[
                "aoa-evals:docs/architecture/AOA_EVALS_MCP_CONTRACT.md",
                "abyss-stack:mcp/services/aoa-evals-mcp",
            ],
        ),
        _signature(
            signature_id="action-signature:artifact-verdict-hook",
            action="route_artifact_verdict_hook",
            object_ref="mechanics/audit/parts/artifact-verdict-hooks",
            wrapper_family="unknown",
            owner_pressure=["aoa-evals"],
            evidence_refs=[
                "aoa-evals:mechanics/audit/parts/artifact-verdict-hooks/README.md",
                "aoa-evals:mechanics/audit/parts/artifact-verdict-hooks/schemas/artifact-to-verdict-hook.schema.json",
            ],
        ),
    ]

    report = build_carrier_intelligence_from_candidate_report(candidate_report=_report(signatures))

    tool = _candidate_by_action(report, "publish_live_receipts")
    mcp = _candidate_by_action(report, "expose_mcp_access_plane")
    hook = _candidate_by_action(report, "route_artifact_verdict_hook")

    assert tool.carrier_kind == "tool"
    assert tool.execution_posture == "callable_blocked"
    assert "no_callable_execution" in tool.stop_lines
    assert mcp.carrier_kind == "mcp"
    assert mcp.owner_scope == "cross_repo"
    assert mcp.execution_posture == "install_blocked"
    assert mcp.installability == "owner_required"
    assert "no_mcp_registration" in mcp.stop_lines
    assert hook.carrier_kind == "hook"
    assert hook.execution_posture == "install_blocked"
    assert hook.installability == "install_blocked"
    assert "no_hook_installation" in hook.stop_lines


def test_carrier_intelligence_keeps_single_unknown_event_candidate_only() -> None:
    signature = ActionSignature(
        signature_id="action-signature:unknown-carrier",
        family="unknown",
        action="notice_unfamiliar_action",
        object="unresolved pressure",
        trigger="one unresolved event",
        inputs=[],
        steps=[],
        outputs=[],
        verification=[],
        failure_modes=[],
        stop_lines=["no_single_event_promotion"],
        owner_pressure=[],
        evidence_refs=[],
        wrapper_family_hint="unknown",
    )

    report = build_carrier_intelligence_from_candidate_report(
        candidate_report=_report([signature], repeated=False)
    )
    candidate = report.carrier_candidates[0]

    assert candidate.carrier_kind == "unknown"
    assert candidate.owner_scope == "unknown"
    assert candidate.carrier_readiness.draftability != "draftable"
    assert "single_event_cannot_promote" in candidate.carrier_readiness.blockers


def test_carrier_intelligence_sibling_resemblance_does_not_force_sdk_local() -> None:
    signature = _signature(
        signature_id="action-signature:wrong-sdk-resemblance",
        action="record_writeback_mutation",
        object_ref="aoa-memo writeback route",
        wrapper_family="sdk_mechanic",
        owner_pressure=["aoa-memo"],
        evidence_refs=["aoa-memo:mechanics/writeback/README.md"],
    )

    report = build_carrier_intelligence_from_candidate_report(candidate_report=_report([signature]))
    candidate = report.carrier_candidates[0]

    assert candidate.owner_scope == "owner_repo"
    assert candidate.owner_scope != "sdk_local"


def test_carrier_index_is_navigation_only_and_groups_carrier_axes() -> None:
    signatures = [
        _signature(
            signature_id="action-signature:tool",
            action="publish_live_receipts",
            object_ref="scripts/publish_live_receipts.py",
            wrapper_family="unknown",
            owner_pressure=["aoa-evals"],
            evidence_refs=["aoa-evals:mechanics/publication-receipts/parts/live-publisher/scripts/publish_live_receipts.py"],
        ),
        _signature(
            signature_id="action-signature:mechanic",
            action="return_writeback_target",
            object_ref="mechanics/writeback/README.md",
            wrapper_family="memo",
            owner_pressure=["aoa-memo"],
            evidence_refs=["aoa-memo:mechanics/writeback/README.md"],
            family="context_memory",
        ),
    ]
    report = build_carrier_intelligence_from_candidate_report(
        candidate_report=_report(signatures),
        sample_limit=1,
    )

    index = build_checkpoint_carrier_candidate_intelligence_index(report)

    assert index["artifact_type"] == "checkpoint_carrier_candidate_intelligence_navigation_index_v1"
    assert "GraphRAG authority" in index["boundary_note"]
    assert "accepted mechanics" in index["boundary_note"]
    assert index["counts"]["by_carrier_kind"]["mechanic"] == 1
    assert index["counts"]["by_carrier_kind"]["tool"] == 1
    assert "by_owner_scope" in index
    assert "by_installability" in index
    assert index["counts"]["graph_anchors"] > 0
    assert index["sample_audit"][0]["verdict"] == "unreviewed"


def test_checkpoint_carrier_intelligence_cli_writes_generated_navigation_index(
    workspace_root: Path,
) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    intent_text = "recurring workflow needs better handoff proof and recall"
    sdk.checkpoints.append(
        repo_root=str(workspace_root / "aoa-sdk"),
        checkpoint_kind="manual",
        intent_text=intent_text,
    )
    sdk.checkpoints.append(
        repo_root=str(workspace_root / "aoa-sdk"),
        checkpoint_kind="manual",
        intent_text=intent_text,
    )

    result = CliRunner().invoke(
        app,
        [
            "checkpoint",
            "carrier-intelligence",
            str(workspace_root / "aoa-sdk"),
            "--sample-limit",
            "1",
            "--write-index",
            "--root",
            str(workspace_root / "aoa-sdk"),
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    index_ref = Path(payload["generated_index_ref"])
    assert payload["report_type"] == "checkpoint_carrier_candidate_intelligence_report_v1"
    assert payload["carrier_candidates"]
    assert index_ref.exists()

    index = json.loads(index_ref.read_text(encoding="utf-8"))
    assert index["artifact_type"] == "checkpoint_carrier_candidate_intelligence_navigation_index_v1"
    assert "not accepted mechanics" in index["boundary_note"]
    assert "mechanic" in index["by_carrier_kind"]


def test_checkpoint_carrier_intelligence_backfills_legacy_candidate_clusters(
    workspace_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "AOA_SESSION_ID", "runtime-legacy-carrier-intelligence"
    )
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    note_dir = (
        workspace_root
        / "aoa-sdk"
        / ".aoa"
        / "session-growth"
        / "current"
        / "runtime-legacy-carrier-intelligence"
        / "aoa-sdk"
    )
    _write_legacy_checkpoint_entry(note_dir, observed_at="2026-04-10T14:00:00Z")
    _write_legacy_checkpoint_entry(note_dir, observed_at="2026-04-10T14:01:00Z")

    report = sdk.checkpoints.carrier_intelligence(
        repo_root=str(workspace_root / "aoa-sdk"),
        sample_limit=1,
    )

    carrier = _candidate_by_action(report, "repeat_manual_workflow")
    assert carrier.carrier_kind == "mechanic"
    assert carrier.owner_scope == "cross_repo"
    assert carrier.source_wrapper_family == "playbook"
    assert carrier.carrier_readiness.draftability == "reviewable"
    assert report.sample_audit[0].verdict == "unreviewed"
