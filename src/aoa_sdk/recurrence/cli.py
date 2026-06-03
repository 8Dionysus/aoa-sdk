from __future__ import annotations

from .cli_core import recur_app
from .cli_graph import graph_app
from .cli_hooks import hooks_app
from .cli_live import live_app
from .cli_project import project_app
from .cli_review import review_app


recur_app.add_typer(hooks_app, name="hooks")
recur_app.add_typer(graph_app, name="graph")
recur_app.add_typer(live_app, name="live")
recur_app.add_typer(review_app, name="review")
recur_app.add_typer(project_app, name="project")


__all__ = ["recur_app"]
