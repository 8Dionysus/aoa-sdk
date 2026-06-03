from __future__ import annotations

import json
from typing import Literal

import typer

from ..workspace.bootstrap import bootstrap_workspace
from ..workspace.discovery import Workspace
from ..workspace.roots import KNOWN_REPOS
from .common import _workspace_payload


workspace_app = typer.Typer(help="Inspect workspace topology")


@workspace_app.command("inspect")
def workspace_inspect(
    root: str = typer.Argument("."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    workspace = Workspace.discover(root)
    payload = _workspace_payload(workspace)

    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return

    typer.echo(f"root: {payload['root']}")
    typer.echo(f"federation_root: {payload['federation_root']}")
    typer.echo(f"federation_root_source: {payload['federation_root_source']}")
    typer.echo(f"manifest: {payload['manifest'] or 'none'}")

    for repo in KNOWN_REPOS:
        repo_payload = payload["repos"][repo]
        path = repo_payload["path"]
        origin = repo_payload["origin"]
        if path is None:
            typer.echo(f"{repo}: missing")
            continue
        typer.echo(f"{repo}: {path} [{origin}]")


@workspace_app.command("bootstrap")
def workspace_bootstrap(
    target_root: str = typer.Argument(..., help="Sibling-workspace root that already contains the public repos."),
    mode: Literal["symlink", "copy"] = typer.Option("symlink", "--mode", help="Foundation install mode: symlink or copy."),
    execute: bool = typer.Option(False, "--execute", help="Apply the bootstrap plan instead of only reporting it."),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Replace conflicting foundation installs when the current target does not match the source export.",
    ),
    write_agents: bool = typer.Option(
        True,
        "--write-agents/--no-write-agents",
        help="Write one root-level AGENTS.md when it is missing.",
    ),
    overwrite_agents: bool = typer.Option(
        False,
        "--overwrite-agents",
        help="Replace an existing root-level AGENTS.md with the canonical workspace guidance.",
    ),
    allow_partial: bool = typer.Option(
        False,
        "--allow-partial",
        help="Allow bootstrap planning even when the canonical sibling workspace is incomplete.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    report = bootstrap_workspace(
        target_root,
        mode=mode,
        execute=execute,
        overwrite=overwrite,
        write_agents=write_agents,
        overwrite_agents=overwrite_agents,
        strict_layout=not allow_partial,
    )
    payload = report.model_dump(mode="json")
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
    else:
        typer.echo(f"workspace_root: {report.workspace_root}")
        typer.echo(f"foundation_id: {report.foundation_id}")
        typer.echo(f"profile: {report.canonical_install_profile}")
        typer.echo(f"ready: {report.ready}")
        typer.echo(f"executed: {report.executed}")
        typer.echo(f"verified: {report.verified if report.verified is not None else 'not-run'}")
        typer.echo(f"missing_required_repos: {', '.join(report.missing_required_repos) or 'none'}")
        if report.agents_file is not None:
            typer.echo(f"root_agents: {report.agents_file.path} [{report.agents_file.action}]")
        typer.echo("install_steps:")
        for step in report.install_steps:
            typer.echo(f"  - {step.skill_name}: {step.action}")
        if report.warnings:
            typer.echo("warnings:")
            for warning in report.warnings:
                typer.echo(f"  - {warning}")
        if report.blockers:
            typer.echo("blockers:")
            for blocker in report.blockers:
                typer.echo(f"  - {blocker}")
    if not report.ready or (execute and report.verified is not True):
        raise typer.Exit(code=1)
