from __future__ import annotations

import json

import typer

from ..closeout import CloseoutAPI
from ..workspace.discovery import Workspace
from .rendering import (
    _print_kernel_next_brief,
    _print_owner_follow_through,
    _print_workflow_follow_through,
)


closeout_app = typer.Typer(help="Run bounded reviewed-session closeout orchestration")


@closeout_app.command("run")
def closeout_run(
    manifest: str = typer.Argument(..., help="Path to the reviewed session closeout manifest."),
    root: str = typer.Option(".", "--root", help="Workspace root used for federation discovery."),
    report_output: str | None = typer.Option(
        None, "--report-output", help="Optional JSON path where the closeout report should be written."
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    workspace = Workspace.discover(root)
    closeout = CloseoutAPI(workspace)
    report = closeout.run(manifest, report_output=report_output)
    payload = report.model_dump(mode="json")

    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return

    typer.echo(f"closeout_id: {report.closeout_id}")
    typer.echo(f"session_ref: {report.session_ref}")
    typer.echo(f"manifest: {report.manifest_path}")
    typer.echo(f"trigger: {report.trigger}")
    typer.echo(f"reviewed: {report.reviewed}")
    typer.echo(f"audit_only: {report.audit_only}")
    for item in report.publisher_runs:
        typer.echo(
            f"published: {item.publisher} -> {item.log_path} "
            f"(appended={item.appended_count if item.appended_count is not None else 'unknown'}, "
            f"skipped={item.duplicate_skip_count if item.duplicate_skip_count is not None else 'unknown'})"
        )
    if not report.stats_refresh.command:
        typer.echo(report.stats_refresh.stdout or "stats: skipped")
    elif report.stats_refresh.cleared:
        typer.echo(
            f"stats: cleared live state across {report.stats_refresh.source_count or 'unknown'} sources"
        )
    else:
        typer.echo(
            f"stats: refreshed {report.stats_refresh.receipt_count or 'unknown'} receipts "
            f"from {report.stats_refresh.source_count or 'unknown'} sources"
        )
    _print_kernel_next_brief(report.kernel_next_step_brief)
    _print_owner_follow_through(
        report.owner_follow_through_briefs,
        handoff_path=report.owner_handoff_path,
    )
    _print_workflow_follow_through(report.workflow_follow_through_briefs)
    if report_output:
        typer.echo(f"report: {report_output}")


@closeout_app.command("build-manifest")
def closeout_build_manifest(
    request: str = typer.Argument(..., help="Path to the reviewed closeout build request."),
    root: str = typer.Option(".", "--root", help="Workspace root used for federation discovery."),
    manifest_dir: str | None = typer.Option(
        None, "--manifest-dir", help="Override the canonical built-manifest directory."
    ),
    enqueue: bool = typer.Option(
        False, "--enqueue", help="Immediately enqueue the built manifest into the canonical inbox."
    ),
    inbox_dir: str | None = typer.Option(None, "--inbox-dir", help="Override the canonical inbox directory."),
    overwrite: bool = typer.Option(
        False, "--overwrite", help="Replace an existing built or queued manifest with the same closeout id."
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    workspace = Workspace.discover(root)
    closeout = CloseoutAPI(workspace)
    report = closeout.build_manifest(
        request,
        manifest_dir=manifest_dir,
        enqueue=enqueue,
        inbox_dir=inbox_dir,
        overwrite=overwrite,
    )
    payload = report.model_dump(mode="json")

    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return

    typer.echo(f"closeout_id: {report.closeout_id}")
    typer.echo(f"session_ref: {report.session_ref}")
    typer.echo(f"request: {report.request_path}")
    typer.echo(f"manifest: {report.manifest_path}")
    typer.echo(f"reviewed_artifact: {report.reviewed_artifact_path}")
    typer.echo(f"audit_only: {report.audit_only}")
    if report.enqueue_report is not None:
        typer.echo(f"queued_manifest: {report.enqueue_report.queued_manifest_path}")
        typer.echo(f"queue_depth: {report.enqueue_report.queue_depth}")


@closeout_app.command("submit-reviewed")
def closeout_submit_reviewed(
    reviewed_artifact: str = typer.Argument(..., help="Path to the reviewed session artifact."),
    session_ref: str = typer.Option(..., "--session-ref", help="Canonical session_ref for the reviewed session."),
    root: str = typer.Option(".", "--root", help="Workspace root used for federation discovery."),
    receipt_paths: list[str] = typer.Option(
        None,
        "--receipt-path",
        help="Receipt JSON or JSONL file to include in the closeout request. Repeat for multiple files.",
    ),
    receipt_dirs: list[str] = typer.Option(
        None,
        "--receipt-dir",
        help="Directory scanned for receipt JSON or JSONL files. Repeat for multiple directories.",
    ),
    closeout_id: str | None = typer.Option(None, "--closeout-id", help="Optional explicit closeout id."),
    audit_refs: list[str] = typer.Option(
        None,
        "--audit-ref",
        help="Extra reviewed audit artifact that should be carried into the closeout request.",
    ),
    trigger: str = typer.Option("reviewed-closeout", "--trigger", help="Closeout trigger label."),
    notes: str | None = typer.Option(None, "--notes", help="Optional closeout notes."),
    request_dir: str | None = typer.Option(None, "--request-dir", help="Override the canonical request directory."),
    manifest_dir: str | None = typer.Option(
        None, "--manifest-dir", help="Override the canonical built-manifest directory."
    ),
    inbox_dir: str | None = typer.Option(None, "--inbox-dir", help="Override the canonical inbox directory."),
    enqueue: bool = typer.Option(
        True, "--enqueue/--no-enqueue", help="Immediately enqueue the built manifest into the canonical inbox."
    ),
    allow_empty: bool = typer.Option(
        False,
        "--allow-empty",
        help="Allow audit-only reviewed closeout submission when the outer wrapper has no owner-local receipt bundle yet.",
    ),
    overwrite: bool = typer.Option(
        False, "--overwrite", help="Replace an existing request, built manifest, or queued manifest with the same id."
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    workspace = Workspace.discover(root)
    closeout = CloseoutAPI(workspace)
    report = closeout.submit_reviewed(
        reviewed_artifact,
        session_ref=session_ref,
        receipt_paths=receipt_paths or [],
        receipt_dirs=receipt_dirs or [],
        closeout_id=closeout_id,
        audit_refs=audit_refs or [],
        trigger=trigger,
        notes=notes,
        request_dir=request_dir,
        manifest_dir=manifest_dir,
        inbox_dir=inbox_dir,
        enqueue=enqueue,
        overwrite=overwrite,
        allow_empty=allow_empty,
    )
    payload = report.model_dump(mode="json")

    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return

    typer.echo(f"closeout_id: {report.closeout_id}")
    typer.echo(f"session_ref: {report.session_ref}")
    typer.echo(f"request: {report.request_path}")
    typer.echo(f"reviewed_artifact: {report.reviewed_artifact_path}")
    typer.echo(f"audit_only: {report.audit_only}")
    typer.echo(f"receipt_count: {len(report.receipt_paths)}")
    typer.echo(f"publishers: {', '.join(report.detected_publishers)}")
    typer.echo(f"manifest: {report.build_report.manifest_path}")
    if report.build_report.enqueue_report is not None:
        typer.echo(f"queued_manifest: {report.build_report.enqueue_report.queued_manifest_path}")
        typer.echo(f"queue_depth: {report.build_report.enqueue_report.queue_depth}")


@closeout_app.command("enqueue-current")
def closeout_enqueue_current(
    manifest: str = typer.Argument(..., help="Path to the reviewed closeout manifest to queue."),
    root: str = typer.Option(".", "--root", help="Workspace root used for federation discovery."),
    inbox_dir: str | None = typer.Option(None, "--inbox-dir", help="Override the canonical inbox directory."),
    overwrite: bool = typer.Option(
        False, "--overwrite", help="Replace an existing queued manifest with the same closeout id."
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    workspace = Workspace.discover(root)
    closeout = CloseoutAPI(workspace)
    report = closeout.enqueue(manifest, inbox_dir=inbox_dir, overwrite=overwrite)
    payload = report.model_dump(mode="json")

    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return

    typer.echo(f"closeout_id: {report.closeout_id}")
    typer.echo(f"session_ref: {report.session_ref}")
    typer.echo(f"source_manifest: {report.source_manifest_path}")
    typer.echo(f"queued_manifest: {report.queued_manifest_path}")
    typer.echo(f"queue_depth: {report.queue_depth}")
    typer.echo(f"overwritten: {'yes' if report.overwritten else 'no'}")


@closeout_app.command("process-inbox")
def closeout_process_inbox(
    root: str = typer.Argument(".", help="Workspace root used for federation discovery."),
    inbox_dir: str | None = typer.Option(None, "--inbox-dir", help="Override the inbox directory."),
    processed_dir: str | None = typer.Option(
        None, "--processed-dir", help="Override the processed-manifest directory."
    ),
    failed_dir: str | None = typer.Option(None, "--failed-dir", help="Override the failed-manifest directory."),
    report_dir: str | None = typer.Option(None, "--report-dir", help="Override the closeout report directory."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    workspace = Workspace.discover(root)
    closeout = CloseoutAPI(workspace)
    report = closeout.process_inbox(
        inbox_dir=inbox_dir,
        processed_dir=processed_dir,
        failed_dir=failed_dir,
        report_dir=report_dir,
    )
    payload = report.model_dump(mode="json")

    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
    else:
        typer.echo(f"inbox: {report.inbox_dir}")
        typer.echo(f"processed: {report.processed_count}")
        typer.echo(f"failed: {report.failed_count}")
        for item in report.items:
            summary = item.archived_manifest_path or item.manifest_path
            typer.echo(f"{item.status}: {summary}")
            if item.report_path:
                typer.echo(f"  report: {item.report_path}")
            _print_kernel_next_brief(item.kernel_next_step_brief, indent="  ")
            _print_owner_follow_through(
                item.owner_follow_through_briefs,
                handoff_path=item.owner_handoff_path,
                indent="  ",
            )
            _print_workflow_follow_through(
                item.workflow_follow_through_briefs,
                indent="  ",
            )
            if item.error:
                typer.echo(f"  error: {item.error}")

    if report.failed_count:
        raise typer.Exit(code=1)


@closeout_app.command("status")
def closeout_status(
    root: str = typer.Argument(".", help="Workspace root used for federation discovery."),
    request_dir: str | None = typer.Option(None, "--request-dir", help="Override the request directory."),
    manifest_dir: str | None = typer.Option(None, "--manifest-dir", help="Override the built-manifest directory."),
    inbox_dir: str | None = typer.Option(None, "--inbox-dir", help="Override the inbox directory."),
    processed_dir: str | None = typer.Option(
        None, "--processed-dir", help="Override the processed-manifest directory."
    ),
    failed_dir: str | None = typer.Option(None, "--failed-dir", help="Override the failed-manifest directory."),
    report_dir: str | None = typer.Option(None, "--report-dir", help="Override the closeout report directory."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    workspace = Workspace.discover(root)
    closeout = CloseoutAPI(workspace)
    report = closeout.status(
        request_dir=request_dir,
        manifest_dir=manifest_dir,
        inbox_dir=inbox_dir,
        processed_dir=processed_dir,
        failed_dir=failed_dir,
        report_dir=report_dir,
    )
    payload = report.model_dump(mode="json")

    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return

    typer.echo(f"root: {report.root_dir}")
    typer.echo(f"requests: {report.request_dir}")
    typer.echo(f"manifests: {report.manifest_dir}")
    typer.echo(f"inbox: {report.inbox_dir}")
    typer.echo(f"review_requests: {report.request_count}")
    typer.echo(f"built_manifests: {report.manifest_count}")
    typer.echo(f"pending: {report.pending_manifest_count}")
    typer.echo(f"processed: {report.processed_manifest_count}")
    typer.echo(f"failed: {report.failed_manifest_count}")
    typer.echo(f"reports: {report.report_count}")
    typer.echo(f"handoffs: {report.handoff_count}")
    if report.latest_request_path:
        typer.echo(f"latest_request: {report.latest_request_path}")
    if report.latest_manifest_path:
        typer.echo(f"latest_manifest: {report.latest_manifest_path}")
    if report.latest_report_path:
        typer.echo(f"latest_report: {report.latest_report_path}")
    if report.latest_handoff_path:
        typer.echo(f"latest_handoff: {report.latest_handoff_path}")
    if report.latest_processed_manifest_path:
        typer.echo(f"latest_processed: {report.latest_processed_manifest_path}")
    if report.latest_failed_manifest_path:
        typer.echo(f"latest_failed: {report.latest_failed_manifest_path}")
