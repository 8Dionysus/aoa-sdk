from __future__ import annotations

import json
from typing import Any

import typer

from ..compatibility import CompatibilityAPI
from ..workspace.discovery import Workspace
from ..workspace.roots import KNOWN_REPOS

app = typer.Typer(help="AoA SDK CLI")
workspace_app = typer.Typer(help="Inspect workspace topology")
compatibility_app = typer.Typer(help="Inspect compatibility of consumed surfaces")

app.add_typer(workspace_app, name="workspace")
app.add_typer(compatibility_app, name="compatibility")


def _workspace_payload(workspace: Workspace) -> dict[str, Any]:
    repos: dict[str, dict[str, str | None]] = {}
    for repo in KNOWN_REPOS:
        path = workspace.repo_roots.get(repo)
        origin = workspace.repo_origins.get(repo)
        repos[repo] = {
            "path": str(path) if path is not None else None,
            "origin": origin,
        }
    return {
        "root": str(workspace.root),
        "federation_root": str(workspace.federation_root),
        "federation_root_source": workspace.federation_root_source,
        "manifest": str(workspace.manifest_path) if workspace.manifest_path else None,
        "repos": repos,
    }


@app.command()
def version() -> None:
    print("aoa-sdk 0.1.0")


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


if __name__ == "__main__":
    app()
