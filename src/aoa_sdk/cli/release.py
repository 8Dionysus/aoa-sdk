from __future__ import annotations

import json
from pathlib import Path

import typer

from ..api import AoASDK
from ..release.api import ReleaseAuditPhase
from .rendering import _print_release_audit, _print_release_publish


release_app = typer.Typer(help="Audit and publish bounded repository releases")


def _release_sdk(root: str) -> AoASDK:
    candidate = Path(root).expanduser().resolve()
    sdk_root = candidate if (candidate / "src" / "aoa_sdk").exists() else candidate / "aoa-sdk"
    if not (sdk_root / "src" / "aoa_sdk").exists():
        raise typer.BadParameter(f"Could not locate aoa-sdk under {candidate}")
    return AoASDK.from_workspace(sdk_root)

@release_app.command("audit")
def release_audit(
    workspace_root: str = typer.Argument(..., help="Workspace root containing aoa-sdk and sibling owner repos."),
    phase: ReleaseAuditPhase = typer.Option(
        "preflight",
        "--phase",
        help="Audit phase: preflight, postpublish, or cadence.",
    ),
    repo: str | None = typer.Option(None, "--repo", help="One owner repo to audit."),
    all_repos: bool = typer.Option(False, "--all", help="Audit every owner repo discovered in the workspace."),
    strict: bool = typer.Option(False, "--strict", help="Exit non-zero when any repo fails the selected phase."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    if phase not in {"preflight", "postpublish", "cadence"}:
        raise typer.BadParameter("phase must be one of: preflight, postpublish, cadence")
    sdk = _release_sdk(workspace_root)
    include_all = all_repos or repo is None
    result = sdk.release.audit(
        workspace_root=workspace_root,
        phase=phase,
        repo=repo,
        include_all=include_all,
        strict=strict,
    )
    if json_output:
        typer.echo(json.dumps(result.model_dump(mode="json"), indent=2, ensure_ascii=True))
    else:
        _print_release_audit(result)
    if strict and not result.passed:
        raise typer.Exit(1)


@release_app.command("publish")
def release_publish(
    workspace_root: str = typer.Argument(..., help="Workspace root containing aoa-sdk and sibling owner repos."),
    repo: str | None = typer.Option(None, "--repo", help="One owner repo to publish."),
    all_due: bool = typer.Option(False, "--all-due", help="Publish every repo that is currently release-due."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Report actions without mutating tags or releases."),
    confirm: bool = typer.Option(False, "--confirm", help="Create or update tags and GitHub Releases."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    if dry_run and confirm:
        raise typer.BadParameter("choose either --dry-run or --confirm")
    effective_dry_run = dry_run or not confirm
    sdk = _release_sdk(workspace_root)
    result = sdk.release.publish(
        workspace_root=workspace_root,
        repo=repo,
        all_due=all_due,
        dry_run=effective_dry_run,
    )
    if json_output:
        typer.echo(json.dumps(result.model_dump(mode="json"), indent=2, ensure_ascii=True))
    else:
        _print_release_publish(result)
    if not result.passed:
        raise typer.Exit(1)
