from __future__ import annotations

import typer

app = typer.Typer(help="AoA SDK CLI")

@app.command()
def version() -> None:
    print("aoa-sdk 0.1.0a1")
