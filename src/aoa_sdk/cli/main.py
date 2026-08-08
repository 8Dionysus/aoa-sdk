from __future__ import annotations

import typer

from ..recurrence.cli import recur_app
from .checkpoint import checkpoint_app
from .common import _resolve_checkpoint_hook_repos as _resolve_checkpoint_hook_repos
from .compatibility import compatibility_app
from .organs import organs_app
from .release import release_app
from .route import route_app
from .skills import skills_app
from .surfaces import surfaces_app
from .workspace import workspace_app


__all__ = ["app", "_resolve_checkpoint_hook_repos"]


app = typer.Typer(help="AoA SDK CLI")
app.add_typer(workspace_app, name="workspace")
app.add_typer(compatibility_app, name="compatibility")
app.add_typer(skills_app, name="skills")
app.add_typer(recur_app, name="recur")
app.add_typer(surfaces_app, name="surfaces")
app.add_typer(checkpoint_app, name="checkpoint")
app.add_typer(release_app, name="release")
app.add_typer(organs_app, name="organs")
app.add_typer(route_app, name="route")


@app.command()
def version() -> None:
    print("aoa-sdk 0.10.0")


if __name__ == "__main__":
    app()
