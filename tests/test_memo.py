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
