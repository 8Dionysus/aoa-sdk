from pathlib import Path

from aoa_sdk import AoASDK


def test_from_workspace_resolves_root(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    assert sdk.workspace.root == (workspace_root / "aoa-sdk").resolve()
    assert sdk.workspace.federation_root == workspace_root.resolve()
    assert sdk.workspace.federation_root_source == "manifest:layout.federation_roots"
    assert sdk.workspace.manifest_path == (workspace_root / "aoa-sdk" / ".aoa" / "workspace.toml").resolve()
    assert sdk.workspace.has_repo("aoa-skills")
    assert sdk.workspace.surface_path("aoa-skills", "generated/runtime_discovery_index.json").exists()


def test_prefers_abyss_stack_source_checkout_over_runtime_mirror(
    workspace_root: Path,
) -> None:
    runtime_mirror = workspace_root / "abyss-stack" / "Configs"
    runtime_mirror.mkdir(parents=True, exist_ok=True)

    source_checkout = workspace_root / "src" / "abyss-stack"
    source_checkout.mkdir(parents=True, exist_ok=True)
    (source_checkout / ".git").mkdir()
    (source_checkout / "README.md").write_text("# abyss-stack\n", encoding="utf-8")

    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    assert sdk.workspace.has_repo("abyss-stack")
    assert sdk.workspace.repo_path("abyss-stack") == source_checkout.resolve()
    assert sdk.workspace.repo_origins["abyss-stack"] == "manifest:repos.abyss-stack.preferred"


def test_repo_path_env_override_wins(workspace_root: Path, monkeypatch) -> None:
    source_checkout = workspace_root / "alt" / "abyss-stack"
    source_checkout.mkdir(parents=True)
    (source_checkout / ".git").mkdir()
    (source_checkout / "README.md").write_text("# abyss-stack\n", encoding="utf-8")

    monkeypatch.setenv("AOA_SDK_REPO_PATH_ABYSS_STACK", str(source_checkout))

    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    assert sdk.workspace.repo_path("abyss-stack") == source_checkout.resolve()
    assert sdk.workspace.repo_origins["abyss-stack"] == "env:AOA_SDK_REPO_PATH_ABYSS_STACK"


def test_external_root_env_adds_repo_search_prefix(workspace_root: Path, monkeypatch) -> None:
    source_checkout = workspace_root / "worktrees" / "Tree-of-Sophia"
    source_checkout.mkdir(parents=True)
    (source_checkout / ".git").mkdir()
    (source_checkout / "README.md").write_text("# Tree-of-Sophia\n", encoding="utf-8")

    monkeypatch.setenv("AOA_SDK_EXTERNAL_ROOTS", str(workspace_root / "worktrees"))

    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    assert sdk.workspace.repo_path("Tree-of-Sophia") == source_checkout.resolve()
    assert sdk.workspace.repo_origins["Tree-of-Sophia"] == "env:AOA_SDK_EXTERNAL_ROOTS"
