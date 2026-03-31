from pathlib import Path

from typer.testing import CliRunner

from aoa_sdk.cli.main import app


def test_workspace_inspect_reports_manifest_and_repo_paths(workspace_root: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["workspace", "inspect", str(workspace_root / "aoa-sdk")])

    assert result.exit_code == 0
    assert f"manifest: {(workspace_root / 'aoa-sdk' / '.aoa' / 'workspace.toml').resolve()}" in result.stdout
    assert f"aoa-sdk: {(workspace_root / 'aoa-sdk').resolve()} [federation-root]" in result.stdout
