"""Recovery helpers for skipped post-commit checkpoint reviews."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, Protocol, cast

from ...errors import SurfaceNotFound
from ...models import CheckpointAfterCommitReport, CheckpointRuntimeSessionRef
from ...workspace.discovery import Workspace
from ..hooks.git_boundary import run_git
from ..runtime.sessions import (
    probe_existing_checkpoint_runtime_session,
)
from ..topology.paths import post_commit_status_path


class AfterCommitCapture(Protocol):
    def __call__(
        self,
        *,
        repo_root: str,
        commit_ref: str = "HEAD",
        runtime_session_file: str | None = None,
        checkpoint_kind: Literal["auto", "commit", "owner_followthrough"] = "auto",
    ) -> CheckpointAfterCommitReport: ...


def load_latest_post_commit_status(
    workspace: Workspace,
    repo_label: str,
) -> tuple[Path, CheckpointAfterCommitReport] | None:
    status_path = post_commit_status_path(workspace, repo_label)
    if not status_path.exists():
        return None
    try:
        return status_path, CheckpointAfterCommitReport.model_validate_json(
            status_path.read_text(encoding="utf-8")
        )
    except Exception:
        return None


def is_unresolved_skipped_after_commit_report(report: CheckpointAfterCommitReport) -> bool:
    return (
        report.status == "skipped_no_active_session"
        and report.manual_review_requested
        and report.agent_review_status != "reviewed"
    )


def after_commit_report_matches_commit(
    report: CheckpointAfterCommitReport,
    *,
    commit_metadata: dict[str, Any],
    commit_ref: str,
) -> bool:
    commit_sha = cast(str | None, commit_metadata.get("commit_sha"))
    commit_short_sha = cast(str | None, commit_metadata.get("commit_short_sha"))
    if report.commit_sha is not None and commit_sha is not None:
        return report.commit_sha == commit_sha
    if report.commit_short_sha is not None and commit_short_sha is not None:
        return report.commit_short_sha == commit_short_sha
    return report.commit_ref == commit_ref


def after_commit_report_matches_session_path(
    report: CheckpointAfterCommitReport,
    session_path: Path,
) -> bool:
    if report.runtime_session_file_ref is None:
        return False
    return (
        Path(report.runtime_session_file_ref).expanduser().resolve()
        == session_path.expanduser().resolve()
    )


def after_commit_report_is_reachable_head(
    repo_root_path: Path,
    report: CheckpointAfterCommitReport,
) -> bool:
    if report.commit_sha is None:
        return False
    result = run_git(
        repo_root_path,
        "merge-base",
        "--is-ancestor",
        report.commit_sha,
        "HEAD",
        check=False,
    )
    return result.returncode == 0


def unresolved_skipped_post_commit_status_for_boundary(
    workspace: Workspace,
    *,
    repo_root_path: Path,
    repo_label: str,
) -> tuple[Path, CheckpointAfterCommitReport] | None:
    loaded = load_latest_post_commit_status(workspace, repo_label)
    if loaded is None:
        return None
    status_path, report = loaded
    if not is_unresolved_skipped_after_commit_report(report):
        return None
    if not after_commit_report_is_reachable_head(repo_root_path, report):
        return None
    return status_path, report


def skipped_after_commit_pending_ref(report: CheckpointAfterCommitReport) -> str:
    return report.commit_sha or report.commit_short_sha or report.commit_ref


def skipped_after_commit_required_action(
    *,
    repo_root_path: Path,
    workspace_root: Path,
    boundary: Literal["push", "merge"],
    report: CheckpointAfterCommitReport,
) -> str:
    pending_ref = skipped_after_commit_pending_ref(report)
    return (
        "unresolved skipped checkpoint blocks "
        f"{boundary}; post-commit requested review for {pending_ref} "
        "but no host runtime identity existed; from the active Codex/AoA session run "
        f"`aoa checkpoint after-commit {repo_root_path} --commit-ref {pending_ref} "
        f"--root {workspace_root}`, then run the reported review command"
    )


def recover_skipped_after_commit_for_review(
    *,
    workspace: Workspace,
    repo_root: str,
    repo_label: str,
    commit_ref: str,
    commit_metadata: dict[str, Any],
    session_path: Path | None,
    capture_after_commit: AfterCommitCapture,
) -> tuple[Path | None, CheckpointRuntimeSessionRef] | None:
    loaded = load_latest_post_commit_status(workspace, repo_label)
    if loaded is None:
        return None
    status_path, skipped_report = loaded
    if not is_unresolved_skipped_after_commit_report(skipped_report):
        return None
    if not after_commit_report_matches_commit(
        skipped_report,
        commit_metadata=commit_metadata,
        commit_ref=commit_ref,
    ):
        return None
    active_session_path, runtime_session = probe_existing_checkpoint_runtime_session(
        workspace=workspace,
        runtime_session_file=str(session_path) if session_path is not None else None,
    )
    if runtime_session is None:
        raise SurfaceNotFound(
            "checkpoint review recovery requires an existing host runtime identity; "
            "SDK does not create session state"
        )

    recovered_report = capture_after_commit(
        repo_root=repo_root,
        commit_ref=commit_ref,
        runtime_session_file=str(active_session_path) if active_session_path is not None else None,
        checkpoint_kind=skipped_report.checkpoint_kind,
    )
    if recovered_report.status != "captured":
        detail = recovered_report.error_text or recovered_report.status
        raise SurfaceNotFound(
            "checkpoint review recovery could not capture skipped post-commit "
            f"checkpoint from {status_path}: {detail}"
        )

    recovered_session_path, runtime_session = probe_existing_checkpoint_runtime_session(
        workspace=workspace,
        runtime_session_file=str(active_session_path) if active_session_path is not None else None,
    )
    if runtime_session is None:
        raise SurfaceNotFound(
            "checkpoint review recovery lost the host runtime identity after capture"
        )
    return recovered_session_path, runtime_session
