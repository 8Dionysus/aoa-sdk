from pathlib import Path

import pytest

from aoa_sdk import AoASDK
from aoa_sdk.errors import RecordNotFound


def test_governed_run_artifact_readers_follow_preferred_stack_source(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    manifest = sdk.governed_runs.manifest("p4-sample-run")
    audit = sdk.governed_runs.audit("p4-sample-run")

    assert sdk.workspace.repo_path("abyss-stack") == (workspace_root / "src" / "abyss-stack").resolve()
    assert manifest.run_id == "p4-sample-run"
    assert manifest.selected_playbook["playbook_id"] == "AOA-P-0011"
    assert audit.audit_verdict == "partial"
    assert audit.replayable is True

    contract = sdk.playbooks.review_packet_contract(manifest.selected_playbook["playbook_id"])
    eval_template = next(
        item
        for item in sdk.evals.runtime_candidate_templates(template_kind="runtime_evidence_selection")
        if item.template_name == "return-anchor-integrity-wrapper-v1"
    )
    memo_target = sdk.memo.writeback_target(manifest.matched_memo_writeback_targets[0]["runtime_surface"])

    assert contract.source_review_refs[0] == "playbooks/bounded-change-safe/PLAYBOOK.md"
    assert audit.recommended_review_targets[0]["ref"] == contract.source_review_refs[0]
    assert manifest.matched_eval_template_entries[0]["template_name"] == eval_template.template_name
    assert memo_target.target_kind == manifest.matched_memo_writeback_targets[0]["target_kind"]


def test_governed_run_artifact_readers_accept_explicit_run_dir(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    run_dir = workspace_root / "src" / "abyss-stack" / "Logs" / "governed-runs" / "p4-sample-run"

    manifest = sdk.governed_runs.manifest(run_dir)
    audit = sdk.governed_runs.audit(run_dir)

    assert manifest.run_id == "p4-sample-run"
    assert audit.safe_replay_command == "scripts/aoa-governed-run replay-review-packets p4-sample-run"


def test_governed_run_artifact_readers_fail_for_unknown_run(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    with pytest.raises(RecordNotFound):
        sdk.governed_runs.manifest("missing-run")
