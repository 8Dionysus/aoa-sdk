from __future__ import annotations

import json

import typer

from ..workspace.discovery import Workspace
from .api import RecurrenceAPI
from .io import (
    persist_graph_closure_report,
    persist_graph_delta_report,
    persist_graph_snapshot,
)


graph_app = typer.Typer(
    help="Inspect typed recurrence graph closure, snapshots, and deltas."
)


@graph_app.command("snapshot")
def recur_graph_snapshot(
    report_output: str | None = typer.Option(
        None, "--report-output", help="Optional output path."
    ),
    root: str = typer.Option(
        ".", "--root", help="Workspace root used for federation discovery."
    ),
    include_manifest_diagnostics: bool = typer.Option(
        True,
        "--include-manifest-diagnostics/--skip-manifest-diagnostics",
        help="Carry manifest diagnostics into the graph snapshot.",
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Emit machine-readable JSON."
    ),
) -> None:
    workspace = Workspace.discover(root)
    api = RecurrenceAPI(workspace)
    snapshot = api.graph_snapshot(
        include_manifest_diagnostics=include_manifest_diagnostics
    )
    report_path = persist_graph_snapshot(workspace, snapshot, output=report_output)
    payload = snapshot.model_dump(mode="json")
    payload["report_path"] = str(report_path)
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    typer.echo(f"report_path: {report_path}")
    typer.echo(f"nodes: {snapshot.node_count}")
    typer.echo(f"edges: {snapshot.edge_count}")
    if snapshot.manifest_diagnostics:
        typer.echo(f"manifest_diagnostics: {len(snapshot.manifest_diagnostics)}")


@graph_app.command("diff")
def recur_graph_diff(
    before_path: str = typer.Argument(..., help="Before graph-snapshot JSON."),
    after_path: str = typer.Argument(..., help="After graph-snapshot JSON."),
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
    report = api.graph_delta(before_path, after_path)
    report_path = persist_graph_delta_report(workspace, report, output=report_output)
    payload = report.model_dump(mode="json")
    payload["report_path"] = str(report_path)
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    typer.echo(f"report_path: {report_path}")
    typer.echo(f"summary: {report.summary}")


@graph_app.command("closure")
def recur_graph_closure(
    component: list[str] = typer.Option(
        None,
        "--component",
        help="Repeatable direct component_ref to expand from.",
    ),
    depth_limit: int = typer.Option(
        8, "--depth-limit", help="Maximum typed-edge traversal depth."
    ),
    include_optional: bool = typer.Option(
        True,
        "--include-optional/--skip-optional",
        help="Include recommended/advisory edges in closure.",
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
    report = api.graph_closure(
        direct_component_refs=component or [],
        depth_limit=depth_limit,
        include_optional=include_optional,
    )
    report_path = persist_graph_closure_report(workspace, report, output=report_output)
    payload = report.model_dump(mode="json")
    payload["report_path"] = str(report_path)
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    typer.echo(f"report_path: {report_path}")
    typer.echo(f"nodes: {len(report.nodes)}")
    typer.echo(f"external_impacts: {len(report.external_impacts)}")
    typer.echo(f"batches: {len(report.propagation_batches)}")
    if report.cycles:
        typer.echo(f"cycles: {len(report.cycles)}")
    if report.unresolved_edges:
        typer.echo("unresolved_edges:")
        for item in report.unresolved_edges:
            typer.echo(f"  - {item}")
