from __future__ import annotations

import json

from typer.testing import CliRunner

from aoa_sdk.cli.main import app


def test_skills_cli_exposes_only_passive_inspection_commands() -> None:
    result = CliRunner().invoke(app, ["skills", "--help"])

    assert result.exit_code == 0
    assert "inspect" in result.stdout
    assert "capability" in result.stdout
    for retired_name in (
        "detect",
        "dispatch",
        "activate",
        "deactivate",
        "enter",
        "guard",
    ):
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


def test_skills_cli_reads_v3_owner_home_without_install_or_projection_claim(
    skill_environment_fixture,
    owner_home_payload,
) -> None:
    fixture = skill_environment_fixture
    result = CliRunner().invoke(
        app,
        [
            "skills",
            "inspect",
            str(fixture.repo_root),
            "--user-skill-root",
            str(fixture.user_root),
            "--root",
            str(fixture.workspace_root),
            "--json",
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    source = next(
        root for root in payload["roots"] if root["root_kind"] == "owner-source"
    )
    assert source["source_schema_version"] == "aoa_skill_home_port_v3"
    assert source["exposures"][0]["mode"] == "profile-eligible"
    assert source["entries"][0]["status"] == "owner-source"
    assert not any(root["root_kind"] == "repo-projection" for root in payload["roots"])
