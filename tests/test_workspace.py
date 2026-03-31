from pathlib import Path

from aoa_sdk import AoASDK


def test_from_workspace_resolves_root(tmp_path: Path) -> None:
    sdk = AoASDK.from_workspace(tmp_path)

    assert sdk.workspace.root == tmp_path.resolve()
