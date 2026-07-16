from __future__ import annotations

import json

from typer.testing import CliRunner

from aoa_sdk.cli.main import app


def test_skills_cli_exposes_only_passive_inspection_commands() -> None:
    result = CliRunner().invoke(app, ["skills", "--help"])

    assert result.exit_code == 0
    assert "inspect" in result.stdout
    assert "capability" in result.stdout
    for retired_name in ("detect", "dispatch", "activate", "deactivate", "enter", "guard"):
        assert retired_name not in result.stdout


def test_skills_cli_reports_scopes_and_exact_capability(
    skill_environment_fixture,
) -> None:
    runner = CliRunner()
    inspected = runner.invoke(
        app,
        [
            "skills",
            "inspect",
            str(skill_environment_fixture.repo_root),
            "--user-skill-root",
            str(skill_environment_fixture.user_root),
            "--root",
            str(skill_environment_fixture.workspace_root),
            "--json",
        ],
    )

    assert inspected.exit_code == 0
    report = json.loads(inspected.stdout)
    assert [root["root_kind"] for root in report["roots"]] == [
        "source-export",
        "user",
        "repo-projection",
        "workspace-legacy",
    ]

    capability = runner.invoke(
        app,
        [
            "skills",
            "capability",
            "workflow.operations.checkpoint-closeout",
            "--root",
            str(skill_environment_fixture.workspace_root),
            "--json",
        ],
    )
    assert capability.exit_code == 0
    payload = json.loads(capability.stdout)
    assert payload["node"]["id"] == "workflow.operations.checkpoint-closeout"
    assert payload["node"]["owner"]["repo"] == "aoa-playbooks"
    assert payload["outgoing"][0]["kind"] == "primary-parent"


def test_skills_cli_rejects_unknown_capability(skill_environment_fixture) -> None:
    result = CliRunner().invoke(
        app,
        [
            "skills",
            "capability",
            "missing.capability",
            "--root",
            str(skill_environment_fixture.workspace_root),
            "--json",
        ],
    )

    assert result.exit_code == 1
    assert "not present in the owner graph" in result.stderr
