from pathlib import Path

from aoa_sdk import AoASDK


def test_kag_local_read_path(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    registry = sdk.kag.registry()
    federation_spine = sdk.kag.federation_spine()
    tiny_bundle = sdk.kag.tiny_bundle()
    inspect_result = sdk.kag.inspect("AOA-K-0011")
    query_mode = sdk.kag.query_mode("local_search")
    regrounding = sdk.kag.regrounding("source_export_reentry")
    repo_entry = sdk.kag.repo_entry("Tree-of-Sophia")

    assert registry[0].id == "AOA-K-0001"
    assert federation_spine.repo_count == 2
    assert tiny_bundle.bundle_item_count == len(tiny_bundle.bundle_items)
    assert inspect_result.surface_id == "AOA-K-0011"
    assert inspect_result.pack["surface_id"] == "AOA-K-0011"
    assert query_mode.mode == "local_search"
    assert query_mode.reasoning_scenarios
    assert query_mode.regrounding_modes
    assert regrounding.mode_id == "source_export_reentry"
    assert repo_entry.repo == "Tree-of-Sophia"
