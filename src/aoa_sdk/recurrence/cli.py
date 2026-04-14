from __future__ import annotations

import json
from typing import cast

import typer

from ..workspace.discovery import Workspace
from .api import RecurrenceAPI
from .io import (
    persist_beacon_packet,
    persist_candidate_ledger,
    persist_change_signal,
    persist_gap_report,
    persist_hook_run_report,
    persist_observation_packet,
    persist_propagation_plan,
    persist_return_handoff,
    persist_usage_gap_report,
)
from .models import HookEvent

recur_app = typer.Typer(help="Plan recurrence propagation, emit beacons, and keep reviewed return handoffs explicit.")
hooks_app = typer.Typer(help="Run thin observation producers without turning them into a hidden scheduler.")
recur_app.add_typer(hooks_app, name="hooks")

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
        raise typer.BadParameter(f"unsupported event {value!r}; expected one of: {allowed}")
    return cast(HookEvent, value)


@recur_app.command("detect")
def recur_detect(
    repo_root: str = typer.Argument(".", help="Repository root where the change was observed."),
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
    report_output: str | None = typer.Option(None, "--report-output", help="Optional output path."),
    root: str = typer.Option(".", "--root", help="Workspace root used for federation discovery."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
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
    report_output: str | None = typer.Option(None, "--report-output", help="Optional output path."),
    root: str = typer.Option(".", "--root", help="Workspace root used for federation discovery."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
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
    report_output: str | None = typer.Option(None, "--report-output", help="Optional output path."),
    root: str = typer.Option(".", "--root", help="Workspace root used for federation discovery."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    workspace = Workspace.discover(root)
    api = RecurrenceAPI(workspace)
    report = api.doctor(signal_path)
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
def recur_return_handoff(
    plan_path: str = typer.Argument(..., help="Path to a propagation-plan JSON file."),
    report_output: str | None = typer.Option(None, "--report-output", help="Optional output path."),
    reviewed: bool = typer.Option(
        True,
        "--reviewed/--not-reviewed",
        help="Return handoff stays reviewed-only by default.",
    ),
    root: str = typer.Option(".", "--root", help="Workspace root used for federation discovery."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
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
    report_output: str | None = typer.Option(None, "--report-output", help="Optional output path."),
    root: str = typer.Option(".", "--root", help="Workspace root used for federation discovery."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    workspace = Workspace.discover(root)
    api = RecurrenceAPI(workspace)
    packet = api.observe(signal_path, supplemental_paths=supplemental, hook_run_paths=hook_run)
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
    observations_path: str = typer.Argument(..., help="Path to an observation-packet JSON file."),
    report_output: str | None = typer.Option(None, "--report-output", help="Optional output path."),
    root: str = typer.Option(".", "--root", help="Workspace root used for federation discovery."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
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
        typer.echo(f"- {item.kind} status={item.status} target={item.target_repo} component={item.component_ref}")


@recur_app.command("ledger")
def recur_ledger(
    beacons_path: str = typer.Argument(..., help="Path to a beacon-packet JSON file."),
    report_output: str | None = typer.Option(None, "--report-output", help="Optional output path."),
    include_lower_status: bool = typer.Option(
        True,
        "--include-lower-status/--candidates-only",
        help="Keep hint/watch rows in the ledger, or restrict to candidate and review_ready rows.",
    ),
    root: str = typer.Option(".", "--root", help="Workspace root used for federation discovery."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
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
        typer.echo(f"- {item.kind} status={item.status} decision={item.decision_surface or '-'}")


@recur_app.command("usage-gaps")
def recur_usage_gaps(
    beacons_path: str = typer.Argument(..., help="Path to a beacon-packet JSON file."),
    report_output: str | None = typer.Option(None, "--report-output", help="Optional output path."),
    root: str = typer.Option(".", "--root", help="Workspace root used for federation discovery."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
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
        typer.echo(f"- {item.beacon_ref} status={item.status} decision={item.decision_surface or '-'}")


@hooks_app.command("list")
def recur_hooks_list(
    event: str | None = typer.Option(
        None,
        "--event",
        help="Optional event filter, for example session_stop or user_prompt_submit.",
    ),
    root: str = typer.Option(".", "--root", help="Workspace root used for federation discovery."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    workspace = Workspace.discover(root)
    api = RecurrenceAPI(workspace)
    parsed_event = _parse_hook_event(event) if event is not None else None
    bindings = api.hooks(event=parsed_event) if parsed_event is not None else api.hooks()
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
    event: str = typer.Option(..., "--event", help="Hook event to run, for example session_stop."),
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
    report_output: str | None = typer.Option(None, "--report-output", help="Optional output path."),
    root: str = typer.Option(".", "--root", help="Workspace root used for federation discovery."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    workspace = Workspace.discover(root)
    api = RecurrenceAPI(workspace)
    report = api.run_hooks(event=_parse_hook_event(event), signal_or_path=signal_path, binding_refs=binding_ref)
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
