"""Generated checkpoint lifecycle navigation indexes."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from ..models import CheckpointLifecycleAuditReport, CheckpointLifecycleEntry
from ..workspace.discovery import Workspace


def checkpoint_lifecycle_index_path(workspace: Workspace) -> Path:
    return (
        workspace.repo_path("aoa-sdk")
        / ".aoa"
        / "session-growth"
        / "indexes"
        / "checkpoint-lifecycle-navigation.min.json"
    )


def build_checkpoint_lifecycle_index(
    report: CheckpointLifecycleAuditReport,
) -> dict[str, Any]:
    entries = sorted(
        report.entries,
        key=lambda entry: (
            entry.repo_label,
            entry.runtime_session_id or "",
            entry.session_ref or "",
            entry.current_dir,
        ),
    )
    lifecycle = [_entry_summary(entry) for entry in entries]
    unresolved_review = [
        _entry_summary(entry)
        for entry in entries
        if entry.lifecycle_state in {"pending_review", "session_closed_pending_review"}
    ]
    session_memory_refs = [
        {
            "runtime_session_id": entry.runtime_session_id,
            "repo_label": entry.repo_label,
            "session_memory_session_id": entry.session_memory_session_id,
            "session_memory_archive_ref": entry.session_memory_archive_ref,
            "session_memory_status": entry.session_memory_status,
            "checkpoint_note_ref": entry.note_ref,
        }
        for entry in entries
        if entry.session_memory_archive_ref
    ]
    anchors, edges = _graph_ready(entries)
    return {
        "schema_version": 1,
        "artifact_type": "checkpoint_lifecycle_navigation_index_v1",
        "boundary_note": (
            "Generated navigation only; checkpoint notes, lifecycle JSONL, "
            "closeout artifacts, and aoa-session-memory archives remain stronger evidence."
        ),
        "repo_label": report.repo_label,
        "active_runtime_session_id": report.active_runtime_session_id,
        "counts": {
            "entries": len(entries),
            "lifecycle": dict(sorted(Counter(entry.lifecycle_state for entry in entries).items())),
            "unresolved_review": len(unresolved_review),
            "session_memory_refs": len(session_memory_refs),
            "graph_anchors": len(anchors),
            "graph_edges": len(edges),
        },
        "lifecycle": lifecycle,
        "unresolved_review": unresolved_review,
        "session_memory_refs": sorted(
            session_memory_refs,
            key=lambda item: (
                str(item["repo_label"]),
                str(item["runtime_session_id"]),
                str(item["session_memory_archive_ref"]),
            ),
        ),
        "by_repo": _group_entries(entries, "repo_label"),
        "by_owner_hint": _owner_hint_index(entries),
        "by_candidate": _candidate_index(entries),
        "by_commit": _commit_index(entries),
        "graph_ready": {
            "anchors": anchors,
            "edges": edges,
        },
    }


def write_checkpoint_lifecycle_index(
    *,
    workspace: Workspace,
    report: CheckpointLifecycleAuditReport,
) -> Path:
    path = checkpoint_lifecycle_index_path(workspace)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = build_checkpoint_lifecycle_index(report)
    path.write_text(
        json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _entry_summary(entry: CheckpointLifecycleEntry) -> dict[str, Any]:
    return {
        "repo_label": entry.repo_label,
        "runtime_session_id": entry.runtime_session_id,
        "session_ref": entry.session_ref,
        "lifecycle_state": entry.lifecycle_state,
        "state": entry.state,
        "review_status": entry.review_status,
        "agent_review_status": entry.agent_review_status,
        "active_runtime_scope": entry.active_runtime_scope,
        "closable": entry.closable,
        "archiveable": entry.archiveable,
        "required_action": entry.required_action,
        "note_ref": entry.note_ref,
        "session_memory_archive_ref": entry.session_memory_archive_ref,
        "session_memory_session_id": entry.session_memory_session_id,
        "session_memory_status": entry.session_memory_status,
        "current_dir": entry.current_dir,
        "reason": entry.reason,
    }


def _group_entries(entries: list[CheckpointLifecycleEntry], key: str) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for entry in entries:
        value = getattr(entry, key)
        if isinstance(value, str) and value:
            grouped[value].append(entry.runtime_session_id or entry.session_ref or entry.current_dir)
    return {name: sorted(values) for name, values in sorted(grouped.items())}


def _owner_hint_index(entries: list[CheckpointLifecycleEntry]) -> dict[str, list[str]]:
    grouped: dict[str, set[str]] = defaultdict(set)
    for entry in entries:
        for ref in entry.evidence_refs:
            if ref.startswith("context:"):
                grouped[ref.removeprefix("context:")].add(entry.runtime_session_id or entry.current_dir)
            if ref.startswith("aoa-") and ":" in ref:
                grouped[ref.split(":", 1)[0]].add(entry.runtime_session_id or entry.current_dir)
    return {key: sorted(values) for key, values in sorted(grouped.items())}


def _candidate_index(entries: list[CheckpointLifecycleEntry]) -> dict[str, list[str]]:
    grouped: dict[str, set[str]] = defaultdict(set)
    for entry in entries:
        for ref in entry.evidence_refs:
            if ref.startswith(("candidate:", "aoa-", "context:")):
                grouped[ref].add(entry.runtime_session_id or entry.current_dir)
    return {key: sorted(values) for key, values in sorted(grouped.items())}


def _commit_index(entries: list[CheckpointLifecycleEntry]) -> dict[str, list[str]]:
    grouped: dict[str, set[str]] = defaultdict(set)
    for entry in entries:
        for pending_ref in entry.pending_refs:
            if pending_ref:
                grouped[pending_ref].add(entry.runtime_session_id or entry.current_dir)
        for ref in entry.evidence_refs:
            if ref.startswith("commit:"):
                grouped[ref].add(entry.runtime_session_id or entry.current_dir)
    return {key: sorted(values) for key, values in sorted(grouped.items())}


def _graph_ready(
    entries: list[CheckpointLifecycleEntry],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    anchors_by_id: dict[str, dict[str, str]] = {}
    edges: list[dict[str, str]] = []
    for entry in entries:
        checkpoint_anchor = _anchor_id("checkpoint", entry.runtime_session_id or entry.session_ref or entry.current_dir)
        anchors_by_id[checkpoint_anchor] = {
            "id": checkpoint_anchor,
            "kind": "checkpoint",
            "ref": entry.note_ref or entry.current_dir,
        }
        for kind, value in (
            ("repo", entry.repo_label),
            ("runtime_session", entry.runtime_session_id),
            ("session_ref", entry.session_ref),
            ("session_memory_archive", entry.session_memory_archive_ref),
            ("lifecycle_event", entry.lifecycle_state),
            ("closeout_artifact", entry.closeout_context_ref),
            ("closeout_artifact", entry.closeout_execution_report_ref),
        ):
            if not value:
                continue
            target = _anchor_id(kind, value)
            anchors_by_id[target] = {"id": target, "kind": kind, "ref": value}
            edges.append({"source": checkpoint_anchor, "target": target, "relation": f"has_{kind}"})
        for ref in entry.evidence_refs:
            evidence_kind = (
                "commit"
                if ref.startswith("commit:")
                else "candidate"
                if ref.startswith("candidate:")
                else None
            )
            if evidence_kind is None:
                continue
            target = _anchor_id(evidence_kind, ref)
            anchors_by_id[target] = {"id": target, "kind": evidence_kind, "ref": ref}
            edges.append(
                {"source": checkpoint_anchor, "target": target, "relation": f"has_{evidence_kind}"}
            )
    anchors = sorted(anchors_by_id.values(), key=lambda item: (item["kind"], item["id"]))
    return anchors, sorted(edges, key=lambda item: (item["source"], item["relation"], item["target"]))


def _anchor_id(kind: str, value: str) -> str:
    safe = "".join(ch.lower() if ch.isalnum() else "-" for ch in value).strip("-")
    while "--" in safe:
        safe = safe.replace("--", "-")
    return f"{kind}:{safe[:96] or 'unknown'}"
