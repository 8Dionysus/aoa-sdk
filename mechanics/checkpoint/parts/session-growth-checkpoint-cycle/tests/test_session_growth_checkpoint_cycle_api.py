from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from aoa_sdk import AoASDK
from aoa_sdk.checkpoints.registry import CheckpointsAPI
from aoa_sdk.errors import InvalidSurface, SurfaceNotFound


def _write_runtime_metadata(
    path: Path,
    *,
    session_id: str,
    codex_thread_id: str | None = None,
    legacy_skill_fields: bool = False,
) -> Path:
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
    payload: dict[str, object] = {
        "schema_version": 1,
        "session_id": session_id,
        "created_at": "2026-07-15T12:00:00Z",
        "codex_thread_id": codex_thread_id,
        "codex_rollout_path": str(rollout_path.resolve()),
    }
    if legacy_skill_fields:
        payload.update(
            {
                "profile": "retired-sdk-profile",
                "active_skills": ["retired-skill"],
                "activation_log": [{"skill": "retired-skill"}],
            }
        )
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
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


def _current_scope(workspace_root: Path, session_id: str, repo: str = "aoa-sdk") -> Path:
    return (
        workspace_root
        / "aoa-sdk"
        / ".aoa"
        / "session-growth"
        / "current"
        / session_id
        / repo
    )


def test_checkpoint_mutation_requires_host_identity_and_creates_no_sdk_session(
    workspace_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = workspace_root / "aoa-sdk"
    sdk = AoASDK.from_workspace(repo_root)

    with pytest.raises(SurfaceNotFound, match="host-provided runtime session identity"):
        sdk.checkpoints.append(
            repo_root=str(repo_root),
            checkpoint_kind="manual",
            intent_text="preserve one reviewed checkpoint candidate",
        )

    retired_session_path = repo_root / ".aoa" / "skill-runtime-session.json"
    assert not retired_session_path.exists()

    monkeypatch.setenv("CODEX_THREAD_ID", "thread-host-owned")
    note = sdk.checkpoints.append(
        repo_root=str(repo_root),
        checkpoint_kind="manual",
        intent_text="preserve one reviewed checkpoint candidate",
    )

    assert note.runtime_session_id == "thread-host-owned"
    assert (_current_scope(workspace_root, "thread-host-owned") / "checkpoint-note.json").is_file()
    assert not retired_session_path.exists()


def test_explicit_runtime_metadata_is_read_only_and_sessions_stay_separate(
    workspace_root: Path,
) -> None:
    repo_root = workspace_root / "aoa-sdk"
    sdk = AoASDK.from_workspace(repo_root)
    first_metadata = _write_runtime_metadata(
        repo_root / ".aoa" / "runtime-one.json",
        session_id="runtime-one",
        legacy_skill_fields=True,
    )
    second_metadata = _write_runtime_metadata(
        repo_root / ".aoa" / "runtime-two.json",
        session_id="runtime-two",
    )
    original_legacy_payload = first_metadata.read_text(encoding="utf-8")

    first = sdk.checkpoints.append(
        repo_root=str(repo_root),
        checkpoint_kind="manual",
        intent_text="first session evidence",
        runtime_session_file=str(first_metadata),
    )
    second = sdk.checkpoints.append(
        repo_root=str(repo_root),
        checkpoint_kind="manual",
        intent_text="second session evidence",
        runtime_session_file=str(second_metadata),
    )

    assert first.runtime_session_id == "runtime-one"
    assert second.runtime_session_id == "runtime-two"
    assert first.session_ref != second.session_ref
    assert first_metadata.read_text(encoding="utf-8") == original_legacy_payload
    assert (_current_scope(workspace_root, "runtime-one") / "checkpoint-note.json").is_file()
    assert (_current_scope(workspace_root, "runtime-two") / "checkpoint-note.json").is_file()
    assert sdk.checkpoints.status(
        repo_root=str(repo_root),
        runtime_session_file=str(first_metadata),
    ).session_ref == first.session_ref


def test_host_and_metadata_identity_conflict_is_rejected_without_checkpoint_write(
    workspace_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = workspace_root / "aoa-sdk"
    metadata = _write_runtime_metadata(
        repo_root / ".aoa" / "runtime-conflict.json",
        session_id="runtime-conflict",
        codex_thread_id="thread-metadata",
    )
    original = metadata.read_text(encoding="utf-8")
    monkeypatch.setenv("CODEX_THREAD_ID", "thread-host")

    with pytest.raises(InvalidSurface, match="different Codex thread"):
        AoASDK.from_workspace(repo_root).checkpoints.append(
            repo_root=str(repo_root),
            checkpoint_kind="manual",
            intent_text="conflicting identity must not write",
            runtime_session_file=str(metadata),
        )

    assert metadata.read_text(encoding="utf-8") == original
    assert not (repo_root / ".aoa" / "session-growth" / "current").exists()


def test_capture_from_phase_is_read_only_at_ingress_and_routes_capabilities(
    workspace_root: Path,
) -> None:
    repo_root = workspace_root / "aoa-sdk"
    sdk = AoASDK.from_workspace(repo_root)

    ingress = sdk.checkpoints.capture_from_phase(
        repo_root=str(repo_root),
        phase="ingress",
        intent_text="inspect current checkpoint posture",
        mutation_surface="none",
    )

    assert ingress.appended is False
    assert ingress.reason == "no_checkpoint_signal"
    assert not (repo_root / ".aoa" / "session-growth" / "current").exists()

    metadata = _write_runtime_metadata(
        repo_root / ".aoa" / "runtime-capture.json",
        session_id="runtime-capture",
    )
    captured = sdk.checkpoints.capture_from_phase(
        repo_root=str(repo_root),
        phase="pre-mutation",
        intent_text="commit the bounded checkpoint evidence change",
        mutation_surface="code",
        runtime_session_file=str(metadata),
    )

    assert captured.appended is True
    assert captured.note is not None
    assert captured.note.runtime_session_id == "runtime-capture"
    assert {
        target.target_ref for target in captured.session_end_capability_candidates
    } >= {"workflow.operations.checkpoint-closeout"}
    assert all(
        "execut" in target.why or "review" in target.why
        for target in captured.session_end_capability_candidates
    )


def test_after_commit_review_materialize_and_archive_preserve_owner_boundaries(
    workspace_root: Path,
) -> None:
    repo_root = workspace_root / "aoa-sdk"
    _init_git_repo(repo_root)
    commit_sha = _commit(repo_root, "refine reviewed checkpoint owner handoff")
    metadata = _write_runtime_metadata(
        repo_root / ".aoa" / "runtime-closeout.json",
        session_id="runtime-closeout",
        codex_thread_id="thread-closeout",
    )
    sdk = AoASDK.from_workspace(repo_root)

    captured = sdk.checkpoints.after_commit(
        repo_root=str(repo_root),
        commit_ref="HEAD",
        runtime_session_file=str(metadata),
    )

    assert captured.status == "captured"
    assert captured.commit_sha == commit_sha
    assert captured.runtime_session_id == "runtime-closeout"
    assert captured.runtime_session_file_ref == str(metadata)
    assert captured.agent_review_status == "pending"

    reviewed_note = sdk.checkpoints.review_note(
        repo_root=str(repo_root),
        commit_ref="HEAD",
        summary="Reviewed the checkpoint evidence and retained only owner candidates.",
        findings=["No capability execution was observed."],
        evidence_refs=[captured.report_path],
        related_capability_refs=["workflow.operations.checkpoint-closeout"],
        next_owner_moves=["Let each owner decide whether to accept its candidate."],
        runtime_session_file=str(metadata),
    )

    assert reviewed_note.agent_review_status == "reviewed"
    assert "workflow.operations.checkpoint-closeout" in (
        reviewed_note.related_capability_refs
    )

    reviewed_artifact = repo_root / ".aoa" / "reviewed-closeout.md"
    reviewed_artifact.write_text(
        "\n".join(
            [
                "# Reviewed checkpoint",
                "",
                f"Session ref: `{reviewed_note.session_ref}`",
                "",
                "- owner candidates remain review-only",
                "- no capability execution was observed",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    materialized = sdk.checkpoints.materialize_closeout_handoff(
        repo_root=str(repo_root),
        reviewed_artifact_path=str(reviewed_artifact),
        runtime_session_file=str(metadata),
    )

    assert materialized.materialization_mode == "reviewed_evidence_bundle"
    assert materialized.capability_execution_claimed is False
    assert materialized.related_workflow_ref == (
        "workflow.operations.checkpoint-closeout"
    )
    assert materialized.runtime_session_id == "runtime-closeout"
    assert any(
        target["target_ref"] == "skill.aoa-session-harvest"
        and target["lifecycle_posture"] == "candidate"
        and target["use_posture"] == "candidate-only"
        for target in json.loads(Path(materialized.context_ref).read_text(encoding="utf-8"))[
            "capability_candidates"
        ]
    )
    assert {stage.stage_id for stage in materialized.stages} == {
        "reviewed-evidence-bundle",
        "owner-candidate-handoff",
    }
    sdk_state_root = (repo_root / ".aoa").resolve()
    for ref in [
        *materialized.produced_artifact_refs,
        *materialized.produced_receipt_refs,
    ]:
        assert Path(ref).resolve().is_relative_to(sdk_state_root)
    evidence_packet = json.loads(
        Path(materialized.produced_artifact_refs[0]).read_text(encoding="utf-8")
    )
    receipt = json.loads(
        Path(materialized.produced_receipt_refs[0]).read_text(encoding="utf-8")
    )
    assert evidence_packet["capability_execution_claimed"] is False
    assert receipt["payload"]["capability_execution_claimed"] is False
    assert "execution_order" not in evidence_packet

    lifecycle = sdk.checkpoints.lifecycle_audit(
        repo_root=str(repo_root),
        runtime_session_file=str(metadata),
    )
    entry = next(
        item
        for item in lifecycle.entries
        if item.runtime_session_id == "runtime-closeout"
    )
    assert entry.lifecycle_state == "closeout_materialized"
    assert entry.closable is True

    preview = sdk.checkpoints.close_archive(
        repo_root=str(repo_root),
        runtime_session_id="runtime-closeout",
        runtime_session_file=str(metadata),
        dry_run=True,
    )
    assert preview.archived_count == 1
    assert _current_scope(workspace_root, "runtime-closeout").is_dir()

    applied = sdk.checkpoints.close_archive(
        repo_root=str(repo_root),
        runtime_session_id="runtime-closeout",
        runtime_session_file=str(metadata),
        dry_run=False,
    )
    assert applied.archived_count == 1
    assert not _current_scope(workspace_root, "runtime-closeout").exists()
    archived_note = json.loads(
        (Path(applied.archive_refs[0]) / "checkpoint-note.json").read_text(
            encoding="utf-8"
        )
    )
    assert archived_note["state"] == "closed"
    assert archived_note["lifecycle_events"][-1]["lifecycle_state"] == "closed"


def test_closeout_materialization_without_runtime_identity_writes_nothing(
    workspace_root: Path,
) -> None:
    repo_root = workspace_root / "aoa-sdk"
    reviewed_artifact = repo_root / ".aoa" / "reviewed-without-identity.md"
    reviewed_artifact.parent.mkdir(parents=True, exist_ok=True)
    reviewed_artifact.write_text(
        "# Reviewed artifact\n\nSession ref: `session:missing-identity`\n",
        encoding="utf-8",
    )

    with pytest.raises(SurfaceNotFound, match="host-provided runtime session identity"):
        AoASDK.from_workspace(repo_root).checkpoints.materialize_closeout_handoff(
            repo_root=str(repo_root),
            reviewed_artifact_path=str(reviewed_artifact),
        )

    assert not (repo_root / ".aoa" / "session-growth").exists()
    assert not (repo_root / ".aoa" / "closeout").exists()


def test_closeout_rejects_reviewed_artifact_from_another_session(
    workspace_root: Path,
) -> None:
    repo_root = workspace_root / "aoa-sdk"
    metadata = _write_runtime_metadata(
        repo_root / ".aoa" / "runtime-scope.json",
        session_id="runtime-scope",
    )
    sdk = AoASDK.from_workspace(repo_root)
    sdk.checkpoints.append(
        repo_root=str(repo_root),
        checkpoint_kind="manual",
        intent_text="keep session scope explicit",
        runtime_session_file=str(metadata),
    )
    reviewed_artifact = repo_root / ".aoa" / "reviewed-wrong-session.md"
    reviewed_artifact.write_text(
        "# Reviewed artifact\n\nSession ref: `session:another-session`\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="does not match"):
        sdk.checkpoints.build_closeout_context(
            repo_root=str(repo_root),
            reviewed_artifact_path=str(reviewed_artifact),
            runtime_session_file=str(metadata),
        )


def test_retired_skill_session_and_execution_entrypoints_are_absent() -> None:
    assert not hasattr(CheckpointsAPI, "capture_from_skill_phase")
    assert not hasattr(CheckpointsAPI, "execute_closeout_chain")
