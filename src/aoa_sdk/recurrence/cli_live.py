from __future__ import annotations

import json

import typer

from ..workspace.discovery import Workspace
from .api import RecurrenceAPI
from .io import persist_observation_packet


live_app = typer.Typer(
    help="Collect live owner-authored observation surfaces without mutating canon."
)


@live_app.command("producers")
def recur_live_producers(
    root: str = typer.Option(
        ".", "--root", help="Workspace root used for federation discovery."
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Emit machine-readable JSON."
    ),
) -> None:
    workspace = Workspace.discover(root)
    api = RecurrenceAPI(workspace)
    producers = api.live_producers()
    payload = {"count": len(producers), "producers": producers}
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    typer.echo(f"producers: {len(producers)}")
    for item in producers:
        typer.echo(f"- {item}")


@live_app.command("observe")
def recur_live_observe(
    producer: list[str] = typer.Option(
        None,
        "--producer",
        help="Repeatable producer filter. Omit to run every live observation producer.",
    ),
    max_per_producer: int = typer.Option(
        200, "--max-per-producer", help="Safety cap per producer."
    ),
    report_output: str | None = typer.Option(
        None, "--report-output", help="Optional output path."
    ),
    root: str = typer.Option(
        ".", "--root", help="Workspace root used for federation discovery."
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Emit machine-readable JSON."
    ),
) -> None:
    workspace = Workspace.discover(root)
    api = RecurrenceAPI(workspace)
    packet = api.live_observations(
        producers=producer or None,
        max_observations_per_producer=max_per_producer,
    )
    report_path = persist_observation_packet(workspace, packet, output=report_output)
    payload = packet.model_dump(mode="json")
    payload["report_path"] = str(report_path)
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    typer.echo(f"report_path: {report_path}")
    typer.echo(f"observations: {len(packet.observations)}")
    by_signal: dict[str, int] = {}
    for item in packet.observations:
        by_signal[item.signal] = by_signal.get(item.signal, 0) + 1
    for signal, count in sorted(by_signal.items()):
        typer.echo(f"- {signal}: {count}")
