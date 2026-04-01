import json
from pathlib import Path

from typer.testing import CliRunner

from aoa_sdk.cli.main import app


def test_workspace_inspect_reports_manifest_and_repo_paths(workspace_root: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["workspace", "inspect", str(workspace_root / "aoa-sdk")])

    assert result.exit_code == 0
    assert f"manifest: {(workspace_root / 'aoa-sdk' / '.aoa' / 'workspace.toml').resolve()}" in result.stdout
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


def test_compatibility_check_can_emit_repo_filtered_json(workspace_root: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "compatibility",
            "check",
            str(workspace_root / "aoa-sdk"),
            "--repo",
            "aoa-skills",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["repo"] == "aoa-skills"
    assert payload["compatible"] is True
    assert payload["checks"]
    assert all(entry["repo"] == "aoa-skills" for entry in payload["checks"])


def test_compatibility_check_can_emit_kag_repo_filtered_json(workspace_root: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "compatibility",
            "check",
            str(workspace_root / "aoa-sdk"),
            "--repo",
            "aoa-kag",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["repo"] == "aoa-kag"
    assert payload["compatible"] is True
    assert payload["checks"]
    assert all(entry["repo"] == "aoa-kag" for entry in payload["checks"])
