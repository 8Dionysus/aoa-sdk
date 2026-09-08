from __future__ import annotations

import json
from pathlib import Path
import sys
from subprocess import CompletedProcess

import pytest
from typer.testing import CliRunner

from aoa_sdk.cli.main import app
from aoa_sdk.workspace import os_profile
from aoa_sdk.workspace.bootstrap import bootstrap_workspace
from aoa_sdk.workspace.os_profile import bootstrap_os_profile


OWNER_SCRIPT = Path("scripts/install_os_skill_profile.py")
OWNER_CONFIG = Path("config/os_skill_profiles.json")
def _owner_inputs(workspace_root: Path) -> None:
    owner_root = workspace_root / "aoa-skills"
    (owner_root / OWNER_SCRIPT.parent).mkdir(parents=True, exist_ok=True)
    (owner_root / OWNER_CONFIG.parent).mkdir(parents=True, exist_ok=True)
    (owner_root / OWNER_SCRIPT).write_text("# fake owner entrypoint\n", encoding="utf-8")
    (owner_root / OWNER_CONFIG).write_text("{}\n", encoding="utf-8")


def test_os_profile_transport_uses_explicit_argv_and_opaque_payload(
    workspace_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _owner_inputs(workspace_root)
    calls: list[tuple[list[str], dict[str, object]]] = []

    def fake_runner(command: list[str], **kwargs: object) -> CompletedProcess[str]:
        calls.append((command, kwargs))
        return CompletedProcess(
            command,
            0,
            stdout=json.dumps({"schema_version": "owner-plan", "skills": [{"name": "opaque"}]}),
            stderr="",
        )

    target = workspace_root / "disposable-codex-skills"
    report = bootstrap_os_profile(
        workspace_root / "aoa-sdk",
        user_skill_root=target,
        source_roots={"explicit-owner": workspace_root / "aoa-evals"},
        runner=fake_runner,
    )

    assert len(calls) == 1
    command, kwargs = calls[0]
    assert command[0] == sys.executable
    assert command[1] == "-B"
    assert command[2].endswith("scripts/install_os_skill_profile.py")
    assert command[command.index("--profile") + 1] == "os-user-default"
    assert command[command.index("--dest-root") + 1] == str(target.resolve())
    assert "--check" not in command
    assert "--execute" not in command
    assert "--replace-unmanaged" not in command
    assert "--prune-managed" not in command
    assert "--owner-repo" not in command
    assert kwargs["shell"] is False
    assert kwargs["check"] is False
    assert kwargs["capture_output"] is True
    assert report.owner_payload == {
        "schema_version": "owner-plan",
        "skills": [{"name": "opaque"}],
    }
    assert report.exit_code == 0
    assert report.execute_requested is False
    assert report.check_requested is False
    assert report.executed is False
    assert report.verified is None
    assert report.execution_state == "not-requested"
    assert report.verification_state == "not-requested"
    payload = report.model_dump(mode="json")
    assert "ready" not in payload
    assert "admitted" not in payload


def test_os_profile_preserves_symlink_destination_for_owner_guard(
    workspace_root: Path,
) -> None:
    _owner_inputs(workspace_root)
    actual = workspace_root / "actual-codex-skills"
    actual.mkdir()
    alias = workspace_root / "alias-codex-skills"
    alias.symlink_to(actual, target_is_directory=True)

    def fake_runner(command: list[str], **kwargs: object) -> CompletedProcess[str]:
        return CompletedProcess(command, 0, stdout=json.dumps({"plan": "opaque"}), stderr="")

    report = bootstrap_os_profile(
        workspace_root / "aoa-sdk",
        user_skill_root=alias,
        runner=fake_runner,
    )

    assert report.owner_command[report.owner_command.index("--dest-root") + 1] == str(alias.absolute())


def test_os_profile_transport_bounds_owner_diagnostics(
    workspace_root: Path,
) -> None:
    _owner_inputs(workspace_root)

    def fake_runner(command: list[str], **kwargs: object) -> CompletedProcess[str]:
        return CompletedProcess(
            command,
            7,
            stdout="not-json\n" + ("x" * 5000),
            stderr="\n".join(f"owner-error-{index}" for index in range(40)),
        )

    report = bootstrap_os_profile(
        workspace_root / "aoa-sdk",
        user_skill_root=workspace_root / "disposable-codex-skills",
        check=True,
        runner=fake_runner,
    )

    assert report.exit_code == 7
    assert report.owner_payload == {}
    assert report.verified is False
    assert len(report.diagnostics) <= 8
    assert all(len(item) <= 2048 for item in report.diagnostics)
    assert any("owner stdout is not JSON" in item for item in report.diagnostics)


@pytest.mark.parametrize("stdout", ["", "[]", "not-json"])
def test_os_profile_rc0_without_object_payload_is_unknown(
    workspace_root: Path,
    stdout: str,
) -> None:
    _owner_inputs(workspace_root)

    def fake_runner(command: list[str], **kwargs: object) -> CompletedProcess[str]:
        return CompletedProcess(command, 0, stdout=stdout, stderr="")

    report = bootstrap_os_profile(
        workspace_root / "aoa-sdk",
        user_skill_root=workspace_root / "disposable-codex-skills",
        runner=fake_runner,
    )

    assert report.exit_code == 0
    assert report.owner_payload == {}
    assert report.execution_state == "unknown"
    assert report.verification_state == "unknown"
    assert report.verified is None
    assert report.diagnostics


def test_workspace_bootstrap_cli_passes_owner_overrides_and_fails_unknown_payload(
    workspace_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _owner_inputs(workspace_root)
    calls: list[tuple[list[str], dict[str, object]]] = []

    def fake_runner(command: list[str], **kwargs: object) -> CompletedProcess[str]:
        calls.append((command, kwargs))
        return CompletedProcess(command, 0, stdout="[]", stderr="")

    monkeypatch.setattr(os_profile.subprocess, "run", fake_runner)
    target = workspace_root / "disposable-codex-skills"
    result = CliRunner().invoke(
        app,
        [
            "workspace",
            "bootstrap",
            str(workspace_root / "aoa-sdk"),
            "--user-skill-root",
            str(target),
            "--source-root",
            f"aoa-evals={workspace_root / 'aoa-evals'}",
            "--os-root",
            str(workspace_root / "federation"),
            "--json",
        ],
    )

    assert result.exit_code == 1, result.output
    payload = json.loads(result.stdout)
    assert payload["execution_state"] == "unknown"
    assert payload["verified"] is None
    assert "--check" not in calls[0][0]
    assert "--os-root" in calls[0][0]
    assert calls[0][0][calls[0][0].index("--os-root") + 1] == str(
        (workspace_root / "federation").resolve()
    )
    assert f"aoa-evals={(workspace_root / 'aoa-evals').resolve()}" in calls[0][0]
    assert not target.exists()


def test_legacy_user_profile_returns_migration_hint_without_alias(
    workspace_root: Path,
) -> None:
    report = bootstrap_workspace(
        workspace_root / "aoa-sdk",
        profile_name="user-default",
        user_skill_root=workspace_root / "disposable-codex-skills",
        execute=True,
    )

    assert report.ready is True
    assert report.executed is True
    assert report.steps == [] or report.steps[0].skill_name == "aoa-decision"
    assert any("No profile alias was applied" in warning for warning in report.warnings)


@pytest.mark.parametrize(
    ("kwargs", "option"),
    [
        ({"check": True}, "--check"),
        ({"replace_unmanaged": True}, "--replace-unmanaged"),
        ({"prune_managed": True}, "--prune-managed"),
        ({"allow_dirty_source": True}, "--allow-dirty-source"),
        ({"source_roots": {"owner": Path("owner")}}, "--source-root"),
        ({"os_root": Path("federation")}, "--os-root"),
    ],
)
def test_portable_profile_rejects_os_installer_options(
    workspace_root: Path,
    kwargs: dict[str, object],
    option: str,
) -> None:
    with pytest.raises(ValueError, match=rf"{option}.*os-user-default"):
        bootstrap_workspace(
            workspace_root / "aoa-sdk",
            profile_name="user-default",
            **kwargs,
        )
