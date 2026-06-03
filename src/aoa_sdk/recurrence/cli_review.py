from __future__ import annotations

import json
from typing import cast

import typer

from ..workspace.discovery import Workspace
from .api import RecurrenceAPI
from .io import (
    persist_owner_review_decision,
    persist_review_decision_close_report,
    persist_review_decision_ledger,
    persist_review_suppression_memory,
)
from .models import ReviewDecisionAction


review_app = typer.Typer(
    help="Close review beacons with explicit owner decisions and suppression memory."
)


@review_app.command("decision-template")
def recur_review_decision_template(
    review_queue_path: str = typer.Argument(
        ..., help="Path to a review-queue JSON file."
    ),
    item_ref: str | None = typer.Option(
        None, "--item-ref", help="Review queue item_ref to close."
    ),
    beacon_ref: str | None = typer.Option(
        None, "--beacon-ref", help="Beacon ref to close."
    ),
    decision: str = typer.Option(
        "defer", "--decision", help="accept|reject|defer|reanchor|split|merge|suppress"
    ),
    reviewer: str = typer.Option("owner-review", "--reviewer", help="Reviewer label."),
    rationale: str = typer.Option("", "--rationale", help="Initial rationale text."),
    cluster_ref: str | None = typer.Option(
        None, "--cluster-ref", help="Optional provisional SDK cluster_ref."
    ),
    next_review_after: str | None = typer.Option(
        None, "--next-review-after", help="Optional owner review date/window."
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
    decision_packet = api.review_decision_template(
        review_queue_path,
        item_ref=item_ref,
        beacon_ref=beacon_ref,
        decision=cast(ReviewDecisionAction, decision),
        reviewer=reviewer,
        rationale=rationale,
        cluster_ref=cluster_ref,
        next_review_after=next_review_after,
    )
    report_path = persist_owner_review_decision(
        workspace, decision_packet, output=report_output
    )
    payload = decision_packet.model_dump(mode="json")
    payload["report_path"] = str(report_path)
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    typer.echo(f"report_path: {report_path}")
    typer.echo(f"decision_ref: {decision_packet.decision_ref}")
    typer.echo(f"decision: {decision_packet.decision}")
    typer.echo(f"owner_repo: {decision_packet.owner_repo}")


@review_app.command("close")
def recur_review_close(
    review_queue_path: str = typer.Argument(
        ..., help="Path to a review-queue JSON file."
    ),
    decision_path: list[str] = typer.Option(
        None,
        "--decision",
        help="Repeatable owner-review-decision JSON path.",
    ),
    report_output: str | None = typer.Option(
        None, "--report-output", help="Optional close-report path."
    ),
    ledger_output: str | None = typer.Option(
        None, "--ledger-output", help="Optional ledger path."
    ),
    suppression_output: str | None = typer.Option(
        None, "--suppression-output", help="Optional suppression-memory path."
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
    report = api.review_close(
        review_queue_path, decision_paths=list(decision_path or [])
    )
    report_path = persist_review_decision_close_report(
        workspace, report, output=report_output
    )
    ledger_path = persist_review_decision_ledger(
        workspace, report.ledger, output=ledger_output
    )
    suppression_path = persist_review_suppression_memory(
        workspace, report.suppression_memory, output=suppression_output
    )
    payload = report.model_dump(mode="json")
    payload["report_path"] = str(report_path)
    payload["ledger_path"] = str(ledger_path)
    payload["suppression_path"] = str(suppression_path)
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    typer.echo(f"report_path: {report_path}")
    typer.echo(f"ledger_path: {ledger_path}")
    typer.echo(f"suppression_path: {suppression_path}")
    typer.echo(f"closed: {len(report.closed_item_refs)}")
    typer.echo(f"unresolved: {len(report.unresolved_item_refs)}")
    if report.warnings:
        typer.echo("warnings:")
        for warning in report.warnings:
            typer.echo(f"- {warning}")
