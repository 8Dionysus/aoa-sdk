import json
from pathlib import Path

from typer.testing import CliRunner

from aoa_sdk.cli.main import app
from aoa_sdk.workspace.roots import WORKSPACE_REQUIRED_REPOS


def _seed_bootstrap_workspace(workspace_root: Path) -> None:
    for repo in WORKSPACE_REQUIRED_REPOS:
        repo_root = workspace_root / repo
        repo_root.mkdir(parents=True, exist_ok=True)
        readme = repo_root / "README.md"
        if not readme.exists():
            readme.write_text(f"# {repo}\n", encoding="utf-8")

    foundation_path = workspace_root / "aoa-skills" / "generated" / "project_foundation_profile.min.json"
    foundation = json.loads(foundation_path.read_text(encoding="utf-8"))
    skills_root = workspace_root / "aoa-skills" / ".agents" / "skills"
    for skill_name in foundation["skills"]:
        skill_dir = skills_root / skill_name
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            skill_file.write_text(f"# {skill_name}\n", encoding="utf-8")


def test_workspace_bootstrap_reports_missing_repos(workspace_root: Path) -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        ["workspace", "bootstrap", str(workspace_root), "--json"],
    )

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["missing_required_repos"] == ["Tree-of-Sophia", "Dionysus"]
    assert payload["ready"] is False
    assert payload["executed"] is False


def test_workspace_bootstrap_execute_installs_foundation_and_agents(workspace_root: Path) -> None:
    _seed_bootstrap_workspace(workspace_root)
    runner = CliRunner()

    result = runner.invoke(
        app,
        ["workspace", "bootstrap", str(workspace_root), "--execute", "--json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ready"] is True
    assert payload["executed"] is True
    assert payload["verified"] is True
    assert payload["agents_file"]["action"] == "write"
    assert (workspace_root / "AGENTS.md").exists()
    assert (workspace_root / ".agents" / "skills" / "aoa-change-protocol").is_symlink()
    assert (workspace_root / ".agents" / "skills" / "aoa-checkpoint-closeout-bridge").is_symlink()


def test_workspace_bootstrap_rejects_unknown_install_mode(workspace_root: Path) -> None:
    _seed_bootstrap_workspace(workspace_root)
    runner = CliRunner()

    result = runner.invoke(
        app,
        ["workspace", "bootstrap", str(workspace_root), "--mode", "symink", "--json"],
    )

    assert result.exit_code != 0
    assert "Invalid value" in result.output


def test_workspace_bootstrap_copy_mode_replaces_existing_skill_symlink(
    workspace_root: Path,
) -> None:
    _seed_bootstrap_workspace(workspace_root)
    runner = CliRunner()

    result = runner.invoke(
        app,
        ["workspace", "bootstrap", str(workspace_root), "--execute", "--json"],
    )
    assert result.exit_code == 0, result.output

    result = runner.invoke(
        app,
        [
            "workspace",
            "bootstrap",
            str(workspace_root),
            "--mode",
            "copy",
            "--execute",
            "--overwrite",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    installed_skill = workspace_root / ".agents" / "skills" / "aoa-change-protocol"
    assert installed_skill.is_dir()
    assert not installed_skill.is_symlink()
