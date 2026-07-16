from __future__ import annotations

import json

import typer

from ..api import AoASDK
from .common import (
    _resolve_checkpoint_git_boundary,
    _resolve_checkpoint_hook_repos,
    _resolve_checkpoint_managed_hooks,
)
from .rendering import (
    _print_checkpoint_after_commit_report,
    _print_checkpoint_backlog_audit,
    _print_candidate_intelligence_report,
    _print_carrier_intelligence_report,
    _print_checkpoint_git_boundary,
    _print_checkpoint_hook_install,
    _print_checkpoint_hook_status,
    _print_checkpoint_lifecycle_archive_result,
    _print_checkpoint_lifecycle_audit,
    _print_checkpoint_note,
    _print_checkpoint_promotion,
    _print_checkpoint_session_reconcile_result,
    _print_closeout_context,
    _print_closeout_materialization_report,
)


checkpoint_app = typer.Typer(help="Capture checkpoint-aware session-growth notes and reviewed promotions")


@checkpoint_app.command("append")
def checkpoint_append(
    repo_root: str = typer.Argument(..., help="Repository root or repo-relative path used as the checkpoint context."),
    kind: str = typer.Option(
        ...,
        "--kind",
        help="Checkpoint kind: manual, commit, verify_green, pr_opened, pr_merged, pause, or owner_followthrough.",
    ),
    intent_text: str = typer.Option("", "--intent-text", help="Intent text used for checkpoint-aware surface detection."),
    mutation_surface: str = typer.Option(
        "none",
        "--mutation-surface",
        help="Mutation class: none, code, repo-config, infra, runtime, or public-share.",
    ),
    runtime_session_file: str | None = typer.Option(
        None,
        "--runtime-session-file",
        help="Optional external runtime session metadata file.",
    ),
    mark_reviewable: bool = typer.Option(
        False,
        "--mark-reviewable",
        help="Mark this checkpoint as manually reviewable even if repeat density is still low.",
    ),
    root: str = typer.Option(".", "--root", help="Workspace root used for federation discovery."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    note = AoASDK.from_workspace(root).checkpoints.append(
        repo_root=repo_root,
        checkpoint_kind=kind,  # type: ignore[arg-type]
        intent_text=intent_text,
        mutation_surface=mutation_surface,  # type: ignore[arg-type]
        runtime_session_file=runtime_session_file,
        manual_review_requested=mark_reviewable,
    )
    payload = note.model_dump(mode="json")
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    _print_checkpoint_note(note)


@checkpoint_app.command("mark")
def checkpoint_mark(
    repo_root: str = typer.Argument(..., help="Repository root or repo-relative path used as the checkpoint context."),
    kind: str = typer.Option(
        ...,
        "--kind",
        help="Checkpoint kind: manual, commit, verify_green, pr_opened, pr_merged, pause, or owner_followthrough.",
    ),
    intent_text: str = typer.Option(
        ...,
        "--intent-text",
        help="Concrete milestone summary to record in the session checkpoint ledger.",
    ),
    mutation_surface: str = typer.Option(
        "none",
        "--mutation-surface",
        help="Mutation class: none, code, repo-config, infra, runtime, or public-share.",
    ),
    runtime_session_file: str | None = typer.Option(
        None,
        "--runtime-session-file",
        help="Optional external runtime session metadata file.",
    ),
    mark_reviewable: bool = typer.Option(
        True,
        "--mark-reviewable/--no-mark-reviewable",
        help="Mark this explicit milestone as manually reviewable by default.",
    ),
    root: str = typer.Option(".", "--root", help="Workspace root used for federation discovery."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    note = AoASDK.from_workspace(root).checkpoints.append(
        repo_root=repo_root,
        checkpoint_kind=kind,  # type: ignore[arg-type]
        intent_text=intent_text,
        mutation_surface=mutation_surface,  # type: ignore[arg-type]
        runtime_session_file=runtime_session_file,
        manual_review_requested=mark_reviewable,
    )
    payload = note.model_dump(mode="json")
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    _print_checkpoint_note(note)


@checkpoint_app.command("after-commit")
def checkpoint_after_commit(
    repo_root: str = typer.Argument(..., help="Repository root or repo-relative path used as the checkpoint context."),
    commit_ref: str = typer.Option("HEAD", "--commit-ref", help="Committed git ref to capture, usually HEAD."),
    checkpoint_kind: str = typer.Option(
        "auto",
        "--kind",
        "--checkpoint-kind",
        help="Post-commit checkpoint kind: auto, commit, or owner_followthrough.",
    ),
    runtime_session_file: str | None = typer.Option(
        None,
        "--runtime-session-file",
        help="Optional external runtime session metadata file; otherwise host environment identity is used.",
    ),
    root: str = typer.Option(".", "--root", help="Workspace root used for federation discovery."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    report = AoASDK.from_workspace(root).checkpoints.after_commit(
        repo_root=repo_root,
        commit_ref=commit_ref,
        runtime_session_file=runtime_session_file,
        checkpoint_kind=checkpoint_kind,  # type: ignore[arg-type]
    )
    payload = report.model_dump(mode="json")
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    _print_checkpoint_after_commit_report(report)


@checkpoint_app.command("review-note")
def checkpoint_review_note(
    repo_root: str = typer.Argument(..., help="Repository root or repo-relative path used as the checkpoint context."),
    commit_ref: str = typer.Option("HEAD", "--commit-ref", help="Committed git ref being reviewed."),
    auto: bool = typer.Option(
        False,
        "--auto",
        help="Auto-fill the checkpoint review from the matching auto observation when summary or note lists are omitted.",
    ),
    summary: str | None = typer.Option(
        None,
        "--summary",
        help="Agent-authored summary for this checkpoint review. Required unless --auto is used.",
    ),
    finding: list[str] = typer.Option(
        None,
        "--finding",
        help="Agent-authored finding to carry into the session checkpoint note. Repeat for multiple findings.",
    ),
    candidate_note: list[str] = typer.Option(
        None,
        "--candidate-note",
        help="Agent-authored candidate note naming what/why/owner/where. Repeat for multiple notes.",
    ),
    stats_hint: list[str] = typer.Option(
        None,
        "--stats-hint",
        help="Agent-authored stats hint to verify at reviewed closeout. Repeat for multiple hints.",
    ),
    mechanic_hint: list[str] = typer.Option(
        None,
        "--mechanic-hint",
        help="Agent-authored mechanism or workflow hint to revisit at closeout. Repeat for multiple hints.",
    ),
    closeout_question: list[str] = typer.Option(
        None,
        "--closeout-question",
        help="Question the agent should answer when rereading the full session at closeout. Repeat for multiple questions.",
    ),
    evidence_ref: list[str] = typer.Option(
        None,
        "--evidence-ref",
        help="Evidence reference the agent used while reviewing this checkpoint. Repeat for multiple refs.",
    ),
    next_owner_move: list[str] = typer.Option(
        None,
        "--next-owner-move",
        help="Deferred owner move to consider only at reviewed closeout. Repeat for multiple moves.",
    ),
    related_capability_ref: list[str] = typer.Option(
        None,
        "--related-capability-ref",
        help="Capability related to the review; this does not claim execution. Repeat for multiple refs.",
    ),
    runtime_session_file: str | None = typer.Option(
        None,
        "--runtime-session-file",
        help="Optional external runtime session metadata file; otherwise host environment identity is used.",
    ),
    runtime_session_id: str | None = typer.Option(
        None,
        "--runtime-session-id",
        help="Explicit checkpoint runtime session id for reviewing a stale scoped checkpoint note.",
    ),
    root: str = typer.Option(".", "--root", help="Workspace root used for federation discovery."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    note = AoASDK.from_workspace(root).checkpoints.review_note(
        repo_root=repo_root,
        commit_ref=commit_ref,
        summary=summary,
        auto_fill=auto,
        findings=finding or [],
        candidate_notes=candidate_note or [],
        stats_hints=stats_hint or [],
        mechanic_hints=mechanic_hint or [],
        closeout_questions=closeout_question or [],
        evidence_refs=evidence_ref or [],
        next_owner_moves=next_owner_move or [],
        related_capability_refs=related_capability_ref or [],
        runtime_session_file=runtime_session_file,
        runtime_session_id=runtime_session_id,
    )
    payload = note.model_dump(mode="json")
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    _print_checkpoint_note(note)


@checkpoint_app.command("install-hook")
def checkpoint_install_hook(
    repo: str | None = typer.Option(None, "--repo", help="Repository name that should receive the managed checkpoint hooks."),
    all_owner: bool = typer.Option(
        False,
        "--all-owner",
        help="Install hooks for every mutable owner repo discovered in the workspace.",
    ),
    hook: str = typer.Option(
        "all",
        "--hook",
        help="Managed checkpoint hook to install: post-commit, pre-push, pre-merge-commit, or all.",
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Replace stale existing hook files with the current managed checkpoint hook template.",
    ),
    root: str = typer.Option(".", "--root", help="Workspace root used for federation discovery."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    sdk = AoASDK.from_workspace(root)
    repo_names = _resolve_checkpoint_hook_repos(
        workspace=sdk.workspace,
        repo=repo,
        all_owner=all_owner,
        allow_readonly=True,
    )
    hook_names = _resolve_checkpoint_managed_hooks(hook)
    results = [
        sdk.checkpoints.install_hook(repo_name=repo_name, hook_name=hook_name, overwrite=overwrite)
        for repo_name in repo_names
        for hook_name in hook_names
    ]
    payload = {
        "workspace_root": str(sdk.workspace.root),
        "results": [result.model_dump(mode="json") for result in results],
    }
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    for result in results:
        _print_checkpoint_hook_install(result)


@checkpoint_app.command("hook-status")
def checkpoint_hook_status(
    repo: str | None = typer.Option(None, "--repo", help="Repository name whose managed checkpoint hooks should be inspected."),
    all_owner: bool = typer.Option(
        False,
        "--all-owner",
        help="Inspect hook status for every mutable owner repo discovered in the workspace.",
    ),
    hook: str = typer.Option(
        "all",
        "--hook",
        help="Managed checkpoint hook to inspect: post-commit, pre-push, pre-merge-commit, or all.",
    ),
    root: str = typer.Option(".", "--root", help="Workspace root used for federation discovery."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    sdk = AoASDK.from_workspace(root)
    repo_names = _resolve_checkpoint_hook_repos(
        workspace=sdk.workspace,
        repo=repo,
        all_owner=all_owner,
        allow_readonly=True,
    )
    hook_names = _resolve_checkpoint_managed_hooks(hook)
    statuses = [
        sdk.checkpoints.hook_status(repo_name=repo_name, hook_name=hook_name)
        for repo_name in repo_names
        for hook_name in hook_names
    ]
    payload = {
        "workspace_root": str(sdk.workspace.root),
        "results": [status.model_dump(mode="json") for status in statuses],
    }
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    for status in statuses:
        _print_checkpoint_hook_status(status)


@checkpoint_app.command("git-boundary-check")
def checkpoint_git_boundary_check(
    repo_root: str = typer.Argument(..., help="Repository root or repo name whose current checkpoint note should gate the git boundary."),
    boundary: str = typer.Option(
        ...,
        "--boundary",
        help="Git boundary to check: push or merge.",
    ),
    runtime_session_file: str | None = typer.Option(
        None,
        "--runtime-session-file",
        help="Optional external host runtime metadata file; otherwise host environment identity is used.",
    ),
    root: str = typer.Option(".", "--root", help="Workspace root used for federation discovery."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    resolved_boundary = _resolve_checkpoint_git_boundary(boundary)
    report = AoASDK.from_workspace(root).checkpoints.git_boundary_check(
        repo_root=repo_root,
        boundary=resolved_boundary,
        runtime_session_file=runtime_session_file,
    )
    payload = report.model_dump(mode="json")
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
    else:
        _print_checkpoint_git_boundary(report)
    if report.status in {"blocked_pending_review", "blocked_unresolved_checkpoint"}:
        raise typer.Exit(1)


@checkpoint_app.command("status")
def checkpoint_status(
    repo_root: str = typer.Argument(..., help="Repository root or repo-relative path used as the checkpoint context."),
    runtime_session_file: str | None = typer.Option(
        None,
        "--runtime-session-file",
        help="Optional external host runtime metadata file; otherwise host environment identity is used.",
    ),
    root: str = typer.Option(".", "--root", help="Workspace root used for federation discovery."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    note = AoASDK.from_workspace(root).checkpoints.status(repo_root=repo_root, runtime_session_file=runtime_session_file)
    payload = note.model_dump(mode="json")
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    _print_checkpoint_note(note)


@checkpoint_app.command("candidate-intelligence")
def checkpoint_candidate_intelligence(
    repo_root: str = typer.Argument(
        ...,
        help="Repository root or repo-relative path used as the checkpoint context.",
    ),
    sample_limit: int = typer.Option(
        0,
        "--sample-limit",
        min=0,
        help="Bounded number of unreviewed classifier samples to include.",
    ),
    write_index: bool = typer.Option(
        False,
        "--write-index/--no-write-index",
        help="Write the generated checkpoint candidate-intelligence navigation index.",
    ),
    runtime_session_file: str | None = typer.Option(
        None,
        "--runtime-session-file",
        help="Optional external host runtime metadata file; otherwise host environment identity is used.",
    ),
    root: str = typer.Option(".", "--root", help="Workspace root used for federation discovery."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    report = AoASDK.from_workspace(root).checkpoints.candidate_intelligence(
        repo_root=repo_root,
        runtime_session_file=runtime_session_file,
        sample_limit=sample_limit,
        write_index=write_index,
    )
    payload = report.model_dump(mode="json")
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    _print_candidate_intelligence_report(report)


@checkpoint_app.command("carrier-intelligence")
def checkpoint_carrier_intelligence(
    repo_root: str = typer.Argument(
        ...,
        help="Repository root or repo-relative path used as the checkpoint context.",
    ),
    sample_limit: int = typer.Option(
        0,
        "--sample-limit",
        min=0,
        help="Bounded number of unreviewed carrier samples to include.",
    ),
    write_index: bool = typer.Option(
        False,
        "--write-index/--no-write-index",
        help="Write the generated checkpoint carrier-candidate navigation index.",
    ),
    runtime_session_file: str | None = typer.Option(
        None,
        "--runtime-session-file",
        help="Optional external host runtime metadata file; otherwise host environment identity is used.",
    ),
    root: str = typer.Option(".", "--root", help="Workspace root used for federation discovery."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    report = AoASDK.from_workspace(root).checkpoints.carrier_intelligence(
        repo_root=repo_root,
        runtime_session_file=runtime_session_file,
        sample_limit=sample_limit,
        write_index=write_index,
    )
    payload = report.model_dump(mode="json")
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    _print_carrier_intelligence_report(report)


@checkpoint_app.command("lifecycle-audit")
def checkpoint_lifecycle_audit(
    repo_root: str | None = typer.Argument(
        None,
        help="Optional repository root or repo name used to filter checkpoint lifecycle entries.",
    ),
    runtime_session_file: str | None = typer.Option(
        None,
        "--runtime-session-file",
        help="Optional external host runtime metadata file; otherwise host environment identity is used.",
    ),
    root: str = typer.Option(".", "--root", help="Workspace root used for federation discovery."),
    write_index: bool = typer.Option(
        False,
        "--write-index/--no-write-index",
        help="Write the generated checkpoint lifecycle navigation index.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    report = AoASDK.from_workspace(root).checkpoints.lifecycle_audit(
        repo_root=repo_root,
        runtime_session_file=runtime_session_file,
        write_index=write_index,
    )
    payload = report.model_dump(mode="json")
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    _print_checkpoint_lifecycle_audit(report)


@checkpoint_app.command("backlog-audit")
def checkpoint_backlog_audit(
    repo_root: str | None = typer.Argument(
        None,
        help="Optional repository root or repo name used to filter checkpoint backlog entries.",
    ),
    runtime_session_file: str | None = typer.Option(
        None,
        "--runtime-session-file",
        help="Optional external host runtime metadata file; otherwise host environment identity is used.",
    ),
    root: str = typer.Option(".", "--root", help="Workspace root used for federation discovery."),
    write_index: bool = typer.Option(
        False,
        "--write-index/--no-write-index",
        help="Write the generated checkpoint backlog navigation index.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    report = AoASDK.from_workspace(root).checkpoints.backlog_audit(
        repo_root=repo_root,
        runtime_session_file=runtime_session_file,
        write_index=write_index,
    )
    payload = report.model_dump(mode="json")
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    _print_checkpoint_backlog_audit(report)


@checkpoint_app.command("close-archive")
def checkpoint_close_archive(
    repo_root: str | None = typer.Argument(
        None,
        help="Optional repository root or repo name used to filter checkpoint lifecycle entries.",
    ),
    runtime_session_id: str | None = typer.Option(
        None,
        "--runtime-session-id",
        help="Optional runtime session id or scope key to close/archive.",
    ),
    include_stale: bool = typer.Option(
        False,
        "--include-stale",
        help="Also archive nonpending stale current scopes without marking them closed.",
    ),
    dry_run: bool = typer.Option(
        True,
        "--dry-run/--apply",
        help="Preview by default; use --apply to move checkpoint evidence from current to archive.",
    ),
    runtime_session_file: str | None = typer.Option(
        None,
        "--runtime-session-file",
        help="Optional external host runtime metadata file; otherwise host environment identity is used.",
    ),
    root: str = typer.Option(".", "--root", help="Workspace root used for federation discovery."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    report = AoASDK.from_workspace(root).checkpoints.close_archive(
        repo_root=repo_root,
        runtime_session_file=runtime_session_file,
        runtime_session_id=runtime_session_id,
        dry_run=dry_run,
        include_stale=include_stale,
    )
    payload = report.model_dump(mode="json")
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    _print_checkpoint_lifecycle_archive_result(report)


def _checkpoint_reconcile_sessions_impl(
    *,
    repo_root: str | None,
    runtime_session_id: str | None,
    session_filter: str | None,
    since: str | None,
    until: str | None,
    dry_run: bool,
    write_index: bool,
    runtime_session_file: str | None,
    root: str,
    json_output: bool,
) -> None:
    report = AoASDK.from_workspace(root).checkpoints.reconcile_sessions(
        repo_root=repo_root,
        runtime_session_file=runtime_session_file,
        runtime_session_id=runtime_session_id,
        session_filter=session_filter,
        since=since,
        until=until,
        dry_run=dry_run,
        write_index=write_index,
    )
    payload = report.model_dump(mode="json")
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    _print_checkpoint_session_reconcile_result(report)


@checkpoint_app.command("reconcile-sessions")
def checkpoint_reconcile_sessions(
    repo_root: str | None = typer.Argument(
        None,
        help="Optional repository root or repo name used to filter checkpoint lifecycle entries.",
    ),
    runtime_session_id: str | None = typer.Option(
        None,
        "--runtime-session-id",
        help="Optional runtime session id or scope key to reconcile.",
    ),
    session_filter: str | None = typer.Option(
        None,
        "--session",
        help="Optional session id, session ref, note path, or session-memory archive fragment.",
    ),
    since: str | None = typer.Option(
        None,
        "--since",
        help="Only reconcile checkpoint sessions observed on or after this date/time.",
    ),
    until: str | None = typer.Option(
        None,
        "--until",
        help="Only reconcile checkpoint sessions observed on or before this date/time.",
    ),
    dry_run: bool = typer.Option(
        True,
        "--dry-run/--apply",
        help="Preview by default; use --apply to move checkpoint evidence from current to archive.",
    ),
    write_index: bool = typer.Option(
        True,
        "--write-index/--no-write-index",
        help="Write the generated checkpoint lifecycle navigation index.",
    ),
    runtime_session_file: str | None = typer.Option(
        None,
        "--runtime-session-file",
        help="Optional external host runtime metadata file; otherwise host environment identity is used.",
    ),
    root: str = typer.Option(".", "--root", help="Workspace root used for federation discovery."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    _checkpoint_reconcile_sessions_impl(
        repo_root=repo_root,
        runtime_session_id=runtime_session_id,
        session_filter=session_filter,
        since=since,
        until=until,
        dry_run=dry_run,
        write_index=write_index,
        runtime_session_file=runtime_session_file,
        root=root,
        json_output=json_output,
    )


@checkpoint_app.command("sweep-closed-sessions")
def checkpoint_sweep_closed_sessions(
    repo_root: str | None = typer.Argument(
        None,
        help="Optional repository root or repo name used to filter checkpoint lifecycle entries.",
    ),
    runtime_session_id: str | None = typer.Option(None, "--runtime-session-id"),
    session_filter: str | None = typer.Option(None, "--session"),
    since: str | None = typer.Option(None, "--since"),
    until: str | None = typer.Option(None, "--until"),
    dry_run: bool = typer.Option(True, "--dry-run/--apply"),
    write_index: bool = typer.Option(True, "--write-index/--no-write-index"),
    runtime_session_file: str | None = typer.Option(None, "--runtime-session-file"),
    root: str = typer.Option(".", "--root", help="Workspace root used for federation discovery."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    _checkpoint_reconcile_sessions_impl(
        repo_root=repo_root,
        runtime_session_id=runtime_session_id,
        session_filter=session_filter,
        since=since,
        until=until,
        dry_run=dry_run,
        write_index=write_index,
        runtime_session_file=runtime_session_file,
        root=root,
        json_output=json_output,
    )


@checkpoint_app.command("promote")
def checkpoint_promote(
    repo_root: str = typer.Argument(..., help="Repository root or repo-relative path used as the checkpoint context."),
    target: str = typer.Option(
        ...,
        "--target",
        help="Promotion target: dionysus-note or harvest-handoff.",
    ),
    runtime_session_file: str | None = typer.Option(
        None,
        "--runtime-session-file",
        help="Optional external host runtime metadata file; otherwise host environment identity is used.",
    ),
    root: str = typer.Option(".", "--root", help="Workspace root used for federation discovery."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    promotion = AoASDK.from_workspace(root).checkpoints.promote(
        repo_root=repo_root,
        target=target,  # type: ignore[arg-type]
        runtime_session_file=runtime_session_file,
    )
    payload = promotion.model_dump(mode="json")
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    _print_checkpoint_promotion(promotion)


@checkpoint_app.command("build-closeout-context")
def checkpoint_build_closeout_context(
    repo_root: str = typer.Argument(..., help="Repository root or repo-relative path used as the closeout context."),
    reviewed_artifact: str = typer.Option(
        ...,
        "--reviewed-artifact",
        help="Reviewed session artifact that anchors the closeout evidence bundle.",
    ),
    session_ref: str | None = typer.Option(
        None,
        "--session-ref",
        help="Optional explicit session_ref override when it cannot be derived from the reviewed artifact, receipts, or local note.",
    ),
    receipt_path: list[str] = typer.Option(
        None,
        "--receipt-path",
        help="Receipt JSON or JSONL file that should be included in the closeout evidence bundle. Repeat for multiple files.",
    ),
    receipt_dir: list[str] = typer.Option(
        None,
        "--receipt-dir",
        help="Directory whose JSON or JSONL receipts should be included in the closeout evidence bundle. Repeat for multiple directories.",
    ),
    surface_handoff_path: str | None = typer.Option(
        None,
        "--surface-handoff-path",
        help="Optional reviewed surface handoff path. Defaults to the latest local reviewed handoff for the repo label.",
    ),
    runtime_session_file: str | None = typer.Option(
        None,
        "--runtime-session-file",
        help="Optional external host runtime metadata file; otherwise host environment identity is used.",
    ),
    root: str = typer.Option(".", "--root", help="Workspace root used for federation discovery."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    context = AoASDK.from_workspace(root).checkpoints.build_closeout_context(
        repo_root=repo_root,
        reviewed_artifact_path=reviewed_artifact,
        session_ref=session_ref,
        receipt_paths=receipt_path or [],
        receipt_dirs=receipt_dir or [],
        surface_handoff_path=surface_handoff_path,
        runtime_session_file=runtime_session_file,
    )
    payload = context.model_dump(mode="json")
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    _print_closeout_context(context)


@checkpoint_app.command("materialize-closeout-handoff")
def checkpoint_materialize_closeout_handoff(
    repo_root: str = typer.Argument(..., help="Repository root or repo-relative path used as the closeout context."),
    reviewed_artifact: str = typer.Option(
        ...,
        "--reviewed-artifact",
        help="Reviewed session artifact that anchors the closeout evidence bundle.",
    ),
    session_ref: str | None = typer.Option(
        None,
        "--session-ref",
        help="Optional explicit session_ref override when it cannot be derived from the reviewed artifact, receipts, or local note.",
    ),
    receipt_path: list[str] = typer.Option(
        None,
        "--receipt-path",
        help="Receipt JSON or JSONL file that should be included in the closeout evidence bundle. Repeat for multiple files.",
    ),
    receipt_dir: list[str] = typer.Option(
        None,
        "--receipt-dir",
        help="Directory whose JSON or JSONL receipts should be included in the closeout evidence bundle. Repeat for multiple directories.",
    ),
    surface_handoff_path: str | None = typer.Option(
        None,
        "--surface-handoff-path",
        help="Optional reviewed surface handoff path. Defaults to the latest local reviewed handoff for the repo label.",
    ),
    runtime_session_file: str | None = typer.Option(
        None,
        "--runtime-session-file",
        help="Optional external host runtime metadata file; otherwise host environment identity is used.",
    ),
    root: str = typer.Option(".", "--root", help="Workspace root used for federation discovery."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    report = AoASDK.from_workspace(root).checkpoints.materialize_closeout_handoff(
        repo_root=repo_root,
        reviewed_artifact_path=reviewed_artifact,
        session_ref=session_ref,
        receipt_paths=receipt_path or [],
        receipt_dirs=receipt_dir or [],
        surface_handoff_path=surface_handoff_path,
        runtime_session_file=runtime_session_file,
    )
    payload = report.model_dump(mode="json")
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
        return
    _print_closeout_materialization_report(report)
