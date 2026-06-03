from __future__ import annotations

import json

import typer

from ..compatibility import CompatibilityAPI
from ..workspace.discovery import Workspace
from ..workspace.roots import KNOWN_REPOS


compatibility_app = typer.Typer(help="Inspect compatibility of consumed surfaces")


@compatibility_app.command("check")
def compatibility_check(
    root: str = typer.Argument("."),
    repo: str | None = typer.Option(None, "--repo", help="Restrict checks to one repo."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    workspace = Workspace.discover(root)
    compatibility = CompatibilityAPI(workspace)

    if repo is not None and repo not in KNOWN_REPOS:
        raise typer.BadParameter(f"unknown repo {repo!r}")

    checks = compatibility.check_repo(repo) if repo is not None else compatibility.check_all()
    if repo is not None and not checks:
        raise typer.BadParameter(f"no compatibility rules registered for repo {repo!r}")

    payload = {
        "root": str(workspace.root),
        "federation_root": str(workspace.federation_root),
        "repo": repo,
        "compatible": all(check.compatible for check in checks),
        "checks": [check.model_dump(mode="json") for check in checks],
    }

    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
    else:
        typer.echo(f"root: {payload['root']}")
        typer.echo(f"federation_root: {payload['federation_root']}")
        typer.echo(f"repo: {repo or 'all'}")
        for check in checks:
            status = "ok" if check.compatible else "fail"
            typer.echo(f"{status}: {check.surface_id} -> {check.reason}")

    if not payload["compatible"]:
        raise typer.Exit(code=1)
