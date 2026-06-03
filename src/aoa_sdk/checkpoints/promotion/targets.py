"""Promotion target writers for reviewed checkpoint notes."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from typing import cast

from ...errors import RepoNotFound, SurfaceNotFound
from ...models import SessionCheckpointNote
from ...workspace.discovery import Workspace
from ..hooks.git_boundary import ensure_repo_not_dirty
from ..naming import safe_checkpoint_name
from ..topology.paths import CheckpointPaths


DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")


def promote_to_dionysus(workspace: Workspace, *, paths: CheckpointPaths, note: SessionCheckpointNote) -> list[str]:
    try:
        dionysus_root = workspace.repo_path("Dionysus")
    except RepoNotFound as exc:
        raise SurfaceNotFound("Dionysus workspace is not available for checkpoint-note promotion") from exc
    ensure_repo_not_dirty(dionysus_root, repo_name="Dionysus")

    audits_dir = dionysus_root / "reports" / "ecosystem-audits"
    audits_dir.mkdir(parents=True, exist_ok=True)
    date_str = _date_from_session_ref(note.session_ref) or datetime.now(UTC).date().isoformat()
    session_slug = safe_checkpoint_name(note.session_ref)
    stem = f"{date_str}.{session_slug}.{paths.repo_label}.checkpoint-note"
    json_path = audits_dir / f"{stem}.json"
    md_path = audits_dir / f"{stem}.md"
    source_note_ref = f"repo:aoa-sdk/{paths.note_json.relative_to(paths.root).as_posix()}"
    payload = {
        "schema_version": 1,
        "note_type": "checkpoint_note",
        "session_ref": note.session_ref,
        "promotion_reason": "reviewed checkpoint note promoted from aoa-sdk local session-growth storage",
        "promotion_target": "dionysus_note",
        "source_note_ref": source_note_ref,
        "candidate_clusters": [cluster.model_dump(mode="json") for cluster in note.candidate_clusters],
        "evidence_refs": note.evidence_refs,
        "owner_hints": sorted({cluster.owner_hint for cluster in note.candidate_clusters}),
        "next_owner_moves": note.next_owner_moves,
        "review_status": "reviewed",
    }
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    md_path.write_text(_render_dionysus_checkpoint_markdown(payload), encoding="utf-8")
    return [f"repo:Dionysus/reports/ecosystem-audits/{json_path.name}", f"repo:Dionysus/reports/ecosystem-audits/{md_path.name}"]


def write_harvest_handoff(*, paths: CheckpointPaths, note: SessionCheckpointNote) -> list[str]:
    payload = {
        "schema_version": 1,
        "handoff_type": "checkpoint_harvest_handoff",
        "session_ref": note.session_ref,
        "source_note_ref": str(paths.note_json),
        "candidate_clusters": [cluster.model_dump(mode="json") for cluster in note.candidate_clusters],
        "harvest_candidate_ids": note.harvest_candidate_ids,
        "progression_candidate_ids": note.progression_candidate_ids,
        "upgrade_candidate_ids": note.upgrade_candidate_ids,
        "progression_axis_signals": [signal.model_dump(mode="json") for signal in note.progression_axis_signals],
        "stats_refresh_recommended": note.stats_refresh_recommended,
        "session_end_recommendation": note.session_end_recommendation,
        "next_owner_moves": note.next_owner_moves,
    }
    paths.harvest_handoff.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return [str(paths.harvest_handoff)]


def _render_dionysus_checkpoint_markdown(payload: dict[str, object]) -> str:
    clusters = payload.get("candidate_clusters", [])
    lines = [
        "# Checkpoint Note Promotion",
        "",
        f"Session ref: `{payload['session_ref']}`",
        f"Promotion target: `{payload['promotion_target']}`",
        f"Source note: `{payload['source_note_ref']}`",
        "",
        "## Reviewed Snapshot",
        "",
    ]
    if not isinstance(clusters, list) or not clusters:
        lines.append("- none")
    else:
        for cluster in clusters:
            if not isinstance(cluster, dict):
                continue
            lines.extend(
                [
                    f"### {cluster.get('display_name', 'checkpoint cluster')}",
                    "",
                    f"- candidate id: `{cluster.get('candidate_id', 'unknown')}`",
                    f"- kind: `{cluster.get('candidate_kind', 'unknown')}`",
                    f"- owner hint: `{cluster.get('owner_hint', 'unknown')}`",
                    f"- checkpoint hits: `{cluster.get('checkpoint_hits', 0)}`",
                    "",
                ]
            )
    lines.extend(["## Next Owner Moves", ""])
    next_owner_moves = cast(list[str], payload.get("next_owner_moves", []))
    for move in next_owner_moves:
        lines.append(f"- {move}")
    lines.extend(["", "## Evidence Refs", ""])
    evidence_refs = cast(list[str], payload.get("evidence_refs", []))
    for ref in evidence_refs:
        lines.append(f"- `{ref}`")
    return "\n".join(lines).rstrip() + "\n"


def _date_from_session_ref(session_ref: str) -> str | None:
    match = DATE_RE.search(session_ref)
    return match.group(1) if match else None
