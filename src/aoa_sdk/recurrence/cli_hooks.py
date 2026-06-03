from __future__ import annotations

import json
from typing import cast

import typer

from ..workspace.discovery import Workspace
from .api import RecurrenceAPI
from .io import persist_hook_run_report
from .models import HookEvent


hooks_app = typer.Typer(
    help="Run thin observation producers without turning them into a hidden scheduler."
)


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
