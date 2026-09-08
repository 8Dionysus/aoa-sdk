"""Transport the selected aoa-skills OS profile through its owner command."""

from __future__ import annotations

import json
from collections.abc import Mapping
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Callable

from ..contracts.workspace import (
    OS_PROFILE_MAX_DIAGNOSTIC_CHARS,
    OS_PROFILE_MAX_DIAGNOSTICS,
    OSSkillProfileBootstrapReport,
)
from .discovery import Workspace


OS_PROFILE_NAME = "os-user-default"
OWNER_INSTALLER_RELATIVE_PATH = Path("scripts/install_os_skill_profile.py")
OWNER_PROFILE_CONFIG_RELATIVE_PATH = Path("config/os_skill_profiles.json")

_CLAIM_LIMIT = (
    "owner installer output is transported as an opaque payload; SDK transport "
    "state does not establish skill readiness, admission, routing, or outcomes"
)


def bootstrap_os_profile(
    discovery_root: str | Path,
    *,
    profile_name: str = OS_PROFILE_NAME,
    user_skill_root: str | Path | None = None,
    execute: bool = False,
    check: bool | None = None,
    overwrite: bool = False,
    replace_unmanaged: bool = False,
    prune_managed: bool = False,
    allow_dirty_source: bool = False,
    source_roots: Mapping[str, str | Path] | None = None,
    os_root: str | Path | None = None,
    timeout_seconds: float | None = 120.0,
    workspace: Workspace | None = None,
    runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
) -> OSSkillProfileBootstrapReport:
    """Run the selected OS profile owner installer and preserve its payload.

    The SDK discovers checkouts and supplies them as explicit owner-root
    overrides.  The owner command retains profile validation, dirty-source,
    collision, owner-link, and stale-entry guards.  The default call requests
    the owner's read-only plan; ``check=True`` requests an installed-state
    verification. Execute and check are mutually exclusive because the owner
    CLI uses one action flag per invocation.
    """

    resolved_discovery_root = Path(discovery_root).expanduser().resolve(strict=False)
    current_workspace = workspace or Workspace.discover(resolved_discovery_root)
    discovered_roots = {
        repo: path.resolve(strict=False)
        for repo, path in current_workspace.repo_roots.items()
    }
    explicit_roots = _resolve_source_roots(source_roots)
    discovered_roots.update(explicit_roots)

    source_repo_root = discovered_roots.get("aoa-skills")
    if source_repo_root is None:
        source_repo_root = current_workspace.repo_roots.get("aoa-skills")
    if source_repo_root is None:
        source_repo_root = resolved_discovery_root
    source_repo_root = source_repo_root.resolve(strict=False)

    target_root = _resolve_target_root(user_skill_root)
    resolved_os_root = (
        Path(os_root).expanduser().resolve(strict=False)
        if os_root is not None
        else current_workspace.federation_root.resolve(strict=False)
    )
    owner_script = source_repo_root / OWNER_INSTALLER_RELATIVE_PATH
    config_path = source_repo_root / OWNER_PROFILE_CONFIG_RELATIVE_PATH
    command = _build_owner_command(
        owner_script=owner_script,
        config_path=config_path,
        profile_name=profile_name,
        os_root=resolved_os_root,
        source_roots=discovered_roots,
        target_root=target_root,
        execute=execute,
        check=check,
        overwrite=overwrite,
        replace_unmanaged=replace_unmanaged,
        prune_managed=prune_managed,
        allow_dirty_source=allow_dirty_source,
    )
    check_requested = bool(check)

    base = {
        "discovery_root": str(resolved_discovery_root),
        "source_repo_root": str(source_repo_root),
        "profile_name": profile_name,
        "install_root": str(target_root),
        "target_scope_root": str(target_root),
        "owner_script": str(owner_script),
        "owner_command": command,
        "source_roots": {
            repo: str(path) for repo, path in sorted(discovered_roots.items())
        },
        "execute_requested": execute,
        "check_requested": check_requested,
        "claim_limit": _CLAIM_LIMIT,
    }

    if profile_name != OS_PROFILE_NAME:
        return _report(
            **base,
            execution_state="unknown",
            verification_state="unknown",
            executed=None,
            verified=None,
            diagnostics=[
                f"SDK OS profile adapter accepts only {OS_PROFILE_NAME!r}; "
                f"received {profile_name!r}"
            ],
        )

    if execute and check_requested:
        return _report(
            **base,
            execution_state="unknown",
            verification_state="unknown",
            executed=None,
            verified=None,
            diagnostics=["owner execute and check actions are mutually exclusive"],
        )

    if not owner_script.is_file():
        return _report(
            **base,
            execution_state="unknown",
            verification_state="unknown",
            executed=None,
            verified=None,
            diagnostics=[f"owner installer is missing: {owner_script}"],
        )

    if not config_path.is_file():
        return _report(
            **base,
            execution_state="unknown",
            verification_state="unknown",
            executed=None,
            verified=None,
            diagnostics=[f"owner OS profile config is missing: {config_path}"],
        )

    try:
        completed = _run_owner_command(
            command,
            cwd=source_repo_root,
            timeout_seconds=timeout_seconds,
            runner=runner or subprocess.run,
        )
    except subprocess.TimeoutExpired as exc:
        diagnostics = _stream_diagnostics(
            "owner timeout",
            _as_text(exc.stderr),
        )
        diagnostics.append(
            f"owner installer exceeded timeout of {timeout_seconds:g} seconds"
            if timeout_seconds is not None
            else "owner installer timed out"
        )
        return _report(
            **base,
            execution_state="unknown",
            verification_state="unknown",
            executed=None,
            verified=None,
            diagnostics=_bounded_diagnostics(diagnostics),
        )
    except OSError as exc:
        return _report(
            **base,
            execution_state="unknown",
            verification_state="unknown",
            executed=None,
            verified=None,
            diagnostics=[f"owner installer could not start: {exc}"],
        )

    stdout = _as_text(completed.stdout)
    stderr = _as_text(completed.stderr)
    owner_payload, diagnostics, payload_valid = _decode_owner_payload(stdout)
    diagnostics.extend(_stream_diagnostics("owner stderr", stderr))
    if completed.returncode != 0 and not diagnostics:
        diagnostics.append(f"owner installer exited with code {completed.returncode}")

    if execute:
        if completed.returncode == 0 and payload_valid:
            execution_state = "succeeded"
            executed: bool | None = True
            verification_state = "passed"
            verified: bool | None = True
        elif completed.returncode == 0:
            execution_state = "unknown"
            executed = None
            verification_state = "unknown"
            verified = None
        else:
            execution_state = "failed"
            executed = None
            verification_state = "unknown"
            verified = None
    else:
        if completed.returncode != 0:
            execution_state = "failed"
            executed = None
        elif payload_valid:
            execution_state = "not-requested"
            executed = False
        else:
            execution_state = "unknown"
            executed = None
        if check_requested:
            if completed.returncode != 0:
                verification_state = "failed"
                verified = False
            elif payload_valid:
                verification_state = "passed"
                verified = True
            else:
                verification_state = "unknown"
                verified = None
        elif payload_valid and completed.returncode == 0:
            verification_state = "not-requested"
            verified = None
        else:
            verification_state = "unknown"
            verified = None

    return _report(
        **base,
        execution_state=execution_state,
        verification_state=verification_state,
        executed=executed,
        verified=verified,
        exit_code=completed.returncode,
        owner_payload=owner_payload,
        diagnostics=_bounded_diagnostics(diagnostics),
    )


def _resolve_target_root(explicit_root: str | Path | None) -> Path:
    if explicit_root is None:
        codex_home = os.environ.get("CODEX_HOME")
        raw = (
            Path(codex_home).expanduser() / "skills"
            if codex_home
            else Path.home() / ".codex" / "skills"
        )
    else:
        raw = Path(explicit_root).expanduser()
    absolute = raw.absolute()
    # Preserve an explicit symlink root for the owner command's safety check;
    # canonicalize ordinary paths so reports and argv remain deterministic.
    if absolute.is_symlink():
        return absolute
    return absolute.resolve(strict=False)


def _resolve_source_roots(
    source_roots: Mapping[str, str | Path] | None,
) -> dict[str, Path]:
    if source_roots is None:
        return {}
    resolved: dict[str, Path] = {}
    for repo, root in source_roots.items():
        if not isinstance(repo, str) or not repo:
            raise ValueError("source root owner names must be non-empty strings")
        path = Path(root).expanduser().resolve(strict=False)
        resolved[repo] = path
    return resolved


def _build_owner_command(
    *,
    owner_script: Path,
    config_path: Path,
    profile_name: str,
    os_root: Path,
    source_roots: Mapping[str, Path],
    target_root: Path,
    execute: bool,
    check: bool | None,
    overwrite: bool,
    replace_unmanaged: bool,
    prune_managed: bool,
    allow_dirty_source: bool,
) -> list[str]:
    command = [
        sys.executable,
        "-B",
        str(owner_script),
        "--repo-root",
        str(owner_script.parent.parent),
        "--config",
        str(config_path),
        "--profile",
        profile_name,
        "--os-root",
        str(os_root),
    ]
    for repo, path in sorted(source_roots.items()):
        command.extend(("--source-root", f"{repo}={path}"))
    command.extend(("--dest-root", str(target_root)))
    if execute:
        command.append("--execute")
    elif check:
        command.append("--check")
    if overwrite or replace_unmanaged:
        command.append("--replace-unmanaged")
    if prune_managed:
        command.append("--prune-managed")
    if allow_dirty_source:
        command.append("--allow-dirty-source")
    command.extend(("--format", "json"))
    return command


def _run_owner_command(
    command: list[str],
    *,
    cwd: Path,
    timeout_seconds: float | None,
    runner: Callable[..., subprocess.CompletedProcess[str]],
) -> subprocess.CompletedProcess[str]:
    kwargs: dict[str, Any] = {
        "cwd": cwd,
        "check": False,
        "capture_output": True,
        "text": True,
        "shell": False,
    }
    if timeout_seconds is not None:
        kwargs["timeout"] = timeout_seconds
    return runner(command, **kwargs)


def _decode_owner_payload(stdout: str) -> tuple[dict[str, Any], list[str], bool]:
    if not stdout.strip():
        return {}, ["owner stdout did not contain a JSON payload"], False
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        return {}, [
            _bounded_text(
                f"owner stdout is not JSON: {exc.msg} at character {exc.pos}; "
                f"output={stdout.strip()}"
            )
        ], False
    if not isinstance(payload, dict):
        return {}, [
            _bounded_text(
                f"owner stdout JSON must be an object; received {type(payload).__name__}"
            )
        ], False
    return payload, [], True


def _stream_diagnostics(prefix: str, value: str) -> list[str]:
    if not value.strip():
        return []
    lines = [line.strip() for line in value.splitlines() if line.strip()]
    if not lines:
        lines = [value.strip()]
    diagnostics = [_bounded_text(f"{prefix}: {line}") for line in lines]
    if len(lines) > OS_PROFILE_MAX_DIAGNOSTICS:
        diagnostics.append(f"{prefix}: [additional output truncated]")
    return diagnostics


def _bounded_diagnostics(values: list[str]) -> list[str]:
    bounded: list[str] = []
    for value in values:
        if len(bounded) >= OS_PROFILE_MAX_DIAGNOSTICS:
            break
        bounded.append(_bounded_text(value))
    if len(values) > OS_PROFILE_MAX_DIAGNOSTICS and bounded:
        bounded[-1] = _bounded_text(bounded[-1] + " [diagnostics truncated]")
    return bounded


def _bounded_text(value: str) -> str:
    if len(value) <= OS_PROFILE_MAX_DIAGNOSTIC_CHARS:
        return value
    suffix = "... [truncated]"
    return value[: OS_PROFILE_MAX_DIAGNOSTIC_CHARS - len(suffix)] + suffix


def _as_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _report(**values: Any) -> OSSkillProfileBootstrapReport:
    return OSSkillProfileBootstrapReport(**values)


__all__ = ["OS_PROFILE_NAME", "bootstrap_os_profile"]
