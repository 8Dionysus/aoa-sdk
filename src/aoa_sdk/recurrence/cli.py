from __future__ import annotations

import json
from typing import cast

import typer

from ..workspace.discovery import Workspace
from .api import RecurrenceAPI
from .io import (
    persist_beacon_packet,
    persist_candidate_dossier_packet,
    persist_candidate_ledger,
    persist_change_signal,
    persist_downstream_projection_bundle,
    persist_gap_report,
    persist_graph_closure_report,
    persist_graph_delta_report,
    persist_graph_snapshot,
    persist_hook_run_report,
    persist_kag_projection,
    persist_manifest_scan_report,
    persist_observation_packet,
    persist_owner_review_decision,
    persist_owner_review_summary,
    persist_propagation_plan,
    persist_projection_guard_report,
    persist_return_handoff,
    persist_review_decision_close_report,
    persist_review_decision_ledger,
    persist_review_suppression_memory,
    persist_review_queue,
    persist_routing_projection,
    persist_rollout_window_bundle,
    persist_stats_projection,
    persist_usage_gap_report,
    persist_wiring_plan,
)
from .models import HookEvent, ReviewDecisionAction

recur_app = typer.Typer(
    help="Plan recurrence propagation, emit beacons, and keep reviewed return handoffs explicit."
)
hooks_app = typer.Typer(
    help="Run thin observation producers without turning them into a hidden scheduler."
)
graph_app = typer.Typer(
    help="Inspect typed recurrence graph closure, snapshots, and deltas."
)
live_app = typer.Typer(
    help="Collect live owner-authored observation surfaces without mutating canon."
)
review_app = typer.Typer(
    help="Close review beacons with explicit owner decisions and suppression memory."
)
project_app = typer.Typer(
    help="Emit narrow downstream recurrence projections without authority transfer."
)
recur_app.add_typer(hooks_app, name="hooks")
recur_app.add_typer(graph_app, name="graph")
recur_app.add_typer(live_app, name="live")
recur_app.add_typer(review_app, name="review")
recur_app.add_typer(project_app, name="project")

HOOK_EVENTS: tuple[HookEvent, ...] = (
    "manual_run",
    "session_start",
    "user_prompt_submit",
    "session_stop",
    "receipt_published",
    "generated_surface_refreshed",
    "harvest_written",
    "real_run_published",
    "gate_review_written",
    "runtime_evidence_selected",
)


def _parse_hook_event(value: str) -> HookEvent:
    if value not in HOOK_EVENTS:
        allowed = ", ".join(HOOK_EVENTS)
        raise typer.BadParameter(
            f"unsupported event {value!r}; expected one of: {allowed}"
        )
    return cast(HookEvent, value)


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


@recur_app.command("manifest-scan")
def recur_manifest_scan(
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
    report = api.manifest_scan()
    report_path = persist_manifest_scan_report(workspace, report, output=report_output)
    payload = report.model_dump(mode="json")
    payload["report_path"] = str(report_path)
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    typer.echo(f"report_path: {report_path}")
    typer.echo(f"loaded_components: {len(report.loaded_components)}")
    typer.echo(f"foreign_manifests: {len(report.foreign_manifests)}")
    typer.echo(f"diagnostics: {len(report.diagnostics)}")
    for severity, count in sorted(report.by_severity.items()):
        typer.echo(f"- {severity}: {count}")


@recur_app.command("detect")
def recur_detect(
    repo_root: str = typer.Argument(
        ".", help="Repository root where the change was observed."
    ),
    diff_base: str | None = typer.Option(
        None,
        "--from",
        help="Diff source in the form git:<rev-spec>, for example git:HEAD~1..HEAD.",
    ),
    path: list[str] = typer.Option(
        None,
        "--path",
        help="Repeatable explicit changed path relative to repo_root. Use this instead of --from when needed.",
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
    signal = api.detect(repo_root=repo_root, diff_base=diff_base, paths=path)
    report_path = persist_change_signal(workspace, signal, output=report_output)
    payload = signal.model_dump(mode="json")
    payload["report_path"] = str(report_path)
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    typer.echo(f"report_path: {report_path}")
    typer.echo(f"direct_components: {len(signal.direct_components)}")
    for item in signal.direct_components:
        typer.echo(
            f"- {item.component_ref} [{item.match_class}] "
            f"signals={','.join(item.inferred_signals)} "
            f"paths={','.join(item.matched_paths)}"
        )
    if signal.unmatched_paths:
        typer.echo(f"unmatched_paths: {len(signal.unmatched_paths)}")
        for path_item in signal.unmatched_paths:
            typer.echo(f"  - {path_item}")


@recur_app.command("plan")
def recur_plan(
    signal_path: str = typer.Argument(..., help="Path to a change-signal JSON file."),
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
    plan = api.plan(signal_path)
    report_path = persist_propagation_plan(workspace, plan, output=report_output)
    payload = plan.model_dump(mode="json")
    payload["report_path"] = str(report_path)
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    typer.echo(f"report_path: {report_path}")
    typer.echo(f"summary: {plan.summary}")
    for step in plan.ordered_steps:
        typer.echo(
            f"- {step.step_ref} {step.action} owner={step.owner_repo} "
            f"status={step.status} target={step.component_ref}"
        )
    if plan.unresolved_edges:
        typer.echo("unresolved_edges:")
        for item in plan.unresolved_edges:
            typer.echo(f"  - {item}")
    if plan.open_questions:
        typer.echo("open_questions:")
        for item in plan.open_questions:
            typer.echo(f"  - {item}")


@recur_app.command("doctor")
def recur_doctor(
    signal_path: str | None = typer.Option(
        None,
        "--signal",
        help="Optional change-signal JSON path. When omitted, run the doctor over the planted registry only.",
    ),
    report_output: str | None = typer.Option(
        None, "--report-output", help="Optional output path."
    ),
    root: str = typer.Option(
        ".", "--root", help="Workspace root used for federation discovery."
    ),
    include_manifest_diagnostics: bool = typer.Option(
        True,
        "--include-manifest-diagnostics/--skip-manifest-diagnostics",
        help="Include registry quarantine/foreign/adapter diagnostics in doctor gaps.",
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Emit machine-readable JSON."
    ),
) -> None:
    workspace = Workspace.discover(root)
    api = RecurrenceAPI(workspace)
    report = api.doctor(
        signal_path, include_manifest_diagnostics=include_manifest_diagnostics
    )
    report_path = persist_gap_report(workspace, report, output=report_output)
    payload = report.model_dump(mode="json")
    payload["report_path"] = str(report_path)
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    typer.echo(f"report_path: {report_path}")
    typer.echo(f"components_checked: {len(report.components_checked)}")
    typer.echo(f"gaps: {len(report.gaps)}")
    for item in report.gaps:
        typer.echo(
            f"- {item.gap_ref} severity={item.severity} kind={item.gap_kind} "
            f"component={item.component_ref or '-'}"
        )


@recur_app.command("return-handoff")
@recur_app.command("handoff")
def recur_return_handoff(
    plan_path: str = typer.Argument(..., help="Path to a propagation-plan JSON file."),
    report_output: str | None = typer.Option(
        None, "--report-output", help="Optional output path."
    ),
    reviewed: bool = typer.Option(
        True,
        "--reviewed/--not-reviewed",
        help="Return handoff stays reviewed-only by default.",
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
    handoff = api.build_return_handoff(plan_path, reviewed=reviewed)
    report_path = persist_return_handoff(workspace, handoff, output=report_output)
    payload = handoff.model_dump(mode="json")
    payload["report_path"] = str(report_path)
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    typer.echo(f"report_path: {report_path}")
    typer.echo(f"targets: {len(handoff.targets)}")
    for item in handoff.targets:
        typer.echo(f"- {item.owner_repo} {item.target_kind} -> {item.target}")


@recur_app.command("observe")
def recur_observe(
    signal_path: str | None = typer.Option(
        None,
        "--signal",
        help="Optional change-signal JSON path. Omit it to build an observation packet from supplemental observations only.",
    ),
    supplemental: list[str] = typer.Option(
        None,
        "--supplemental",
        help="Repeatable JSON or JSONL observation inputs to merge into the packet.",
    ),
    hook_run: list[str] = typer.Option(
        None,
        "--hook-run",
        help="Repeatable hook-run report JSON files to merge into the packet.",
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
    packet = api.observe(
        signal_path, supplemental_paths=supplemental, hook_run_paths=hook_run
    )
    report_path = persist_observation_packet(workspace, packet, output=report_output)
    payload = packet.model_dump(mode="json")
    payload["report_path"] = str(report_path)
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    typer.echo(f"report_path: {report_path}")
    typer.echo(f"observations: {len(packet.observations)}")
    for item in packet.observations[:12]:
        typer.echo(f"- {item.component_ref} {item.signal} [{item.category}]")
    if len(packet.observations) > 12:
        typer.echo("...")


@recur_app.command("beacon")
def recur_beacon(
    observations_path: str = typer.Argument(
        ..., help="Path to an observation-packet JSON file."
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
    packet = api.beacon(observations_path)
    report_path = persist_beacon_packet(workspace, packet, output=report_output)
    payload = packet.model_dump(mode="json")
    payload["report_path"] = str(report_path)
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    typer.echo(f"report_path: {report_path}")
    typer.echo(f"entries: {len(packet.entries)}")
    for item in packet.entries:
        typer.echo(
            f"- {item.kind} status={item.status} target={item.target_repo} component={item.component_ref}"
        )


@recur_app.command("ledger")
def recur_ledger(
    beacons_path: str = typer.Argument(..., help="Path to a beacon-packet JSON file."),
    report_output: str | None = typer.Option(
        None, "--report-output", help="Optional output path."
    ),
    include_lower_status: bool = typer.Option(
        True,
        "--include-lower-status/--candidates-only",
        help="Keep hint/watch rows in the ledger, or restrict to candidate and review_ready rows.",
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
    ledger = api.ledger(beacons_path, include_lower_status=include_lower_status)
    report_path = persist_candidate_ledger(workspace, ledger, output=report_output)
    payload = ledger.model_dump(mode="json")
    payload["report_path"] = str(report_path)
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    typer.echo(f"report_path: {report_path}")
    typer.echo(f"entries: {len(ledger.entries)}")
    for item in ledger.entries:
        typer.echo(
            f"- {item.kind} status={item.status} decision={item.decision_surface or '-'}"
        )


@recur_app.command("usage-gaps")
def recur_usage_gaps(
    beacons_path: str = typer.Argument(..., help="Path to a beacon-packet JSON file."),
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
    report = api.usage_gaps(beacons_path)
    report_path = persist_usage_gap_report(workspace, report, output=report_output)
    payload = report.model_dump(mode="json")
    payload["report_path"] = str(report_path)
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    typer.echo(f"report_path: {report_path}")
    typer.echo(f"items: {len(report.items)}")
    for item in report.items:
        typer.echo(
            f"- {item.beacon_ref} status={item.status} decision={item.decision_surface or '-'}"
        )


@recur_app.command("review-queue")
def recur_review_queue(
    beacons_path: str = typer.Argument(..., help="Path to a beacon-packet JSON file."),
    usage_gaps_path: str | None = typer.Option(
        None,
        "--usage-gaps",
        help="Optional usage-gap report. When present, watch-level omission signals may enter the queue.",
    ),
    report_output: str | None = typer.Option(
        None, "--report-output", help="Optional output path."
    ),
    include_lower_status: bool = typer.Option(
        False,
        "--include-lower-status/--candidates-only",
        help="Keep hint/watch rows, or restrict to candidate/review_ready plus watch-level omission signals.",
    ),
    include_watch_usage_gaps: bool = typer.Option(
        True,
        "--include-watch-usage-gaps/--skip-watch-usage-gaps",
        help="Keep omission-oriented watch signals visible even when lower statuses are filtered out.",
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
    queue = api.review_queue(
        beacons_path,
        usage_gap_or_path=usage_gaps_path,
        include_lower_status=include_lower_status,
        include_watch_usage_gaps=include_watch_usage_gaps,
    )
    report_path = persist_review_queue(workspace, queue, output=report_output)
    payload = queue.model_dump(mode="json")
    payload["report_path"] = str(report_path)
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    typer.echo(f"report_path: {report_path}")
    typer.echo(f"items: {len(queue.items)}")
    for item in queue.items:
        typer.echo(
            f"- {item.item_ref} priority={item.priority} lane={item.lane} "
            f"target={item.target_repo} kind={item.kind} status={item.status}"
        )


@recur_app.command("review-dossiers")
def recur_review_dossiers(
    review_queue_path: str = typer.Argument(
        ..., help="Path to a review-queue JSON file."
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
    packet = api.review_dossiers(review_queue_path)
    report_path = persist_candidate_dossier_packet(
        workspace, packet, output=report_output
    )
    payload = packet.model_dump(mode="json")
    payload["report_path"] = str(report_path)
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    typer.echo(f"report_path: {report_path}")
    typer.echo(f"dossiers: {len(packet.dossiers)}")
    for item in packet.dossiers:
        typer.echo(
            f"- {item.dossier_ref} lane={item.lane} target={item.target_repo} status={item.status}"
        )


@recur_app.command("review-summary")
def recur_review_summary(
    review_queue_path: str = typer.Argument(
        ..., help="Path to a review-queue JSON file."
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
    summary = api.review_summary(review_queue_path)
    report_path = persist_owner_review_summary(workspace, summary, output=report_output)
    payload = summary.model_dump(mode="json")
    payload["report_path"] = str(report_path)
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    typer.echo(f"report_path: {report_path}")
    typer.echo(f"owners: {len(summary.owners)}")
    for item in summary.owners:
        typer.echo(
            f"- {item.target_repo} total={item.total_items} statuses={item.by_status}"
        )


@recur_app.command("wiring-plan")
def recur_wiring_plan(
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
    plan = api.wiring_plan()
    report_path = persist_wiring_plan(workspace, plan, output=report_output)
    payload = plan.model_dump(mode="json")
    payload["report_path"] = str(report_path)
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    typer.echo(f"report_path: {report_path}")
    typer.echo(f"snippets: {len(plan.snippets)}")
    for item in plan.snippets:
        typer.echo(f"- {item.scope} -> {item.target_path}")


@recur_app.command("rollout-bundle")
def recur_rollout_bundle(
    wiring_plan_path: str | None = typer.Option(
        None,
        "--wiring-plan",
        help="Optional wiring-plan JSON path. Omit it to build one on the fly.",
    ),
    review_summary_path: str | None = typer.Option(
        None,
        "--review-summary",
        help="Optional owner-review-summary JSON path.",
    ),
    doctor_report_path: str | None = typer.Option(
        None,
        "--doctor",
        help="Optional connectivity-gap report JSON path.",
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
    bundle = api.rollout_bundle(
        wiring_plan_or_path=wiring_plan_path,
        review_summary_or_path=review_summary_path,
        doctor_report_or_path=doctor_report_path,
    )
    report_path = persist_rollout_window_bundle(workspace, bundle, output=report_output)
    payload = bundle.model_dump(mode="json")
    payload["report_path"] = str(report_path)
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    typer.echo(f"report_path: {report_path}")
    typer.echo(f"campaign_window: {bundle.campaign_window.phase}")
    typer.echo(f"drift_review_window: {bundle.drift_review_window.phase}")
    typer.echo(
        f"rollback_followthrough_window: {bundle.rollback_followthrough_window.phase}"
    )


@hooks_app.command("list")
def recur_hooks_list(
    event: str | None = typer.Option(
        None,
        "--event",
        help="Optional event filter, for example session_stop or user_prompt_submit.",
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
    parsed_event = _parse_hook_event(event) if event is not None else None
    bindings = (
        api.hooks(event=parsed_event) if parsed_event is not None else api.hooks()
    )
    payload = {
        "event": parsed_event,
        "count": len(bindings),
        "bindings": [item.model_dump(mode="json") for item in bindings],
    }
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    typer.echo(f"bindings: {len(bindings)}")
    for item in bindings:
        typer.echo(
            f"- {item.binding_ref} event={item.event} producer={item.producer} "
            f"component={item.component_ref}"
        )


@hooks_app.command("run")
def recur_hooks_run(
    event: str = typer.Option(
        ..., "--event", help="Hook event to run, for example session_stop."
    ),
    signal_path: str | None = typer.Option(
        None,
        "--signal",
        help="Optional change-signal JSON path that the hook report should carry as context.",
    ),
    binding_ref: list[str] = typer.Option(
        None,
        "--binding-ref",
        help="Repeatable binding_ref filter. Omit it to run every binding for the selected event.",
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
    report = api.run_hooks(
        event=_parse_hook_event(event),
        signal_or_path=signal_path,
        binding_refs=binding_ref,
    )
    report_path = persist_hook_run_report(workspace, report, output=report_output)
    payload = report.model_dump(mode="json")
    payload["report_path"] = str(report_path)
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    typer.echo(f"report_path: {report_path}")
    typer.echo(f"bindings_run: {len(report.bindings_run)}")
    typer.echo(f"observations: {len(report.observations)}")
    if report.missing_paths:
        typer.echo("missing_paths:")
        for missing_path in report.missing_paths:
            typer.echo(f"  - {missing_path}")
    if report.warnings:
        typer.echo("warnings:")
        for warning in report.warnings:
            typer.echo(f"  - {warning.binding_ref}: {warning.message}")


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
