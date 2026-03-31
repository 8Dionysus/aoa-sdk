from __future__ import annotations

import typer

from ..workspace.discovery import Workspace
from ..workspace.roots import KNOWN_REPOS

app = typer.Typer(help="AoA SDK CLI")
workspace_app = typer.Typer(help="Inspect workspace topology")

app.add_typer(workspace_app, name="workspace")


@app.command()
def version() -> None:
    print("aoa-sdk 0.1.0a1")


@workspace_app.command("inspect")
def workspace_inspect(root: str = typer.Argument(".")) -> None:
    workspace = Workspace.discover(root)

    typer.echo(f"root: {workspace.root}")
    typer.echo(f"federation_root: {workspace.federation_root}")
    typer.echo(f"federation_root_source: {workspace.federation_root_source}")
    typer.echo(f"manifest: {workspace.manifest_path or 'none'}")

    for repo in KNOWN_REPOS:
        path = workspace.repo_roots.get(repo)
        origin = workspace.repo_origins.get(repo)
        if path is None:
            typer.echo(f"{repo}: missing")
            continue
        typer.echo(f"{repo}: {path} [{origin}]")


if __name__ == "__main__":
    app()
