from pathlib import Path

from aoa_sdk import AoASDK


def test_playbooks_local_read_path(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    listed = sdk.playbooks.list(status="active")
    registry_entry = sdk.playbooks.get("AOA-P-0011")
    activation = sdk.playbooks.activation_surface("bounded-change-safe")
    federation = sdk.playbooks.federation_surface("self-agent-checkpoint-rollout")
    handoff = sdk.playbooks.handoff_contracts("bounded-change-safe")
    failure = sdk.playbooks.failure_catalog(code="APPROVAL_REQUIRED")
    recipe = sdk.playbooks.subagent_recipe(playbook="bounded-change-safe")
    seeds = sdk.playbooks.automation_seeds("source-truth-then-share")
    manifest = sdk.playbooks.composition_manifest()
    review_status = sdk.playbooks.review_status("bounded-change-safe")
    review_packet_contract = sdk.playbooks.review_packet_contract("bounded-change-safe")
    review_intake = sdk.playbooks.review_intake("bounded-change-safe")

    assert [item.name for item in listed] == ["bounded-change-safe", "restartable-inquiry-loop"]
    assert registry_entry.name == "bounded-change-safe"
    assert activation.memo_source_route_policy == "required"
    assert federation.playbook_id == "AOA-P-0006"
    assert handoff.name == "bounded-change-safe"
    assert failure.summary.startswith("The requested action crosses an approval boundary")
    assert recipe[0].name == "safety-split"
    assert seeds[0].playbook == "source-truth-then-share"
    assert manifest.total_playbook_count >= manifest.composition_playbook_count
    assert review_status.playbook_id == "AOA-P-0011"
    assert review_status.gate_verdict == "composition-landed"
    assert review_packet_contract.playbook_id == "AOA-P-0011"
    assert review_packet_contract.memo_runtime_surfaces == ["approval_record"]
    assert "aoa-approval-boundary-adherence" in review_packet_contract.eval_anchors
    assert review_intake.playbook_id == "AOA-P-0011"
    assert review_intake.gate_verdict == "composition-landed"
    assert review_intake.review_outcome_targets.gate_reviews == ["docs/gate-reviews/bounded-change-safe.md"]
    assert "memo_candidate" in review_intake.accepted_packet_kinds
