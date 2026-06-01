import json
from pathlib import Path

from typer.testing import CliRunner

from aoa_sdk.cli.main import app


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
