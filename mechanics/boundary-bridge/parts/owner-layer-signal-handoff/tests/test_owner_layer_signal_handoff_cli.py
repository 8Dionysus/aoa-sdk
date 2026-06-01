import json
from pathlib import Path

from typer.testing import CliRunner

from aoa_sdk.cli.main import app


def test_surfaces_detect_cli_can_emit_json_and_persist_default_report(
    workspace_root: Path,
) -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "surfaces",
            "detect",
            str(workspace_root / "aoa-sdk"),
            "--phase",
            "ingress",
            "--intent-text",
            "verify recurring handoff proof",
            "--root",
            str(workspace_root / "aoa-sdk"),
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    expected_path = (
        workspace_root
        / "aoa-sdk"
        / ".aoa"
        / "surface-detection"
        / "aoa-sdk.ingress.latest.json"
    )
    assert payload["report_path"] == str(expected_path)
    assert expected_path.exists()
    assert payload["report"]["phase"] == "ingress"
    assert payload["report"]["skill_report_included"] is True


def test_surfaces_handoff_cli_can_emit_json(workspace_root: Path) -> None:
    runner = CliRunner()
    append_result = runner.invoke(
        app,
        [
            "checkpoint",
            "append",
            str(workspace_root / "aoa-sdk"),
            "--kind",
            "commit",
            "--intent-text",
            "recurring workflow needs better handoff proof and recall",
            "--root",
            str(workspace_root / "aoa-sdk"),
            "--json",
        ],
    )
    assert append_result.exit_code == 0
    append_two_result = runner.invoke(
        app,
        [
            "checkpoint",
            "append",
            str(workspace_root / "aoa-sdk"),
            "--kind",
            "verify_green",
            "--intent-text",
            "recurring workflow needs better handoff proof and recall",
            "--root",
            str(workspace_root / "aoa-sdk"),
            "--json",
        ],
    )
    assert append_two_result.exit_code == 0
    detect_result = runner.invoke(
        app,
        [
            "surfaces",
            "detect",
            str(workspace_root / "aoa-sdk"),
            "--phase",
            "pre-mutation",
            "--intent-text",
            "verify recurring pattern workflow",
            "--mutation-surface",
            "runtime",
            "--root",
            str(workspace_root / "aoa-sdk"),
            "--json",
        ],
    )
    detect_payload = json.loads(detect_result.stdout)

    result = runner.invoke(
        app,
        [
            "surfaces",
            "handoff",
            detect_payload["report_path"],
            "--session-ref",
            "session:test-surface-cli",
            "--reviewed",
            "--root",
            str(workspace_root / "aoa-sdk"),
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    expected_path = (
        workspace_root
        / "aoa-sdk"
        / ".aoa"
        / "surface-detection"
        / "aoa-sdk.closeout-handoff.latest.json"
    )
    assert payload["report_path"] == str(expected_path)
    assert expected_path.exists()
    assert payload["report"]["session_ref"] == "session:test-surface-cli"
    assert payload["report"]["reviewed"] is True
    assert payload["report"]["checkpoint_harvest_candidates"]
    assert payload["report"]["checkpoint_upgrade_candidates"]
    assert payload["report"]["stats_refresh_recommended"] is True


def test_surfaces_handoff_cli_refuses_unreviewed_paths(workspace_root: Path) -> None:
    runner = CliRunner()
    detect_result = runner.invoke(
        app,
        [
            "surfaces",
            "detect",
            str(workspace_root / "aoa-sdk"),
            "--phase",
            "ingress",
            "--intent-text",
            "verify recurring handoff proof",
            "--root",
            str(workspace_root / "aoa-sdk"),
            "--json",
        ],
    )
    detect_payload = json.loads(detect_result.stdout)

    result = runner.invoke(
        app,
        [
            "surfaces",
            "handoff",
            detect_payload["report_path"],
            "--session-ref",
            "session:test-surface-cli-review-gate",
            "--not-reviewed",
            "--root",
            str(workspace_root / "aoa-sdk"),
        ],
    )

    assert result.exit_code != 0
    assert "surface closeout handoff requires reviewed routes" in result.output
