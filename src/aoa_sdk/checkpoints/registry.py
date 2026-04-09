from __future__ import annotations

import json
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, cast

from ..errors import RepoNotFound, SurfaceNotFound
from ..models import (
    CheckpointCaptureResult,
    SessionCheckpointCluster,
    SessionCheckpointHistoryEntry,
    SessionCheckpointNote,
    SessionCheckpointPromotion,
    SurfaceDetectionReport,
)
from ..surfaces import SurfacesAPI
from ..workspace.discovery import Workspace


CHECKPOINT_KINDS = (
    "manual",
    "commit",
    "verify_green",
    "pr_opened",
    "pr_merged",
    "pause",
    "owner_followthrough",
)
PROMOTION_TARGETS = ("dionysus-note", "harvest-handoff")
DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
IGNORABLE_UNTRACKED_DIRS = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
IGNORABLE_UNTRACKED_SUFFIXES = (".pyc", ".pyo", ".pyd")


class CheckpointsAPI:
    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace
        self._surfaces = SurfacesAPI(workspace)

    def append(
        self,
        *,
        repo_root: str,
        checkpoint_kind: Literal[
            "manual",
            "commit",
            "verify_green",
            "pr_opened",
            "pr_merged",
            "pause",
            "owner_followthrough",
        ],
        intent_text: str = "",
        mutation_surface: Literal["none", "code", "repo-config", "infra", "runtime", "public-share"] = "none",
        session_file: str | None = None,
        skill_report_path: str | None = None,
        surface_report: SurfaceDetectionReport | None = None,
        surface_report_path: str | None = None,
        manual_review_requested: bool = False,
    ) -> SessionCheckpointNote:
        paths = _checkpoint_paths(self.workspace, repo_root)
        if paths.note_json.exists():
            existing = SessionCheckpointNote.model_validate_json(paths.note_json.read_text(encoding="utf-8"))
            if existing.state == "closed":
                _archive_current_checkpoint(paths)

        report = surface_report or self._surfaces.detect(
            repo_root=repo_root,
            phase="checkpoint",
            intent_text=intent_text,
            mutation_surface=mutation_surface,
            session_file=session_file,
            skill_report_path=skill_report_path,
            checkpoint_kind=checkpoint_kind,
        )
        if report.phase != "checkpoint":
            raise ValueError("checkpoint append requires a checkpoint-phase surface report")
        if report.checkpoint_kind != checkpoint_kind:
            raise ValueError(
                "checkpoint append requires surface_report.checkpoint_kind to match checkpoint_kind"
            )
        report_path = (
            Path(surface_report_path).expanduser().resolve()
            if surface_report_path is not None
            else paths.surface_report
        )
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(
                {
                    "report_path": str(report_path),
                    "report": report.model_dump(mode="json"),
                },
                indent=2,
                ensure_ascii=True,
            )
            + "\n",
            encoding="utf-8",
        )
        payload = {
            "session_ref": _default_session_ref(paths, existing_note_path=paths.note_json if paths.note_json.exists() else None),
            "repo_root": str(_resolve_context_root(self.workspace, repo_root)),
            "repo_label": paths.repo_label,
            "history_entry": SessionCheckpointHistoryEntry(
                checkpoint_kind=checkpoint_kind,
                observed_at=datetime.now(UTC),
                report_ref=str(report_path),
                intent_text=intent_text,
                checkpoint_should_capture=report.checkpoint_should_capture,
                blocked_by=list(report.blocked_by),
                candidate_clusters=list(report.candidate_clusters),
                manual_review_requested=manual_review_requested,
            ).model_dump(mode="json"),
        }
        paths.jsonl.parent.mkdir(parents=True, exist_ok=True)
        with paths.jsonl.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=True) + "\n")
        return self.status(repo_root=repo_root)

    def capture_from_skill_phase(
        self,
        *,
        repo_root: str,
        phase: Literal["ingress", "pre-mutation"],
        intent_text: str = "",
        mutation_surface: Literal["none", "code", "repo-config", "infra", "runtime", "public-share"] = "none",
        session_file: str | None = None,
        skill_report_path: str | None = None,
        checkpoint_kind: Literal[
            "manual",
            "commit",
            "verify_green",
            "pr_opened",
            "pr_merged",
            "pause",
            "owner_followthrough",
        ] | None = None,
        manual_review_requested: bool = False,
        auto_capture: bool = True,
    ) -> CheckpointCaptureResult:
        if checkpoint_kind is not None:
            note = self.append(
                repo_root=repo_root,
                checkpoint_kind=checkpoint_kind,
                intent_text=intent_text,
                mutation_surface=mutation_surface,
                session_file=session_file,
                skill_report_path=skill_report_path,
                manual_review_requested=manual_review_requested,
            )
            return CheckpointCaptureResult(
                mode="explicit",
                attempted=True,
                appended=True,
                checkpoint_kind=checkpoint_kind,
                reason="explicit_request",
                note=note,
            )

        if not auto_capture:
            return CheckpointCaptureResult(
                mode="auto",
                attempted=False,
                appended=False,
                checkpoint_kind=None,
                reason="auto_disabled",
                note=None,
            )

        inferred_kind = _infer_auto_checkpoint_kind(intent_text=intent_text)
        report = self._surfaces.detect(
            repo_root=repo_root,
            phase="checkpoint",
            intent_text=intent_text,
            mutation_surface=mutation_surface,
            session_file=session_file,
            skill_report_path=skill_report_path,
            checkpoint_kind=inferred_kind,
        )
        if not report.checkpoint_should_capture:
            return CheckpointCaptureResult(
                mode="auto",
                attempted=True,
                appended=False,
                checkpoint_kind=inferred_kind,
                reason="no_checkpoint_signal",
                note=None,
            )

        note = self.append(
            repo_root=repo_root,
            checkpoint_kind=inferred_kind,
            intent_text=intent_text,
            mutation_surface=mutation_surface,
            session_file=session_file,
            skill_report_path=skill_report_path,
            surface_report=report,
            manual_review_requested=manual_review_requested,
        )
        return CheckpointCaptureResult(
            mode="auto",
            attempted=True,
            appended=True,
            checkpoint_kind=inferred_kind,
            reason="checkpoint_signal",
            note=note,
        )

    def status(self, *, repo_root: str) -> SessionCheckpointNote:
        paths = _checkpoint_paths(self.workspace, repo_root)
        if not paths.jsonl.exists():
            raise SurfaceNotFound(f"no checkpoint note exists yet for {paths.repo_label}")

        note = _build_checkpoint_note(paths)
        paths.note_json.parent.mkdir(parents=True, exist_ok=True)
        paths.note_json.write_text(note.model_dump_json(indent=2) + "\n", encoding="utf-8")
        paths.note_md.write_text(_render_checkpoint_note_markdown(note, repo_label=paths.repo_label), encoding="utf-8")
        return note

    def promote(
        self,
        *,
        repo_root: str,
        target: Literal["dionysus-note", "harvest-handoff"],
    ) -> SessionCheckpointPromotion:
        if target not in PROMOTION_TARGETS:
            raise ValueError(f"unsupported target {target!r}")

        paths = _checkpoint_paths(self.workspace, repo_root)
        note = self.status(repo_root=repo_root)
        if not note.candidate_clusters:
            raise SurfaceNotFound("cannot promote an empty checkpoint note")

        new_state: Literal["collecting", "reviewable", "promoted", "closed"]
        if target == "dionysus-note":
            output_refs = _promote_to_dionysus(self.workspace, paths=paths, note=note)
            new_state = "promoted"
            note.review_status = "reviewed"
        else:
            output_refs = _write_harvest_handoff(paths=paths, note=note)
            new_state = "closed"
            note.review_status = "reviewed"

        note.state = new_state  # type: ignore[assignment]
        note.evidence_refs = list(dict.fromkeys([*note.evidence_refs, *output_refs]))
        note.next_owner_moves = _dedupe_strings(
            [
                *note.next_owner_moves,
                "use the explicit session-harvest family after reviewed closeout",
            ]
        )
        paths.note_json.write_text(note.model_dump_json(indent=2) + "\n", encoding="utf-8")
        paths.note_md.write_text(_render_checkpoint_note_markdown(note, repo_label=paths.repo_label), encoding="utf-8")

        return SessionCheckpointPromotion(
            session_ref=note.session_ref,
            target=target,
            promoted_at=datetime.now(UTC),
            source_note_ref=str(paths.note_json),
            output_refs=output_refs,
            resulting_state=new_state,
        )


class _CheckpointPaths:
    def __init__(self, *, root: Path, repo_label: str, current_dir: Path, surface_report: Path) -> None:
        self.root = root
        self.repo_label = repo_label
        self.current_dir = current_dir
        self.jsonl = current_dir / "checkpoint-note.jsonl"
        self.note_json = current_dir / "checkpoint-note.json"
        self.note_md = current_dir / "checkpoint-note.md"
        self.harvest_handoff = current_dir / "harvest-handoff.json"
        self.surface_report = surface_report


def _checkpoint_paths(workspace: Workspace, repo_root: str) -> _CheckpointPaths:
    repo_label = _resolve_context_label(workspace, repo_root)
    sdk_root = workspace.repo_path("aoa-sdk")
    current_dir = sdk_root / ".aoa" / "session-growth" / "current" / repo_label
    surface_report = sdk_root / ".aoa" / "surface-detection" / f"{repo_label}.checkpoint.latest.json"
    return _CheckpointPaths(root=sdk_root, repo_label=repo_label, current_dir=current_dir, surface_report=surface_report)


def _resolve_context_root(workspace: Workspace, repo_root: str) -> Path:
    resolved_repo_root = Path(repo_root).expanduser()
    if not resolved_repo_root.is_absolute():
        return (workspace.root / resolved_repo_root).resolve()
    return resolved_repo_root.resolve()


def _resolve_context_label(workspace: Workspace, repo_root: str) -> str:
    resolved_repo_root = _resolve_context_root(workspace, repo_root)
    return "workspace" if resolved_repo_root == workspace.federation_root else resolved_repo_root.name


def _default_session_ref(paths: _CheckpointPaths, *, existing_note_path: Path | None) -> str:
    if existing_note_path and existing_note_path.exists():
        try:
            existing = SessionCheckpointNote.model_validate_json(existing_note_path.read_text(encoding="utf-8"))
            if existing.session_ref:
                return existing.session_ref
        except Exception:
            pass
    date_str = datetime.now(UTC).date().isoformat()
    return f"session:{date_str}-{paths.repo_label}-checkpoint-growth"


def _infer_auto_checkpoint_kind(
    *,
    intent_text: str,
) -> Literal["manual", "commit", "verify_green", "pr_opened", "pr_merged", "pause", "owner_followthrough"]:
    normalized = re.sub(r"[\s_-]+", " ", intent_text.strip().lower())
    if any(token in normalized for token in ("owner follow through", "owner handoff", "follow through")):
        return "owner_followthrough"
    if any(token in normalized for token in ("pull request merged", "pr merged", "merged pr", "merge complete")):
        return "pr_merged"
    if any(token in normalized for token in ("pull request", "open pr", "pr open", "review thread")):
        return "pr_opened"
    if any(
        token in normalized
        for token in (
            "verify green",
            "green verify",
            "all green",
            "tests green",
            "verified",
            "verification",
            "verify",
        )
    ):
        return "verify_green"
    if any(token in normalized for token in ("resume later", "continue later", "pick up later", "pause")):
        return "pause"
    if "checkpoint" in normalized or "commit" in normalized:
        return "commit"
    return "commit"


def _archive_current_checkpoint(paths: _CheckpointPaths) -> None:
    archive_root = paths.root / ".aoa" / "session-growth" / "archive"
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    archive_dir = archive_root / f"{paths.repo_label}-{timestamp}"
    archive_dir.mkdir(parents=True, exist_ok=True)
    for source in (paths.jsonl, paths.note_json, paths.note_md, paths.harvest_handoff):
        if source.exists():
            source.rename(archive_dir / source.name)


def _build_checkpoint_note(paths: _CheckpointPaths) -> SessionCheckpointNote:
    entries: list[SessionCheckpointHistoryEntry] = []
    session_ref: str | None = None
    repo_scope: set[str] = {paths.repo_label}
    for raw_line in paths.jsonl.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        payload = json.loads(line)
        if session_ref is None and isinstance(payload.get("session_ref"), str):
            session_ref = payload["session_ref"]
        entry = SessionCheckpointHistoryEntry.model_validate(payload["history_entry"])
        entries.append(entry)
    if session_ref is None:
        session_ref = _default_session_ref(paths, existing_note_path=None)

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
        except Exception:
            pass

    cluster_map: dict[tuple[str, str], SessionCheckpointCluster] = {}
    all_blocked: set[str] = set()
    all_evidence: set[str] = set(existing_evidence_refs)
    next_owner_moves: set[str] = set(existing_next_owner_moves)
    manual_review_requested = False
    has_owner_followthrough = False

    for entry in entries:
        if entry.manual_review_requested:
            manual_review_requested = True
        if entry.checkpoint_kind == "owner_followthrough":
            has_owner_followthrough = True
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
            merged_evidence = _dedupe_strings([*(existing.evidence_refs if existing else []), *cluster.evidence_refs])
            merged_moves = _dedupe_strings([*(existing.next_owner_moves if existing else []), *cluster.next_owner_moves])
            merged_promote_if = _dedupe_strings([*(existing.promote_if if existing else []), *cluster.promote_if])
            merged_blocked = _dedupe_strings([*(existing.blocked_by if existing else []), *cluster.blocked_by])
            merged_session_end_targets = _dedupe_session_end_targets(
                [*(existing.session_end_targets if existing else []), *cluster_session_end_targets]
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
                promote_if=merged_promote_if,
                defer_reason=cluster.defer_reason or (existing.defer_reason if existing else None),
                blocked_by=merged_blocked,
                next_owner_moves=merged_moves,
            )
            all_evidence.update(merged_evidence)
            next_owner_moves.update(merged_moves)

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
    upgrade_candidate_ids = [
        cluster.candidate_id for cluster in candidate_clusters if "upgrade" in cluster.session_end_targets
    ]
    stats_refresh_recommended = bool(candidate_clusters)
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
        state=state,
        repo_scope=sorted(repo_scope),
        checkpoint_history=entries,
        candidate_clusters=candidate_clusters,
        promotion_recommendation=recommendation,
        carry_until_session_closeout=state not in {"promoted", "closed"},
        session_end_recommendation=_derive_session_end_recommendation(
            harvest_candidate_ids=harvest_candidate_ids,
            upgrade_candidate_ids=upgrade_candidate_ids,
        ),
        harvest_candidate_ids=harvest_candidate_ids,
        upgrade_candidate_ids=upgrade_candidate_ids,
        stats_refresh_recommended=stats_refresh_recommended,
        blocked_by=sorted(all_blocked),
        review_status="reviewed" if existing_review_status == "reviewed" else "unreviewed",
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
                    {"at reviewed closeout, review upgrade candidates before any owner-layer promotion"}
                    if upgrade_candidate_ids
                    else set()
                ),
            }
        ),
    )
    return note


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
    values: list[Literal["harvest", "upgrade"]],
) -> list[Literal["harvest", "upgrade"]]:
    deduped: list[Literal["harvest", "upgrade"]] = []
    for value in values:
        if value not in deduped:
            deduped.append(value)
    return deduped


def _legacy_session_end_targets_for_candidate_kind(
    candidate_kind: str,
) -> list[Literal["harvest", "upgrade"]]:
    targets: list[Literal["harvest", "upgrade"]] = ["harvest"]
    if candidate_kind in {"route", "pattern", "proof", "recall", "role"}:
        targets.append("upgrade")
    return targets


def _derive_session_end_recommendation(
    *,
    harvest_candidate_ids: list[str],
    upgrade_candidate_ids: list[str],
) -> Literal["hold", "harvest", "upgrade", "harvest_and_upgrade"]:
    if harvest_candidate_ids and upgrade_candidate_ids:
        return "harvest_and_upgrade"
    if upgrade_candidate_ids:
        return "upgrade"
    if harvest_candidate_ids:
        return "harvest"
    return "hold"


def _render_checkpoint_note_markdown(note: SessionCheckpointNote, *, repo_label: str) -> str:
    lines = [
        "# Session Checkpoint Note",
        "",
        f"Session ref: `{note.session_ref}`",
        f"Repo label: `{repo_label}`",
        f"State: `{note.state}`",
        f"Review status: `{note.review_status}`",
        f"Promotion recommendation: `{note.promotion_recommendation}`",
        f"Carry until session closeout: `{'yes' if note.carry_until_session_closeout else 'no'}`",
        f"Session-end recommendation: `{note.session_end_recommendation}`",
        f"Stats refresh recommended at closeout: `{'yes' if note.stats_refresh_recommended else 'no'}`",
        "",
        "## Repo Scope",
        "",
    ]
    lines.extend(f"- `{scope}`" for scope in note.repo_scope)
    if note.harvest_candidate_ids:
        lines.extend(["", "## Harvest Candidates", ""])
        lines.extend(f"- `{candidate_id}`" for candidate_id in note.harvest_candidate_ids)
    if note.upgrade_candidate_ids:
        lines.extend(["", "## Upgrade Candidates", ""])
        lines.extend(f"- `{candidate_id}`" for candidate_id in note.upgrade_candidate_ids)
    lines.extend(["", "## Candidate Clusters", ""])
    if not note.candidate_clusters:
        lines.append("- none")
    for cluster in note.candidate_clusters:
        lines.extend(
            [
                f"### {cluster.display_name}",
                "",
                f"- candidate id: `{cluster.candidate_id}`",
                f"- kind: `{cluster.candidate_kind}`",
                f"- owner hint: `{cluster.owner_hint}`",
                f"- checkpoint hits: `{cluster.checkpoint_hits}`",
                f"- confidence: `{cluster.confidence}`",
                f"- review status: `{cluster.review_status}`",
                f"- source surface: `{cluster.source_surface_ref}`",
                f"- session-end targets: {', '.join(f'`{target}`' for target in cluster.session_end_targets) or '`none`'}",
            ]
        )
        if cluster.blocked_by:
            lines.append("- blocked by: " + ", ".join(f"`{item}`" for item in cluster.blocked_by))
        if cluster.defer_reason:
            lines.append(f"- defer reason: {cluster.defer_reason}")
        if cluster.evidence_refs:
            lines.append("- evidence refs:")
            lines.extend(f"  - `{ref}`" for ref in cluster.evidence_refs)
        if cluster.promote_if:
            lines.append("- promote if:")
            lines.extend(f"  - {item}" for item in cluster.promote_if)
        if cluster.next_owner_moves:
            lines.append("- next owner moves:")
            lines.extend(f"  - {item}" for item in cluster.next_owner_moves)
        lines.append("")
    lines.extend(["## Checkpoint History", ""])
    for entry in note.checkpoint_history:
        lines.append(
            f"- `{entry.checkpoint_kind}` at `{entry.observed_at.isoformat()}` -> "
            + (", ".join(cluster.candidate_id for cluster in entry.candidate_clusters) or "no surviving candidates")
        )
    if note.blocked_by:
        lines.extend(["", "## Blocked By", ""])
        lines.extend(f"- `{item}`" for item in note.blocked_by)
    if note.next_owner_moves:
        lines.extend(["", "## Next Owner Moves", ""])
        lines.extend(f"- {item}" for item in note.next_owner_moves)
    return "\n".join(lines).rstrip() + "\n"


def _promote_to_dionysus(workspace: Workspace, *, paths: _CheckpointPaths, note: SessionCheckpointNote) -> list[str]:
    try:
        dionysus_root = workspace.repo_path("Dionysus")
    except RepoNotFound as exc:
        raise SurfaceNotFound("Dionysus workspace is not available for checkpoint-note promotion") from exc
    _ensure_repo_not_dirty(dionysus_root, repo_name="Dionysus")

    audits_dir = dionysus_root / "reports" / "ecosystem-audits"
    audits_dir.mkdir(parents=True, exist_ok=True)
    date_str = _date_from_session_ref(note.session_ref) or datetime.now(UTC).date().isoformat()
    stem = f"{date_str}.{paths.repo_label}.checkpoint-note"
    json_path = audits_dir / f"{stem}.json"
    md_path = audits_dir / f"{stem}.md"
    source_note_ref = f"repo:aoa-sdk/.aoa/session-growth/current/{paths.repo_label}/checkpoint-note.json"
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


def _write_harvest_handoff(*, paths: _CheckpointPaths, note: SessionCheckpointNote) -> list[str]:
    payload = {
        "schema_version": 1,
        "handoff_type": "checkpoint_harvest_handoff",
        "session_ref": note.session_ref,
        "source_note_ref": str(paths.note_json),
        "candidate_clusters": [cluster.model_dump(mode="json") for cluster in note.candidate_clusters],
        "harvest_candidate_ids": note.harvest_candidate_ids,
        "upgrade_candidate_ids": note.upgrade_candidate_ids,
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


def _ensure_repo_not_dirty(repo_root: Path, *, repo_name: str) -> None:
    if not (repo_root / ".git").exists():
        return
    result = subprocess.run(
        ["git", "-C", str(repo_root), "status", "--porcelain"],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return
    meaningful_lines = [
        line
        for line in result.stdout.splitlines()
        if line.strip() and not _is_ignorable_untracked_status(line, repo_root=repo_root)
    ]
    if meaningful_lines:
        raise SurfaceNotFound(f"{repo_name} is dirty; keep the reviewed promotion on the local checkpoint note for now")


def _is_ignorable_untracked_status(line: str, *, repo_root: Path) -> bool:
    if not line.startswith("?? "):
        return False
    raw_path = line[3:].strip()
    candidate = repo_root / raw_path.rstrip("/\\")
    if candidate.is_dir():
        return _directory_contains_only_ignorable_cache(candidate)
    return _is_ignorable_cache_path(raw_path)


def _directory_contains_only_ignorable_cache(directory: Path) -> bool:
    for path in directory.rglob("*"):
        if path.is_dir():
            continue
        if not _is_ignorable_cache_path(str(path.relative_to(directory))):
            return False
    return True


def _is_ignorable_cache_path(raw_path: str) -> bool:
    normalized = raw_path.replace("\\", "/")
    parts = [part for part in normalized.split("/") if part]
    if any(part in IGNORABLE_UNTRACKED_DIRS for part in parts):
        return True
    return normalized.endswith(IGNORABLE_UNTRACKED_SUFFIXES)


def _date_from_session_ref(session_ref: str) -> str | None:
    match = DATE_RE.search(session_ref)
    return match.group(1) if match else None


def _dedupe_strings(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))
