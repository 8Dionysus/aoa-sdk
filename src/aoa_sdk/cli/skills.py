from __future__ import annotations

import json

import typer

from ..api import AoASDK
from ..skills.detector import enrich_report_with_checkpoint_bridge
from ..workspace.discovery import Workspace
from .common import (
    _merge_checkpoint_capture,
    _resolve_host_available_skills,
    _resolve_skill_report_path,
    _write_skill_report,
)
from .rendering import _print_checkpoint_capture, _print_skill_detection_report


skills_app = typer.Typer(help="Read project skill layers and run phase-aware skill detection/dispatch")


@skills_app.command("detect")
def skills_detect(
    repo_root: str = typer.Argument(..., help="Repository root or repo-relative path used as task context."),
    phase: str = typer.Option(..., "--phase", help="Detection phase: ingress, pre-mutation, checkpoint, or closeout."),
    intent_text: str = typer.Option("", "--intent-text", help="Intent text used for tiny-router style matching."),
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
    host_skill: list[str] = typer.Option(
        None,
        "--host-skill",
        help="Repeatable host-visible skill name used to annotate recommendation availability.",
    ),
    host_skill_manifest: str | None = typer.Option(
        None,
        "--host-skill-manifest",
        help="Optional JSON manifest with {'skills': [...]} used to annotate host-visible skill availability.",
    ),
    root: str = typer.Option(".", "--root", help="Workspace root used for federation discovery."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    host_available_skills, host_availability_source = _resolve_host_available_skills(
        host_skills=host_skill,
        host_skill_manifest=host_skill_manifest,
    )
    sdk_report = AoASDK.from_workspace(root).skills.detect(
        repo_root=repo_root,
        phase=phase,  # type: ignore[arg-type]
        intent_text=intent_text,
        mutation_surface=mutation_surface,  # type: ignore[arg-type]
        closeout_path=closeout_path,
        host_available_skills=host_available_skills,
        host_availability_source=host_availability_source,  # type: ignore[arg-type]
    )
    payload = sdk_report.model_dump(mode="json")
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    _print_skill_detection_report(sdk_report)


@skills_app.command("dispatch")
def skills_dispatch(
    repo_root: str = typer.Argument(..., help="Repository root or repo-relative path used as task context."),
    phase: str = typer.Option(..., "--phase", help="Dispatch phase: ingress, pre-mutation, checkpoint, or closeout."),
    intent_text: str = typer.Option("", "--intent-text", help="Intent text used for tiny-router style matching."),
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
    session_file: str | None = typer.Option(
        None,
        "--session-file",
        help="Optional skill runtime session file. Defaults to the canonical session contract path.",
    ),
    host_skill: list[str] = typer.Option(
        None,
        "--host-skill",
        help="Repeatable host-visible skill name used to annotate recommendation availability.",
    ),
    host_skill_manifest: str | None = typer.Option(
        None,
        "--host-skill-manifest",
        help="Optional JSON manifest with {'skills': [...]} used to annotate host-visible skill availability.",
    ),
    root: str = typer.Option(".", "--root", help="Workspace root used for federation discovery."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    host_available_skills, host_availability_source = _resolve_host_available_skills(
        host_skills=host_skill,
        host_skill_manifest=host_skill_manifest,
    )
    sdk_report = AoASDK.from_workspace(root).skills.dispatch(
        repo_root=repo_root,
        phase=phase,  # type: ignore[arg-type]
        intent_text=intent_text,
        mutation_surface=mutation_surface,  # type: ignore[arg-type]
        closeout_path=closeout_path,
        session_file=session_file,
        host_available_skills=host_available_skills,
        host_availability_source=host_availability_source,  # type: ignore[arg-type]
    )
    payload = sdk_report.model_dump(mode="json")
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    _print_skill_detection_report(sdk_report)


@skills_app.command("enter")
def skills_enter(
    repo_root: str = typer.Argument(".", help="Repository root or workspace root used as task context."),
    intent_text: str = typer.Option("", "--intent-text", help="Short task summary used for ingress detection."),
    session_file: str | None = typer.Option(
        None,
        "--session-file",
        help="Optional skill runtime session file. Defaults to the canonical session contract path.",
    ),
    report_output: str | None = typer.Option(
        None,
        "--report-output",
        help="Optional JSON path for the persisted ingress dispatch report.",
    ),
    checkpoint_kind: str | None = typer.Option(
        None,
        "--checkpoint-kind",
        help="Optional explicit checkpoint kind to append after ingress dispatch: manual, commit, verify_green, pr_opened, pr_merged, pause, or owner_followthrough.",
    ),
    mark_checkpoint_reviewable: bool = typer.Option(
        False,
        "--mark-checkpoint-reviewable",
        help="When a checkpoint is appended explicitly or automatically, mark it as manually reviewable.",
    ),
    auto_checkpoint: bool = typer.Option(
        True,
        "--auto-checkpoint/--no-auto-checkpoint",
        help="Ingress stays read-only by default; use --checkpoint-kind when an explicit checkpoint append is intended.",
    ),
    host_skill: list[str] = typer.Option(
        None,
        "--host-skill",
        help="Repeatable host-visible skill name used to annotate recommendation availability.",
    ),
    host_skill_manifest: str | None = typer.Option(
        None,
        "--host-skill-manifest",
        help="Optional JSON manifest with {'skills': [...]} used to annotate host-visible skill availability.",
    ),
    root: str = typer.Option(".", "--root", help="Workspace root used for federation discovery."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    workspace = Workspace.discover(root)
    sdk = AoASDK.from_workspace(root)
    host_available_skills, host_availability_source = _resolve_host_available_skills(
        host_skills=host_skill,
        host_skill_manifest=host_skill_manifest,
    )
    sdk_report = sdk.skills.dispatch(
        repo_root=repo_root,
        phase="ingress",
        intent_text=intent_text,
        mutation_surface="none",
        session_file=session_file,
        host_available_skills=host_available_skills,
        host_availability_source=host_availability_source,  # type: ignore[arg-type]
    )
    report_path = _resolve_skill_report_path(
        workspace=workspace,
        repo_root=repo_root,
        phase="ingress",
        report_output=report_output,
    )
    payload = _write_skill_report(report_path, sdk_report)
    checkpoint_capture = sdk.checkpoints.capture_from_skill_phase(
        repo_root=repo_root,
        phase="ingress",
        intent_text=intent_text,
        mutation_surface="none",
        session_file=session_file,
        skill_report_path=str(report_path),
        checkpoint_kind=checkpoint_kind,  # type: ignore[arg-type]
        manual_review_requested=mark_checkpoint_reviewable,
        auto_capture=auto_checkpoint,
    )
    sdk_report = enrich_report_with_checkpoint_bridge(
        workspace,
        report=sdk_report,
        repo_root=repo_root,
        checkpoint_capture=checkpoint_capture,
        host_available_skills=host_available_skills,
        host_availability_source=host_availability_source,  # type: ignore[arg-type]
    )
    payload = _write_skill_report(report_path, sdk_report)
    payload = _merge_checkpoint_capture(payload, checkpoint_capture)
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    typer.echo(f"report_path: {payload['report_path']}")
    _print_checkpoint_capture(checkpoint_capture)
    if checkpoint_capture.note is not None:
        typer.echo(f"checkpoint_note_state: {checkpoint_capture.note.state}")
        typer.echo(f"checkpoint_recommendation: {checkpoint_capture.note.promotion_recommendation}")
    _print_skill_detection_report(sdk_report)


@skills_app.command("guard")
def skills_guard(
    repo_root: str = typer.Argument(..., help="Repository root or workspace root used as task context."),
    intent_text: str = typer.Option("", "--intent-text", help="Short task summary used for pre-mutation detection."),
    mutation_surface: str = typer.Option(
        "code",
        "--mutation-surface",
        help="Mutation class: code, repo-config, infra, runtime, or public-share.",
    ),
    session_file: str | None = typer.Option(
        None,
        "--session-file",
        help="Optional skill runtime session file. Defaults to the canonical session contract path.",
    ),
    report_output: str | None = typer.Option(
        None,
        "--report-output",
        help="Optional JSON path for the persisted pre-mutation dispatch report.",
    ),
    checkpoint_kind: str | None = typer.Option(
        None,
        "--checkpoint-kind",
        help="Optional explicit checkpoint kind to append after guard dispatch: manual, commit, verify_green, pr_opened, pr_merged, pause, or owner_followthrough.",
    ),
    mark_checkpoint_reviewable: bool = typer.Option(
        False,
        "--mark-checkpoint-reviewable",
        help="When a checkpoint is appended explicitly or automatically, mark it as manually reviewable.",
    ),
    auto_checkpoint: bool = typer.Option(
        True,
        "--auto-checkpoint/--no-auto-checkpoint",
        help="Auto-append one local checkpoint note only when checkpoint-phase surface detection finds a real growth signal.",
    ),
    host_skill: list[str] = typer.Option(
        None,
        "--host-skill",
        help="Repeatable host-visible skill name used to annotate recommendation availability.",
    ),
    host_skill_manifest: str | None = typer.Option(
        None,
        "--host-skill-manifest",
        help="Optional JSON manifest with {'skills': [...]} used to annotate host-visible skill availability.",
    ),
    root: str = typer.Option(".", "--root", help="Workspace root used for federation discovery."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    workspace = Workspace.discover(root)
    sdk = AoASDK.from_workspace(root)
    host_available_skills, host_availability_source = _resolve_host_available_skills(
        host_skills=host_skill,
        host_skill_manifest=host_skill_manifest,
    )
    sdk_report = sdk.skills.dispatch(
        repo_root=repo_root,
        phase="pre-mutation",
        intent_text=intent_text,
        mutation_surface=mutation_surface,  # type: ignore[arg-type]
        session_file=session_file,
        host_available_skills=host_available_skills,
        host_availability_source=host_availability_source,  # type: ignore[arg-type]
    )
    report_path = _resolve_skill_report_path(
        workspace=workspace,
        repo_root=repo_root,
        phase="pre-mutation",
        mutation_surface=mutation_surface,
        report_output=report_output,
    )
    payload = _write_skill_report(report_path, sdk_report)
    checkpoint_capture = sdk.checkpoints.capture_from_skill_phase(
        repo_root=repo_root,
        phase="pre-mutation",
        intent_text=intent_text,
        mutation_surface=mutation_surface,  # type: ignore[arg-type]
        session_file=session_file,
        skill_report_path=str(report_path),
        checkpoint_kind=checkpoint_kind,  # type: ignore[arg-type]
        manual_review_requested=mark_checkpoint_reviewable,
        auto_capture=auto_checkpoint,
    )
    sdk_report = enrich_report_with_checkpoint_bridge(
        workspace,
        report=sdk_report,
        repo_root=repo_root,
        checkpoint_capture=checkpoint_capture,
        host_available_skills=host_available_skills,
        host_availability_source=host_availability_source,  # type: ignore[arg-type]
    )
    payload = _write_skill_report(report_path, sdk_report)
    payload = _merge_checkpoint_capture(payload, checkpoint_capture)
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    typer.echo(f"report_path: {payload['report_path']}")
    _print_checkpoint_capture(checkpoint_capture)
    if checkpoint_capture.note is not None:
        typer.echo(f"checkpoint_note_state: {checkpoint_capture.note.state}")
        typer.echo(f"checkpoint_recommendation: {checkpoint_capture.note.promotion_recommendation}")
    _print_skill_detection_report(sdk_report)
