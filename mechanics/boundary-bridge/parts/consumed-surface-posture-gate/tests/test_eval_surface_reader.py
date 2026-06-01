from pathlib import Path

from aoa_sdk import AoASDK


def test_evals_local_read_path(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    listed = sdk.evals.list(category="artifact")
    capsule = sdk.evals.inspect("aoa-bounded-change-quality")
    expanded = sdk.evals.expand("aoa-bounded-change-quality", sections=["verification"])
    comparison = sdk.evals.comparison_entries(name="aoa-regression-same-task")
    runtime_templates = sdk.evals.runtime_candidate_templates(playbook_id="AOA-P-0006")
    hook_templates = sdk.evals.runtime_candidate_templates(template_kind="artifact_to_verdict_hook")
    intake_templates = sdk.evals.runtime_candidate_intake(playbook_id="AOA-P-0006")
    selection_intake = sdk.evals.runtime_candidate_intake(template_kind="runtime_evidence_selection")

    assert [item.name for item in listed] == ["aoa-bounded-change-quality"]
    assert capsule.name == "aoa-bounded-change-quality"
    assert [section.key for section in expanded.sections] == ["verification"]
    assert comparison.baseline_mode == "fixed-baseline"
    assert runtime_templates[0].eval_anchor == "aoa-approval-boundary-adherence"
    assert any(item.template_name == "workhorse-q4-vs-q6-latency-tradeoff" for item in hook_templates) is False
    assert any(item.template_name == "aoa-p-0006-approval-boundary-hook" for item in hook_templates)
    assert intake_templates[0].review_guide_ref == "docs/TRACE_EVAL_BRIDGE.md"
    assert intake_templates[0].candidate_acceptance_posture == "candidate_until_eval_review"
    assert selection_intake[0].template_name == "return-anchor-integrity-wrapper-v1"
