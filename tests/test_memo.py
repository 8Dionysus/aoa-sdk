from pathlib import Path

from aoa_sdk import AoASDK


def test_memo_local_read_path(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    doctrine = sdk.memo.inspect("charter")
    capsule = sdk.memo.capsule("AOA-M-0001")
    expanded = sdk.memo.expand("charter", sections=["Mission"])
    recalled = sdk.memo.recall(mode="semantic", query="charter")
    obj = sdk.memo.inspect_object("memo.anchor.2026-03-23.charter-operating-axis")
    obj_capsule = sdk.memo.capsule_object("aoa-memo charter remains a stable operating anchor")
    obj_expanded = sdk.memo.expand_object(
        "memo.anchor.2026-03-23.charter-operating-axis",
        sections=["Trust and Lifecycle"],
    )
    recalled_objects = sdk.memo.recall_object(mode="semantic", query="charter")
    writeback = sdk.memo.writeback_map("checkpoint_export")
    writeback_targets = sdk.memo.writeback_targets()
    writeback_target = sdk.memo.writeback_target("distillation_claim_candidate")
    writeback_intake_entries = sdk.memo.writeback_intake()
    writeback_intake_target = sdk.memo.writeback_intake("distillation_claim_candidate")
    writeback_governance_entries = sdk.memo.writeback_governance()
    writeback_governance_target = sdk.memo.writeback_governance("distillation_claim_candidate")

    assert doctrine.id == "AOA-M-0001"
    assert capsule.name == "charter"
    assert [section.heading for section in expanded.sections] == ["Mission"]
    assert [item.name for item in recalled] == ["charter"]
    assert obj.kind == "anchor"
    assert obj_capsule.strongest_next_source == "CHARTER.md#core-rules"
    assert [section.heading for section in obj_expanded.sections] == ["Trust and Lifecycle"]
    assert [item.id for item in recalled_objects] == ["memo.anchor.2026-03-23.charter-operating-axis"]
    assert writeback.mapping.target_kind == "state_capsule"
    assert writeback.mapping.writeback_class == "checkpoint_export"
    assert writeback.runtime_boundary["scratchpad_posture"] == "runtime_local_only"
    assert writeback_targets[0].runtime_surface == "checkpoint_export"
    assert writeback_target.target_kind == "claim"
    assert writeback_target.requires_human_review is True
    assert writeback_intake_entries[0].runtime_surface == "approval_record"
    assert writeback_intake_target.target_kind == "claim"
    assert writeback_intake_target.intake_posture == "review_candidate_only"
    assert "docs/QUEST_EVIDENCE_WRITEBACK.md" in writeback_intake_target.owner_review_refs
    assert writeback_governance_entries[0].runtime_surface == "approval_record"
    assert writeback_governance_target.writeback_class == "reviewed_candidate"
    assert writeback_governance_target.intake_posture == "review_candidate_only"
    assert writeback_governance_target.governance_passed is True


def test_memo_runtime_writeback_governance_resolves_through_targets_and_intake(
    workspace_root: Path,
) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    reviewed_candidate_targets = {
        "distillation_bridge_candidate": "bridge",
        "distillation_claim_candidate": "claim",
        "distillation_pattern_candidate": "pattern",
    }

    for governance in sdk.memo.writeback_governance():
        target = sdk.memo.writeback_target(governance.runtime_surface)
        intake = sdk.memo.writeback_intake(governance.runtime_surface)

        assert governance.in_writeback_targets is True
        assert governance.in_writeback_intake is True
        assert target.target_kind == governance.target_kind
        assert intake.target_kind == governance.target_kind
        assert intake.writeback_class == governance.writeback_class
        assert intake.requires_human_review == governance.requires_human_review
        assert intake.review_state_default == governance.review_state_default

    for runtime_surface, target_kind in reviewed_candidate_targets.items():
        target = sdk.memo.writeback_target(runtime_surface)
        intake = sdk.memo.writeback_intake(runtime_surface)
        governance = sdk.memo.writeback_governance(runtime_surface)

        assert target.target_kind == target_kind
        assert intake.target_kind == target_kind
        assert governance.target_kind == target_kind
        assert target.writeback_class == "reviewed_candidate"
        assert intake.writeback_class == "reviewed_candidate"
        assert governance.writeback_class == "reviewed_candidate"
        assert target.requires_human_review is True
        assert intake.requires_human_review is True
        assert governance.requires_human_review is True
        assert intake.intake_posture == "review_candidate_only"
        assert governance.intake_posture == "review_candidate_only"
        assert governance.governance_passed is True
        assert governance.blockers == []
