from __future__ import annotations

import json
import subprocess
from pathlib import Path

from typer.testing import CliRunner

from aoa_sdk.cli.main import app


def _write_runtime_metadata(path: Path, *, session_id: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    rollout_path = path.parent / f"{session_id}.jsonl"
    rollout_path.write_text(
        json.dumps(
            {
                "type": "event_msg",
                "payload": {
                    "type": "user_message",
                    "message": "review the checkpoint evidence",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "session_id": session_id,
                "created_at": "2026-07-15T12:00:00Z",
                "codex_thread_id": f"thread-{session_id}",
                "codex_rollout_path": str(rollout_path.resolve()),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def _init_git_repo(repo_root: Path) -> None:
    subprocess.run(
        ["git", "init"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "AoA Test"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "aoa@example.test"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )


def _commit(repo_root: Path, subject: str) -> str:
    readme = repo_root / "README.md"
    readme.write_text(
        readme.read_text(encoding="utf-8") + f"\n{subject}\n",
        encoding="utf-8",
    )
    subprocess.run(
        ["git", "add", "README.md"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "commit", "-m", subject],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def test_checkpoint_append_cli_requires_explicit_runtime_identity(
    workspace_root: Path,
) -> None:
    repo_root = workspace_root / "aoa-sdk"
    runner = CliRunner()
    missing = runner.invoke(
        app,
        [
            "checkpoint",
            "append",
            str(repo_root),
            "--kind",
            "manual",
            "--intent-text",
            "preserve reviewed checkpoint evidence",
            "--root",
            str(repo_root),
            "--json",
        ],
    )

    assert missing.exit_code != 0
    assert not (repo_root / ".aoa" / "session-growth").exists()

    metadata = _write_runtime_metadata(
        repo_root / ".aoa" / "runtime-cli.json",
        session_id="runtime-cli",
    )
    original_metadata = metadata.read_text(encoding="utf-8")
    captured = runner.invoke(
        app,
        [
            "checkpoint",
            "append",
            str(repo_root),
            "--kind",
            "manual",
            "--intent-text",
            "preserve reviewed checkpoint evidence",
            "--runtime-session-file",
            str(metadata),
            "--root",
            str(repo_root),
            "--json",
        ],
    )

    assert captured.exit_code == 0, captured.stdout
    payload = json.loads(captured.stdout)
    assert payload["runtime_session_id"] == "runtime-cli"
    assert metadata.read_text(encoding="utf-8") == original_metadata
    assert (
        repo_root
        / ".aoa"
        / "session-growth"
        / "current"
        / "runtime-cli"
        / "aoa-sdk"
        / "checkpoint-note.json"
    ).is_file()


def test_checkpoint_cli_review_materialize_and_close_archive(
    workspace_root: Path,
) -> None:
    repo_root = workspace_root / "aoa-sdk"
    _init_git_repo(repo_root)
    commit_sha = _commit(repo_root, "refine checkpoint owner handoff")
    metadata = _write_runtime_metadata(
        repo_root / ".aoa" / "runtime-cli-closeout.json",
        session_id="runtime-cli-closeout",
    )
    runner = CliRunner()
    common = [
        "--runtime-session-file",
        str(metadata),
        "--root",
        str(repo_root),
        "--json",
    ]

    captured = runner.invoke(
        app,
        [
            "checkpoint",
            "after-commit",
            str(repo_root),
            "--commit-ref",
            "HEAD",
            *common,
        ],
    )
    assert captured.exit_code == 0, captured.stdout
    captured_payload = json.loads(captured.stdout)
    assert captured_payload["status"] == "captured"
    assert captured_payload["commit_sha"] == commit_sha
    assert captured_payload["agent_review_status"] == "pending"

    reviewed = runner.invoke(
        app,
        [
            "checkpoint",
            "review-note",
            str(repo_root),
            "--commit-ref",
            "HEAD",
            "--summary",
            "Reviewed owner candidates; no capability execution was observed.",
            "--finding",
            "The SDK must only materialize reviewed evidence.",
            "--related-capability-ref",
            "workflow.operations.checkpoint-closeout",
            *common,
        ],
    )
    assert reviewed.exit_code == 0, reviewed.stdout
    reviewed_payload = json.loads(reviewed.stdout)
    assert reviewed_payload["agent_review_status"] == "reviewed"

    reviewed_artifact = repo_root / ".aoa" / "reviewed-cli-closeout.md"
    reviewed_artifact.write_text(
        "\n".join(
            [
                "# Reviewed checkpoint",
                "",
                f"Session ref: `{reviewed_payload['session_ref']}`",
                "",
                "- owner candidates remain review-only",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    materialized = runner.invoke(
        app,
        [
            "checkpoint",
            "materialize-closeout-handoff",
            str(repo_root),
            "--reviewed-artifact",
            str(reviewed_artifact),
            *common,
        ],
    )
    assert materialized.exit_code == 0, materialized.stdout
    materialized_payload = json.loads(materialized.stdout)
    assert materialized_payload["capability_execution_claimed"] is False
    assert materialized_payload["materialization_mode"] == (
        "reviewed_evidence_bundle"
    )
    assert all(
        Path(ref).resolve().is_relative_to((repo_root / ".aoa").resolve())
        for ref in [
            *materialized_payload["produced_artifact_refs"],
            *materialized_payload["produced_receipt_refs"],
        ]
    )

    lifecycle = runner.invoke(
        app,
        [
            "checkpoint",
            "lifecycle-audit",
            str(repo_root),
            *common,
        ],
    )
    assert lifecycle.exit_code == 0, lifecycle.stdout
    lifecycle_payload = json.loads(lifecycle.stdout)
    entry = next(
        item
        for item in lifecycle_payload["entries"]
        if item["runtime_session_id"] == "runtime-cli-closeout"
    )
    assert entry["lifecycle_state"] == "closeout_materialized"

    preview = runner.invoke(
        app,
        [
            "checkpoint",
            "close-archive",
            str(repo_root),
            "--runtime-session-id",
            "runtime-cli-closeout",
            *common,
        ],
    )
    assert preview.exit_code == 0, preview.stdout
    assert json.loads(preview.stdout)["dry_run"] is True

    applied = runner.invoke(
        app,
        [
            "checkpoint",
            "close-archive",
            str(repo_root),
            "--runtime-session-id",
            "runtime-cli-closeout",
            "--apply",
            *common,
        ],
    )
    assert applied.exit_code == 0, applied.stdout
    applied_payload = json.loads(applied.stdout)
    assert applied_payload["archived_count"] == 1
    archived_note = json.loads(
        (Path(applied_payload["archive_refs"][0]) / "checkpoint-note.json").read_text(
            encoding="utf-8"
        )
    )
    assert archived_note["state"] == "closed"


def test_checkpoint_cli_exposes_materialization_not_execution() -> None:
    result = CliRunner().invoke(app, ["checkpoint", "--help"])

    assert result.exit_code == 0
    assert "materialize-closeout-handoff" in result.stdout
    assert "execute-closeout-chain" not in result.stdout
