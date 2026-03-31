from pathlib import Path

from aoa_sdk import AoASDK


def test_from_workspace_resolves_root(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    assert sdk.workspace.root == (workspace_root / "aoa-sdk").resolve()
    assert sdk.workspace.federation_root == workspace_root.resolve()
    assert sdk.workspace.has_repo("aoa-skills")
    assert sdk.workspace.surface_path("aoa-skills", "generated/runtime_discovery_index.json").exists()


def test_prefers_abyss_stack_source_checkout_over_runtime_mirror(
    workspace_root: Path,
    monkeypatch,
) -> None:
    runtime_mirror = workspace_root / "abyss-stack" / "Configs"
    runtime_mirror.mkdir(parents=True)

    source_checkout = workspace_root / "src" / "abyss-stack"
    source_checkout.mkdir(parents=True)
    (source_checkout / ".git").mkdir()
    (source_checkout / "README.md").write_text("# abyss-stack\n", encoding="utf-8")

    monkeypatch.setenv("HOME", str(workspace_root))

    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    assert sdk.workspace.has_repo("abyss-stack")
    assert sdk.workspace.repo_path("abyss-stack") == source_checkout.resolve()
