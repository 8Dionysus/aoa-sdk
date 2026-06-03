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
