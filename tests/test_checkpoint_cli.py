import json
from pathlib import Path

from typer.testing import CliRunner

from aoa_sdk.cli.main import app


def test_surfaces_detect_cli_supports_checkpoint_phase(workspace_root: Path) -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "surfaces",
            "detect",
            str(workspace_root / "aoa-sdk"),
            "--phase",
            "checkpoint",
            "--checkpoint-kind",
            "commit",
            "--intent-text",
            "recurring workflow needs better handoff proof and recall",
            "--root",
            str(workspace_root / "aoa-sdk"),
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["report"]["phase"] == "checkpoint"
    assert payload["report"]["checkpoint_kind"] == "commit"
    assert payload["report"]["checkpoint_should_capture"] is True


def test_checkpoint_cli_append_status_and_promote_handoff(workspace_root: Path) -> None:
    runner = CliRunner()

    append = runner.invoke(
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
    assert append.exit_code == 0

    append_two = runner.invoke(
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
    assert append_two.exit_code == 0

    status = runner.invoke(
        app,
        [
            "checkpoint",
            "status",
            str(workspace_root / "aoa-sdk"),
            "--root",
            str(workspace_root / "aoa-sdk"),
            "--json",
        ],
    )
    promote = runner.invoke(
        app,
        [
            "checkpoint",
            "promote",
            str(workspace_root / "aoa-sdk"),
            "--target",
            "harvest-handoff",
            "--root",
            str(workspace_root / "aoa-sdk"),
            "--json",
        ],
    )

    assert status.exit_code == 0
    assert promote.exit_code == 0
    status_payload = json.loads(status.stdout)
    promote_payload = json.loads(promote.stdout)
    handoff_path = workspace_root / "aoa-sdk" / ".aoa" / "session-growth" / "current" / "aoa-sdk" / "harvest-handoff.json"
    assert status_payload["state"] == "reviewable"
    assert promote_payload["target"] == "harvest-handoff"
    assert handoff_path.exists()


def test_skills_guard_can_auto_append_checkpoint_note(workspace_root: Path, install_host_skills) -> None:
    install_host_skills(workspace_root, ["aoa-change-protocol"])
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "skills",
            "guard",
            str(workspace_root / "aoa-sdk"),
            "--intent-text",
            "plan verify a bounded change",
            "--mutation-surface",
            "code",
            "--checkpoint-kind",
            "verify_green",
            "--root",
            str(workspace_root),
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["checkpoint_note"]["state"] in {"collecting", "reviewable"}
    note_path = workspace_root / "aoa-sdk" / ".aoa" / "session-growth" / "current" / "aoa-sdk" / "checkpoint-note.json"
    assert note_path.exists()


def test_surfaces_detect_cli_can_append_checkpoint_note(workspace_root: Path) -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "surfaces",
            "detect",
            str(workspace_root / "aoa-sdk"),
            "--phase",
            "checkpoint",
            "--checkpoint-kind",
            "commit",
            "--append-note",
            "--intent-text",
            "recurring workflow needs better handoff proof and recall",
            "--root",
            str(workspace_root / "aoa-sdk"),
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["report"]["phase"] == "checkpoint"
    assert payload["checkpoint_note"]["promotion_recommendation"] in {
        "local_note",
        "dionysus_note",
        "harvest_handoff",
    }
