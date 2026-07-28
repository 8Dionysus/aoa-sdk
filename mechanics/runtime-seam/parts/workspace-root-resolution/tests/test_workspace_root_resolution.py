from pathlib import Path

from aoa_sdk import AoASDK


def test_from_workspace_resolves_root(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    assert sdk.workspace.root == (workspace_root / "aoa-sdk").resolve()
    assert sdk.workspace.federation_root == workspace_root.resolve()
    assert sdk.workspace.federation_root_source == "manifest:layout.federation_roots"
    assert sdk.workspace.manifest_path == (workspace_root / "aoa-sdk" / ".aoa" / "workspace.toml").resolve()
    assert sdk.workspace.has_repo("aoa-skills")
    assert sdk.workspace.routing_bundle_root == (
        workspace_root
        / "abyss-stack"
        / "Knowledge"
        / "federation"
        / "aoa-routing"
    ).resolve()
    assert sdk.workspace.routing_bundle_root_source == (
        "manifest:control_plane.routing_bundle_root"
    )
    assert sdk.workspace.routing_source_lock_path is None
    assert sdk.workspace.routing_source_lock_source == (
        "package:canonical-routing-source-lock"
    )
    assert sdk.workspace.organ_registry_path == (
        workspace_root
        / ".aoa"
        / "organ-access"
        / "organ-registry.source.json"
    ).resolve()
    assert sdk.workspace.organ_registry_source == (
        "manifest:organ_access.registry_source"
    )
    assert sdk.workspace.surface_path(
        "aoa-skills",
        "generated/agent_skill_catalog.json",
    ).exists()


def test_manifest_patterns_stay_anchored_when_started_below_checkout(
    workspace_root: Path,
) -> None:
    nested = workspace_root / "aoa-sdk" / "src" / "aoa_sdk" / "control_plane"
    nested.mkdir(parents=True, exist_ok=True)

    sdk = AoASDK.from_workspace(nested)

    assert sdk.workspace.root == nested.resolve()
    assert sdk.workspace.manifest_path == (
        workspace_root / "aoa-sdk" / ".aoa" / "workspace.toml"
    ).resolve()
    assert sdk.workspace.federation_root == workspace_root.resolve()
    assert sdk.workspace.routing_bundle_root == (
        workspace_root
        / "abyss-stack"
        / "Knowledge"
        / "federation"
        / "aoa-routing"
    ).resolve()
    assert sdk.workspace.organ_registry_path == (
        workspace_root
        / ".aoa"
        / "organ-access"
        / "organ-registry.source.json"
    ).resolve()


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
