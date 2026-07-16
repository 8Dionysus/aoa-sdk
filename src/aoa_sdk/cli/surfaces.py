from __future__ import annotations

import json

import typer

from ..api import AoASDK
from ..models import SessionCheckpointNote
from ..workspace.discovery import Workspace
from .common import (
    _load_surface_detection_report,
    _merge_checkpoint_note,
    _resolve_surface_handoff_path,
    _resolve_surface_report_path,
    _write_surface_handoff,
    _write_surface_report,
)
from .rendering import _print_surface_detection_report, _print_surface_handoff


surfaces_app = typer.Typer(help="Read additive AoA surface-detection reports and reviewed closeout handoffs")


@surfaces_app.command("detect")
def surfaces_detect(
    repo_root: str = typer.Argument(..., help="Repository root or repo-relative path used as task context."),
    phase: str = typer.Option(..., "--phase", help="Detection phase: ingress, in-flight, pre-mutation, checkpoint, or closeout."),
    intent_text: str = typer.Option("", "--intent-text", help="Intent text used for additive surface detection."),
    mutation_surface: str = typer.Option(
        "none",
        "--mutation-surface",
        help="Mutation class: none, code, repo-config, infra, runtime, or public-share.",
    ),
    closeout_path: str | None = typer.Option(
        None,
        "--closeout-path",
        help="Optional closeout report or manifest path when phase=closeout.",
    ),
    report_output: str | None = typer.Option(
        None,
        "--report-output",
        help="Optional JSON path for the persisted surface-detection report.",
    ),
    checkpoint_kind: str | None = typer.Option(
        None,
        "--checkpoint-kind",
        help="Optional checkpoint kind when phase=checkpoint: manual, commit, verify_green, pr_opened, pr_merged, pause, or owner_followthrough.",
    ),
    append_note: bool = typer.Option(
        False,
        "--append-note",
        help="When phase=checkpoint, append the detected checkpoint note into aoa-sdk local session-growth storage.",
    ),
    mark_checkpoint_reviewable: bool = typer.Option(
        False,
        "--mark-checkpoint-reviewable",
        help="When used with --append-note, mark the appended checkpoint as manually reviewable.",
    ),
    root: str = typer.Option(".", "--root", help="Workspace root used for federation discovery."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    workspace = Workspace.discover(root)
    sdk = AoASDK.from_workspace(root)
    if append_note and phase != "checkpoint":
        raise typer.BadParameter("--append-note is only valid when --phase checkpoint")
    if append_note and checkpoint_kind is None:
        raise typer.BadParameter("--append-note requires --checkpoint-kind")
    report = sdk.surfaces.detect(
        repo_root=repo_root,
        phase=phase,  # type: ignore[arg-type]
        intent_text=intent_text,
        mutation_surface=mutation_surface,  # type: ignore[arg-type]
        closeout_path=closeout_path,
        checkpoint_kind=checkpoint_kind,  # type: ignore[arg-type]
    )
    report_path = _resolve_surface_report_path(
        workspace=workspace,
        repo_root=repo_root,
        phase=phase,
        report_output=report_output,
    )
    payload = _write_surface_report(report_path, report)
    checkpoint_note: SessionCheckpointNote | None = None
    if append_note:
        checkpoint_note = sdk.checkpoints.append(
            repo_root=repo_root,
            checkpoint_kind=checkpoint_kind,  # type: ignore[arg-type]
            intent_text=intent_text,
            mutation_surface=mutation_surface,  # type: ignore[arg-type]
            surface_report=report,
            surface_report_path=str(report_path),
            manual_review_requested=mark_checkpoint_reviewable,
        )
        payload = _merge_checkpoint_note(payload, checkpoint_note)
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    typer.echo(f"report_path: {payload['report_path']}")
    if checkpoint_note is not None:
        typer.echo(f"checkpoint_note_state: {checkpoint_note.state}")
        typer.echo(f"checkpoint_recommendation: {checkpoint_note.promotion_recommendation}")
    _print_surface_detection_report(report)


@surfaces_app.command("handoff")
def surfaces_handoff(
    surface_report: str = typer.Argument(..., help="Path to a persisted surface-detection report."),
    session_ref: str = typer.Option(..., "--session-ref", help="Canonical session_ref for the reviewed route."),
    reviewed: bool = typer.Option(
        True,
        "--reviewed/--not-reviewed",
        help="Surface closeout handoff is allowed only for reviewed routes.",
    ),
    report_output: str | None = typer.Option(
        None,
        "--report-output",
        help="Optional JSON path for the persisted surface closeout handoff report.",
    ),
    root: str = typer.Option(".", "--root", help="Workspace root used for federation discovery."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    if not reviewed:
        raise typer.BadParameter("surface closeout handoff requires reviewed routes; use --reviewed for the real handoff path")

    workspace = Workspace.discover(root)
    surface_detection_report = _load_surface_detection_report(surface_report)
    report = AoASDK.from_workspace(root).surfaces.build_closeout_handoff(
        surface_report,
        session_ref=session_ref,
        reviewed=reviewed,
    )
    payload = _write_surface_handoff(
        _resolve_surface_handoff_path(
            workspace=workspace,
            repo_root=surface_detection_report.repo_root,
            report_output=report_output,
        ),
        report,
    )
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    typer.echo(f"report_path: {payload['report_path']}")
    _print_surface_handoff(report)
