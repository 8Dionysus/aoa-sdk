from __future__ import annotations

import json
from typing import Any

import typer

from ..closeout import CloseoutAPI
from ..compatibility import CompatibilityAPI
from ..workspace.discovery import Workspace
from ..workspace.roots import KNOWN_REPOS

app = typer.Typer(help="AoA SDK CLI")
workspace_app = typer.Typer(help="Inspect workspace topology")
compatibility_app = typer.Typer(help="Inspect compatibility of consumed surfaces")
closeout_app = typer.Typer(help="Run bounded reviewed-session closeout orchestration")

app.add_typer(workspace_app, name="workspace")
app.add_typer(compatibility_app, name="compatibility")
app.add_typer(closeout_app, name="closeout")


def _workspace_payload(workspace: Workspace) -> dict[str, Any]:
    repos: dict[str, dict[str, str | None]] = {}
    for repo in KNOWN_REPOS:
        path = workspace.repo_roots.get(repo)
        origin = workspace.repo_origins.get(repo)
        repos[repo] = {
            "path": str(path) if path is not None else None,
            "origin": origin,
        }
    return {
        "root": str(workspace.root),
        "federation_root": str(workspace.federation_root),
        "federation_root_source": workspace.federation_root_source,
        "manifest": str(workspace.manifest_path) if workspace.manifest_path else None,
        "repos": repos,
    }


@app.command()
def version() -> None:
    print("aoa-sdk 0.1.0")


@workspace_app.command("inspect")
def workspace_inspect(
    root: str = typer.Argument("."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    workspace = Workspace.discover(root)
    payload = _workspace_payload(workspace)

    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return

    typer.echo(f"root: {payload['root']}")
    typer.echo(f"federation_root: {payload['federation_root']}")
    typer.echo(f"federation_root_source: {payload['federation_root_source']}")
    typer.echo(f"manifest: {payload['manifest'] or 'none'}")

    for repo in KNOWN_REPOS:
        repo_payload = payload["repos"][repo]
        path = repo_payload["path"]
        origin = repo_payload["origin"]
        if path is None:
            typer.echo(f"{repo}: missing")
            continue
        typer.echo(f"{repo}: {path} [{origin}]")


@compatibility_app.command("check")
def compatibility_check(
    root: str = typer.Argument("."),
    repo: str | None = typer.Option(None, "--repo", help="Restrict checks to one repo."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    workspace = Workspace.discover(root)
    compatibility = CompatibilityAPI(workspace)

    if repo is not None and repo not in KNOWN_REPOS:
        raise typer.BadParameter(f"unknown repo {repo!r}")

    checks = compatibility.check_repo(repo) if repo is not None else compatibility.check_all()
    if repo is not None and not checks:
        raise typer.BadParameter(f"no compatibility rules registered for repo {repo!r}")

    payload = {
        "root": str(workspace.root),
        "federation_root": str(workspace.federation_root),
        "repo": repo,
        "compatible": all(check.compatible for check in checks),
        "checks": [check.model_dump(mode="json") for check in checks],
    }

    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
    else:
        typer.echo(f"root: {payload['root']}")
        typer.echo(f"federation_root: {payload['federation_root']}")
        typer.echo(f"repo: {repo or 'all'}")
        for check in checks:
            status = "ok" if check.compatible else "fail"
            typer.echo(f"{status}: {check.surface_id} -> {check.reason}")

    if not payload["compatible"]:
        raise typer.Exit(code=1)


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
    for item in report.publisher_runs:
        typer.echo(
            f"published: {item.publisher} -> {item.log_path} "
            f"(appended={item.appended_count if item.appended_count is not None else 'unknown'}, "
            f"skipped={item.duplicate_skip_count if item.duplicate_skip_count is not None else 'unknown'})"
        )
    if report.stats_refresh.cleared:
        typer.echo(
            f"stats: cleared live state across {report.stats_refresh.source_count or 'unknown'} sources"
        )
    else:
        typer.echo(
            f"stats: refreshed {report.stats_refresh.receipt_count or 'unknown'} receipts "
            f"from {report.stats_refresh.source_count or 'unknown'} sources"
        )
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
    if report.enqueue_report is not None:
        typer.echo(f"queued_manifest: {report.enqueue_report.queued_manifest_path}")
        typer.echo(f"queue_depth: {report.enqueue_report.queue_depth}")


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
            if item.error:
                typer.echo(f"  error: {item.error}")

    if report.failed_count:
        raise typer.Exit(code=1)


@closeout_app.command("status")
def closeout_status(
    root: str = typer.Argument(".", help="Workspace root used for federation discovery."),
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
    typer.echo(f"manifests: {report.manifest_dir}")
    typer.echo(f"inbox: {report.inbox_dir}")
    typer.echo(f"built_manifests: {report.manifest_count}")
    typer.echo(f"pending: {report.pending_manifest_count}")
    typer.echo(f"processed: {report.processed_manifest_count}")
    typer.echo(f"failed: {report.failed_manifest_count}")
    typer.echo(f"reports: {report.report_count}")
    if report.latest_manifest_path:
        typer.echo(f"latest_manifest: {report.latest_manifest_path}")
    if report.latest_report_path:
        typer.echo(f"latest_report: {report.latest_report_path}")
    if report.latest_processed_manifest_path:
        typer.echo(f"latest_processed: {report.latest_processed_manifest_path}")
    if report.latest_failed_manifest_path:
        typer.echo(f"latest_failed: {report.latest_failed_manifest_path}")


if __name__ == "__main__":
    app()
