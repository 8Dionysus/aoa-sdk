from __future__ import annotations

import json

import typer

from ..workspace.discovery import Workspace
from .api import RecurrenceAPI
from .io import (
    persist_downstream_projection_bundle,
    persist_kag_projection,
    persist_projection_guard_report,
    persist_routing_projection,
    persist_stats_projection,
)


project_app = typer.Typer(
    help="Emit narrow downstream recurrence projections without authority transfer."
)


@project_app.command("routing")
def recur_project_routing(
    plan_path: str | None = typer.Option(
        None, "--plan", help="Optional propagation-plan JSON."
    ),
    doctor_path: str | None = typer.Option(
        None, "--doctor", help="Optional connectivity-gap-report JSON."
    ),
    handoff_path: str | None = typer.Option(
        None, "--handoff", help="Optional return-handoff JSON."
    ),
    review_queue_path: str | None = typer.Option(
        None, "--review-queue", help="Optional review-queue JSON."
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
    projection = api.routing_projection(
        plan_or_path=plan_path,
        gap_report_or_path=doctor_path,
        return_handoff_or_path=handoff_path,
        review_queue_or_path=review_queue_path,
    )
    report_path = persist_routing_projection(
        workspace, projection, output=report_output
    )
    payload = projection.model_dump(mode="json")
    payload["report_path"] = str(report_path)
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    typer.echo(f"report_path: {report_path}")
    typer.echo(f"owner_hints: {len(projection.owner_hints)}")
    typer.echo(f"return_hints: {len(projection.return_hints)}")
    typer.echo(f"gap_hints: {len(projection.gap_hints)}")


@project_app.command("stats")
def recur_project_stats(
    doctor_path: str | None = typer.Option(
        None, "--doctor", help="Optional connectivity-gap-report JSON."
    ),
    beacon_path: str | None = typer.Option(
        None, "--beacon", help="Optional beacon-packet JSON."
    ),
    review_queue_path: str | None = typer.Option(
        None, "--review-queue", help="Optional review-queue JSON."
    ),
    review_summary_path: str | None = typer.Option(
        None, "--review-summary", help="Optional owner-review-summary JSON."
    ),
    decision_report_path: str | None = typer.Option(
        None, "--decision-report", help="Optional review-decision-close-report JSON."
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
    projection = api.stats_projection(
        gap_report_or_path=doctor_path,
        beacon_or_path=beacon_path,
        review_queue_or_path=review_queue_path,
        review_summary_or_path=review_summary_path,
        decision_report_or_path=decision_report_path,
    )
    report_path = persist_stats_projection(workspace, projection, output=report_output)
    payload = projection.model_dump(mode="json")
    payload["report_path"] = str(report_path)
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    typer.echo(f"report_path: {report_path}")
    typer.echo(f"coverage: {projection.coverage.total}")
    typer.echo(f"gaps: {projection.gaps.total}")
    typer.echo(f"beacons: {projection.beacons.total}")
    typer.echo(f"review: {projection.review.total}")


@project_app.command("kag")
def recur_project_kag(
    plan_path: str | None = typer.Option(
        None, "--plan", help="Optional propagation-plan JSON."
    ),
    doctor_path: str | None = typer.Option(
        None, "--doctor", help="Optional connectivity-gap-report JSON."
    ),
    handoff_path: str | None = typer.Option(
        None, "--handoff", help="Optional return-handoff JSON."
    ),
    beacon_path: str | None = typer.Option(
        None, "--beacon", help="Optional beacon-packet JSON."
    ),
    review_queue_path: str | None = typer.Option(
        None, "--review-queue", help="Optional review-queue JSON."
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
    projection = api.kag_projection(
        plan_or_path=plan_path,
        gap_report_or_path=doctor_path,
        return_handoff_or_path=handoff_path,
        beacon_or_path=beacon_path,
        review_queue_or_path=review_queue_path,
    )
    report_path = persist_kag_projection(workspace, projection, output=report_output)
    payload = projection.model_dump(mode="json")
    payload["report_path"] = str(report_path)
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    typer.echo(f"report_path: {report_path}")
    typer.echo(
        f"donor_refresh_obligations: {len(projection.donor_refresh_obligations)}"
    )
    typer.echo(
        f"retrieval_invalidation_hints: {len(projection.retrieval_invalidation_hints)}"
    )
    typer.echo(f"source_strength_hints: {len(projection.source_strength_hints)}")


@project_app.command("build")
def recur_project_build(
    plan_path: str | None = typer.Option(
        None, "--plan", help="Optional propagation-plan JSON."
    ),
    doctor_path: str | None = typer.Option(
        None, "--doctor", help="Optional connectivity-gap-report JSON."
    ),
    handoff_path: str | None = typer.Option(
        None, "--handoff", help="Optional return-handoff JSON."
    ),
    beacon_path: str | None = typer.Option(
        None, "--beacon", help="Optional beacon-packet JSON."
    ),
    review_queue_path: str | None = typer.Option(
        None, "--review-queue", help="Optional review-queue JSON."
    ),
    review_summary_path: str | None = typer.Option(
        None, "--review-summary", help="Optional owner-review-summary JSON."
    ),
    decision_report_path: str | None = typer.Option(
        None, "--decision-report", help="Optional review-decision-close-report JSON."
    ),
    no_routing: bool = typer.Option(False, "--no-routing", help="Skip routing."),
    no_stats: bool = typer.Option(False, "--no-stats", help="Skip stats."),
    no_kag: bool = typer.Option(False, "--no-kag", help="Skip KAG."),
    report_output: str | None = typer.Option(
        None, "--report-output", help="Optional bundle output path."
    ),
    guard_output: str | None = typer.Option(
        None, "--guard-output", help="Optional guard report output path."
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
    bundle = api.downstream_projection_bundle(
        plan_or_path=plan_path,
        gap_report_or_path=doctor_path,
        return_handoff_or_path=handoff_path,
        beacon_or_path=beacon_path,
        review_queue_or_path=review_queue_path,
        review_summary_or_path=review_summary_path,
        decision_report_or_path=decision_report_path,
        include_routing=not no_routing,
        include_stats=not no_stats,
        include_kag=not no_kag,
    )
    bundle_path = persist_downstream_projection_bundle(
        workspace,
        bundle,
        output=report_output,
    )
    guard_path = persist_projection_guard_report(
        workspace,
        bundle.guard_report,
        output=guard_output,
    )
    payload = bundle.model_dump(mode="json")
    payload["report_path"] = str(bundle_path)
    payload["guard_report_path"] = str(guard_path)
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    typer.echo(f"report_path: {bundle_path}")
    typer.echo(f"guard_report_path: {guard_path}")
    typer.echo(f"surfaces: {len(bundle.surfaces)}")
    typer.echo(f"guard_violations: {len(bundle.guard_report.violations)}")
