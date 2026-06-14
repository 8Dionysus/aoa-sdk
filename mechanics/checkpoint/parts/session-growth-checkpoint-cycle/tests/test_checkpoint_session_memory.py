from __future__ import annotations

import json
from pathlib import Path

import pytest

from aoa_sdk import AoASDK
from aoa_sdk.checkpoints.session_memory import resolve_checkpoint_session_memory
from aoa_sdk.workspace.discovery import Workspace


THREAD_ID = "019f0000-0000-7000-8000-sessionmemory"
SESSION_LABEL = "2026-06-03__001__checkpoint-session-memory"


def test_checkpoint_session_memory_resolves_existing_archive(workspace_root: Path) -> None:
    _write_session_memory_fixture(workspace_root)

    ref, freshness = resolve_checkpoint_session_memory(
        workspace=Workspace.discover(workspace_root),
        session_trace_thread_id=THREAD_ID,
        session_trace_ref=f"/tmp/rollout-{THREAD_ID}.jsonl",
    )

    assert ref is not None
    assert freshness.status == "current"
    assert ref.session_id == THREAD_ID
    assert ref.session_label == SESSION_LABEL
    assert ref.authority_contract == "archive_indexes_are_route_evidence_not_reviewed_truth"
    assert ref.route_signal_layers == ["authority_surface", "verification_state"]
    assert ref.route_signal_summary[0].top_keys == {"source": 3, "runtime": 1}


def test_build_closeout_context_attaches_session_memory_ref(
    workspace_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CODEX_THREAD_ID", THREAD_ID)
    _write_session_memory_fixture(workspace_root)
    session_file = workspace_root / "runtime-session.json"
    session_file.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "profile": "aoa-sdk",
                "session_id": "runtime-session-1",
                "created_at": "2026-06-03T00:00:00Z",
                "updated_at": "2026-06-03T00:00:00Z",
                "codex_thread_id": THREAD_ID,
                "codex_rollout_path": f"/tmp/rollout-{THREAD_ID}.jsonl",
                "active_skills": [],
                "activation_log": [],
            }
        ),
        encoding="utf-8",
    )
    reviewed_artifact = workspace_root / "reviewed-artifact.json"
    reviewed_artifact.write_text(
        json.dumps({"session_ref": "session:checkpoint-session-memory"}),
        encoding="utf-8",
    )

    context = AoASDK.from_workspace(workspace_root).checkpoints.build_closeout_context(
        repo_root=str(workspace_root / "aoa-sdk"),
        reviewed_artifact_path=str(reviewed_artifact),
        session_ref="session:checkpoint-session-memory",
        session_file=str(session_file),
    )

    assert context.session_memory_ref is not None
    assert context.session_memory_ref.session_id == THREAD_ID
    assert context.session_memory_freshness.status == "current"
    assert any("aoa-session-memory archive" in note for note in context.notes)
    assert any("freshness caution" in note for note in context.notes)


def test_session_memory_route_evidence_does_not_advance_progression_verdict(
    workspace_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CODEX_THREAD_ID", raising=False)
    _write_session_memory_fixture(workspace_root)
    repo_root = workspace_root / "aoa-sdk"
    sdk = AoASDK.from_workspace(repo_root)
    runtime_session_id = "runtime-session-memory-route"
    session_ref = "session:checkpoint-session-memory-route"
    trace_path = repo_root / ".aoa" / "runtime-trace.jsonl"
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    trace_path.write_text(
        json.dumps(
            {
                "type": "event_msg",
                "payload": {
                    "type": "user_message",
                    "message": "one candidate survived",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    session_file = _write_runtime_session_file(
        repo_root / ".aoa" / "runtime-session.json",
        session_id=runtime_session_id,
        codex_thread_id=THREAD_ID,
        codex_rollout_path=str(trace_path),
    )
    note_dir = (
        repo_root
        / ".aoa"
        / "session-growth"
        / "current"
        / runtime_session_id
        / "aoa-sdk"
    )
    _write_checkpoint_candidate_note(
        note_dir=note_dir,
        session_ref=session_ref,
        runtime_session_id=runtime_session_id,
        repo_root=repo_root,
    )
    sdk.checkpoints.status(repo_root=str(repo_root), session_file=str(session_file))
    reviewed_artifact = repo_root / ".aoa" / "reviewed-session-memory-route.json"
    reviewed_artifact.write_text(
        json.dumps(
            {
                "session_ref": session_ref,
                "summary": "one candidate survived",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = sdk.checkpoints.execute_closeout_chain(
        repo_root=str(repo_root),
        reviewed_artifact_path=str(reviewed_artifact),
        session_file=str(session_file),
    )

    progression_packet_path = next(
        Path(path) for path in report.produced_artifact_refs if path.endswith("PROGRESSION_DELTA.json")
    )
    progression_packet = json.loads(progression_packet_path.read_text(encoding="utf-8"))

    assert report.session_memory_ref is not None
    assert report.session_memory_ref.session_id == THREAD_ID
    assert progression_packet["session_memory_ref"]["session_id"] == THREAD_ID
    assert progression_packet["candidate_ids"] == ["candidate:route:session-memory-route"]
    assert progression_packet["verdict"] == "hold"
    assert progression_packet["axis_deltas"] == {"change_legibility": 0}


def _write_session_memory_fixture(workspace_root: Path) -> None:
    aoa_root = workspace_root / ".aoa"
    session_dir = aoa_root / "sessions" / SESSION_LABEL
    raw_dir = session_dir / "raw"
    raw_dir.mkdir(parents=True)
    raw_path = raw_dir / "session.raw.jsonl"
    raw_path.write_text('{"type":"session_meta"}\n', encoding="utf-8")
    blocks_index = raw_dir / "blocks.index.json"
    blocks_index.write_text("[]\n", encoding="utf-8")
    manifest = {
        "session_id": THREAD_ID,
        "session_label": SESSION_LABEL,
        "session_title": "Checkpoint session-memory",
        "updated_at": "2026-06-03T00:00:00Z",
        "archive_status": "indexed",
        "distillation_status": "raw_archived",
        "review_status": "provisional",
        "source": {"transcript_path": f"/tmp/rollout-{THREAD_ID}.jsonl"},
        "raw": {
            "path": str(raw_path),
            "line_count": 1,
            "indexing_status": "indexed",
            "blocks_index": str(blocks_index),
        },
        "raw_blocks": {"index": str(blocks_index), "blocks": []},
        "segments": [],
    }
    (session_dir / "session.manifest.json").write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )
    session_index = {
        "session_id": THREAD_ID,
        "updated_at": "2026-06-03T00:00:00Z",
        "event_count": 1,
        "work_context": {
            "status": "resolved",
            "work_name": "aoa-sdk",
            "work_family": "aoa",
            "confidence": "high",
        },
        "conversation_act_counts": {"operator_question": 1},
        "session_act_counts": {"operator_prompt": 1},
        "route_signal_counts": {
            "authority_surface": {"source": 3, "runtime": 1},
            "verification_state": {"success_observed": 2},
        },
    }
    (session_dir / "session.index.json").write_text(
        json.dumps(session_index),
        encoding="utf-8",
    )
    registry = [
        {
            "session_id": THREAD_ID,
            "session_label": SESSION_LABEL,
            "session_title": "Checkpoint session-memory",
            "path": str(session_dir),
            "transcript_path": f"/tmp/rollout-{THREAD_ID}.jsonl",
            "archive_status": "indexed",
            "distillation_status": "raw_archived",
            "event_count": 1,
            "segment_count": 0,
            "updated_at": "2026-06-03T00:00:00Z",
        }
    ]
    (aoa_root / "session-registry.json").write_text(
        json.dumps(registry),
        encoding="utf-8",
    )


def _write_runtime_session_file(
    path: Path,
    *,
    session_id: str,
    codex_thread_id: str,
    codex_rollout_path: str,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "profile": "aoa-sdk",
                "session_id": session_id,
                "created_at": "2026-06-03T00:00:00Z",
                "updated_at": "2026-06-03T00:00:00Z",
                "codex_thread_id": codex_thread_id,
                "codex_rollout_path": codex_rollout_path,
                "active_skills": [],
                "activation_log": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def _write_checkpoint_candidate_note(
    *,
    note_dir: Path,
    session_ref: str,
    runtime_session_id: str,
    repo_root: Path,
) -> None:
    note_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "session_ref": session_ref,
        "runtime_session_id": runtime_session_id,
        "runtime_session_created_at": "2026-06-03T00:00:00Z",
        "repo_root": str(repo_root.resolve()),
        "repo_label": "aoa-sdk",
        "history_entry": {
            "checkpoint_kind": "verify_green",
            "observed_at": "2026-06-03T00:00:00Z",
            "report_ref": str(note_dir / "aoa-sdk-report.json"),
            "intent_text": "one candidate survived",
            "checkpoint_should_capture": True,
            "blocked_by": [],
            "agent_review_status": "not_required",
            "candidate_clusters": [
                {
                    "candidate_id": "candidate:route:session-memory-route",
                    "candidate_kind": "route",
                    "owner_hint": "aoa-playbooks",
                    "display_name": "Session memory route unit",
                    "source_surface_ref": "aoa-sdk:checkpoint",
                    "evidence_refs": ["path:reviewed-session-memory-route.json"],
                    "confidence": "medium",
                    "session_end_targets": ["harvest", "progression"],
                    "progression_axis_signals": [
                        {
                            "axis": "change_legibility",
                            "movement": "hold",
                            "why": "candidate exists for closeout routing, but does not itself advance progression",
                            "evidence_refs": ["path:reviewed-session-memory-route.json"],
                            "candidate_ids": ["candidate:route:session-memory-route"],
                        }
                    ],
                    "promote_if": [],
                    "defer_reason": None,
                    "blocked_by": [],
                    "next_owner_moves": [
                        "keep route evidence attached without changing progression scoring"
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
