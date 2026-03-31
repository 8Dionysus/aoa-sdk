from pathlib import Path

from aoa_sdk import AoASDK


def test_from_workspace_resolves_root(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    assert sdk.workspace.root == (workspace_root / "aoa-sdk").resolve()
    assert sdk.workspace.federation_root == workspace_root.resolve()
    assert sdk.workspace.has_repo("aoa-skills")
    assert sdk.workspace.surface_path("aoa-skills", "generated/runtime_discovery_index.json").exists()
