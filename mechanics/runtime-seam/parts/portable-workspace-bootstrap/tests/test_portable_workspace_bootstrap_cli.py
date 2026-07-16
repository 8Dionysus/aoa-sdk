from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from aoa_sdk.cli.main import app


def _invoke_bootstrap(
    workspace_root: Path,
    user_root: Path,
    *extra: str,
):
    return CliRunner().invoke(
        app,
        [
            "workspace",
            "bootstrap",
            str(workspace_root),
            "--user-skill-root",
            str(user_root),
            *extra,
            "--json",
        ],
    )


def _tree_files(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_workspace_bootstrap_dry_run_plans_exact_user_profile_without_mutation(
    workspace_root: Path,
) -> None:
    user_root = workspace_root / "host-skills"

    result = _invoke_bootstrap(workspace_root, user_root)

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["profile_name"] == "user-default"
    assert payload["profile_scope"] == "user"
    assert payload["install_mode"] == "copy"
    assert payload["ready"] is True
    assert payload["executed"] is False
    assert payload["verified"] is None
    assert [(step["skill_name"], step["action"]) for step in payload["steps"]] == [
        ("aoa-decision", "create")
    ]
    assert not user_root.exists()
    assert not (workspace_root / "AGENTS.md").exists()
    assert not (workspace_root / ".agents").exists()


def test_workspace_bootstrap_execute_copies_and_verifies_the_full_owner_tree(
    workspace_root: Path,
) -> None:
    user_root = workspace_root / "host-skills"
    source = workspace_root / "aoa-skills" / ".agents" / "skills" / "aoa-decision"

    result = _invoke_bootstrap(workspace_root, user_root, "--execute")

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    installed = user_root / "aoa-decision"
    assert payload["ready"] is True
    assert payload["executed"] is True
    assert payload["verified"] is True
    assert installed.is_dir()
    assert not installed.is_symlink()
    assert _tree_files(installed) == _tree_files(source)
    assert not (workspace_root / "AGENTS.md").exists()
    assert not (workspace_root / ".agents").exists()


def test_workspace_bootstrap_preserves_conflict_until_explicit_overwrite(
    workspace_root: Path,
) -> None:
    user_root = workspace_root / "host-skills"
    installed = user_root / "aoa-decision"
    source = workspace_root / "aoa-skills" / ".agents" / "skills" / "aoa-decision"
    first = _invoke_bootstrap(workspace_root, user_root, "--execute")
    assert first.exit_code == 0, first.output
    (installed / "SKILL.md").write_text("# host drift\n", encoding="utf-8")

    conflict = _invoke_bootstrap(workspace_root, user_root, "--execute")

    assert conflict.exit_code == 1, conflict.output
    conflict_payload = json.loads(conflict.stdout)
    assert conflict_payload["ready"] is False
    assert conflict_payload["executed"] is False
    assert conflict_payload["verified"] is None
    assert conflict_payload["steps"][0]["action"] == "conflict"
    assert "aoa-decision: conflict" in conflict_payload["blockers"]
    assert (installed / "SKILL.md").read_text(encoding="utf-8") == "# host drift\n"

    replaced = _invoke_bootstrap(
        workspace_root,
        user_root,
        "--execute",
        "--overwrite",
    )

    assert replaced.exit_code == 0, replaced.output
    replaced_payload = json.loads(replaced.stdout)
    assert replaced_payload["steps"][0]["action"] == "replace"
    assert replaced_payload["verified"] is True
    assert _tree_files(installed) == _tree_files(source)


def test_workspace_bootstrap_rejects_repo_profile_without_projection_plan(
    workspace_root: Path,
) -> None:
    user_root = workspace_root / "host-skills"

    result = _invoke_bootstrap(
        workspace_root,
        user_root,
        "--profile",
        "repo-default",
        "--execute",
    )

    assert result.exit_code == 1, result.output
    payload = json.loads(result.stdout)
    assert payload["profile_scope"] == "repo"
    assert payload["ready"] is False
    assert payload["executed"] is False
    assert payload["verified"] is None
    assert payload["steps"] == []
    assert any("owner builder" in blocker for blocker in payload["blockers"])
    assert not user_root.exists()
    assert not (workspace_root / ".agents").exists()


def test_workspace_bootstrap_reports_legacy_workspace_copy_without_touching_it(
    workspace_root: Path,
) -> None:
    user_root = workspace_root / "host-skills"
    legacy = workspace_root / ".agents" / "skills" / "legacy-skill" / "SKILL.md"
    legacy.parent.mkdir(parents=True)
    legacy.write_text("# legacy\n", encoding="utf-8")

    result = _invoke_bootstrap(workspace_root, user_root, "--execute")

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["legacy_workspace_root"] == str(workspace_root / ".agents" / "skills")
    assert any("left untouched" in warning for warning in payload["warnings"])
    assert legacy.read_text(encoding="utf-8") == "# legacy\n"
