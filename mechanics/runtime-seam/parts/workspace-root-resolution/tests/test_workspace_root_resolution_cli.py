import json
from pathlib import Path

from typer.testing import CliRunner

from aoa_sdk.cli.main import app


def test_workspace_inspect_reports_manifest_and_repo_paths(workspace_root: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["workspace", "inspect", str(workspace_root / "aoa-sdk")])

    assert result.exit_code == 0
    assert f"manifest: {(workspace_root / 'aoa-sdk' / '.aoa' / 'workspace.toml').resolve()}" in result.stdout
    assert (
        "routing_bundle_root: "
        f"{(workspace_root / 'abyss-stack' / 'Knowledge' / 'federation' / 'aoa-routing').resolve()} "
        "[manifest:control_plane.routing_bundle_root]"
    ) in result.stdout
    assert (
        "routing_source_lock: package default "
        "[package:canonical-routing-source-lock]"
    ) in result.stdout
    assert f"aoa-sdk: {(workspace_root / 'aoa-sdk').resolve()} [federation-root]" in result.stdout


def test_workspace_inspect_can_emit_json(workspace_root: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["workspace", "inspect", str(workspace_root / "aoa-sdk"), "--json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["manifest"] == str(
        (workspace_root / "aoa-sdk" / ".aoa" / "workspace.toml").resolve()
    )
    assert payload["repos"]["aoa-sdk"]["origin"] == "federation-root"
    assert payload["control_plane"]["routing_bundle_root"] == str(
        (
            workspace_root
            / "abyss-stack"
            / "Knowledge"
            / "federation"
            / "aoa-routing"
        ).resolve()
    )
    assert payload["control_plane"]["routing_source_lock"] is None
    assert payload["control_plane"]["routing_source_lock_source"] == (
        "package:canonical-routing-source-lock"
    )


def test_workspace_inspect_default_root_anchors_manifest_patterns(
    workspace_root: Path,
    monkeypatch,
) -> None:
    nested = workspace_root / "aoa-sdk" / "src" / "aoa_sdk" / "control_plane"
    nested.mkdir(parents=True, exist_ok=True)
    monkeypatch.chdir(nested)

    result = CliRunner().invoke(app, ["workspace", "inspect", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["root"] == str(nested.resolve())
    assert payload["federation_root"] == str(workspace_root.resolve())
    assert payload["control_plane"]["routing_bundle_root"] == str(
        (
            workspace_root
            / "abyss-stack"
            / "Knowledge"
            / "federation"
            / "aoa-routing"
        ).resolve()
    )
