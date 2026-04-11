from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path

import pytest

from aoa_sdk import AoASDK
from aoa_sdk.errors import SurfaceNotFound
from aoa_sdk.skills.session import probe_session


@pytest.fixture(autouse=True)
def _clear_codex_thread_id(monkeypatch) -> None:
    monkeypatch.delenv("CODEX_THREAD_ID", raising=False)


def _checkpoint_note_dir(
    workspace_root: Path,
    *,
    repo_label: str,
    runtime_session_id: str | None = None,
) -> Path:
    current_root = workspace_root / "aoa-sdk" / ".aoa" / "session-growth" / "current"
    if runtime_session_id is None:
        return current_root / repo_label
    return current_root / runtime_session_id / repo_label


def _write_runtime_session_file(
    path: Path,
    *,
    session_id: str,
    codex_thread_id: str | None = "thread-closeout",
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "profile": "aoa-sdk",
        "session_id": session_id,
        "created_at": "2026-04-10T14:00:00Z",
        "updated_at": "2026-04-10T14:00:00Z",
        "codex_thread_id": codex_thread_id,
        "codex_rollout_path": str((path.parent / "runtime-trace.jsonl").resolve()),
        "active_skills": [],
        "activation_log": [],
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _init_git_repo(repo_root: Path) -> None:
    subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "AoA Test"], cwd=repo_root, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "config", "user.email", "aoa@example.test"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )


def _git_commit(repo_root: Path, *, subject: str, body: str = "") -> str:
    readme = repo_root / "README.md"
    base_text = readme.read_text(encoding="utf-8")
    readme.write_text(base_text + f"\n{subject}\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo_root, check=True, capture_output=True, text=True)
    command = ["git", "commit", "-m", subject]
    if body:
        command.extend(["-m", body])
    subprocess.run(command, cwd=repo_root, check=True, capture_output=True, text=True)
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _write_rollout_trace(
    path: Path,
    *,
    user_message: str = "fix the closeout path",
    assistant_message: str = "implemented the patch and verified the tests",
    tool_call_arguments: str = "{\"cmd\":\"python -m pytest -q\"}",
    tool_output: str = "24 passed",
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    records = [
        {
            "timestamp": "2026-04-10T14:00:00Z",
            "type": "event_msg",
            "payload": {"type": "user_message", "message": user_message},
        },
        {
            "timestamp": "2026-04-10T14:00:01Z",
            "type": "response_item",
            "payload": {
                "type": "message",
                "role": "assistant",
                "content": [{"type": "output_text", "text": assistant_message}],
            },
        },
        {
            "timestamp": "2026-04-10T14:00:02Z",
            "type": "response_item",
            "payload": {
                "type": "function_call",
                "name": "exec_command",
                "arguments": tool_call_arguments,
            },
        },
        {
            "timestamp": "2026-04-10T14:00:03Z",
            "type": "response_item",
            "payload": {
                "type": "function_call_output",
                "call_id": "call-1",
                "output": tool_output,
            },
        },
    ]
    path.write_text(
        "\n".join(json.dumps(record) for record in records) + "\n",
        encoding="utf-8",
    )
    return path


def _write_checkpoint_history_entry(
    *,
    note_dir: Path,
    session_ref: str,
    runtime_session_id: str,
    repo_root: Path,
    repo_label: str,
    candidate_id: str,
    candidate_kind: str,
    owner_hint: str,
    display_name: str,
    source_surface_ref: str,
    evidence_refs: list[str],
    progression_axis_signals: list[dict[str, object]],
    checkpoint_kind: str = "verify_green",
    observed_at: str = "2026-04-10T14:00:00Z",
    intent_text: str = "reviewed closeout candidate survived this runtime session",
    blocked_by: list[str] | None = None,
    promote_if: list[str] | None = None,
    next_owner_moves: list[str] | None = None,
    defer_reason: str | None = None,
) -> None:
    note_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "session_ref": session_ref,
        "runtime_session_id": runtime_session_id,
        "runtime_session_created_at": "2026-04-10T13:55:00Z",
        "repo_root": str(repo_root.resolve()),
        "repo_label": repo_label,
        "history_entry": {
            "checkpoint_kind": checkpoint_kind,
            "observed_at": observed_at,
            "report_ref": str(note_dir / f"{repo_label}-report.json"),
            "intent_text": intent_text,
            "checkpoint_should_capture": True,
            "blocked_by": blocked_by or [],
            "candidate_clusters": [
                {
                    "candidate_id": candidate_id,
                    "candidate_kind": candidate_kind,
                    "owner_hint": owner_hint,
                    "display_name": display_name,
                    "source_surface_ref": source_surface_ref,
                    "evidence_refs": evidence_refs,
                    "confidence": "medium",
                    "session_end_targets": ["harvest", "progression", "upgrade"],
                    "progression_axis_signals": progression_axis_signals,
                    "promote_if": promote_if or [],
                    "defer_reason": defer_reason,
                    "blocked_by": blocked_by or [],
                    "next_owner_moves": next_owner_moves
                    or [
                        "carry the candidate through reviewed session closeout before moving candidates or stats"
                    ],
                }
            ],
            "manual_review_requested": False,
        },
    }
    (note_dir / "checkpoint-note.jsonl").write_text(
        json.dumps(payload) + "\n",
        encoding="utf-8",
    )


def test_surface_detect_checkpoint_phase_emits_candidate_clusters(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    report = sdk.surfaces.detect(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="checkpoint",
        checkpoint_kind="commit",
        intent_text="recurring workflow needs better handoff proof and recall",
    )

    assert report.phase == "checkpoint"
    assert report.checkpoint_kind == "commit"
    assert report.checkpoint_should_capture is True
    assert report.candidate_clusters
    assert report.promotion_recommendation in {"local_note", "dionysus_note"}
    assert {cluster.candidate_kind for cluster in report.candidate_clusters} >= {"route", "proof", "recall"}
    assert all(cluster.lineage_hint is not None for cluster in report.candidate_clusters)
    assert all("candidate_ref" not in cluster.lineage_hint.model_dump() for cluster in report.candidate_clusters if cluster.lineage_hint is not None)


def test_checkpoint_status_becomes_reviewable_after_repeat(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    first = sdk.checkpoints.append(
        repo_root=str(workspace_root / "aoa-sdk"),
        checkpoint_kind="commit",
        intent_text="recurring workflow needs better handoff proof and recall",
    )
    second = sdk.checkpoints.append(
        repo_root=str(workspace_root / "aoa-sdk"),
        checkpoint_kind="verify_green",
        intent_text="recurring workflow needs better handoff proof and recall",
    )

    note_dir = _checkpoint_note_dir(
        workspace_root,
        repo_label="aoa-sdk",
        runtime_session_id=second.runtime_session_id,
    )
    assert first.state == "collecting"
    assert second.state == "reviewable"
    assert (note_dir / "checkpoint-note.jsonl").exists()
    assert (note_dir / "checkpoint-note.json").exists()
    assert (note_dir / "checkpoint-note.md").exists()
    route_cluster = next(cluster for cluster in second.candidate_clusters if cluster.candidate_kind == "route")
    assert route_cluster.checkpoint_hits == 2
    assert route_cluster.review_status == "reviewable"
    assert route_cluster.session_end_targets == ["harvest", "progression", "upgrade"]
    assert {signal.axis for signal in route_cluster.progression_axis_signals} == {
        "change_legibility",
        "deep_readiness",
    }
    assert second.carry_until_session_closeout is True
    assert second.session_end_recommendation == "harvest_progression_and_upgrade"
    assert second.harvest_candidate_ids
    assert second.progression_candidate_ids
    assert second.upgrade_candidate_ids
    assert second.progression_axis_signals
    assert second.stats_refresh_recommended is True
    assert second.checkpoint_history[-1].observed_at_local is not None
    assert second.checkpoint_history[-1].observed_at_local.endswith(("-00:00", "-01:00", "-02:00", "-03:00", "-04:00", "-05:00", "-06:00", "-07:00", "-08:00", "-09:00", "-10:00", "-11:00", "-12:00", "+00:00", "+01:00", "+02:00", "+03:00", "+04:00", "+05:00", "+06:00", "+07:00", "+08:00", "+09:00", "+10:00", "+11:00", "+12:00", "+13:00", "+14:00"))
    assert second.checkpoint_history[-1].observed_tz


def test_checkpoint_peek_status_does_not_create_runtime_session_file(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    session_file = workspace_root / "aoa-sdk" / ".aoa" / "skill-runtime-session.json"
    note_dir = _checkpoint_note_dir(workspace_root, repo_label="aoa-sdk")
    _write_checkpoint_history_entry(
        note_dir=note_dir,
        session_ref="session:test-read-only-peek",
        runtime_session_id="runtime-session-peek",
        repo_root=workspace_root / "aoa-sdk",
        repo_label="aoa-sdk",
        candidate_id="candidate:route:aoa-playbooks-playbook-registry-min",
        candidate_kind="route",
        owner_hint="aoa-playbooks",
        display_name="Recurring route candidate",
        source_surface_ref="aoa-playbooks.playbook_registry.min",
        evidence_refs=["aoa-playbooks.playbook_registry.min"],
        progression_axis_signals=[],
    )

    note = sdk.checkpoints.peek_status(repo_root=str(workspace_root / "aoa-sdk"))

    assert note.session_ref == "session:test-read-only-peek"
    assert not session_file.exists()


def test_probe_session_returns_none_without_creating_runtime_session_file(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    session_path, session = probe_session(sdk.workspace, None)

    assert session is None
    assert session_path == workspace_root / "aoa-sdk" / ".aoa" / "skill-runtime-session.json"
    assert not session_path.exists()


def test_probe_session_returns_none_for_empty_runtime_session_file(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    session_path = workspace_root / "aoa-sdk" / ".aoa" / "skill-runtime-session.json"
    session_path.parent.mkdir(parents=True, exist_ok=True)
    session_path.write_text("", encoding="utf-8")

    resolved_path, session = probe_session(sdk.workspace, None)

    assert resolved_path == session_path
    assert session is None


def test_after_commit_skips_without_active_session_and_writes_status_artifact(workspace_root: Path) -> None:
    repo_root = workspace_root / "aoa-sdk"
    _init_git_repo(repo_root)
    commit_sha = _git_commit(repo_root, subject="plan verify a bounded change", body="checkpoint skip path")
    sdk = AoASDK.from_workspace(repo_root)

    report = sdk.checkpoints.after_commit(repo_root=str(repo_root), commit_ref="HEAD")

    status_path = workspace_root / "aoa-sdk" / ".aoa" / "session-growth" / "post-commit-status" / "aoa-sdk.latest.json"
    assert report.status == "skipped_no_active_session"
    assert report.commit_sha == commit_sha
    assert report.commit_subject == "plan verify a bounded change"
    assert report.changed_paths == ["README.md"]
    assert report.note_ref is None
    assert status_path.exists()
    assert not _checkpoint_note_dir(workspace_root, repo_label="aoa-sdk").exists()


def test_after_commit_reports_session_resolution_failure(workspace_root: Path) -> None:
    repo_root = workspace_root / "aoa-sdk"
    _init_git_repo(repo_root)
    commit_sha = _git_commit(repo_root, subject="plan verify a bounded change")
    contract_path = workspace_root / "aoa-skills" / "generated" / "runtime_session_contract.json"
    contract_path.unlink()
    sdk = AoASDK.from_workspace(repo_root)

    report = sdk.checkpoints.after_commit(repo_root=str(repo_root), commit_ref="HEAD")

    status_path = workspace_root / "aoa-sdk" / ".aoa" / "session-growth" / "post-commit-status" / "aoa-sdk.latest.json"
    assert report.status == "failed"
    assert report.commit_sha == commit_sha
    assert report.session_file is None
    assert report.error_text
    assert status_path.exists()


def test_after_commit_captures_reviewable_note_and_surface_context(
    workspace_root: Path,
    install_host_skills,
) -> None:
    install_host_skills(workspace_root, ["aoa-change-protocol"])
    repo_root = workspace_root / "aoa-sdk"
    _init_git_repo(repo_root)
    commit_sha = _git_commit(
        repo_root,
        subject="plan verify a bounded change",
        body="checkpoint capture body",
    )
    session_file = _write_runtime_session_file(
        workspace_root / "aoa-sdk" / ".aoa" / "skill-runtime-session.json",
        session_id="runtime-after-commit",
    )
    sdk = AoASDK.from_workspace(repo_root)

    report = sdk.checkpoints.after_commit(
        repo_root=str(repo_root),
        commit_ref="HEAD",
        session_file=str(session_file),
    )

    note_dir = _checkpoint_note_dir(
        workspace_root,
        repo_label="aoa-sdk",
        runtime_session_id="runtime-after-commit",
    )
    note_payload = json.loads((note_dir / "checkpoint-note.json").read_text(encoding="utf-8"))
    skill_payload = json.loads(Path(report.skill_report_path).read_text(encoding="utf-8"))
    surface_payload = json.loads(Path(report.surface_report_path).read_text(encoding="utf-8"))
    session_payload = json.loads(session_file.read_text(encoding="utf-8"))

    assert report.status == "captured"
    assert report.commit_sha == commit_sha
    assert report.commit_subject == "plan verify a bounded change"
    assert report.commit_body == "checkpoint capture body"
    assert report.changed_paths == ["README.md"]
    assert report.checkpoint_kind == "commit"
    assert report.mutation_surface == "code"
    assert report.manual_review_requested is True
    assert report.agent_review_required is True
    assert report.agent_review_status == "pending"
    assert report.agent_review_command is not None
    assert Path(report.report_path).exists()
    assert Path(report.skill_report_path).exists()
    assert Path(report.surface_report_path).exists()
    assert Path(report.note_ref).exists()
    assert note_payload["state"] == "reviewable"
    assert note_payload["agent_review_status"] == "pending"
    assert note_payload["agent_review_required"] is True
    assert note_payload["agent_review_pending_refs"] == [commit_sha]
    assert note_payload["checkpoint_history"][-1]["checkpoint_kind"] == "commit"
    assert note_payload["checkpoint_history"][-1]["manual_review_requested"] is True
    assert note_payload["checkpoint_history"][-1]["agent_review_status"] == "pending"
    assert skill_payload["report"]["phase"] == "checkpoint"
    assert skill_payload["report"]["activate_now"][0]["skill_name"] == "aoa-change-protocol"
    assert surface_payload["report"]["phase"] == "checkpoint"
    assert "aoa-change-protocol" in surface_payload["report"]["active_skill_names"]
    assert session_payload["active_skills"][0]["name"] == "aoa-change-protocol"
    assert any(entry["name"] == "aoa-change-protocol" for entry in session_payload["activation_log"])


def test_after_commit_owner_followthrough_uses_public_share_checkpoint(
    workspace_root: Path,
) -> None:
    repo_root = workspace_root / "aoa-sdk"
    _init_git_repo(repo_root)
    commit_sha = _git_commit(
        repo_root,
        subject="owner follow-through after reviewed closeout",
        body="checkpoint capture body",
    )
    session_file = _write_runtime_session_file(
        workspace_root / "aoa-sdk" / ".aoa" / "skill-runtime-session.json",
        session_id="runtime-owner-followthrough",
    )
    sdk = AoASDK.from_workspace(repo_root)

    report = sdk.checkpoints.after_commit(
        repo_root=str(repo_root),
        commit_ref="HEAD",
        session_file=str(session_file),
    )

    note_dir = _checkpoint_note_dir(
        workspace_root,
        repo_label="aoa-sdk",
        runtime_session_id="runtime-owner-followthrough",
    )
    note_payload = json.loads((note_dir / "checkpoint-note.json").read_text(encoding="utf-8"))
    surface_payload = json.loads(Path(report.surface_report_path).read_text(encoding="utf-8"))

    assert report.status == "captured"
    assert report.commit_sha == commit_sha
    assert report.checkpoint_kind == "owner_followthrough"
    assert report.mutation_surface == "public-share"
    assert report.agent_review_status == "pending"
    assert report.agent_review_command is not None
    assert note_payload["checkpoint_history"][-1]["checkpoint_kind"] == "owner_followthrough"
    assert note_payload["checkpoint_history"][-1]["manual_review_requested"] is True
    assert note_payload["checkpoint_history"][-1]["agent_review_status"] == "pending"
    assert surface_payload["report"]["checkpoint_kind"] == "owner_followthrough"
    assert surface_payload["report"]["mutation_surface"] == "public-share"


def test_after_commit_records_closed_session_followthrough_without_rotating_note(
    workspace_root: Path,
) -> None:
    repo_root = workspace_root / "aoa-sdk"
    _init_git_repo(repo_root)
    _git_commit(repo_root, subject="plan verify a bounded change")
    session_file = _write_runtime_session_file(
        workspace_root / "aoa-sdk" / ".aoa" / "skill-runtime-session.json",
        session_id="runtime-closed-followthrough",
    )
    sdk = AoASDK.from_workspace(repo_root)
    sdk.checkpoints.append(
        repo_root=str(repo_root),
        checkpoint_kind="commit",
        intent_text="recurring workflow needs better handoff proof and recall",
        mutation_surface="code",
        session_file=str(session_file),
    )
    note = sdk.checkpoints.append(
        repo_root=str(repo_root),
        checkpoint_kind="verify_green",
        intent_text="recurring workflow needs better handoff proof and recall",
        mutation_surface="code",
        session_file=str(session_file),
    )
    sdk.checkpoints.promote(
        repo_root=str(repo_root),
        target="harvest-handoff",
        session_file=str(session_file),
    )
    note_dir = _checkpoint_note_dir(
        workspace_root,
        repo_label="aoa-sdk",
        runtime_session_id=note.runtime_session_id,
    )
    closed_note_payload = json.loads((note_dir / "checkpoint-note.json").read_text(encoding="utf-8"))
    history_count = len(closed_note_payload["checkpoint_history"])
    commit_sha = _git_commit(repo_root, subject="owner follow-through promote reviewed closeout")

    report = sdk.checkpoints.after_commit(
        repo_root=str(repo_root),
        commit_ref=commit_sha,
        session_file=str(session_file),
    )

    archive_root = workspace_root / "aoa-sdk" / ".aoa" / "session-growth" / "archive"
    refreshed_note_payload = json.loads((note_dir / "checkpoint-note.json").read_text(encoding="utf-8"))

    assert report.status == "recorded_closed_session_followthrough"
    assert report.checkpoint_kind == "owner_followthrough"
    assert report.mutation_surface == "public-share"
    assert report.manual_review_requested is False
    assert report.note_ref == str(note_dir / "checkpoint-note.json")
    assert report.error_text is not None
    assert Path(report.report_path).exists()
    assert refreshed_note_payload["state"] == "closed"
    assert len(refreshed_note_payload["checkpoint_history"]) == history_count
    assert refreshed_note_payload["checkpoint_history"][-1]["checkpoint_kind"] == "verify_green"
    assert not archive_root.exists()


def test_checkpoint_review_note_adds_agent_authored_checkpoint_review(workspace_root: Path) -> None:
    repo_root = workspace_root / "aoa-sdk"
    _init_git_repo(repo_root)
    commit_sha = _git_commit(repo_root, subject="plan verify a bounded change")
    session_file = _write_runtime_session_file(
        workspace_root / "aoa-sdk" / ".aoa" / "skill-runtime-session.json",
        session_id="runtime-agent-review",
    )
    sdk = AoASDK.from_workspace(repo_root)
    captured = sdk.checkpoints.after_commit(
        repo_root=str(repo_root),
        commit_ref="HEAD",
        session_file=str(session_file),
    )

    note = sdk.checkpoints.review_note(
        repo_root=str(repo_root),
        commit_ref="HEAD",
        summary="Agent reviewed the post-commit checkpoint and confirmed the hook/review seam is the candidate.",
        findings=["what: post-commit hook now records a pending checkpoint review; why: prevents silent commit checkpoints"],
        candidate_notes=["where: aoa-sdk owns the control-plane review-note command and hook template"],
        stats_hints=["stats: refresh session-growth automation counters only after reviewed closeout"],
        mechanic_hints=["mechanic: commit is not complete for the agent until review-note is written"],
        closeout_questions=["did the full session confirm the hook/review split or reveal missing candidate types?"],
        evidence_refs=[captured.report_path],
        next_owner_moves=["carry the agent-authored review into closeout before stats refresh"],
        applied_skill_names=["aoa-change-protocol"],
        session_file=str(session_file),
    )
    report_payload = json.loads(Path(captured.report_path).read_text(encoding="utf-8"))

    assert note.agent_review_status == "reviewed"
    assert note.agent_review_required is False
    assert note.agent_reviews
    assert note.agent_reviews[-1].commit_sha == commit_sha
    assert note.agent_reviews[-1].summary.startswith("Agent reviewed")
    assert note.agent_reviews[-1].findings
    assert note.agent_reviews[-1].stats_hints
    assert note.checkpoint_history[-1].agent_review_status == "reviewed"
    assert report_payload["agent_review_status"] == "reviewed"
    assert report_payload["agent_review_ref"] == note.agent_reviews[-1].review_id


def test_after_commit_failure_writes_artifact_without_corrupting_checkpoint_state(workspace_root: Path) -> None:
    repo_root = workspace_root / "aoa-sdk"
    _init_git_repo(repo_root)
    _git_commit(repo_root, subject="plan verify a bounded change")
    session_file = _write_runtime_session_file(
        workspace_root / "aoa-sdk" / ".aoa" / "skill-runtime-session.json",
        session_id="runtime-after-commit-failure",
    )
    sdk = AoASDK.from_workspace(repo_root)

    report = sdk.checkpoints.after_commit(
        repo_root=str(repo_root),
        commit_ref="missing-ref",
        session_file=str(session_file),
    )

    note_dir = _checkpoint_note_dir(
        workspace_root,
        repo_label="aoa-sdk",
        runtime_session_id="runtime-after-commit-failure",
    )
    fallback_status = workspace_root / "aoa-sdk" / ".aoa" / "session-growth" / "post-commit-status" / "aoa-sdk.latest.json"

    assert report.status == "failed"
    assert report.error_text
    assert Path(report.report_path).exists()
    assert fallback_status.exists()
    assert not (note_dir / "checkpoint-note.json").exists()
    assert not (note_dir / "checkpoint-note.jsonl").exists()


def test_after_commit_uses_thread_scoped_runtime_sessions(workspace_root: Path, monkeypatch) -> None:
    repo_root = workspace_root / "aoa-sdk"
    _init_git_repo(repo_root)
    _git_commit(repo_root, subject="plan verify a bounded change")
    sdk = AoASDK.from_workspace(repo_root)

    monkeypatch.setenv("CODEX_THREAD_ID", "thread-one")
    thread_one_session = _write_runtime_session_file(
        workspace_root / "aoa-sdk" / ".aoa" / "skill-runtime-sessions" / "thread-one.json",
        session_id="runtime-thread-one",
        codex_thread_id="thread-one",
    )
    report_one = sdk.checkpoints.after_commit(repo_root=str(repo_root), commit_ref="HEAD")

    monkeypatch.setenv("CODEX_THREAD_ID", "thread-two")
    thread_two_session = _write_runtime_session_file(
        workspace_root / "aoa-sdk" / ".aoa" / "skill-runtime-sessions" / "thread-two.json",
        session_id="runtime-thread-two",
        codex_thread_id="thread-two",
    )
    report_two = sdk.checkpoints.after_commit(repo_root=str(repo_root), commit_ref="HEAD")

    assert thread_one_session.exists()
    assert thread_two_session.exists()
    assert report_one.status == "captured"
    assert report_two.status == "captured"
    assert report_one.runtime_session_id == "runtime-thread-one"
    assert report_two.runtime_session_id == "runtime-thread-two"
    assert Path(report_one.report_path).parent != Path(report_two.report_path).parent
    assert "runtime-thread-one" in report_one.report_path
    assert "runtime-thread-two" in report_two.report_path


def test_capture_from_skill_phase_auto_appends_only_when_growth_signal_exists(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    capture = sdk.checkpoints.capture_from_skill_phase(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="pre-mutation",
        intent_text="recurring workflow needs better handoff proof and recall",
        mutation_surface="code",
    )

    note_dir = _checkpoint_note_dir(
        workspace_root,
        repo_label="aoa-sdk",
        runtime_session_id=capture.note.runtime_session_id if capture.note is not None else None,
    )
    assert capture.mode == "auto"
    assert capture.appended is True
    assert capture.reason == "checkpoint_signal"
    assert capture.checkpoint_kind == "commit"
    assert capture.note is not None
    assert (note_dir / "checkpoint-note.json").exists()


def test_capture_from_skill_phase_reports_no_signal_without_writing_note(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    capture = sdk.checkpoints.capture_from_skill_phase(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="ingress",
        intent_text="plan a cross-repo change",
        mutation_surface="none",
    )

    note_dir = workspace_root / "aoa-sdk" / ".aoa" / "session-growth" / "current" / "aoa-sdk"
    assert capture.mode == "auto"
    assert capture.appended is False
    assert capture.reason == "no_checkpoint_signal"
    assert capture.note is None
    assert not note_dir.exists()


def test_capture_from_skill_phase_read_only_ingress_does_not_append_diagnostic_checkpoint(
    workspace_root: Path,
) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    runtime_session_id = "runtime-session-diagnostic"
    session_file = _write_runtime_session_file(
        workspace_root / "aoa-sdk" / ".aoa" / "test-runtime-session-diagnostic.json",
        session_id=runtime_session_id,
    )
    note_dir = _checkpoint_note_dir(
        workspace_root,
        repo_label="aoa-sdk",
        runtime_session_id=runtime_session_id,
    )
    _write_checkpoint_history_entry(
        note_dir=note_dir,
        session_ref="session:test-read-only-diagnostic",
        runtime_session_id=runtime_session_id,
        repo_root=workspace_root / "aoa-sdk",
        repo_label="aoa-sdk",
        candidate_id="candidate:route:aoa-playbooks-playbook-registry-min",
        candidate_kind="route",
        owner_hint="aoa-playbooks",
        display_name="Recurring route candidate",
        source_surface_ref="aoa-playbooks.playbook_registry.min",
        evidence_refs=["aoa-playbooks.playbook_registry.min"],
        progression_axis_signals=[],
    )
    jsonl_path = note_dir / "checkpoint-note.jsonl"
    original_jsonl = jsonl_path.read_text(encoding="utf-8")

    capture = sdk.checkpoints.capture_from_skill_phase(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="ingress",
        intent_text="diagnose why checkpoint closeout skill failed to orient in session space and mixed candidate scopes",
        mutation_surface="none",
        session_file=str(session_file),
    )

    assert capture.mode == "auto"
    assert capture.appended is False
    assert capture.reason == "no_checkpoint_signal"
    assert capture.checkpoint_kind is None
    assert capture.note is not None
    assert capture.harvest_candidate_ids == ["candidate:route:aoa-playbooks-playbook-registry-min"]
    assert jsonl_path.read_text(encoding="utf-8") == original_jsonl
    assert not (note_dir / "checkpoint-note.json").exists()
    assert not (
        workspace_root / "aoa-sdk" / ".aoa" / "surface-detection" / "aoa-sdk.checkpoint.latest.json"
    ).exists()


def test_surface_detect_checkpoint_phase_emits_growth_cluster_for_explicit_commit_intent(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    report = sdk.surfaces.detect(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="checkpoint",
        checkpoint_kind="commit",
        intent_text="commit bounded patch",
        mutation_surface="code",
    )

    assert report.checkpoint_should_capture is True
    growth_cluster = next(cluster for cluster in report.candidate_clusters if cluster.candidate_kind == "growth")
    assert growth_cluster.owner_hint == "aoa-sdk"
    assert growth_cluster.source_surface_ref == "aoa-sdk:checkpoint_auto_capture.commit"
    assert "mutation_surface:code" in growth_cluster.evidence_refs


def test_surface_detect_checkpoint_phase_emits_growth_cluster_for_opened_pr(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    report = sdk.surfaces.detect(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="checkpoint",
        checkpoint_kind="pr_opened",
        intent_text="opened aoa-skills PR #157 after protected main rejected direct push",
        mutation_surface="public-share",
    )

    assert report.checkpoint_should_capture is True
    growth_cluster = next(cluster for cluster in report.candidate_clusters if cluster.candidate_kind == "growth")
    assert growth_cluster.owner_hint == "aoa-sdk"
    assert growth_cluster.source_surface_ref == "aoa-sdk:checkpoint_auto_capture.pr_opened"
    assert "mutation_surface:public-share" in growth_cluster.evidence_refs
    assert {signal.axis for signal in growth_cluster.progression_axis_signals} == {
        "execution_reliability",
        "change_legibility",
        "review_sharpness",
    }


def test_surface_detect_checkpoint_phase_keeps_growth_cluster_with_heuristic_candidates(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    report = sdk.surfaces.detect(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="checkpoint",
        checkpoint_kind="verify_green",
        intent_text="verified checkpoint mark captures public-share PR milestones with release_check green",
        mutation_surface="code",
    )

    assert report.checkpoint_should_capture is True
    assert any(cluster.candidate_kind == "route" for cluster in report.candidate_clusters)
    assert any(
        cluster.source_surface_ref == "aoa-sdk:checkpoint_auto_capture.verify_green"
        for cluster in report.candidate_clusters
    )


def test_capture_from_skill_phase_auto_appends_for_explicit_commit_intent(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    capture = sdk.checkpoints.capture_from_skill_phase(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="pre-mutation",
        intent_text="commit bounded patch",
        mutation_surface="code",
    )

    note_dir = _checkpoint_note_dir(
        workspace_root,
        repo_label="aoa-sdk",
        runtime_session_id=capture.note.runtime_session_id if capture.note is not None else None,
    )
    assert capture.mode == "auto"
    assert capture.appended is True
    assert capture.reason == "checkpoint_signal"
    assert capture.checkpoint_kind == "commit"
    assert capture.note is not None
    growth_cluster = next(cluster for cluster in capture.note.candidate_clusters if cluster.candidate_kind == "growth")
    assert growth_cluster.session_end_targets == ["harvest", "progression"]
    assert {signal.axis for signal in growth_cluster.progression_axis_signals} == {
        "execution_reliability",
        "change_legibility",
    }
    assert capture.note.harvest_candidate_ids == [growth_cluster.candidate_id]
    assert capture.note.progression_candidate_ids == [growth_cluster.candidate_id]
    assert capture.note.upgrade_candidate_ids == []
    assert [target.skill_name for target in capture.session_end_skill_targets] == [
        "aoa-session-donor-harvest",
        "aoa-session-progression-lift",
        "aoa-quest-harvest",
    ]
    assert capture.progression_axis_signals
    assert capture.stats_refresh_recommended is True
    assert capture.session_end_next_honest_move is not None
    assert capture.captured_at is not None
    assert capture.captured_at_local is not None
    assert capture.captured_tz
    assert (note_dir / "checkpoint-note.json").exists()


def test_capture_from_skill_phase_reports_existing_session_end_targets_when_skip_has_live_note(
    workspace_root: Path,
) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    sdk.checkpoints.append(
        repo_root=str(workspace_root / "aoa-sdk"),
        checkpoint_kind="commit",
        intent_text="recurring workflow needs better handoff proof and recall",
    )
    sdk.checkpoints.append(
        repo_root=str(workspace_root / "aoa-sdk"),
        checkpoint_kind="verify_green",
        intent_text="recurring workflow needs better handoff proof and recall",
    )

    capture = sdk.checkpoints.capture_from_skill_phase(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="pre-mutation",
        intent_text="refresh generated contracts",
        mutation_surface="code",
    )

    assert capture.appended is False
    assert capture.reason == "no_checkpoint_signal"
    assert capture.note is not None
    assert capture.note_ref is not None
    assert [target.skill_name for target in capture.session_end_skill_targets] == [
        "aoa-session-donor-harvest",
        "aoa-session-progression-lift",
        "aoa-quest-harvest",
    ]
    assert capture.progression_axis_signals
    assert capture.stats_refresh_recommended is True
    assert capture.session_end_next_honest_move is not None
    assert capture.harvest_candidate_ids
    assert capture.progression_candidate_ids


def test_checkpoint_append_session_ref_tracks_runtime_session_identity(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    session_file = workspace_root / "aoa-sdk" / ".aoa" / "checkpoint-skill-session.json"

    first = sdk.checkpoints.append(
        repo_root=str(workspace_root / "aoa-sdk"),
        checkpoint_kind="commit",
        intent_text="commit bounded patch",
        session_file=str(session_file),
    )
    second = sdk.checkpoints.append(
        repo_root=str(workspace_root / "aoa-sdk"),
        checkpoint_kind="verify_green",
        intent_text="verify green for bounded patch",
        session_file=str(session_file),
    )

    session_payload = json.loads(session_file.read_text(encoding="utf-8"))

    assert first.session_ref == second.session_ref
    assert first.runtime_session_id == session_payload["session_id"]
    assert second.runtime_session_id == session_payload["session_id"]
    assert session_payload["session_id"][:12] in first.session_ref
    assert "checkpoint-growth" in first.session_ref


def test_checkpoint_append_rotates_when_runtime_session_changes(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    session_file = workspace_root / "aoa-sdk" / ".aoa" / "checkpoint-skill-session.json"

    first = sdk.checkpoints.append(
        repo_root=str(workspace_root / "aoa-sdk"),
        checkpoint_kind="commit",
        intent_text="commit bounded patch",
        session_file=str(session_file),
    )

    session_payload = json.loads(session_file.read_text(encoding="utf-8"))
    session_payload["session_id"] = "runtime-session-two"
    session_payload["created_at"] = "2026-04-10T12:00:00Z"
    session_payload["updated_at"] = "2026-04-10T12:00:00Z"
    session_file.write_text(json.dumps(session_payload, indent=2) + "\n", encoding="utf-8")

    second = sdk.checkpoints.append(
        repo_root=str(workspace_root / "aoa-sdk"),
        checkpoint_kind="commit",
        intent_text="commit bounded patch",
        session_file=str(session_file),
    )

    first_note_dir = _checkpoint_note_dir(
        workspace_root,
        repo_label="aoa-sdk",
        runtime_session_id=first.runtime_session_id,
    )
    second_note_dir = _checkpoint_note_dir(
        workspace_root,
        repo_label="aoa-sdk",
        runtime_session_id=second.runtime_session_id,
    )
    archive_dirs = sorted((workspace_root / "aoa-sdk" / ".aoa" / "session-growth" / "archive").glob("aoa-sdk-*"))

    assert second.session_ref != first.session_ref
    assert second.runtime_session_id == "runtime-session-two"
    assert (first_note_dir / "checkpoint-note.json").exists()
    assert (second_note_dir / "checkpoint-note.json").exists()
    assert not archive_dirs


def test_checkpoint_append_rotates_promoted_note_into_fresh_checkpoint_cycle(workspace_root: Path) -> None:
    dionysus_root = workspace_root / "Dionysus"
    (dionysus_root / "reports" / "ecosystem-audits").mkdir(parents=True, exist_ok=True)
    (dionysus_root / "README.md").write_text("# Dionysus\n", encoding="utf-8")

    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    session_file = workspace_root / "aoa-sdk" / ".aoa" / "checkpoint-skill-session.json"

    first = sdk.checkpoints.append(
        repo_root=str(workspace_root / "aoa-sdk"),
        checkpoint_kind="commit",
        intent_text="recurring workflow needs better handoff proof and recall",
        mutation_surface="code",
        session_file=str(session_file),
    )
    sdk.checkpoints.append(
        repo_root=str(workspace_root / "aoa-sdk"),
        checkpoint_kind="verify_green",
        intent_text="recurring workflow needs better handoff proof and recall",
        mutation_surface="code",
        session_file=str(session_file),
    )
    sdk.checkpoints.promote(
        repo_root=str(workspace_root / "aoa-sdk"),
        target="dionysus-note",
        session_file=str(session_file),
    )

    second = sdk.checkpoints.append(
        repo_root=str(workspace_root / "aoa-sdk"),
        checkpoint_kind="commit",
        intent_text="commit bounded patch",
        session_file=str(session_file),
    )

    archive_dirs = sorted((workspace_root / "aoa-sdk" / ".aoa" / "session-growth" / "archive").glob("aoa-sdk-*"))

    assert second.session_ref != first.session_ref
    assert second.runtime_session_id == first.runtime_session_id
    assert archive_dirs
    archived_note = json.loads((archive_dirs[-1] / "checkpoint-note.json").read_text(encoding="utf-8"))
    assert archived_note["state"] == "promoted"
    assert archived_note["session_ref"] == first.session_ref


def test_checkpoint_status_archives_stale_current_note_when_runtime_session_changes(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    session_file = workspace_root / "aoa-sdk" / ".aoa" / "checkpoint-skill-session.json"

    first = sdk.checkpoints.append(
        repo_root=str(workspace_root / "aoa-sdk"),
        checkpoint_kind="commit",
        intent_text="commit bounded patch",
        session_file=str(session_file),
    )

    session_payload = json.loads(session_file.read_text(encoding="utf-8"))
    session_payload["session_id"] = "runtime-session-two"
    session_payload["created_at"] = "2026-04-10T12:00:00Z"
    session_payload["updated_at"] = "2026-04-10T12:00:00Z"
    session_file.write_text(json.dumps(session_payload, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(SurfaceNotFound):
        sdk.checkpoints.status(
            repo_root=str(workspace_root / "aoa-sdk"),
            session_file=str(session_file),
        )

    first_note_dir = _checkpoint_note_dir(
        workspace_root,
        repo_label="aoa-sdk",
        runtime_session_id=first.runtime_session_id,
    )
    second_note_dir = _checkpoint_note_dir(
        workspace_root,
        repo_label="aoa-sdk",
        runtime_session_id="runtime-session-two",
    )
    archive_dirs = sorted((workspace_root / "aoa-sdk" / ".aoa" / "session-growth" / "archive").glob("aoa-sdk-*"))

    assert not archive_dirs
    assert (first_note_dir / "checkpoint-note.json").exists()
    assert not (second_note_dir / "checkpoint-note.json").exists()


def test_capture_from_skill_phase_does_not_reuse_stale_current_note(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    session_file = workspace_root / "aoa-sdk" / ".aoa" / "checkpoint-skill-session.json"

    sdk.checkpoints.append(
        repo_root=str(workspace_root / "aoa-sdk"),
        checkpoint_kind="commit",
        intent_text="recurring workflow needs better handoff proof and recall",
        mutation_surface="code",
        session_file=str(session_file),
    )

    session_payload = json.loads(session_file.read_text(encoding="utf-8"))
    session_payload["session_id"] = "runtime-session-two"
    session_payload["created_at"] = "2026-04-10T12:00:00Z"
    session_payload["updated_at"] = "2026-04-10T12:00:00Z"
    session_file.write_text(json.dumps(session_payload, indent=2) + "\n", encoding="utf-8")

    capture = sdk.checkpoints.capture_from_skill_phase(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="pre-mutation",
        intent_text="refresh generated contracts",
        mutation_surface="code",
        session_file=str(session_file),
    )

    assert capture.appended is False
    assert capture.reason == "no_checkpoint_signal"
    assert capture.note is None
    assert capture.note_ref is None
    assert capture.session_end_skill_targets == []
    assert capture.stats_refresh_recommended is False


def test_checkpoint_parallel_runtime_sessions_keep_independent_current_ledgers(
    workspace_root: Path,
    monkeypatch,
) -> None:
    monkeypatch.delenv("CODEX_THREAD_ID", raising=False)
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    session_file_one = _write_runtime_session_file(
        workspace_root / "aoa-sdk" / ".aoa" / "parallel-session-one.json",
        session_id="runtime-session-one",
    )
    session_file_two = _write_runtime_session_file(
        workspace_root / "aoa-sdk" / ".aoa" / "parallel-session-two.json",
        session_id="runtime-session-two",
    )

    first = sdk.checkpoints.append(
        repo_root=str(workspace_root / "aoa-sdk"),
        checkpoint_kind="commit",
        intent_text="commit bounded patch",
        session_file=str(session_file_one),
    )
    second = sdk.checkpoints.append(
        repo_root=str(workspace_root / "aoa-sdk"),
        checkpoint_kind="commit",
        intent_text="commit bounded patch",
        session_file=str(session_file_two),
    )

    first_note_dir = _checkpoint_note_dir(
        workspace_root,
        repo_label="aoa-sdk",
        runtime_session_id="runtime-session-one",
    )
    second_note_dir = _checkpoint_note_dir(
        workspace_root,
        repo_label="aoa-sdk",
        runtime_session_id="runtime-session-two",
    )

    assert first.runtime_session_id == "runtime-session-one"
    assert second.runtime_session_id == "runtime-session-two"
    assert (first_note_dir / "checkpoint-note.json").exists()
    assert (second_note_dir / "checkpoint-note.json").exists()
    assert sdk.checkpoints.status(
        repo_root=str(workspace_root / "aoa-sdk"),
        session_file=str(session_file_one),
    ).runtime_session_id == "runtime-session-one"
    assert sdk.checkpoints.status(
        repo_root=str(workspace_root / "aoa-sdk"),
        session_file=str(session_file_two),
    ).runtime_session_id == "runtime-session-two"


def test_checkpoint_status_backfills_local_timestamp_for_legacy_history_entry(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    note_dir = workspace_root / "aoa-sdk" / ".aoa" / "session-growth" / "current" / "aoa-sdk"
    note_dir.mkdir(parents=True, exist_ok=True)
    legacy_payload = {
        "session_ref": "session:2026-04-09-aoa-sdk-checkpoint-growth",
        "repo_root": str(workspace_root / "aoa-sdk"),
        "repo_label": "aoa-sdk",
        "history_entry": {
            "checkpoint_kind": "commit",
            "observed_at": "2026-04-09T17:54:04Z",
            "report_ref": str(note_dir / "legacy-report.json"),
            "intent_text": "legacy checkpoint",
            "checkpoint_should_capture": False,
            "blocked_by": [],
            "candidate_clusters": [],
            "manual_review_requested": False,
        },
    }
    (note_dir / "checkpoint-note.jsonl").write_text(json.dumps(legacy_payload) + "\n", encoding="utf-8")

    note = sdk.checkpoints.status(repo_root=str(workspace_root / "aoa-sdk"))
    rebuilt_note_dir = _checkpoint_note_dir(
        workspace_root,
        repo_label="aoa-sdk",
        runtime_session_id=note.runtime_session_id,
    )

    expected_local = datetime.fromisoformat("2026-04-09T17:54:04+00:00").astimezone().isoformat()
    assert note.checkpoint_history[0].observed_at_local == expected_local
    assert note.checkpoint_history[0].observed_tz
    rebuilt = json.loads((rebuilt_note_dir / "checkpoint-note.json").read_text(encoding="utf-8"))
    assert rebuilt["checkpoint_history"][0]["observed_at_local"] == expected_local
    assert rebuilt["checkpoint_history"][0]["observed_tz"]


def test_detect_surfaces_checkpoint_bridge_when_runtime_note_exists(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    sdk.checkpoints.append(
        repo_root=str(workspace_root / "aoa-sdk"),
        checkpoint_kind="commit",
        intent_text="recurring workflow needs better handoff proof and recall",
    )
    sdk.checkpoints.append(
        repo_root=str(workspace_root / "aoa-sdk"),
        checkpoint_kind="verify_green",
        intent_text="recurring workflow needs better handoff proof and recall",
    )

    report = sdk.skills.detect(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="ingress",
        intent_text="review the current checkpoint note and name the honest next closeout step",
    )

    assert any(item.skill_name == "aoa-checkpoint-closeout-bridge" for item in report.must_confirm)


def test_checkpoint_promote_writes_dionysus_snapshot_and_updates_note(workspace_root: Path) -> None:
    dionysus_root = workspace_root / "Dionysus"
    (dionysus_root / "reports" / "ecosystem-audits").mkdir(parents=True, exist_ok=True)
    (dionysus_root / "README.md").write_text("# Dionysus\n", encoding="utf-8")

    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    sdk.checkpoints.append(
        repo_root=str(workspace_root / "aoa-sdk"),
        checkpoint_kind="commit",
        intent_text="recurring workflow needs better handoff proof and recall",
    )
    sdk.checkpoints.append(
        repo_root=str(workspace_root / "aoa-sdk"),
        checkpoint_kind="verify_green",
        intent_text="recurring workflow needs better handoff proof and recall",
    )

    promotion = sdk.checkpoints.promote(
        repo_root=str(workspace_root / "aoa-sdk"),
        target="dionysus-note",
    )

    promoted_json = list((dionysus_root / "reports" / "ecosystem-audits").glob("*.aoa-sdk.checkpoint-note.json"))
    promoted_md = list((dionysus_root / "reports" / "ecosystem-audits").glob("*.aoa-sdk.checkpoint-note.md"))

    assert promotion.target == "dionysus-note"
    assert promotion.resulting_state == "promoted"
    assert promoted_json
    assert promoted_md
    assert any("repo:Dionysus/reports/ecosystem-audits/" in ref for ref in promotion.output_refs)
    with pytest.raises(SurfaceNotFound):
        sdk.checkpoints.status(repo_root=str(workspace_root / "aoa-sdk"))


def test_checkpoint_promote_to_dionysus_uses_session_specific_filenames(workspace_root: Path) -> None:
    dionysus_root = workspace_root / "Dionysus"
    (dionysus_root / "reports" / "ecosystem-audits").mkdir(parents=True, exist_ok=True)
    (dionysus_root / "README.md").write_text("# Dionysus\n", encoding="utf-8")

    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    session_file = workspace_root / "aoa-sdk" / ".aoa" / "checkpoint-skill-session.json"
    sdk.checkpoints.append(
        repo_root=str(workspace_root / "aoa-sdk"),
        checkpoint_kind="commit",
        intent_text="recurring workflow needs better handoff proof and recall",
        mutation_surface="code",
        session_file=str(session_file),
    )
    sdk.checkpoints.append(
        repo_root=str(workspace_root / "aoa-sdk"),
        checkpoint_kind="verify_green",
        intent_text="recurring workflow needs better handoff proof and recall",
        mutation_surface="code",
        session_file=str(session_file),
    )

    first = sdk.checkpoints.promote(
        repo_root=str(workspace_root / "aoa-sdk"),
        target="dionysus-note",
        session_file=str(session_file),
    )

    session_payload = json.loads(session_file.read_text(encoding="utf-8"))
    session_payload["session_id"] = "runtime-session-two"
    session_payload["created_at"] = "2026-04-10T12:00:00Z"
    session_payload["updated_at"] = "2026-04-10T12:00:00Z"
    session_file.write_text(json.dumps(session_payload, indent=2) + "\n", encoding="utf-8")

    sdk.checkpoints.append(
        repo_root=str(workspace_root / "aoa-sdk"),
        checkpoint_kind="commit",
        intent_text="recurring workflow needs better handoff proof and recall",
        mutation_surface="code",
        session_file=str(session_file),
    )
    sdk.checkpoints.append(
        repo_root=str(workspace_root / "aoa-sdk"),
        checkpoint_kind="verify_green",
        intent_text="recurring workflow needs better handoff proof and recall",
        mutation_surface="code",
        session_file=str(session_file),
    )

    second = sdk.checkpoints.promote(
        repo_root=str(workspace_root / "aoa-sdk"),
        target="dionysus-note",
        session_file=str(session_file),
    )

    promoted_json = sorted(
        path.name
        for path in (dionysus_root / "reports" / "ecosystem-audits").glob("*.aoa-sdk.checkpoint-note.json")
    )

    assert first.output_refs != second.output_refs
    assert len(promoted_json) == 2
    assert len(set(promoted_json)) == 2


def test_checkpoint_promote_harvest_handoff_closes_note(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    sdk.checkpoints.append(
        repo_root=str(workspace_root / "aoa-sdk"),
        checkpoint_kind="commit",
        intent_text="recurring workflow needs better handoff proof and recall",
    )
    note = sdk.checkpoints.append(
        repo_root=str(workspace_root / "aoa-sdk"),
        checkpoint_kind="verify_green",
        intent_text="recurring workflow needs better handoff proof and recall",
    )

    promotion = sdk.checkpoints.promote(
        repo_root=str(workspace_root / "aoa-sdk"),
        target="harvest-handoff",
    )

    handoff_path = (
        _checkpoint_note_dir(
            workspace_root,
            repo_label="aoa-sdk",
            runtime_session_id=note.runtime_session_id,
        )
        / "harvest-handoff.json"
    )

    assert promotion.target == "harvest-handoff"
    assert promotion.resulting_state == "closed"
    assert handoff_path.exists()
    assert promotion.output_refs == [str(handoff_path)]
    with pytest.raises(SurfaceNotFound):
        sdk.checkpoints.status(repo_root=str(workspace_root / "aoa-sdk"))


def test_surface_closeout_handoff_links_checkpoint_note(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    sdk.checkpoints.append(
        repo_root=str(workspace_root / "aoa-sdk"),
        checkpoint_kind="commit",
        intent_text="recurring workflow needs better handoff proof and recall",
    )
    sdk.checkpoints.append(
        repo_root=str(workspace_root / "aoa-sdk"),
        checkpoint_kind="verify_green",
        intent_text="recurring workflow needs better handoff proof and recall",
    )
    report = sdk.surfaces.detect(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="closeout",
        intent_text="recurring workflow needs better handoff proof and recall",
    )

    handoff = sdk.surfaces.build_closeout_handoff(
        report,
        session_ref="session:test-checkpoint-closeout-handoff",
    )

    assert handoff.checkpoint_note_ref is not None
    assert handoff.surviving_checkpoint_clusters
    assert handoff.checkpoint_harvest_candidates
    assert handoff.checkpoint_progression_candidates
    assert handoff.checkpoint_upgrade_candidates
    assert handoff.checkpoint_progression_axes
    assert handoff.stats_refresh_recommended is True
    assert all(cluster.lineage_hint is not None for cluster in handoff.surviving_checkpoint_clusters)
    route_lineage = next(
        cluster.lineage_hint
        for cluster in handoff.surviving_checkpoint_clusters
        if cluster.lineage_hint is not None and cluster.candidate_kind == "route"
    )
    assert route_lineage is not None
    assert route_lineage.cluster_ref.startswith("cluster:route:")
    assert route_lineage.owner_hypothesis == "aoa-playbooks"
    assert route_lineage.owner_shape == "playbook"
    assert "candidate_ref" not in route_lineage.model_dump()
    assert any(target.skill_name == "aoa-session-donor-harvest" for target in handoff.handoff_targets)
    assert any(target.skill_name == "aoa-session-progression-lift" for target in handoff.handoff_targets)
    assert any(target.skill_name == "aoa-quest-harvest" for target in handoff.handoff_targets)


def test_build_closeout_context_uses_note_handoff_and_receipts(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    reviewed_artifact = workspace_root / "aoa-sdk" / ".aoa" / "reviewed-session.md"
    reviewed_artifact.write_text(
        "\n".join(
            [
                "# Reviewed Session Artifact",
                "",
                "Session ref: `session:test-checkpoint-closeout-execute`",
                "",
                "- boundary review completed",
                "- verify green completed",
                "- repeated route evidence remained visible",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    sdk.checkpoints.append(
        repo_root=str(workspace_root / "aoa-sdk"),
        checkpoint_kind="commit",
        intent_text="recurring workflow needs better handoff proof and recall",
    )
    note = sdk.checkpoints.append(
        repo_root=str(workspace_root / "aoa-sdk"),
        checkpoint_kind="verify_green",
        intent_text="recurring workflow needs better handoff proof and recall",
    )
    note_dir = _checkpoint_note_dir(
        workspace_root,
        repo_label="aoa-sdk",
        runtime_session_id=note.runtime_session_id,
    )
    jsonl_path = note_dir / "checkpoint-note.jsonl"
    jsonl_lines = []
    for raw_line in jsonl_path.read_text(encoding="utf-8").splitlines():
        payload = json.loads(raw_line)
        payload["session_ref"] = "session:test-checkpoint-closeout-execute"
        jsonl_lines.append(json.dumps(payload))
    jsonl_path.write_text("\n".join(jsonl_lines) + "\n", encoding="utf-8")
    sdk.checkpoints.status(repo_root=str(workspace_root / "aoa-sdk"))

    report = sdk.surfaces.detect(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="closeout",
        intent_text="recurring workflow needs better handoff proof and recall",
    )
    handoff = sdk.surfaces.build_closeout_handoff(
        report,
        session_ref="session:test-checkpoint-closeout-execute",
    )
    handoff_path = workspace_root / "aoa-sdk" / ".aoa" / "surface-detection" / "aoa-sdk.closeout-handoff.latest.json"
    handoff_path.write_text(
        json.dumps({"report_path": str(handoff_path), "report": handoff.model_dump(mode="json")}, indent=2)
        + "\n",
        encoding="utf-8",
    )

    receipt_path = workspace_root / "aoa-sdk" / ".aoa" / "reviewed-receipt.json"
    receipt_path.write_text(
        json.dumps(
            {
                "event_kind": "harvest_packet_receipt",
                "event_id": "evt-existing-harvest",
                "observed_at": "2026-04-09T12:00:00Z",
                "run_ref": "run-existing-harvest",
                "session_ref": "session:test-checkpoint-closeout-execute",
                "actor_ref": "aoa-skills:aoa-session-donor-harvest",
                "object_ref": {"repo": "aoa-skills", "kind": "skill", "id": "aoa-session-donor-harvest"},
                "evidence_refs": [{"kind": "reviewed_artifact", "ref": str(reviewed_artifact)}],
                "payload": {"route_ref": "route:test-checkpoint-closeout-execute"},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    context = sdk.checkpoints.build_closeout_context(
        repo_root=str(workspace_root / "aoa-sdk"),
        reviewed_artifact_path=str(reviewed_artifact),
        receipt_paths=[str(receipt_path)],
    )

    assert context.session_ref == "session:test-checkpoint-closeout-execute"
    assert context.built_at_local is not None
    assert context.built_tz
    assert context.checkpoint_note_ref is not None
    assert context.surface_handoff_ref is not None
    assert context.receipt_refs == [str(receipt_path.resolve())]
    assert context.candidate_lineage_map
    route_lineage = next(
        hint
        for hint in context.candidate_lineage_map
        if hint.owner_hypothesis == "aoa-playbooks"
    )
    assert route_lineage.cluster_ref.startswith("cluster:route:")
    assert route_lineage.nearest_wrong_target == "aoa-skills"
    assert "candidate_ref" not in route_lineage.model_dump()
    assert [target.skill_name for target in context.ordered_skill_plan] == [
        "aoa-session-donor-harvest",
        "aoa-session-progression-lift",
        "aoa-quest-harvest",
    ]
    assert (note_dir / "closeout-context.json").exists()


def test_build_closeout_context_keeps_same_kind_mutation_lineage_seams_distinct(
    workspace_root: Path,
) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    reviewed_artifact = workspace_root / "aoa-sdk" / ".aoa" / "reviewed-session.md"
    reviewed_artifact.parent.mkdir(parents=True, exist_ok=True)
    reviewed_artifact.write_text("# Reviewed Session\n\n- checkpoint evidence reviewed\n", encoding="utf-8")

    sdk.checkpoints.append(
        repo_root=str(workspace_root / "aoa-sdk"),
        checkpoint_kind="commit",
        intent_text="commit checkpoint for code seam",
        mutation_surface="code",
    )
    sdk.checkpoints.append(
        repo_root=str(workspace_root / "aoa-sdk"),
        checkpoint_kind="commit",
        intent_text="commit checkpoint for public share seam",
        mutation_surface="public-share",
    )

    context = sdk.checkpoints.build_closeout_context(
        repo_root=str(workspace_root / "aoa-sdk"),
        reviewed_artifact_path=str(reviewed_artifact),
    )
    lineage_refs = [
        hint.cluster_ref
        for hint in context.candidate_lineage_map
        if hint.owner_hypothesis == "aoa-sdk"
    ]

    assert len(lineage_refs) == 2
    assert len(set(lineage_refs)) == 2
    assert any("commit-code" in cluster_ref for cluster_ref in lineage_refs)
    assert any("commit-public-share" in cluster_ref for cluster_ref in lineage_refs)


def test_build_closeout_context_aggregates_runtime_session_notes_across_repo_labels(
    workspace_root: Path,
    monkeypatch,
) -> None:
    monkeypatch.delenv("CODEX_THREAD_ID", raising=False)
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    runtime_session_id = "runtime-session-shared"
    session_file = _write_runtime_session_file(
        workspace_root / "aoa-sdk" / ".aoa" / "test-runtime-session.json",
        session_id=runtime_session_id,
    )
    rollout_path = _write_rollout_trace(
        workspace_root / "aoa-sdk" / ".aoa" / "runtime-trace.jsonl",
        assistant_message="reviewed the route and recall work, then verified the patch",
    )
    reviewed_artifact = workspace_root / "aoa-sdk" / ".aoa" / "reviewed-runtime-fan-in.md"
    reviewed_artifact.write_text(
        "\n".join(
            [
                "# Reviewed Session Artifact",
                "",
                "Session ref: `session:test-runtime-fan-in-closeout`",
                "",
                "- the full runtime session should reread route and recall evidence together",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    route_note_dir = _checkpoint_note_dir(
        workspace_root,
        repo_label="aoa-sdk",
        runtime_session_id=runtime_session_id,
    )
    _write_checkpoint_history_entry(
        note_dir=route_note_dir,
        session_ref="session:test-runtime-fan-in-closeout",
        runtime_session_id=runtime_session_id,
        repo_root=workspace_root / "aoa-sdk",
        repo_label="aoa-sdk",
        candidate_id="candidate:route:aoa-playbooks-playbook-registry-min",
        candidate_kind="route",
        owner_hint="aoa-playbooks",
        display_name="Recurring route candidate",
        source_surface_ref="aoa-playbooks.playbook_registry.min",
        evidence_refs=[
            "aoa-playbooks.playbook_registry.min",
            "aoa-techniques.technique_promotion_readiness.min",
        ],
        progression_axis_signals=[
            {
                "axis": "change_legibility",
                "movement": "hold",
                "why": "route evidence should survive the runtime-session fan-in",
                "evidence_refs": ["aoa-playbooks.playbook_registry.min"],
                "candidate_ids": ["candidate:route:aoa-playbooks-playbook-registry-min"],
            }
        ],
        blocked_by=["owner-ambiguity"],
        promote_if=["repeat the same owner hint across another reviewed checkpoint"],
        defer_reason="owner ambiguity still exceeds checkpoint-note promotion authority",
    )

    recall_note_dir = _checkpoint_note_dir(
        workspace_root,
        repo_label="aoa-memo",
        runtime_session_id=runtime_session_id,
    )
    _write_checkpoint_history_entry(
        note_dir=recall_note_dir,
        session_ref="session:test-aoa-memo-ledger",
        runtime_session_id=runtime_session_id,
        repo_root=workspace_root / "aoa-memo",
        repo_label="aoa-memo",
        candidate_id="candidate:recall:aoa-memo-memory-catalog-min",
        candidate_kind="recall",
        owner_hint="aoa-memo",
        display_name="Memo semantic recall",
        source_surface_ref="aoa-memo.memory_catalog.min",
        evidence_refs=["aoa-memo.memory_catalog.min"],
        progression_axis_signals=[
            {
                "axis": "provenance_hygiene",
                "movement": "hold",
                "why": "recall evidence should survive the runtime-session fan-in",
                "evidence_refs": ["aoa-memo.memory_catalog.min"],
                "candidate_ids": ["candidate:recall:aoa-memo-memory-catalog-min"],
            }
        ],
        blocked_by=["thin-evidence"],
        promote_if=["write back only bounded, provenance-aware memory; memory is not proof"],
        defer_reason="thin evidence should stay local until another checkpoint confirms the same candidate",
    )

    sdk.checkpoints.status(
        repo_root=str(workspace_root / "aoa-sdk"),
        session_file=str(session_file),
    )
    sdk.checkpoints.status(
        repo_root=str(workspace_root / "aoa-memo"),
        session_file=str(session_file),
    )

    context = sdk.checkpoints.build_closeout_context(
        repo_root=str(workspace_root / "aoa-sdk"),
        reviewed_artifact_path=str(reviewed_artifact),
        session_file=str(session_file),
    )

    assert context.session_ref == "session:test-runtime-fan-in-closeout"
    assert context.runtime_session_id == runtime_session_id
    assert context.session_trace_ref == str(rollout_path.resolve())
    assert context.session_trace_thread_id == "thread-closeout"
    assert context.checkpoint_note_ref == str((route_note_dir / "checkpoint-note.json").resolve())
    assert {
        Path(ref).parent.name for ref in context.checkpoint_note_refs
    } == {"aoa-sdk", "aoa-memo"}
    assert set(context.candidate_map.harvest_candidate_ids) == {
        "candidate:route:aoa-playbooks-playbook-registry-min",
        "candidate:recall:aoa-memo-memory-catalog-min",
    }
    assert set(context.candidate_map.progression_candidate_ids) == {
        "candidate:route:aoa-playbooks-playbook-registry-min",
        "candidate:recall:aoa-memo-memory-catalog-min",
    }
    assert set(context.candidate_map.upgrade_candidate_ids) == {
        "candidate:route:aoa-playbooks-playbook-registry-min",
        "candidate:recall:aoa-memo-memory-catalog-min",
    }
    assert {"aoa-sdk", "aoa-memo", "aoa-playbooks"} <= set(context.repo_scope)
    assert {"change_legibility", "provenance_hygiene"} <= {
        signal.axis for signal in context.progression_axis_signals
    }
    assert any("aggregated runtime-session checkpoint notes" in note for note in context.notes)
    assert any("Codex rollout trace" in note for note in context.notes)


def test_build_closeout_context_fails_when_repo_root_checkpoint_session_mismatches_reviewed_artifact(
    workspace_root: Path,
    monkeypatch,
) -> None:
    monkeypatch.delenv("CODEX_THREAD_ID", raising=False)
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    runtime_session_id = "runtime-session-mismatch"
    session_file = _write_runtime_session_file(
        workspace_root / "aoa-sdk" / ".aoa" / "test-runtime-session-mismatch.json",
        session_id=runtime_session_id,
    )
    reviewed_artifact = workspace_root / "aoa-sdk" / ".aoa" / "reviewed-runtime-mismatch.md"
    reviewed_artifact.write_text(
        "\n".join(
            [
                "# Reviewed Session Artifact",
                "",
                "Session ref: `session:test-reviewed-artifact`",
                "",
                "- closeout should fail closed when the repo-root checkpoint note belongs to another session",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    route_note_dir = _checkpoint_note_dir(
        workspace_root,
        repo_label="aoa-sdk",
        runtime_session_id=runtime_session_id,
    )
    _write_checkpoint_history_entry(
        note_dir=route_note_dir,
        session_ref="session:test-other-checkpoint-session",
        runtime_session_id=runtime_session_id,
        repo_root=workspace_root / "aoa-sdk",
        repo_label="aoa-sdk",
        candidate_id="candidate:route:aoa-playbooks-playbook-registry-min",
        candidate_kind="route",
        owner_hint="aoa-playbooks",
        display_name="Recurring route candidate",
        source_surface_ref="aoa-playbooks.playbook_registry.min",
        evidence_refs=["aoa-playbooks.playbook_registry.min"],
        progression_axis_signals=[],
    )
    sdk.checkpoints.status(
        repo_root=str(workspace_root / "aoa-sdk"),
        session_file=str(session_file),
    )

    with pytest.raises(ValueError, match="repo-root checkpoint session_ref"):
        sdk.checkpoints.build_closeout_context(
            repo_root=str(workspace_root / "aoa-sdk"),
            reviewed_artifact_path=str(reviewed_artifact),
            session_file=str(session_file),
        )


def test_execute_closeout_chain_emits_artifacts_and_receipts_even_without_note(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    reviewed_artifact = workspace_root / "aoa-sdk" / ".aoa" / "reviewed-session-no-note.md"
    reviewed_artifact.write_text(
        "\n".join(
            [
                "# Reviewed Session Artifact",
                "",
                "Session ref: `session:test-closeout-without-note`",
                "",
                "- verify green completed",
                "- boundary and provenance review completed",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    report = sdk.checkpoints.execute_closeout_chain(
        repo_root=str(workspace_root / "aoa-sdk"),
        reviewed_artifact_path=str(reviewed_artifact),
    )

    assert report.session_ref == "session:test-closeout-without-note"
    assert report.execution_mode == "mechanical_bridge_artifact_build"
    assert report.mechanical_bridge_only is True
    assert report.agent_skill_application_required is True
    assert report.authority_contract == "reviewed_artifact_primary_checkpoint_hints_provisional"
    assert report.checkpoint_note_ref is None
    assert report.surface_handoff_ref is None
    assert [step.skill_name for step in report.executed_skills] == [
        "aoa-session-donor-harvest",
        "aoa-session-progression-lift",
        "aoa-quest-harvest",
    ]
    assert report.skipped_skills == []
    assert {step.execution_mode for step in report.executed_skills} == {"mechanical_artifact_builder"}
    assert all(step.agent_skill_application_required for step in report.executed_skills)
    assert report.executed_at_local is not None
    assert report.executed_tz
    assert report.produced_artifact_refs
    assert report.produced_receipt_refs
    assert "agent-led skill application" in report.final_stop_reason
    for path in [*report.produced_artifact_refs, *report.produced_receipt_refs]:
        assert Path(path).exists()
    receipt_payloads = {
        Path(path).name: json.loads(Path(path).read_text(encoding="utf-8"))
        for path in report.produced_receipt_refs
    }
    assert receipt_payloads["HARVEST_PACKET_RECEIPT.json"]["actor_ref"] == "aoa-skills:aoa-session-donor-harvest"
    assert (
        receipt_payloads["PROGRESSION_DELTA_RECEIPT.json"]["actor_ref"]
        == "aoa-skills:aoa-session-progression-lift"
    )
    assert receipt_payloads["QUEST_PROMOTION_RECEIPT.json"]["actor_ref"] == "aoa-skills:aoa-quest-harvest"
    assert (
        receipt_payloads["CORE_SKILL_APPLICATION_RECEIPT.harvest.json"]["actor_ref"]
        == "aoa-skills:aoa-session-donor-harvest"
    )
    execution_report_path = (
        _checkpoint_note_dir(
            workspace_root,
            repo_label="aoa-sdk",
            runtime_session_id=report.runtime_session_id,
        )
        / "closeout-execution-report.json"
    )
    assert report.context_ref == str(execution_report_path.with_name("closeout-context.json"))
    assert execution_report_path.exists()


def test_execute_closeout_chain_uses_aggregated_runtime_session_notes(
    workspace_root: Path,
    monkeypatch,
) -> None:
    monkeypatch.delenv("CODEX_THREAD_ID", raising=False)
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    runtime_session_id = "runtime-session-execute-shared"
    session_file = _write_runtime_session_file(
        workspace_root / "aoa-sdk" / ".aoa" / "test-runtime-session-exec.json",
        session_id=runtime_session_id,
    )
    rollout_path = _write_rollout_trace(
        workspace_root / "aoa-sdk" / ".aoa" / "runtime-trace.jsonl",
        assistant_message="reviewed the repeated route, implemented the patch, and verified the test surface",
        tool_output="verified green after patch review",
    )
    reviewed_artifact = workspace_root / "aoa-sdk" / ".aoa" / "reviewed-runtime-fan-in-exec.md"
    reviewed_artifact.write_text(
        "\n".join(
            [
                "# Reviewed Session Artifact",
                "",
                "Session ref: `session:test-runtime-fan-in-execute`",
                "",
                "- route evidence stayed repeated across the session",
                "- recall evidence stayed provenance-aware across the session",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    route_note_dir = _checkpoint_note_dir(
        workspace_root,
        repo_label="aoa-sdk",
        runtime_session_id=runtime_session_id,
    )
    _write_checkpoint_history_entry(
        note_dir=route_note_dir,
        session_ref="session:test-runtime-fan-in-execute",
        runtime_session_id=runtime_session_id,
        repo_root=workspace_root / "aoa-sdk",
        repo_label="aoa-sdk",
        candidate_id="candidate:route:aoa-playbooks-playbook-registry-min",
        candidate_kind="route",
        owner_hint="aoa-playbooks",
        display_name="Recurring route candidate",
        source_surface_ref="aoa-playbooks.playbook_registry.min",
        evidence_refs=[
            "aoa-playbooks.playbook_registry.min",
            "aoa-techniques.technique_promotion_readiness.min",
        ],
        progression_axis_signals=[
            {
                "axis": "change_legibility",
                "movement": "hold",
                "why": "route evidence should stay visible at closeout",
                "evidence_refs": ["aoa-playbooks.playbook_registry.min"],
                "candidate_ids": ["candidate:route:aoa-playbooks-playbook-registry-min"],
            }
        ],
        blocked_by=["owner-ambiguity"],
        promote_if=["repeat the same owner hint across another reviewed checkpoint"],
        defer_reason="owner ambiguity still exceeds checkpoint-note promotion authority",
    )
    recall_note_dir = _checkpoint_note_dir(
        workspace_root,
        repo_label="aoa-memo",
        runtime_session_id=runtime_session_id,
    )
    _write_checkpoint_history_entry(
        note_dir=recall_note_dir,
        session_ref="session:test-aoa-memo-exec-ledger",
        runtime_session_id=runtime_session_id,
        repo_root=workspace_root / "aoa-memo",
        repo_label="aoa-memo",
        candidate_id="candidate:recall:aoa-memo-memory-catalog-min",
        candidate_kind="recall",
        owner_hint="aoa-memo",
        display_name="Memo semantic recall",
        source_surface_ref="aoa-memo.memory_catalog.min",
        evidence_refs=["aoa-memo.memory_catalog.min"],
        progression_axis_signals=[
            {
                "axis": "provenance_hygiene",
                "movement": "hold",
                "why": "recall evidence should stay visible at closeout",
                "evidence_refs": ["aoa-memo.memory_catalog.min"],
                "candidate_ids": ["candidate:recall:aoa-memo-memory-catalog-min"],
            }
        ],
        blocked_by=["thin-evidence"],
        promote_if=["write back only bounded, provenance-aware memory; memory is not proof"],
        defer_reason="thin evidence should stay local until another checkpoint confirms the same candidate",
    )

    sdk.checkpoints.status(
        repo_root=str(workspace_root / "aoa-sdk"),
        session_file=str(session_file),
    )
    sdk.checkpoints.status(
        repo_root=str(workspace_root / "aoa-memo"),
        session_file=str(session_file),
    )

    report = sdk.checkpoints.execute_closeout_chain(
        repo_root=str(workspace_root / "aoa-sdk"),
        reviewed_artifact_path=str(reviewed_artifact),
        session_file=str(session_file),
    )
    scoped_note_dir = _checkpoint_note_dir(
        workspace_root,
        repo_label="aoa-sdk",
        runtime_session_id=runtime_session_id,
    )
    legacy_note_dir = _checkpoint_note_dir(workspace_root, repo_label="aoa-sdk")

    assert report.runtime_session_id == runtime_session_id
    assert report.execution_mode == "mechanical_bridge_artifact_build"
    assert report.agent_skill_application_required is True
    assert report.session_trace_ref == str(rollout_path.resolve())
    assert report.session_trace_thread_id == "thread-closeout"
    assert report.context_ref == str(scoped_note_dir / "closeout-context.json")
    assert (scoped_note_dir / "closeout-context.json").exists()
    assert (scoped_note_dir / "closeout-execution-report.json").exists()
    assert not (legacy_note_dir / "closeout-execution-report.json").exists()
    assert {
        Path(ref).parent.name for ref in report.checkpoint_note_refs
    } == {"aoa-sdk", "aoa-memo"}
    assert all(scoped_note_dir in Path(ref).parents for ref in report.produced_artifact_refs)
    assert all(scoped_note_dir in Path(ref).parents for ref in report.produced_receipt_refs)

    harvest_packet_path = next(
        Path(path) for path in report.produced_artifact_refs if path.endswith("HARVEST_PACKET.json")
    )
    harvest_packet = json.loads(harvest_packet_path.read_text(encoding="utf-8"))
    assert harvest_packet["authority_contract"] == {
        "contract": "reviewed_artifact_primary_checkpoint_hints_provisional",
        "bridge_output": "mechanical_artifact_build",
        "checkpoint_notes": "focus_hints_only_not_final_authority",
        "reviewed_artifact": "primary_closeout_evidence",
        "agent_skill_application": "required_for_final_session_analysis",
    }
    assert {item["owner_repo_recommendation"] for item in harvest_packet["accepted_candidates"]} == {
        "aoa-playbooks",
        "aoa-memo",
    }

    progression_packet_path = next(
        Path(path) for path in report.produced_artifact_refs if path.endswith("PROGRESSION_DELTA.json")
    )
    progression_packet = json.loads(progression_packet_path.read_text(encoding="utf-8"))
    assert progression_packet["authority_contract"]["checkpoint_notes"] == "focus_hints_only_not_final_authority"
    assert set(progression_packet["candidate_ids"]) == {
        "candidate:route:aoa-playbooks-playbook-registry-min",
        "candidate:recall:aoa-memo-memory-catalog-min",
    }
    assert progression_packet["session_trace_ref"] == str(rollout_path.resolve())

    quest_promotion_path = next(
        Path(path) for path in report.produced_artifact_refs if path.endswith("QUEST_PROMOTION.json")
    )
    quest_promotion = json.loads(quest_promotion_path.read_text(encoding="utf-8"))
    quest_promotions_path = next(
        Path(path) for path in report.produced_artifact_refs if path.endswith("QUEST_PROMOTIONS.json")
    )
    quest_promotions = json.loads(quest_promotions_path.read_text(encoding="utf-8"))
    assert quest_promotion["authority_contract"]["agent_skill_application"] == "required_for_final_session_analysis"
    assert quest_promotions["authority_contract"]["bridge_output"] == "mechanical_artifact_build"
    expected_candidate_refs = {
        "candidate:route:aoa-playbooks-playbook-registry-min",
        "candidate:recall:aoa-memo-memory-catalog-min",
    }
    assert quest_promotion["multi_candidate_followup_required"] is True
    assert set(quest_promotion["candidate_refs"]) == expected_candidate_refs
    assert len(quest_promotion["additional_candidate_refs"]) == 1
    assert quest_promotions["accepted_candidate_count"] == 2
    assert {
        entry["bounded_unit_ref"] for entry in quest_promotions["promotions"]
    } == expected_candidate_refs
    assert {entry["owner_repo"] for entry in quest_promotions["promotions"]} == {
        "aoa-playbooks",
        "aoa-memo",
    }


def test_execute_closeout_chain_uses_codex_session_trace_as_closeout_evidence(
    workspace_root: Path,
    monkeypatch,
) -> None:
    monkeypatch.delenv("CODEX_THREAD_ID", raising=False)
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    session_file = _write_runtime_session_file(
        workspace_root / "aoa-sdk" / ".aoa" / "test-runtime-session-trace.json",
        session_id="runtime-session-trace",
    )
    rollout_path = _write_rollout_trace(
        workspace_root / "aoa-sdk" / ".aoa" / "runtime-trace.jsonl",
        user_message="fix the boundary and provenance issues before closeout",
        assistant_message="implemented the patch change, verified the tests, and completed the review with clear boundary notes",
        tool_call_arguments="{\"cmd\":\"python -m pytest -q tests/test_checkpoints.py\"}",
        tool_output="24 passed; verification complete",
    )
    reviewed_artifact = workspace_root / "aoa-sdk" / ".aoa" / "reviewed-runtime-trace.md"
    reviewed_artifact.write_text(
        "\n".join(
            [
                "# Reviewed Session Artifact",
                "",
                "Session ref: `session:test-runtime-trace-closeout`",
                "",
                "- one bounded candidate survived",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    _write_checkpoint_history_entry(
        note_dir=_checkpoint_note_dir(
            workspace_root,
            repo_label="aoa-sdk",
            runtime_session_id="runtime-session-trace",
        ),
        session_ref="session:test-runtime-trace-closeout",
        runtime_session_id="runtime-session-trace",
        repo_root=workspace_root / "aoa-sdk",
        repo_label="aoa-sdk",
        candidate_id="candidate:route:aoa-playbooks-playbook-registry-min",
        candidate_kind="route",
        owner_hint="aoa-playbooks",
        display_name="Recurring route candidate",
        source_surface_ref="aoa-playbooks.playbook_registry.min",
        evidence_refs=["aoa-playbooks.playbook_registry.min"],
        progression_axis_signals=[],
        blocked_by=["owner-ambiguity"],
        defer_reason="owner ambiguity still exceeds checkpoint-note promotion authority",
    )

    sdk.checkpoints.status(
        repo_root=str(workspace_root / "aoa-sdk"),
        session_file=str(session_file),
    )

    report = sdk.checkpoints.execute_closeout_chain(
        repo_root=str(workspace_root / "aoa-sdk"),
        reviewed_artifact_path=str(reviewed_artifact),
        session_file=str(session_file),
    )

    progression_packet_path = next(
        Path(path) for path in report.produced_artifact_refs if path.endswith("PROGRESSION_DELTA.json")
    )
    progression_packet = json.loads(progression_packet_path.read_text(encoding="utf-8"))

    assert report.session_trace_ref == str(rollout_path.resolve())
    assert progression_packet["session_trace_ref"] == str(rollout_path.resolve())
    assert progression_packet["verdict"] == "advance"
    assert progression_packet["axis_deltas"]["boundary_integrity"] == 1
    assert progression_packet["axis_deltas"]["execution_reliability"] == 1
    assert progression_packet["axis_deltas"]["review_sharpness"] == 1
    assert progression_packet["axis_deltas"]["proof_discipline"] == 1
    assert progression_packet["axis_deltas"]["provenance_hygiene"] == 1


def test_execute_closeout_chain_routes_pattern_candidates_to_techniques(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    reviewed_artifact = workspace_root / "aoa-sdk" / ".aoa" / "reviewed-session-pattern.md"
    reviewed_artifact.write_text(
        "\n".join(
            [
                "# Reviewed Session Artifact",
                "",
                "Session ref: `session:test-closeout-pattern-technique`",
                "",
                "- repeated bounded discipline showed up across the session",
                "- technique extraction now looks more honest than direct skill packaging",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    note_dir = workspace_root / "aoa-sdk" / ".aoa" / "session-growth" / "current" / "aoa-sdk"
    note_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_payload = {
        "session_ref": "session:test-closeout-pattern-technique",
        "repo_root": str((workspace_root / "aoa-sdk").resolve()),
        "repo_label": "aoa-sdk",
        "history_entry": {
            "checkpoint_kind": "verify_green",
            "observed_at": "2026-04-09T12:00:00Z",
            "report_ref": str(note_dir / "pattern-report.json"),
            "intent_text": "lift repeated bounded discipline into a reviewed closeout candidate",
            "checkpoint_should_capture": True,
            "blocked_by": [],
            "candidate_clusters": [
                {
                    "candidate_id": "candidate:pattern:aoa-techniques-technique-promotion-readiness-min",
                    "candidate_kind": "pattern",
                    "owner_hint": "aoa-sdk",
                    "display_name": "Reusable practice candidate",
                    "source_surface_ref": "aoa-techniques.technique_promotion_readiness.min",
                    "evidence_refs": [
                        "aoa-techniques.technique_promotion_readiness.min",
                    ],
                    "confidence": "medium",
                    "session_end_targets": ["harvest", "progression", "upgrade"],
                    "progression_axis_signals": [],
                    "promote_if": ["repeat the same owner hint across another reviewed checkpoint"],
                    "defer_reason": None,
                    "blocked_by": [],
                    "next_owner_moves": [
                        "carry the candidate through reviewed session closeout before moving candidates or stats"
                    ],
                }
            ],
            "manual_review_requested": False,
        },
    }
    (note_dir / "checkpoint-note.jsonl").write_text(
        json.dumps(checkpoint_payload) + "\n",
        encoding="utf-8",
    )
    sdk.checkpoints.status(repo_root=str(workspace_root / "aoa-sdk"))

    report = sdk.checkpoints.execute_closeout_chain(
        repo_root=str(workspace_root / "aoa-sdk"),
        reviewed_artifact_path=str(reviewed_artifact),
    )

    harvest_packet = json.loads(Path(report.produced_artifact_refs[0]).read_text(encoding="utf-8"))
    accepted_candidate = harvest_packet["accepted_candidates"][0]
    assert accepted_candidate["owner_repo_recommendation"] == "aoa-techniques"
    assert accepted_candidate["abstraction_shape"] == "technique"
    assert accepted_candidate["chosen_next_artifact"].startswith("techniques/")
