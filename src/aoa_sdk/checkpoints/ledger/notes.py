"""Checkpoint note ledger assembly and runtime note loading."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, Protocol, cast

from ...errors import SurfaceNotFound
from ...models import (
    CheckpointLineageHint,
    ProgressionAxisSignal,
    SessionCheckpointAgentReview,
    SessionCheckpointCluster,
    SessionCheckpointHistoryEntry,
    SessionCheckpointNote,
    SessionEndSkillTarget,
)
from ...workspace.discovery import Workspace
from ..naming import safe_checkpoint_name
from ..render.markdown import render_checkpoint_note_markdown
from ..review.agent_review import (
    agent_review_commit_keys,
    agent_review_key,
    collect_review_carry,
    history_entry_review_key,
)
from ..timestamps import coerce_datetime, with_local_timestamp_default
from ..topology.paths import (
    CheckpointPaths,
    checkpoint_current_root,
    checkpoint_paths_for_label,
    checkpoint_runtime_scope_key,
)


SESSION_REF_TIMESTAMP_FORMAT = "%Y-%m-%dT%H-%M-%S-%fZ"


class CheckpointStatusAPI(Protocol):
    workspace: Workspace

    def status(self, *, repo_root: str, session_file: str | None = None) -> SessionCheckpointNote: ...

    def peek_status(self, *, repo_root: str, session_file: str | None = None) -> SessionCheckpointNote: ...


def load_checkpoint_note(path: Path) -> SessionCheckpointNote | None:
    try:
        return SessionCheckpointNote.model_validate_json(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def should_rotate_checkpoint_note(
    existing_note: SessionCheckpointNote,
    *,
    runtime_session_id: str | None,
) -> bool:
    if existing_note.state in {"closed", "promoted"}:
        return True
    if runtime_session_id is None:
        return False
    if existing_note.runtime_session_id is None:
        return True
    return existing_note.runtime_session_id != runtime_session_id


def should_hide_current_checkpoint_note(
    note: SessionCheckpointNote,
    *,
    runtime_session_id: str | None,
) -> bool:
    if note.state in {"closed", "promoted"}:
        return True
    if runtime_session_id is None:
        return False
    if note.runtime_session_id is None:
        return False
    return note.runtime_session_id != runtime_session_id


def default_session_ref(
    paths: CheckpointPaths,
    *,
    existing_note: SessionCheckpointNote | None,
    runtime_session_id: str | None,
) -> str:
    if existing_note is not None and existing_note.state not in {"closed", "promoted"} and existing_note.session_ref:
        return existing_note.session_ref
    timestamp = datetime.now(UTC).strftime(SESSION_REF_TIMESTAMP_FORMAT)
    runtime_suffix = f"-{safe_checkpoint_name(runtime_session_id)[:12]}" if runtime_session_id else ""
    return f"session:{timestamp}-{paths.repo_label}-checkpoint-growth{runtime_suffix}"


def archive_current_checkpoint(paths: CheckpointPaths) -> None:
    archive_root = paths.root / ".aoa" / "session-growth" / "archive"
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    archive_stem = (
        f"{paths.repo_label}-{paths.runtime_scope_key}-{timestamp}"
        if paths.runtime_scope_key is not None
        else f"{paths.repo_label}-{timestamp}"
    )
    archive_dir = archive_root / archive_stem
    archive_dir.mkdir(parents=True, exist_ok=True)
    for source in (
        paths.jsonl,
        paths.note_json,
        paths.note_md,
        paths.harvest_handoff,
        paths.post_commit_report,
        paths.closeout_context,
        paths.closeout_execution_report,
    ):
        if source.exists():
            source.rename(archive_dir / source.name)
    if paths.closeout_artifacts.exists():
        paths.closeout_artifacts.rename(archive_dir / paths.closeout_artifacts.name)


def move_current_checkpoint(*, source_paths: CheckpointPaths, target_paths: CheckpointPaths) -> None:
    if source_paths.current_dir == target_paths.current_dir:
        return
    if not source_paths.current_dir.exists():
        return
    target_paths.current_dir.parent.mkdir(parents=True, exist_ok=True)
    if not target_paths.current_dir.exists():
        source_paths.current_dir.rename(target_paths.current_dir)
        return
    for source, target in (
        (source_paths.jsonl, target_paths.jsonl),
        (source_paths.note_json, target_paths.note_json),
        (source_paths.note_md, target_paths.note_md),
        (source_paths.harvest_handoff, target_paths.harvest_handoff),
        (source_paths.post_commit_report, target_paths.post_commit_report),
        (source_paths.closeout_context, target_paths.closeout_context),
        (source_paths.closeout_execution_report, target_paths.closeout_execution_report),
    ):
        if source.exists():
            source.rename(target)
    if source_paths.closeout_artifacts.exists():
        source_paths.closeout_artifacts.rename(target_paths.closeout_artifacts)


def merge_checkpoint_lineage_hint(
    existing: CheckpointLineageHint | None,
    incoming: CheckpointLineageHint | None,
) -> CheckpointLineageHint | None:
    if existing is None:
        return incoming
    if incoming is None:
        return existing
    axis_pressure = dict(existing.axis_pressure)
    axis_pressure.update(incoming.axis_pressure)
    return existing.model_copy(
        update={
            "owner_hypothesis": incoming.owner_hypothesis or existing.owner_hypothesis,
            "owner_shape": incoming.owner_shape or existing.owner_shape,
            "nearest_wrong_target": incoming.nearest_wrong_target or existing.nearest_wrong_target,
            "status_posture": incoming.status_posture,
            "evidence_refs": _dedupe_strings([*existing.evidence_refs, *incoming.evidence_refs]),
            "axis_pressure": axis_pressure,
            "supersedes": _dedupe_strings([*existing.supersedes, *incoming.supersedes]),
            "merged_into": incoming.merged_into or existing.merged_into,
            "drop_reason": incoming.drop_reason or existing.drop_reason,
        }
    )


def build_checkpoint_note(paths: CheckpointPaths) -> SessionCheckpointNote:
    entries: list[SessionCheckpointHistoryEntry] = []
    agent_review_map: dict[str, SessionCheckpointAgentReview] = {}
    session_ref: str | None = None
    runtime_session_id: str | None = None
    runtime_session_created_at: datetime | None = None
    repo_scope: set[str] = {paths.repo_label}
    for raw_line in paths.jsonl.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        payload = json.loads(line)
        if session_ref is None and isinstance(payload.get("session_ref"), str):
            session_ref = payload["session_ref"]
        if runtime_session_id is None and isinstance(payload.get("runtime_session_id"), str):
            runtime_session_id = payload["runtime_session_id"]
        if runtime_session_created_at is None:
            runtime_session_created_at = coerce_datetime(payload.get("runtime_session_created_at"))
        if "agent_review" in payload:
            review = SessionCheckpointAgentReview.model_validate(payload["agent_review"])
            reviewed_at_local, reviewed_tz = with_local_timestamp_default(
                utc_value=review.reviewed_at,
                local_value=review.reviewed_at_local,
                tz_name=review.reviewed_tz,
            )
            if reviewed_at_local != review.reviewed_at_local or reviewed_tz != review.reviewed_tz:
                review = review.model_copy(
                    update={
                        "reviewed_at_local": reviewed_at_local,
                        "reviewed_tz": reviewed_tz,
                    }
                )
            review_key = agent_review_key(review)
            if review_key in agent_review_map:
                del agent_review_map[review_key]
            agent_review_map[review_key] = review
            continue
        entry = SessionCheckpointHistoryEntry.model_validate(payload["history_entry"])
        observed_at_local, observed_tz = with_local_timestamp_default(
            utc_value=entry.observed_at,
            local_value=entry.observed_at_local,
            tz_name=entry.observed_tz,
        )
        if observed_at_local != entry.observed_at_local or observed_tz != entry.observed_tz:
            entry = entry.model_copy(
                update={
                    "observed_at_local": observed_at_local,
                    "observed_tz": observed_tz,
                }
            )
        entries.append(entry)
    if runtime_session_id is None:
        runtime_session_id = paths.runtime_session_id
    if session_ref is None:
        session_ref = default_session_ref(
            paths,
            existing_note=None,
            runtime_session_id=runtime_session_id,
        )
    agent_reviews = list(agent_review_map.values())

    existing_state = "collecting"
    existing_review_status = "unreviewed"
    existing_evidence_refs: list[str] = []
    existing_next_owner_moves: list[str] = []
    if paths.note_json.exists():
        try:
            existing_note = SessionCheckpointNote.model_validate_json(paths.note_json.read_text(encoding="utf-8"))
            existing_state = existing_note.state
            existing_review_status = existing_note.review_status
            existing_evidence_refs = list(existing_note.evidence_refs)
            existing_next_owner_moves = list(existing_note.next_owner_moves)
            if runtime_session_id is None:
                runtime_session_id = existing_note.runtime_session_id
            if runtime_session_created_at is None:
                runtime_session_created_at = existing_note.runtime_session_created_at
        except Exception:
            pass

    cluster_map: dict[tuple[str, str], SessionCheckpointCluster] = {}
    all_blocked: set[str] = set()
    all_evidence: set[str] = set(existing_evidence_refs)
    next_owner_moves: set[str] = set(existing_next_owner_moves)
    manual_review_requested = False
    has_owner_followthrough = False
    reviewed_commit_keys = agent_review_commit_keys(agent_reviews)
    normalized_entries: list[SessionCheckpointHistoryEntry] = []

    for entry in entries:
        if entry.agent_review_status == "pending" and history_entry_review_key(entry) in reviewed_commit_keys:
            entry = entry.model_copy(
                update={
                    "agent_review_status": "reviewed",
                    "agent_review_ref": reviewed_commit_keys[history_entry_review_key(entry)],
                }
            )
        normalized_entries.append(entry)
    entries = normalized_entries

    for entry in entries:
        if entry.manual_review_requested:
            manual_review_requested = True
        if entry.checkpoint_kind == "owner_followthrough":
            has_owner_followthrough = True
        if entry.auto_observation is not None:
            all_evidence.update(entry.auto_observation.evidence_refs)
            next_owner_moves.update(entry.auto_observation.next_owner_moves)
        all_blocked.update(entry.blocked_by)
        for cluster in entry.candidate_clusters:
            repo_scope.add(cluster.owner_hint)
            key = (cluster.candidate_id, cluster.owner_hint)
            existing = cluster_map.get(key)
            cluster_session_end_targets = (
                list(cluster.session_end_targets)
                if cluster.session_end_targets
                else _legacy_session_end_targets_for_candidate_kind(cluster.candidate_kind)
            )
            cluster_progression_axis_signals = (
                list(cluster.progression_axis_signals)
                if cluster.progression_axis_signals
                else _legacy_progression_axis_signals_for_cluster(cluster)
            )
            merged_evidence = _dedupe_strings([*(existing.evidence_refs if existing else []), *cluster.evidence_refs])
            merged_moves = _dedupe_strings([*(existing.next_owner_moves if existing else []), *cluster.next_owner_moves])
            merged_promote_if = _dedupe_strings([*(existing.promote_if if existing else []), *cluster.promote_if])
            merged_blocked = _dedupe_strings([*(existing.blocked_by if existing else []), *cluster.blocked_by])
            merged_session_end_targets = _dedupe_session_end_targets(
                [*(existing.session_end_targets if existing else []), *cluster_session_end_targets]
            )
            merged_progression_axis_signals = _merge_progression_axis_signals(
                [*(existing.progression_axis_signals if existing else []), *cluster_progression_axis_signals]
            )
            confidence = _max_confidence(existing.confidence if existing else None, cluster.confidence)
            checkpoint_hits = (existing.checkpoint_hits if existing else 0) + 1
            cluster_map[key] = SessionCheckpointCluster(
                candidate_id=cluster.candidate_id,
                candidate_kind=cluster.candidate_kind,
                owner_hint=cluster.owner_hint,
                display_name=cluster.display_name,
                source_surface_ref=cluster.source_surface_ref,
                checkpoint_hits=checkpoint_hits,
                evidence_refs=merged_evidence,
                confidence=confidence,
                session_end_targets=merged_session_end_targets,
                progression_axis_signals=merged_progression_axis_signals,
                promote_if=merged_promote_if,
                defer_reason=cluster.defer_reason or (existing.defer_reason if existing else None),
                blocked_by=merged_blocked,
                next_owner_moves=merged_moves,
                lineage_hint=merge_checkpoint_lineage_hint(
                    existing.lineage_hint if existing is not None else None,
                    cluster.lineage_hint,
                ),
            )
            all_evidence.update(merged_evidence)
            next_owner_moves.update(merged_moves)

    for review in agent_reviews:
        all_evidence.update(review.evidence_refs)
        next_owner_moves.update(review.next_owner_moves)
    note_review_carry = collect_review_carry(agent_reviews)

    candidate_clusters: list[SessionCheckpointCluster] = []
    for checkpoint_cluster in cluster_map.values():
        review_status: Literal["collecting", "reviewable", "promoted", "closed"] = "collecting"
        if checkpoint_cluster.checkpoint_hits >= 2 or manual_review_requested:
            review_status = "reviewable"
        if existing_state == "promoted":
            review_status = "promoted"
        elif existing_state == "closed":
            review_status = "closed"
        checkpoint_cluster.review_status = review_status
        candidate_clusters.append(checkpoint_cluster)
        all_blocked.update(checkpoint_cluster.blocked_by)
        if checkpoint_cluster.defer_reason:
            all_blocked.add(checkpoint_cluster.defer_reason)

    candidate_clusters.sort(key=lambda item: (-item.checkpoint_hits, item.candidate_id, item.owner_hint))
    harvest_candidate_ids = [
        cluster.candidate_id for cluster in candidate_clusters if "harvest" in cluster.session_end_targets
    ]
    progression_candidate_ids = [
        cluster.candidate_id for cluster in candidate_clusters if "progression" in cluster.session_end_targets
    ]
    upgrade_candidate_ids = [
        cluster.candidate_id for cluster in candidate_clusters if "upgrade" in cluster.session_end_targets
    ]
    progression_axis_signals = _aggregate_progression_axis_signals(candidate_clusters)
    stats_refresh_recommended = bool(candidate_clusters)
    pending_agent_review_refs = [
        entry.commit_sha or entry.commit_short_sha or entry.intent_text
        for entry in entries
        if entry.agent_review_status == "pending"
    ]
    agent_review_status: Literal["none", "pending", "reviewed"] = "none"
    if pending_agent_review_refs:
        agent_review_status = "pending"
    elif agent_reviews:
        agent_review_status = "reviewed"
    recommendation = _derive_promotion_recommendation(
        candidate_clusters=candidate_clusters,
        has_owner_followthrough=has_owner_followthrough,
        state=existing_state,
    )
    state = _derive_note_state(
        existing_state=existing_state,
        candidate_clusters=candidate_clusters,
        recommendation=recommendation,
    )

    note = SessionCheckpointNote(
        session_ref=session_ref,
        runtime_session_id=runtime_session_id,
        runtime_session_created_at=runtime_session_created_at,
        state=state,
        repo_scope=sorted(repo_scope),
        checkpoint_history=entries,
        candidate_clusters=candidate_clusters,
        promotion_recommendation=recommendation,
        carry_until_session_closeout=state not in {"promoted", "closed"},
        session_end_recommendation=_derive_session_end_recommendation(
            harvest_candidate_ids=harvest_candidate_ids,
            progression_candidate_ids=progression_candidate_ids,
            upgrade_candidate_ids=upgrade_candidate_ids,
        ),
        harvest_candidate_ids=harvest_candidate_ids,
        progression_candidate_ids=progression_candidate_ids,
        upgrade_candidate_ids=upgrade_candidate_ids,
        progression_axis_signals=progression_axis_signals,
        stats_refresh_recommended=stats_refresh_recommended,
        agent_review_status=agent_review_status,
        agent_review_required=bool(pending_agent_review_refs),
        agent_review_pending_refs=_dedupe_strings(pending_agent_review_refs),
        review_refs=note_review_carry.review_refs,
        auto_observation_refs=note_review_carry.auto_observation_refs,
        applied_skill_names=note_review_carry.applied_skill_names,
        summaries=note_review_carry.summaries,
        findings=note_review_carry.findings,
        candidate_notes=note_review_carry.candidate_notes,
        stats_hints=note_review_carry.stats_hints,
        mechanic_hints=note_review_carry.mechanic_hints,
        closeout_questions=note_review_carry.closeout_questions,
        agent_reviews=agent_reviews,
        blocked_by=sorted(all_blocked),
        review_status=(
            "reviewed"
            if not pending_agent_review_refs
            and (existing_review_status == "reviewed" or agent_review_status == "reviewed")
            else "unreviewed"
        ),
        evidence_refs=sorted(all_evidence),
        next_owner_moves=sorted(
            {
                *next_owner_moves,
                *(
                    {"carry the checkpoint note through the end of the session before moving candidates or stats"}
                    if candidate_clusters
                    else set()
                ),
                *(
                    {"at reviewed closeout, bundle harvest candidates before refreshing stats"}
                    if harvest_candidate_ids
                    else set()
                ),
                *(
                    {"at reviewed closeout, lift provisional progression axes before any final quest verdict"}
                    if progression_candidate_ids
                    else set()
                ),
                *(
                    {"at reviewed closeout, review upgrade candidates before any owner-layer promotion"}
                    if upgrade_candidate_ids
                    else set()
                ),
            }
        ),
    )
    return note


def load_runtime_checkpoint_note(
    api: CheckpointStatusAPI,
    *,
    repo_root: str,
    session_file: str | None = None,
) -> SessionCheckpointNote | None:
    try:
        return api.status(repo_root=repo_root, session_file=session_file)
    except SurfaceNotFound:
        return None


def peek_runtime_checkpoint_note(
    api: CheckpointStatusAPI,
    *,
    repo_root: str,
    session_file: str | None = None,
) -> SessionCheckpointNote | None:
    try:
        return api.peek_status(repo_root=repo_root, session_file=session_file)
    except SurfaceNotFound:
        return None


def load_runtime_scoped_checkpoint_notes(
    api: CheckpointStatusAPI,
    *,
    runtime_session_id: str,
) -> list[tuple[CheckpointPaths, SessionCheckpointNote]]:
    current_root = checkpoint_current_root(api.workspace)
    if not current_root.exists():
        return []

    runtime_scope_key = checkpoint_runtime_scope_key(runtime_session_id)
    if runtime_scope_key is None:
        return []

    scope_root = current_root / runtime_scope_key
    if not scope_root.exists():
        return []

    records: list[tuple[CheckpointPaths, SessionCheckpointNote]] = []
    for current_dir in sorted(path for path in scope_root.iterdir() if path.is_dir()):
        paths = checkpoint_paths_for_label(
            api.workspace,
            current_dir.name,
            runtime_session_id=runtime_session_id,
        )
        if not paths.jsonl.exists():
            continue
        note = build_checkpoint_note(paths)
        if note.runtime_session_id != runtime_session_id:
            continue
        if should_hide_current_checkpoint_note(note, runtime_session_id=runtime_session_id):
            archive_current_checkpoint(paths)
            continue
        records.append((paths, note))
    return records


def load_runtime_checkpoint_notes_for_closeout(
    api: CheckpointStatusAPI,
    *,
    repo_root: str,
    resolved_session_ref: str,
    primary_note: SessionCheckpointNote | None,
) -> list[tuple[CheckpointPaths, SessionCheckpointNote]]:
    current_root = checkpoint_current_root(api.workspace)
    if not current_root.exists():
        return []

    runtime_session_id = primary_note.runtime_session_id if primary_note is not None else None
    records: list[tuple[CheckpointPaths, SessionCheckpointNote]] = []
    candidate_paths: list[CheckpointPaths] = []
    seen_dirs: set[Path] = set()
    if runtime_session_id is not None:
        scope_key = checkpoint_runtime_scope_key(runtime_session_id)
        if scope_key is not None:
            scope_root = current_root / scope_key
            if scope_root.exists():
                for current_dir in sorted(path for path in scope_root.iterdir() if path.is_dir()):
                    paths = checkpoint_paths_for_label(
                        api.workspace,
                        current_dir.name,
                        runtime_session_id=runtime_session_id,
                    )
                    seen_dirs.add(paths.current_dir)
                    candidate_paths.append(paths)
    else:
        for current_dir in sorted(path for path in current_root.iterdir() if path.is_dir()):
            if not (current_dir / "checkpoint-note.jsonl").exists():
                continue
            paths = checkpoint_paths_for_label(api.workspace, current_dir.name, runtime_session_id=None)
            if paths.current_dir in seen_dirs:
                continue
            candidate_paths.append(paths)
            seen_dirs.add(paths.current_dir)

    for paths in candidate_paths:
        if not paths.jsonl.exists():
            continue
        note = build_checkpoint_note(paths)
        if runtime_session_id is not None and note.runtime_session_id != runtime_session_id:
            if note.runtime_session_id is not None and paths.runtime_session_id is None:
                archive_current_checkpoint(paths)
            continue
        if should_hide_current_checkpoint_note(note, runtime_session_id=runtime_session_id):
            archive_current_checkpoint(paths)
            continue
        if not checkpoint_note_matches_closeout_scope(
            note,
            resolved_session_ref=resolved_session_ref,
            runtime_session_id=runtime_session_id,
        ):
            continue
        paths.note_json.parent.mkdir(parents=True, exist_ok=True)
        paths.note_json.write_text(note.model_dump_json(indent=2) + "\n", encoding="utf-8")
        paths.note_md.write_text(
            render_checkpoint_note_markdown(note, repo_label=paths.repo_label),
            encoding="utf-8",
        )
        records.append((paths, note))
    return records


def checkpoint_note_matches_closeout_scope(
    note: SessionCheckpointNote,
    *,
    resolved_session_ref: str,
    runtime_session_id: str | None,
) -> bool:
    if runtime_session_id is not None:
        if note.runtime_session_id == runtime_session_id:
            return True
        if note.runtime_session_id is not None:
            return False
    return note.session_ref == resolved_session_ref


def derive_session_end_skill_targets(note: SessionCheckpointNote | None) -> list[SessionEndSkillTarget]:
    if note is None or not note.candidate_clusters:
        return []

    all_candidate_ids = [cluster.candidate_id for cluster in note.candidate_clusters]
    return [
        SessionEndSkillTarget(
            skill_name="aoa-session-donor-harvest",
            why="reviewed closeout should start from donor harvest so checkpoint-led hints are reread against the full reviewed artifact before any later verdict",
            candidate_ids=list(note.harvest_candidate_ids or all_candidate_ids),
        ),
        SessionEndSkillTarget(
            skill_name="aoa-session-progression-lift",
            why="reviewed closeout should gather one final multi-axis progression delta after donor harvest rereads the reviewed artifact",
            candidate_ids=list(note.progression_candidate_ids or all_candidate_ids),
        ),
        SessionEndSkillTarget(
            skill_name="aoa-quest-harvest",
            why="reviewed closeout should keep final quest triage last, after donor harvest and progression lift have both completed",
            candidate_ids=list(note.upgrade_candidate_ids),
        ),
    ]


def derive_session_end_next_honest_move(
    *,
    note: SessionCheckpointNote | None,
    session_end_targets: list[SessionEndSkillTarget],
) -> str | None:
    if note is None or not session_end_targets:
        return None

    if note.agent_review_pending_refs:
        refs_preview = ", ".join(note.agent_review_pending_refs[:3])
        if len(note.agent_review_pending_refs) > 3:
            refs_preview += f" (+{len(note.agent_review_pending_refs) - 3} more)"
        return (
            "Before reviewed closeout, write `aoa checkpoint review-note --auto` for pending checkpoint commit(s): "
            + refs_preview
            + "."
        )

    skill_names = [target.skill_name for target in session_end_targets]
    if note.stats_refresh_recommended:
        return (
            "At reviewed closeout, run aoa-checkpoint-closeout-bridge so it raises "
            + ", ".join(skill_names)
            + " and refresh stats only after the reviewed handoff is assembled."
        )
    return "At reviewed closeout, run aoa-checkpoint-closeout-bridge and raise " + ", ".join(skill_names) + "."


def merge_progression_axis_signals(values: list[ProgressionAxisSignal]) -> list[ProgressionAxisSignal]:
    return _merge_progression_axis_signals(values)


def _derive_promotion_recommendation(
    *,
    candidate_clusters: list[SessionCheckpointCluster],
    has_owner_followthrough: bool,
    state: str,
) -> Literal["none", "local_note", "dionysus_note", "harvest_handoff"]:
    if state == "closed":
        return "harvest_handoff"
    if state == "promoted":
        return "dionysus_note"
    if not candidate_clusters:
        return "none"
    reviewable = [cluster for cluster in candidate_clusters if cluster.review_status == "reviewable"]
    if not reviewable:
        return "local_note"
    if has_owner_followthrough or len(reviewable) >= 2:
        return "harvest_handoff"
    if any(len(cluster.evidence_refs) >= 3 and "owner-ambiguity" not in cluster.blocked_by for cluster in reviewable):
        return "dionysus_note"
    return "local_note"


def _derive_note_state(
    *,
    existing_state: str,
    candidate_clusters: list[SessionCheckpointCluster],
    recommendation: str,
) -> Literal["collecting", "reviewable", "promoted", "closed"]:
    if existing_state in {"promoted", "closed"}:
        return existing_state  # type: ignore[return-value]
    if recommendation in {"dionysus_note", "harvest_handoff"} or any(
        cluster.review_status == "reviewable" for cluster in candidate_clusters
    ):
        return "reviewable"
    return "collecting"


def _max_confidence(left: str | None, right: str) -> Literal["low", "medium", "high"]:
    rank = {"low": 1, "medium": 2, "high": 3}
    if left is None:
        return right  # type: ignore[return-value]
    return left if rank[left] >= rank[right] else right  # type: ignore[return-value]


def _dedupe_session_end_targets(
    values: list[Literal["harvest", "progression", "upgrade"]],
) -> list[Literal["harvest", "progression", "upgrade"]]:
    deduped: list[Literal["harvest", "progression", "upgrade"]] = []
    for value in values:
        if value not in deduped:
            deduped.append(value)
    return deduped


def _legacy_session_end_targets_for_candidate_kind(
    candidate_kind: str,
) -> list[Literal["harvest", "progression", "upgrade"]]:
    targets: list[Literal["harvest", "progression", "upgrade"]] = ["harvest", "progression"]
    if candidate_kind in {"route", "pattern", "proof", "recall", "role"}:
        targets.append("upgrade")
    return targets


def _legacy_progression_axis_signals_for_cluster(
    cluster: SessionCheckpointHistoryEntry | SessionCheckpointCluster | object,
) -> list[ProgressionAxisSignal]:
    candidate_kind = getattr(cluster, "candidate_kind", None)
    source_surface_ref = getattr(cluster, "source_surface_ref", None)
    blocked_by = getattr(cluster, "blocked_by", None)
    evidence_refs = getattr(cluster, "evidence_refs", None)
    candidate_id = getattr(cluster, "candidate_id", None)
    if not isinstance(candidate_kind, str) or not isinstance(source_surface_ref, str):
        return []
    return _progression_axis_signals_for_candidate(
        candidate_kind=candidate_kind,
        source_surface_ref=source_surface_ref,
        blocked_by=list(blocked_by) if isinstance(blocked_by, list) else [],
        evidence_refs=list(evidence_refs) if isinstance(evidence_refs, list) else [],
        candidate_id=candidate_id if isinstance(candidate_id, str) else None,
    )


def _progression_axis_signals_for_candidate(
    *,
    candidate_kind: str,
    source_surface_ref: str,
    blocked_by: list[str],
    evidence_refs: list[str],
    candidate_id: str | None,
) -> list[ProgressionAxisSignal]:
    templates: list[tuple[str, str, str]]
    if candidate_kind == "growth":
        templates = [
            (
                "execution_reliability",
                "advance",
                "bounded mutation evidence suggests the session improved execution reliability, subject to reviewed closeout confirmation",
            ),
            (
                "change_legibility",
                "advance",
                "the checkpoint seam makes the change easier to narrate and verify later",
            ),
        ]
        if source_surface_ref.endswith("verify_green"):
            templates.append(
                (
                    "proof_discipline",
                    "advance",
                    "verify-green evidence strengthens proof discipline for the bounded change",
                )
            )
    elif candidate_kind == "route":
        templates = [
            (
                "change_legibility",
                "advance",
                "recurring-route evidence makes the session easier to hand off and replay honestly",
            ),
            (
                "deep_readiness",
                "advance",
                "repeated route evidence hints that the session may be maturing into a reusable pattern",
            ),
        ]
    elif candidate_kind == "pattern":
        templates = [
            (
                "deep_readiness",
                "advance",
                "pattern evidence suggests the route is approaching reusable technique shape",
            ),
            (
                "review_sharpness",
                "advance",
                "naming the pattern sharpens later reviewed interpretation",
            ),
        ]
    elif candidate_kind == "proof":
        templates = [
            (
                "proof_discipline",
                "advance",
                "proof-shaped evidence strengthens the session's reviewed basis",
            ),
            (
                "review_sharpness",
                "advance",
                "explicit proof evidence sharpens reviewed closeout judgment",
            ),
        ]
    elif candidate_kind == "recall":
        templates = [
            (
                "provenance_hygiene",
                "advance",
                "recall surfaces preserve attribution and route memory for later review",
            ),
            (
                "change_legibility",
                "advance",
                "memo-shaped recall makes the session easier to narrate without replaying raw history",
            ),
        ]
    elif candidate_kind == "role":
        templates = [
            (
                "boundary_integrity",
                "hold",
                "role-posture evidence exists, but owner boundaries should stay explicit until reviewed closeout",
            ),
            (
                "deep_readiness",
                "advance",
                "owner-role evidence may reflect deeper readiness once it is reviewed in context",
            ),
        ]
    elif candidate_kind == "risk":
        templates = [
            (
                "boundary_integrity",
                "reanchor",
                "risk-gated checkpoint evidence says progression must stay bounded and reviewed",
            ),
            (
                "proof_discipline",
                "hold",
                "risk-shaped evidence should hold until the reviewed route confirms the same concern",
            ),
        ]
    else:
        templates = [
            (
                "change_legibility",
                "hold",
                "checkpoint evidence exists, but the progression claim should stay provisional until reviewed closeout",
            )
        ]

    signals: list[ProgressionAxisSignal] = []
    for axis, movement, why in templates:
        adjusted = _adjust_progression_movement(movement=movement, blocked_by=blocked_by)
        signals.append(
            ProgressionAxisSignal(
                axis=cast(
                    Literal[
                        "boundary_integrity",
                        "execution_reliability",
                        "change_legibility",
                        "review_sharpness",
                        "proof_discipline",
                        "provenance_hygiene",
                        "deep_readiness",
                    ],
                    axis,
                ),
                movement=cast(Literal["advance", "hold", "reanchor", "downgrade"], adjusted),
                why=why,
                evidence_refs=list(evidence_refs),
                candidate_ids=[candidate_id] if candidate_id is not None else [],
            )
        )
    return signals


def _adjust_progression_movement(
    *,
    movement: str,
    blocked_by: list[str],
) -> str:
    if movement in {"reanchor", "downgrade"}:
        return movement
    if "owner-ambiguity" in blocked_by or "thin-evidence" in blocked_by or "requires-reviewed-route" in blocked_by:
        return "hold"
    return movement


def _merge_progression_axis_signals(values: list[ProgressionAxisSignal]) -> list[ProgressionAxisSignal]:
    merged: dict[str, ProgressionAxisSignal] = {}
    order: list[str] = []
    for value in values:
        existing = merged.get(value.axis)
        if existing is None:
            merged[value.axis] = value.model_copy(
                update={
                    "evidence_refs": _dedupe_strings(value.evidence_refs),
                    "candidate_ids": _dedupe_strings(value.candidate_ids),
                }
            )
            order.append(value.axis)
            continue
        merged[value.axis] = existing.model_copy(
            update={
                "movement": _more_cautious_progression_movement(existing.movement, value.movement),
                "why": existing.why if existing.why == value.why else existing.why,
                "evidence_refs": _dedupe_strings([*existing.evidence_refs, *value.evidence_refs]),
                "candidate_ids": _dedupe_strings([*existing.candidate_ids, *value.candidate_ids]),
            }
        )
    return [merged[axis] for axis in order]


def _aggregate_progression_axis_signals(
    candidate_clusters: list[SessionCheckpointCluster],
) -> list[ProgressionAxisSignal]:
    axis_payloads: dict[str, ProgressionAxisSignal] = {}
    order: list[str] = []
    for cluster in candidate_clusters:
        cluster_signals = (
            list(cluster.progression_axis_signals)
            if cluster.progression_axis_signals
            else _legacy_progression_axis_signals_for_cluster(cluster)
        )
        for signal in cluster_signals:
            existing = axis_payloads.get(signal.axis)
            if existing is None:
                axis_payloads[signal.axis] = signal.model_copy(
                    update={
                        "candidate_ids": _dedupe_strings([cluster.candidate_id, *signal.candidate_ids]),
                        "evidence_refs": _dedupe_strings(signal.evidence_refs),
                    }
                )
                order.append(signal.axis)
                continue
            combined_candidate_ids = _dedupe_strings(
                [*existing.candidate_ids, cluster.candidate_id, *signal.candidate_ids]
            )
            axis_payloads[signal.axis] = existing.model_copy(
                update={
                    "movement": _more_cautious_progression_movement(existing.movement, signal.movement),
                    "why": (
                        "multiple checkpoint candidates touched this axis during the session; progression-lift should review the combined evidence at closeout"
                        if set(combined_candidate_ids) != set(existing.candidate_ids)
                        else existing.why
                    ),
                    "candidate_ids": combined_candidate_ids,
                    "evidence_refs": _dedupe_strings([*existing.evidence_refs, *signal.evidence_refs]),
                }
            )
    return [axis_payloads[axis] for axis in order]


def _more_cautious_progression_movement(left: str, right: str) -> str:
    rank = {"advance": 1, "hold": 2, "reanchor": 3, "downgrade": 4}
    return left if rank[left] >= rank[right] else right


def _derive_session_end_recommendation(
    *,
    harvest_candidate_ids: list[str],
    progression_candidate_ids: list[str],
    upgrade_candidate_ids: list[str],
) -> Literal[
    "hold",
    "harvest",
    "progression",
    "upgrade",
    "harvest_and_progression",
    "progression_and_upgrade",
    "harvest_and_upgrade",
    "harvest_progression_and_upgrade",
]:
    if harvest_candidate_ids and progression_candidate_ids and upgrade_candidate_ids:
        return "harvest_progression_and_upgrade"
    if harvest_candidate_ids and progression_candidate_ids:
        return "harvest_and_progression"
    if progression_candidate_ids and upgrade_candidate_ids:
        return "progression_and_upgrade"
    if harvest_candidate_ids and upgrade_candidate_ids:
        return "harvest_and_upgrade"
    if progression_candidate_ids:
        return "progression"
    if upgrade_candidate_ids:
        return "upgrade"
    if harvest_candidate_ids:
        return "harvest"
    return "hold"


def _dedupe_strings(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))
