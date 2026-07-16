from __future__ import annotations

import json

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
    discovery_root: str = typer.Argument(
        ...,
        help="Workspace or repository path used to discover the aoa-skills owner checkout.",
    ),
    profile_name: str = typer.Option(
        "user-default",
        "--profile",
        help="Exact aoa-skills install profile to apply.",
    ),
    user_skill_root: str | None = typer.Option(
        None,
        "--user-skill-root",
        help="Override the user skill root; otherwise use CODEX_HOME/skills or ~/.codex/skills.",
    ),
    execute: bool = typer.Option(False, "--execute", help="Apply the bootstrap plan instead of only reporting it."),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Replace a conflicting target copy when it differs from the owner export.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    report = bootstrap_workspace(
        discovery_root,
        profile_name=profile_name,
        user_skill_root=user_skill_root,
        execute=execute,
        overwrite=overwrite,
    )
    payload = report.model_dump(mode="json")
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
    else:
        typer.echo(f"discovery_root: {report.discovery_root}")
        typer.echo(f"source_repo_root: {report.source_repo_root}")
        typer.echo(f"profile: {report.profile_name} [{report.profile_scope}]")
        typer.echo(f"install_root: {report.install_root}")
        typer.echo(f"ready: {report.ready}")
        typer.echo(f"executed: {report.executed}")
        typer.echo(f"verified: {report.verified if report.verified is not None else 'not-run'}")
        typer.echo("steps:")
        for step in report.steps:
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
