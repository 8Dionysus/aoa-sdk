"""Generated checkpoint backlog navigation indexes."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from ..models import CheckpointBacklogAuditReport, CheckpointBacklogEntry
from ..workspace.discovery import Workspace
from .naming import safe_checkpoint_name


def checkpoint_backlog_index_path(workspace: Workspace) -> Path:
    return (
        workspace.repo_path("aoa-sdk")
        / ".aoa"
        / "session-growth"
        / "indexes"
        / "checkpoint-backlog-navigation.min.json"
    )


def build_checkpoint_backlog_index(report: CheckpointBacklogAuditReport) -> dict[str, Any]:
    entries = sorted(
        report.entries,
        key=lambda entry: (
            entry.repo_label,
            entry.next_route,
            entry.runtime_session_id or "",
            entry.current_dir,
        ),
    )
    anchors, edges = _graph_ready(entries)
    return {
        "schema_version": 1,
        "artifact_type": "checkpoint_backlog_navigation_index_v1",
        "boundary_note": (
            "Generated navigation only; checkpoint notes, runtime trace files, "
            "raw transcripts, and aoa-session-memory archives remain stronger evidence."
        ),
        "repo_label": report.repo_label,
        "active_runtime_session_id": report.active_runtime_session_id,
        "counts": {
            **dict(sorted(report.counts.items())),
            "graph_anchors": len(anchors),
            "graph_edges": len(edges),
        },
        "entries": [_entry_summary(entry) for entry in entries],
        "by_repo": _group(entries, "repo_label"),
        "by_lifecycle_state": _group(entries, "lifecycle_state"),
        "by_next_route": _group(entries, "next_route"),
        "by_runtime_trace_status": _group(entries, "runtime_trace_status"),
        "by_session_memory_status": _group(entries, "session_memory_status"),
        "runtime_trace_gaps": [
            _entry_summary(entry)
            for entry in entries
            if _is_runtime_trace_gap(entry)
        ],
        "reconcile_ready": [
            _entry_summary(entry)
            for entry in entries
            if entry.next_route == "reconcile_without_closeout"
        ],
        "stop_lines": list(report.stop_lines),
        "graph_ready": {
            "anchors": anchors,
            "edges": edges,
        },
    }


def write_checkpoint_backlog_index(
    *,
    workspace: Workspace,
    report: CheckpointBacklogAuditReport,
) -> Path:
    path = checkpoint_backlog_index_path(workspace)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            build_checkpoint_backlog_index(report),
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def _entry_summary(entry: CheckpointBacklogEntry) -> dict[str, Any]:
    return {
        "repo_label": entry.repo_label,
        "runtime_session_id": entry.runtime_session_id,
        "lifecycle_state": entry.lifecycle_state,
        "review_status": entry.review_status,
        "agent_review_status": entry.agent_review_status,
        "age_days": entry.age_days,
        "note_ref": entry.note_ref,
        "runtime_trace_status": entry.runtime_trace_status,
        "runtime_trace_thread_id": entry.runtime_trace_thread_id,
        "runtime_trace_ref": entry.runtime_trace_ref,
        "source_trace_ref": entry.source_trace_ref,
        "session_memory_status": entry.session_memory_status,
        "session_memory_archive_ref": entry.session_memory_archive_ref,
        "raw_refs": entry.raw_refs,
        "why_open": entry.why_open,
        "next_route": entry.next_route,
        "required_action": entry.required_action,
    }


def _is_runtime_trace_gap(entry: CheckpointBacklogEntry) -> bool:
    return (
        not entry.active_runtime_scope
        and entry.runtime_trace_status in {"resolved", "recoverable"}
        and not entry.session_memory_archive_ref
    )


def _group(entries: list[CheckpointBacklogEntry], attr: str) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for entry in entries:
        value = getattr(entry, attr)
        if not isinstance(value, str) or not value:
            continue
        grouped[value].append(entry.runtime_session_id or entry.current_dir)
    return {key: sorted(values) for key, values in sorted(grouped.items())}


def _graph_ready(
    entries: list[CheckpointBacklogEntry],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    anchors_by_id: dict[str, dict[str, str]] = {}
    edges: list[dict[str, str]] = []
    for entry in entries:
        checkpoint_anchor = _anchor_id(
            "checkpoint",
            entry.runtime_session_id or entry.note_ref or entry.current_dir,
        )
        anchors_by_id[checkpoint_anchor] = {
            "id": checkpoint_anchor,
            "kind": "checkpoint",
            "ref": entry.note_ref or entry.current_dir,
        }
        for kind, value, relation in (
            ("repo", entry.repo_label, "has_repo"),
            ("lifecycle_state", entry.lifecycle_state, "has_lifecycle_state"),
            ("next_route", entry.next_route, "has_next_route"),
            ("runtime_trace", entry.runtime_trace_ref, "has_runtime_trace"),
            ("codex_thread", entry.runtime_trace_thread_id, "has_codex_thread"),
            ("source_trace", entry.source_trace_ref, "has_source_trace"),
            ("session_memory_archive", entry.session_memory_archive_ref, "has_session_memory_archive"),
        ):
            if not value:
                continue
            target = _anchor_id(kind, value)
            anchors_by_id[target] = {"id": target, "kind": kind, "ref": value}
            edges.append({"source": checkpoint_anchor, "target": target, "relation": relation})
        for raw_ref in entry.raw_refs:
            target = _anchor_id("raw_ref", raw_ref)
            anchors_by_id[target] = {"id": target, "kind": "raw_ref", "ref": raw_ref}
            edges.append({"source": checkpoint_anchor, "target": target, "relation": "has_raw_ref"})
    anchors = sorted(anchors_by_id.values(), key=lambda item: (item["kind"], item["id"]))
    return anchors, sorted(edges, key=lambda item: (item["source"], item["relation"], item["target"]))


def _anchor_id(kind: str, value: str) -> str:
    return f"{kind}:{safe_checkpoint_name(value).lower()[:96] or 'unknown'}"
