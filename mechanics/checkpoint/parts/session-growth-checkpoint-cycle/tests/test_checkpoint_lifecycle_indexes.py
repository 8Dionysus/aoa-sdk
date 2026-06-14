from __future__ import annotations

from datetime import datetime, timezone

from aoa_sdk.checkpoints.indexes import build_checkpoint_lifecycle_index
from aoa_sdk.models import CheckpointLifecycleAuditReport, CheckpointLifecycleEntry


def test_lifecycle_index_includes_recoverable_runtime_trace_gaps() -> None:
    entry = CheckpointLifecycleEntry(
        repo_label="aoa-sdk",
        runtime_session_id="runtime-recoverable-trace",
        current_dir="/srv/AbyssOS/aoa-sdk",
        lifecycle_state="session_closed_reviewed_no_closeout",
        runtime_trace_status="recoverable",
        runtime_trace_thread_id="thread-recoverable",
        source_trace_ref="/srv/AbyssOS/.aoa/raw/thread-recoverable.jsonl",
        session_memory_status="missing",
        active_runtime_scope=False,
        required_action="recover_session_memory_archive: /srv/AbyssOS/.aoa/raw/thread-recoverable.jsonl",
        next_route="recover_session_memory_archive",
        reason="closed checkpoint has only recoverable raw trace evidence",
    )
    report = CheckpointLifecycleAuditReport(
        checked_at=datetime.now(timezone.utc),
        repo_label="aoa-sdk",
        entries=[entry],
    )

    payload = build_checkpoint_lifecycle_index(report)

    assert payload["counts"]["runtime_trace_gaps"] == 1
    assert payload["runtime_trace_gaps"] == [
        {
            "repo_label": "aoa-sdk",
            "runtime_session_id": "runtime-recoverable-trace",
            "session_ref": None,
            "lifecycle_state": "session_closed_reviewed_no_closeout",
            "state": None,
            "review_status": None,
            "agent_review_status": None,
            "active_runtime_scope": False,
            "closable": False,
            "archiveable": False,
            "required_action": "recover_session_memory_archive: /srv/AbyssOS/.aoa/raw/thread-recoverable.jsonl",
            "next_route": "recover_session_memory_archive",
            "note_ref": None,
            "runtime_trace_status": "recoverable",
            "runtime_trace_thread_id": "thread-recoverable",
            "runtime_trace_ref": None,
            "source_trace_ref": "/srv/AbyssOS/.aoa/raw/thread-recoverable.jsonl",
            "session_memory_archive_ref": None,
            "session_memory_session_id": None,
            "session_memory_status": "missing",
            "raw_refs": [],
            "current_dir": "/srv/AbyssOS/aoa-sdk",
            "reason": "closed checkpoint has only recoverable raw trace evidence",
        }
    ]
