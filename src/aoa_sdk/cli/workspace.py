from __future__ import annotations

import json
from pathlib import Path

import typer

from ..contracts.workspace import OSSkillProfileBootstrapReport
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
    control_plane = payload["control_plane"]
    typer.echo(
        "routing_bundle_root: "
        f"{control_plane['routing_bundle_root'] or 'none'} "
        f"[{control_plane['routing_bundle_root_source'] or 'unconfigured'}]"
    )
    typer.echo(
        "routing_source_lock: "
        f"{control_plane['routing_source_lock'] or 'package default'} "
        f"[{control_plane['routing_source_lock_source']}]"
    )

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
        "os-user-default",
        "--profile",
        help=(
            "Exact aoa-skills install profile to apply. The default invokes the "
            "owner OS installer; portable profiles remain explicit."
        ),
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
        help=(
            "Replace a conflicting target copy; portable mode uses its copy "
            "planner and OS mode passes the owner replace-unmanaged guard."
        ),
    ),
    check: bool = typer.Option(
        False,
        "--check",
        help="Verify current owner-install state when using the OS profile.",
    ),
    replace_unmanaged: bool = typer.Option(
        False,
        "--replace-unmanaged",
        help="Pass the owner installer collision replacement guard.",
    ),
    prune_managed: bool = typer.Option(
        False,
        "--prune-managed",
        help="Pass the owner installer stale-entry removal guard.",
    ),
    allow_dirty_source: bool = typer.Option(
        False,
        "--allow-dirty-source",
        help="Pass the owner installer dirty-source trial guard.",
    ),
    source_root: list[str] = typer.Option(
        [],
        "--source-root",
        metavar="OWNER=PATH",
        help="Override one owner checkout; repeat for each OWNER=PATH pair.",
    ),
    os_root: str | None = typer.Option(
        None,
        "--os-root",
        help="Override the federation root supplied to the owner installer.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    source_roots: dict[str, str] = {}
    for override in source_root:
        owner, separator, path = override.partition("=")
        if not separator or not owner or not path:
            raise typer.BadParameter(
                "source root must use OWNER=PATH syntax",
                param_hint="--source-root",
            )
        if owner in source_roots:
            raise typer.BadParameter(
                f"duplicate source-root owner {owner!r}",
                param_hint="--source-root",
            )
        source_roots[owner] = str(Path(path).expanduser())
    report = bootstrap_workspace(
        discovery_root,
        profile_name=profile_name,
        user_skill_root=user_skill_root,
        execute=execute,
        overwrite=overwrite,
        check=True if check else None,
        replace_unmanaged=replace_unmanaged,
        prune_managed=prune_managed,
        allow_dirty_source=allow_dirty_source,
        source_roots=source_roots or None,
        os_root=os_root,
    )
    payload = report.model_dump(mode="json")
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
    elif isinstance(report, OSSkillProfileBootstrapReport):
        typer.echo(f"discovery_root: {report.discovery_root}")
        typer.echo(f"source_repo_root: {report.source_repo_root}")
        typer.echo(f"profile: {report.profile_name}")
        typer.echo(f"owner_script: {report.owner_script}")
        typer.echo(f"install_root: {report.install_root}")
        typer.echo(f"execute_requested: {report.execute_requested}")
        typer.echo(f"check_requested: {report.check_requested}")
        typer.echo(f"execution_state: {report.execution_state}")
        typer.echo(f"verification_state: {report.verification_state}")
        typer.echo(f"executed: {report.executed}")
        typer.echo(f"verified: {report.verified}")
        typer.echo(f"exit_code: {report.exit_code if report.exit_code is not None else 'not-run'}")
        typer.echo("owner_payload: " + json.dumps(report.owner_payload, ensure_ascii=True))
        if report.diagnostics:
            typer.echo("diagnostics:")
            for diagnostic in report.diagnostics:
                typer.echo(f"  - {diagnostic}")
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
    if isinstance(report, OSSkillProfileBootstrapReport):
        if (
            (report.check_requested and report.verified is not True)
            or (report.execute_requested and report.verified is not True)
            or report.execution_state in {"failed", "unknown"}
        ):
            raise typer.Exit(code=1)
    elif not report.ready or (execute and report.verified is not True):
        raise typer.Exit(code=1)
