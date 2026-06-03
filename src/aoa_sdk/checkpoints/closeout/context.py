"""Closeout context scope, handoff, receipt, and candidate-map helpers."""

from __future__ import annotations

import json
import re
from pathlib import Path

from ...loaders import load_json
from ...models import (
    CheckpointCloseoutContext,
    CheckpointLineageHint,
    SessionCheckpointCluster,
    SessionCheckpointNote,
    SessionEndSkillTarget,
    SurfaceCloseoutHandoff,
)
from ...workspace.discovery import Workspace
from ..ledger.notes import merge_checkpoint_lineage_hint as _merge_checkpoint_lineage_hint
from .common import _dedupe_strings

SESSION_REF_RE = re.compile(r'"session_ref"\s*:\s*"([^"]+)"|session_ref:\s*`?([^`\s]+)`?|Session ref:\s*`?([^`\n]+)`?')


def _validate_repo_root_closeout_scope(
    *,
    checkpoint_note: SessionCheckpointNote | None,
    resolved_session_ref: str,
) -> None:
    if checkpoint_note is None:
        return
    if checkpoint_note.session_ref == resolved_session_ref:
        return
    raise ValueError(
        "repo-root checkpoint session_ref "
        f"{checkpoint_note.session_ref!r} does not match resolved closeout session {resolved_session_ref!r}; "
        "use the matching reviewed artifact/session ref or the matching session file for that runtime session"
    )


def _surface_handoff_path(workspace: Workspace, repo_root: str, *, override: str | None = None) -> Path:
    if override is not None:
        return Path(override).expanduser().resolve()
    label = _resolve_context_label(workspace, repo_root)
    return workspace.repo_path("aoa-sdk") / ".aoa" / "surface-detection" / f"{label}.closeout-handoff.latest.json"


def _resolve_context_root(workspace: Workspace, repo_root: str) -> Path:
    resolved_repo_root = Path(repo_root).expanduser()
    if not resolved_repo_root.is_absolute():
        return (workspace.root / resolved_repo_root).resolve()
    return resolved_repo_root.resolve()


def _resolve_context_label(workspace: Workspace, repo_root: str) -> str:
    resolved_repo_root = _resolve_context_root(workspace, repo_root)
    return "workspace" if resolved_repo_root == workspace.federation_root else resolved_repo_root.name


def _load_reviewed_surface_handoff(
    *,
    workspace: Workspace,
    repo_root: str,
    handoff_path: str | None,
) -> SurfaceCloseoutHandoff | None:
    path = _surface_handoff_path(workspace, repo_root, override=handoff_path)
    if not path.exists():
        return None
    payload = load_json(path)
    report_payload = payload.get("report", payload) if isinstance(payload, dict) else payload
    handoff = SurfaceCloseoutHandoff.model_validate(report_payload)
    if not handoff.reviewed:
        return None
    return handoff


def _collect_receipt_paths(*, receipt_paths: list[str], receipt_dirs: list[str]) -> list[Path]:
    collected: list[Path] = []
    for item in receipt_paths:
        path = Path(item).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"missing closeout receipt input: {path}")
        if not path.is_file():
            raise ValueError(f"receipt path must be a file: {path}")
        collected.append(path)
    for item in receipt_dirs:
        directory = Path(item).expanduser().resolve()
        if not directory.exists():
            raise FileNotFoundError(f"missing closeout receipt directory: {directory}")
        if not directory.is_dir():
            raise ValueError(f"receipt directory must be a directory: {directory}")
        for candidate in sorted(directory.iterdir()):
            if candidate.is_file() and candidate.suffix in {".json", ".jsonl"}:
                collected.append(candidate.resolve())
    unique: list[Path] = []
    seen: set[Path] = set()
    for path in collected:
        if path in seen:
            continue
        seen.add(path)
        unique.append(path)
    return unique


def _resolve_closeout_session_ref(
    *,
    explicit_session_ref: str | None,
    checkpoint_note: SessionCheckpointNote | None,
    surface_handoff: SurfaceCloseoutHandoff | None,
    reviewed_artifact: Path,
    receipt_paths: list[Path],
) -> str:
    artifact_session_ref = _session_ref_from_reviewed_artifact(reviewed_artifact)
    receipt_session_refs = {
        session_ref
        for session_ref in (_session_ref_from_receipt_file(path) for path in receipt_paths)
        if session_ref is not None
    }
    if len(receipt_session_refs) > 1:
        raise ValueError("receipt inputs contain multiple session_ref values; build one closeout context per session")
    receipt_session_ref = next(iter(receipt_session_refs), None)

    chosen = explicit_session_ref or artifact_session_ref or (
        surface_handoff.session_ref if surface_handoff is not None else None
    ) or receipt_session_ref or (checkpoint_note.session_ref if checkpoint_note is not None else None)
    if chosen is None or not chosen.strip():
        raise ValueError(
            "could not derive session_ref from the reviewed artifact, receipt inputs, reviewed handoff, or checkpoint note; pass --session-ref explicitly"
        )

    if explicit_session_ref is not None and artifact_session_ref is not None and artifact_session_ref != explicit_session_ref:
        raise ValueError(
            f"reviewed artifact session_ref {artifact_session_ref!r} does not match explicit session_ref {explicit_session_ref!r}"
        )
    if receipt_session_ref is not None and receipt_session_ref != chosen:
        raise ValueError(
            f"receipt session_ref {receipt_session_ref!r} does not match the resolved closeout session {chosen!r}"
        )
    return chosen


def _session_ref_from_reviewed_artifact(path: Path) -> str | None:
    try:
        if path.suffix == ".json":
            payload = load_json(path)
            if isinstance(payload, dict):
                session_ref = payload.get("session_ref")
                if isinstance(session_ref, str) and session_ref:
                    return session_ref
    except Exception:
        pass
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    match = SESSION_REF_RE.search(text)
    if match is None:
        return None
    return next((group.strip() for group in match.groups() if isinstance(group, str) and group.strip()), None)


def _session_ref_from_receipt_file(path: Path) -> str | None:
    payloads = _load_receipt_payloads([str(path)])
    session_refs = {
        value
        for value in (
            payload.get("session_ref") if isinstance(payload.get("session_ref"), str) else None
            for payload in payloads
        )
        if value is not None
    }
    if len(session_refs) > 1:
        raise ValueError(f"{path}: mixed session_ref values are not supported in one receipt input")
    session_ref = next(iter(session_refs), None)
    return session_ref if isinstance(session_ref, str) else None


def _load_context_checkpoint_note(context: CheckpointCloseoutContext) -> SessionCheckpointNote | None:
    if context.checkpoint_note_ref is None:
        return None
    return SessionCheckpointNote.model_validate(load_json(context.checkpoint_note_ref))


def _load_context_checkpoint_notes(context: CheckpointCloseoutContext) -> list[SessionCheckpointNote]:
    note_refs = _dedupe_strings(
        [
            *(context.checkpoint_note_refs or []),
            *([context.checkpoint_note_ref] if context.checkpoint_note_ref is not None else []),
        ]
    )
    notes: list[SessionCheckpointNote] = []
    for ref in note_refs:
        notes.append(SessionCheckpointNote.model_validate(load_json(ref)))
    return notes


def _load_context_surface_handoff(context: CheckpointCloseoutContext) -> SurfaceCloseoutHandoff | None:
    if context.surface_handoff_ref is None:
        return None
    payload = load_json(context.surface_handoff_ref)
    report_payload = payload.get("report", payload) if isinstance(payload, dict) else payload
    return SurfaceCloseoutHandoff.model_validate(report_payload)


def _load_receipt_payloads(receipt_refs: list[str]) -> list[dict[str, object]]:
    receipts: list[dict[str, object]] = []
    for ref in receipt_refs:
        path = Path(ref).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"missing closeout receipt input: {path}")
        if path.suffix == ".jsonl":
            for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                line = raw_line.strip()
                if not line:
                    continue
                payload = json.loads(line)
                if not isinstance(payload, dict):
                    raise ValueError(f"{path}:{line_number}: receipt must be an object")
                receipts.append(payload)
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            receipts.append(payload)
            continue
        if not isinstance(payload, list):
            raise ValueError(f"{path}: receipt payload must be an object or list")
        for index, item in enumerate(payload):
            if not isinstance(item, dict):
                raise ValueError(f"{path}[{index}]: receipt must be an object")
            receipts.append(item)
    return receipts


def _closeout_candidate_clusters(
    *,
    notes: list[SessionCheckpointNote],
    handoff: SurfaceCloseoutHandoff | None,
) -> list[SessionCheckpointCluster]:
    deduped: dict[tuple[str, str], SessionCheckpointCluster] = {}
    order: list[tuple[str, str]] = []
    for cluster in [
        *(handoff.surviving_checkpoint_clusters if handoff is not None else []),
        *(cluster for note in notes for cluster in note.candidate_clusters),
    ]:
        key = (cluster.candidate_id, cluster.owner_hint)
        if key not in deduped:
            deduped[key] = cluster
            order.append(key)
    return [deduped[key] for key in order]


def _collect_candidate_lineage_hints(
    clusters: list[SessionCheckpointCluster],
) -> list[CheckpointLineageHint]:
    deduped: dict[str, CheckpointLineageHint] = {}
    order: list[str] = []
    for cluster in clusters:
        if cluster.lineage_hint is None:
            continue
        cluster_ref = cluster.lineage_hint.cluster_ref
        if cluster_ref not in deduped:
            deduped[cluster_ref] = cluster.lineage_hint
            order.append(cluster_ref)
            continue
        deduped[cluster_ref] = _merge_checkpoint_lineage_hint(deduped[cluster_ref], cluster.lineage_hint) or deduped[cluster_ref]
    return [deduped[key] for key in order]


def _derive_closeout_skill_plan(
    *,
    notes: list[SessionCheckpointNote],
    handoff: SurfaceCloseoutHandoff | None,
) -> list[SessionEndSkillTarget]:
    candidate_ids = _dedupe_strings(
        [
            *(cluster.candidate_id for note in notes for cluster in note.candidate_clusters),
            *(cluster.candidate_id for cluster in (handoff.surviving_checkpoint_clusters if handoff is not None else [])),
        ]
    )
    if not candidate_ids:
        return []
    harvest_candidate_ids = _dedupe_strings(
        [candidate_id for note in notes for candidate_id in note.harvest_candidate_ids]
    )
    progression_candidate_ids = _dedupe_strings(
        [candidate_id for note in notes for candidate_id in note.progression_candidate_ids]
    )
    upgrade_candidate_ids = _dedupe_strings(
        [candidate_id for note in notes for candidate_id in note.upgrade_candidate_ids]
    )
    return [
        SessionEndSkillTarget(
            skill_name="aoa-session-donor-harvest",
            why="reviewed closeout should start with donor harvest so checkpoint hints become one bounded packet rooted in the reread session artifact",
            candidate_ids=harvest_candidate_ids or candidate_ids,
        ),
        SessionEndSkillTarget(
            skill_name="aoa-session-progression-lift",
            why="reviewed closeout should reread the reviewed artifact and donor packet before lifting one final multi-axis progression delta",
            candidate_ids=progression_candidate_ids or candidate_ids,
        ),
        SessionEndSkillTarget(
            skill_name="aoa-quest-harvest",
            why="reviewed closeout should only reach final quest triage after donor harvest and progression lift have both completed",
            candidate_ids=upgrade_candidate_ids,
        ),
    ]
