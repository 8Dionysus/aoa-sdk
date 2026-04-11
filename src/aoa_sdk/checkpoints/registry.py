from __future__ import annotations

import json
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, TypedDict, cast

from ..errors import RepoNotFound, SurfaceNotFound
from ..loaders import load_json, write_json
from ..models import (
    CheckpointAfterCommitReport,
    CheckpointCloseoutContext,
    CheckpointCloseoutExecutionReport,
    CheckpointCaptureResult,
    CheckpointHookInstallResult,
    CheckpointHookStatus,
    CloseoutContextCandidateMap,
    CloseoutExecutionStep,
    ProgressionAxisSignal,
    SessionCheckpointAgentReview,
    SessionEndSkillTarget,
    SessionCheckpointCluster,
    SessionCheckpointHistoryEntry,
    SessionCheckpointNote,
    SessionCheckpointPromotion,
    SurfaceCloseoutHandoff,
    SurfaceDetectionReport,
)
from ..skills.discovery import SkillsAPI
from ..skills.session import ensure_session, probe_session, resolve_session_file, save_session
from ..surfaces import SurfacesAPI
from ..workspace.discovery import Workspace
from ..workspace.roots import KNOWN_REPOS


CHECKPOINT_KINDS = (
    "manual",
    "commit",
    "verify_green",
    "pr_opened",
    "pr_merged",
    "pause",
    "owner_followthrough",
)
POST_COMMIT_CHECKPOINT_KINDS = ("auto", "commit", "owner_followthrough")
OWNER_MUTABLE_REPOS = tuple(repo for repo in KNOWN_REPOS if repo != "8Dionysus")
POST_COMMIT_HOOK_TEMPLATE_VERSION = "aoa-sdk-post-commit-hook-v2"
POST_COMMIT_HOOK_MARKER = "# aoa-sdk checkpoint post-commit hook v2"
PROMOTION_TARGETS = ("dionysus-note", "harvest-handoff")
DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
SESSION_REF_RE = re.compile(r'"session_ref"\s*:\s*"([^"]+)"|session_ref:\s*`?([^`\s]+)`?|Session ref:\s*`?([^`\n]+)`?')
SESSION_REF_TIMESTAMP_FORMAT = "%Y-%m-%dT%H-%M-%S-%fZ"
IGNORABLE_UNTRACKED_DIRS = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
IGNORABLE_UNTRACKED_SUFFIXES = (".pyc", ".pyo", ".pyd")
CODEX_TRACE_TEXT_ITEM_TYPES = {"input_text", "output_text"}
CODEX_TRACE_MAX_CHARS = 120_000
CODEX_TRACE_MAX_CHUNK_CHARS = 3_000
SESSION_END_SKILL_ORDER = (
    "aoa-session-donor-harvest",
    "aoa-session-progression-lift",
    "aoa-quest-harvest",
)
ALLOWED_OWNER_REPOS = {
    "aoa-techniques",
    "aoa-skills",
    "aoa-evals",
    "aoa-memo",
    "aoa-playbooks",
    "aoa-agents",
}
DEFAULT_OWNER_BY_CANDIDATE_KIND = {
    "route": "aoa-playbooks",
    "pattern": "aoa-techniques",
    "proof": "aoa-evals",
    "recall": "aoa-memo",
    "role": "aoa-agents",
    "risk": "aoa-evals",
    "growth": "aoa-skills",
}
ABSTRACTION_SHAPE_BY_OWNER = {
    "aoa-techniques": "technique",
    "aoa-skills": "skill",
    "aoa-evals": "eval",
    "aoa-memo": "memo",
    "aoa-playbooks": "playbook",
    "aoa-agents": "agent",
}
DEFAULT_ARTIFACT_BY_OWNER = {
    "aoa-techniques": "techniques/{slug}/TECHNIQUE.md",
    "aoa-skills": "skills/{slug}/SKILL.md",
    "aoa-evals": "evals/{slug}/EVAL.md",
    "aoa-memo": "memo/{slug}.md",
    "aoa-playbooks": "playbooks/{slug}/PLAYBOOK.md",
    "aoa-agents": "agents/{slug}/AGENT.md",
}
QUEST_PROMOTION_VERDICT_BY_OWNER = {
    "aoa-skills": "promote_to_skill",
    "aoa-evals": "promote_to_eval",
    "aoa-memo": "promote_to_memo",
    "aoa-playbooks": "promote_to_playbook",
    "aoa-agents": "promote_to_agent",
    "aoa-techniques": "promote_to_technique",
}
CHECKPOINT_CLOSEOUT_AUTHORITY_CONTRACT: dict[str, object] = {
    "contract": "reviewed_artifact_primary_checkpoint_hints_provisional",
    "bridge_output": "mechanical_artifact_build",
    "checkpoint_notes": "focus_hints_only_not_final_authority",
    "reviewed_artifact": "primary_closeout_evidence",
    "agent_skill_application": "required_for_final_session_analysis",
}


class DonorHarvestOutputs(TypedDict):
    packet: dict[str, object]
    artifact_refs: list[str]
    receipt_refs: list[str]
    reviewed_tokens: set[str]
    receipt_payloads: list[dict[str, object]]


class ProgressionLiftOutputs(TypedDict):
    packet: dict[str, object]
    artifact_refs: list[str]
    receipt_refs: list[str]


class QuestHarvestOutputs(TypedDict):
    packet: dict[str, object]
    artifact_refs: list[str]
    receipt_refs: list[str]


def _local_timestamp_parts(now_utc: datetime | None = None) -> tuple[datetime, str, str]:
    canonical_utc = now_utc or datetime.now(UTC)
    local_now = canonical_utc.astimezone()
    local_tz = local_now.tzname() or local_now.strftime("%z")
    return canonical_utc, local_now.isoformat(), local_tz


def _coerce_datetime(value: datetime | str | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    return datetime.fromisoformat(normalized)


def _with_local_timestamp_fallback(
    *,
    utc_value: datetime | str | None,
    local_value: str | None,
    tz_name: str | None,
) -> tuple[str | None, str | None]:
    if local_value is not None and tz_name is not None:
        return local_value, tz_name
    parsed = _coerce_datetime(utc_value)
    if parsed is None:
        return local_value, tz_name
    local_now = parsed.astimezone()
    return local_value or local_now.isoformat(), tz_name or local_now.tzname() or local_now.strftime("%z")


def _dict_records(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    records: list[dict[str, object]] = []
    for item in value:
        if isinstance(item, dict):
            records.append(cast(dict[str, object], item))
    return records


def _string_field(mapping: dict[str, object], key: str) -> str | None:
    value = mapping.get(key)
    return value if isinstance(value, str) else None


def _utc_timestamp(now_utc: datetime | None = None) -> str:
    canonical_utc = now_utc or datetime.now(UTC)
    return canonical_utc.isoformat().replace("+00:00", "Z")


def _observed_timestamp_fields(now_utc: datetime | None = None) -> dict[str, str]:
    canonical_utc, observed_at_local, observed_tz = _local_timestamp_parts(now_utc)
    return {
        "observed_at": _utc_timestamp(canonical_utc),
        "observed_at_local": observed_at_local,
        "observed_tz": observed_tz,
    }


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
        commit_sha: str | None = None,
        commit_short_sha: str | None = None,
        agent_review_status: Literal["not_required", "pending", "reviewed"] = "not_required",
        agent_review_ref: str | None = None,
    ) -> SessionCheckpointNote:
        runtime_session_id, runtime_session_created_at = _ensure_checkpoint_runtime_session(
            workspace=self.workspace,
            session_file=session_file,
        )
        paths = _resolve_runtime_checkpoint_paths(
            self.workspace,
            repo_root=repo_root,
            runtime_session_id=runtime_session_id,
            migrate_legacy=True,
        )
        existing_note = _load_checkpoint_note(paths.note_json) if paths.note_json.exists() else None
        if paths.note_json.exists():
            if existing_note is not None and _should_rotate_checkpoint_note(
                existing_note,
                runtime_session_id=runtime_session_id,
            ):
                _archive_current_checkpoint(paths)
                existing_note = None

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
        observed_at, observed_at_local, observed_tz = _local_timestamp_parts()
        payload = {
            "session_ref": _default_session_ref(
                paths,
                existing_note=existing_note,
                runtime_session_id=runtime_session_id,
            ),
            "runtime_session_id": runtime_session_id,
            "runtime_session_created_at": (
                runtime_session_created_at.isoformat().replace("+00:00", "Z")
                if runtime_session_created_at is not None
                else None
            ),
            "repo_root": str(_resolve_context_root(self.workspace, repo_root)),
            "repo_label": paths.repo_label,
            "history_entry": SessionCheckpointHistoryEntry(
                checkpoint_kind=checkpoint_kind,
                observed_at=observed_at,
                observed_at_local=observed_at_local,
                observed_tz=observed_tz,
                report_ref=str(report_path),
                intent_text=intent_text,
                checkpoint_should_capture=report.checkpoint_should_capture,
                blocked_by=list(report.blocked_by),
                candidate_clusters=list(report.candidate_clusters),
                manual_review_requested=manual_review_requested,
                commit_sha=commit_sha,
                commit_short_sha=commit_short_sha,
                agent_review_status=agent_review_status,
                agent_review_ref=agent_review_ref,
            ).model_dump(mode="json"),
        }
        paths.jsonl.parent.mkdir(parents=True, exist_ok=True)
        with paths.jsonl.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=True) + "\n")
        return self.status(repo_root=repo_root, session_file=session_file)

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
            captured_at, captured_at_local, captured_tz = _local_timestamp_parts()
            note = self.append(
                repo_root=repo_root,
                checkpoint_kind=checkpoint_kind,
                intent_text=intent_text,
                mutation_surface=mutation_surface,
                session_file=session_file,
                skill_report_path=skill_report_path,
                manual_review_requested=manual_review_requested,
            )
            session_end_targets = _derive_session_end_skill_targets(note)
            return CheckpointCaptureResult(
                mode="explicit",
                attempted=True,
                appended=True,
                checkpoint_kind=checkpoint_kind,
                captured_at=captured_at,
                captured_at_local=captured_at_local,
                captured_tz=captured_tz,
                reason="explicit_request",
                note_ref=_checkpoint_note_ref_for_capture(
                    self.workspace,
                    repo_root,
                    runtime_session_id=note.runtime_session_id,
                ),
                session_end_skill_targets=session_end_targets,
                session_end_next_honest_move=_derive_session_end_next_honest_move(
                    note=note,
                    session_end_targets=session_end_targets,
                ),
                harvest_candidate_ids=list(note.harvest_candidate_ids),
                progression_candidate_ids=list(note.progression_candidate_ids),
                upgrade_candidate_ids=list(note.upgrade_candidate_ids),
                progression_axis_signals=list(note.progression_axis_signals),
                stats_refresh_recommended=note.stats_refresh_recommended,
                note=note,
            )

        if not auto_capture:
            return _checkpoint_capture_result_without_append(
                self,
                repo_root=repo_root,
                session_file=session_file,
                reason="auto_disabled",
                attempted=False,
                checkpoint_kind=None,
                read_only=True,
            )

        if phase == "ingress" and mutation_surface == "none":
            return _checkpoint_capture_result_without_append(
                self,
                repo_root=repo_root,
                session_file=session_file,
                reason="no_checkpoint_signal",
                attempted=True,
                checkpoint_kind=None,
                read_only=True,
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
            return _checkpoint_capture_result_without_append(
                self,
                repo_root=repo_root,
                session_file=session_file,
                reason="no_checkpoint_signal",
                attempted=True,
                checkpoint_kind=inferred_kind,
                read_only=False,
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
        session_end_targets = _derive_session_end_skill_targets(note)
        captured_at, captured_at_local, captured_tz = _local_timestamp_parts()
        return CheckpointCaptureResult(
            mode="auto",
            attempted=True,
            appended=True,
            checkpoint_kind=inferred_kind,
            captured_at=captured_at,
            captured_at_local=captured_at_local,
            captured_tz=captured_tz,
            reason="checkpoint_signal",
            note_ref=_checkpoint_note_ref_for_capture(
                self.workspace,
                repo_root,
                runtime_session_id=note.runtime_session_id,
            ),
            session_end_skill_targets=session_end_targets,
            session_end_next_honest_move=_derive_session_end_next_honest_move(
                note=note,
                session_end_targets=session_end_targets,
            ),
            harvest_candidate_ids=list(note.harvest_candidate_ids),
            progression_candidate_ids=list(note.progression_candidate_ids),
            upgrade_candidate_ids=list(note.upgrade_candidate_ids),
            progression_axis_signals=list(note.progression_axis_signals),
            stats_refresh_recommended=note.stats_refresh_recommended,
            note=note,
        )

    def after_commit(
        self,
        *,
        repo_root: str,
        commit_ref: str = "HEAD",
        session_file: str | None = None,
        checkpoint_kind: Literal["auto", "commit", "owner_followthrough"] = "auto",
    ) -> CheckpointAfterCommitReport:
        if checkpoint_kind not in POST_COMMIT_CHECKPOINT_KINDS:
            raise ValueError(
                "post-commit checkpoint kind must be auto, commit, or owner_followthrough"
            )
        repo_root_path = _resolve_context_root(self.workspace, repo_root)
        repo_label = _resolve_context_label(self.workspace, repo_root)
        session_path = resolve_session_file(self.workspace, session_file)
        runtime_session_id: str | None = None
        runtime_session_created_at: datetime | None = None
        skill_report_path: str | None = None
        surface_report_path: str | None = None
        note_ref: str | None = None
        commit_metadata: dict[str, Any] = {
            "commit_sha": None,
            "commit_short_sha": None,
            "commit_subject": None,
            "commit_body": None,
            "changed_paths": [],
        }

        try:
            session_path, runtime_session = probe_session(self.workspace, session_file)
            commit_metadata = _read_git_commit_metadata(repo_root_path, commit_ref)
            captured_at, captured_at_local, captured_tz = _local_timestamp_parts()
            if runtime_session is None:
                resolved_checkpoint_kind = _resolve_after_commit_checkpoint_kind(
                    checkpoint_kind=checkpoint_kind,
                    commit_subject=commit_metadata["commit_subject"],
                    commit_body=commit_metadata["commit_body"],
                    existing_note=None,
                )
                mutation_surface = _after_commit_mutation_surface(resolved_checkpoint_kind)
                report_path = _post_commit_status_path(self.workspace, repo_label)
                report = CheckpointAfterCommitReport(
                    status="skipped_no_active_session",
                    repo_root=str(repo_root_path),
                    repo_label=repo_label,
                    report_path=str(report_path),
                    commit_ref=commit_ref,
                    commit_sha=commit_metadata["commit_sha"],
                    commit_short_sha=commit_metadata["commit_short_sha"],
                    commit_subject=commit_metadata["commit_subject"],
                    commit_body=commit_metadata["commit_body"],
                    changed_paths=list(commit_metadata["changed_paths"]),
                    checkpoint_kind=resolved_checkpoint_kind,
                    mutation_surface=mutation_surface,
                    captured_at=captured_at,
                    captured_at_local=captured_at_local,
                    captured_tz=captured_tz,
                    session_file=str(session_path),
                )
                _write_after_commit_report(report_path, report)
                return report

            runtime_session_id = runtime_session.session_id
            runtime_session_created_at = runtime_session.created_at.astimezone(UTC)
            paths = _resolve_runtime_checkpoint_paths(
                self.workspace,
                repo_root=repo_root,
                runtime_session_id=runtime_session_id,
                migrate_legacy=True,
            )
            report_path = paths.post_commit_report
            session_file_ref = str(session_path)
            existing_note = _load_checkpoint_note(paths.note_json) if paths.note_json.exists() else None
            resolved_checkpoint_kind = _resolve_after_commit_checkpoint_kind(
                checkpoint_kind=checkpoint_kind,
                commit_subject=commit_metadata["commit_subject"],
                commit_body=commit_metadata["commit_body"],
                existing_note=existing_note,
            )
            mutation_surface = _after_commit_mutation_surface(resolved_checkpoint_kind)
            intent_text = _after_commit_intent(
                commit_short_sha=commit_metadata["commit_short_sha"],
                commit_subject=commit_metadata["commit_subject"],
                checkpoint_kind=resolved_checkpoint_kind,
            )

            if existing_note is not None and existing_note.state in {"closed", "promoted"}:
                is_followthrough = resolved_checkpoint_kind == "owner_followthrough"
                report = CheckpointAfterCommitReport(
                    status=(
                        "recorded_closed_session_followthrough"
                        if is_followthrough
                        else "skipped_closed_session"
                    ),
                    repo_root=str(repo_root_path),
                    repo_label=repo_label,
                    report_path=str(report_path),
                    commit_ref=commit_ref,
                    commit_sha=commit_metadata["commit_sha"],
                    commit_short_sha=commit_metadata["commit_short_sha"],
                    commit_subject=commit_metadata["commit_subject"],
                    commit_body=commit_metadata["commit_body"],
                    changed_paths=list(commit_metadata["changed_paths"]),
                    checkpoint_kind=resolved_checkpoint_kind,
                    mutation_surface=mutation_surface,
                    manual_review_requested=False,
                    captured_at=captured_at,
                    captured_at_local=captured_at_local,
                    captured_tz=captured_tz,
                    session_file=session_file_ref,
                    runtime_session_id=runtime_session_id,
                    runtime_session_created_at=runtime_session_created_at,
                    note_ref=_checkpoint_note_ref_for_capture(
                        self.workspace,
                        repo_root,
                        runtime_session_id=runtime_session_id,
                    ),
                    error_text=(
                        f"checkpoint note is {existing_note.state}; "
                        "owner follow-through was recorded without mutating the closed note"
                        if is_followthrough
                        else f"checkpoint note is {existing_note.state}; start a new runtime session or use owner_followthrough"
                    ),
                )
                _write_after_commit_report(report_path, report)
                return report

            skill_report = SkillsAPI(self.workspace).dispatch(
                repo_root=repo_root,
                phase="checkpoint",
                intent_text=intent_text,
                mutation_surface=mutation_surface,
                session_file=session_file_ref,
            )
            skill_report_path = str(_checkpoint_skill_report_path(self.workspace, repo_root))
            _write_skill_detection_report(
                Path(skill_report_path),
                skill_report.model_dump(mode="json"),
            )

            surface_report = self._surfaces.detect(
                repo_root=repo_root,
                phase="checkpoint",
                intent_text=intent_text,
                mutation_surface=mutation_surface,
                session_file=session_file_ref,
                skill_report_path=skill_report_path,
                checkpoint_kind=resolved_checkpoint_kind,
            )
            surface_report_path = str(paths.surface_report)
            note = self.append(
                repo_root=repo_root,
                checkpoint_kind=resolved_checkpoint_kind,
                intent_text=intent_text,
                mutation_surface=mutation_surface,
                session_file=session_file_ref,
                skill_report_path=skill_report_path,
                surface_report=surface_report,
                surface_report_path=surface_report_path,
                manual_review_requested=True,
                commit_sha=commit_metadata["commit_sha"],
                commit_short_sha=commit_metadata["commit_short_sha"],
                agent_review_status="pending",
            )
            note_ref = _checkpoint_note_ref_for_capture(
                self.workspace,
                repo_root,
                runtime_session_id=note.runtime_session_id,
            )
            report = CheckpointAfterCommitReport(
                status="captured",
                repo_root=str(repo_root_path),
                repo_label=repo_label,
                report_path=str(report_path),
                commit_ref=commit_ref,
                commit_sha=commit_metadata["commit_sha"],
                commit_short_sha=commit_metadata["commit_short_sha"],
                commit_subject=commit_metadata["commit_subject"],
                commit_body=commit_metadata["commit_body"],
                changed_paths=list(commit_metadata["changed_paths"]),
                checkpoint_kind=resolved_checkpoint_kind,
                mutation_surface=mutation_surface,
                captured_at=captured_at,
                captured_at_local=captured_at_local,
                captured_tz=captured_tz,
                session_file=session_file_ref,
                runtime_session_id=runtime_session_id,
                runtime_session_created_at=runtime_session_created_at,
                skill_report_path=skill_report_path,
                surface_report_path=surface_report_path,
                note_ref=note_ref,
                agent_review_required=True,
                agent_review_status="pending",
                agent_review_command=_agent_review_command(
                    repo_root=str(repo_root_path),
                    commit_ref=commit_metadata["commit_sha"] or commit_ref,
                    workspace_root=str(self.workspace.federation_root),
                ),
            )
            _write_after_commit_report(report_path, report)
            return report
        except Exception as exc:
            captured_at, captured_at_local, captured_tz = _local_timestamp_parts()
            failed_checkpoint_kind = _resolve_after_commit_checkpoint_kind(
                checkpoint_kind=checkpoint_kind,
                commit_subject=commit_metadata["commit_subject"],
                commit_body=commit_metadata["commit_body"],
                existing_note=None,
            )
            report_path = (
                _resolve_runtime_checkpoint_paths(
                    self.workspace,
                    repo_root=repo_root,
                    runtime_session_id=runtime_session_id,
                    migrate_legacy=True,
                ).post_commit_report
                if runtime_session_id is not None
                else _post_commit_status_path(self.workspace, repo_label)
            )
            report = CheckpointAfterCommitReport(
                status="failed",
                repo_root=str(repo_root_path),
                repo_label=repo_label,
                report_path=str(report_path),
                commit_ref=commit_ref,
                commit_sha=commit_metadata["commit_sha"],
                commit_short_sha=commit_metadata["commit_short_sha"],
                commit_subject=commit_metadata["commit_subject"],
                commit_body=commit_metadata["commit_body"],
                changed_paths=list(commit_metadata["changed_paths"]),
                checkpoint_kind=failed_checkpoint_kind,
                mutation_surface=_after_commit_mutation_surface(failed_checkpoint_kind),
                captured_at=captured_at,
                captured_at_local=captured_at_local,
                captured_tz=captured_tz,
                session_file=str(session_path),
                runtime_session_id=runtime_session_id,
                runtime_session_created_at=runtime_session_created_at,
                skill_report_path=skill_report_path,
                surface_report_path=surface_report_path,
                note_ref=note_ref,
                error_text=str(exc),
            )
            _write_after_commit_report(report_path, report)
            if runtime_session_id is not None:
                _write_after_commit_report(_post_commit_status_path(self.workspace, repo_label), report)
            return report

    def review_note(
        self,
        *,
        repo_root: str,
        commit_ref: str = "HEAD",
        summary: str,
        findings: list[str] | None = None,
        candidate_notes: list[str] | None = None,
        stats_hints: list[str] | None = None,
        mechanic_hints: list[str] | None = None,
        closeout_questions: list[str] | None = None,
        evidence_refs: list[str] | None = None,
        next_owner_moves: list[str] | None = None,
        applied_skill_names: list[str] | None = None,
        session_file: str | None = None,
    ) -> SessionCheckpointNote:
        if not summary.strip():
            raise ValueError("checkpoint agent review requires a non-empty summary")

        session_path, runtime_session = probe_session(self.workspace, session_file)
        if runtime_session is None:
            raise SurfaceNotFound("checkpoint agent review requires an existing active runtime session")

        repo_root_path = _resolve_context_root(self.workspace, repo_root)
        repo_label = _resolve_context_label(self.workspace, repo_root)
        paths = _resolve_runtime_checkpoint_paths(
            self.workspace,
            repo_root=repo_root,
            runtime_session_id=runtime_session.session_id,
            migrate_legacy=True,
        )
        if not paths.jsonl.exists():
            raise SurfaceNotFound(f"no checkpoint note exists yet for {paths.repo_label}")

        commit_metadata = _read_git_commit_metadata(repo_root_path, commit_ref)
        reviewed_at, reviewed_at_local, reviewed_tz = _local_timestamp_parts()
        review_id = (
            "agent-review:"
            f"{_safe_name(commit_metadata['commit_short_sha'] or commit_ref)}:"
            f"{reviewed_at.strftime('%Y%m%dT%H%M%SZ')}"
        )
        review_evidence_refs = _dedupe_strings(
            [
                *(evidence_refs or []),
                str(paths.post_commit_report),
                str(paths.note_json),
                str(paths.surface_report),
                _checkpoint_skill_report_path(self.workspace, repo_root).as_posix(),
            ]
        )
        review = SessionCheckpointAgentReview(
            review_id=review_id,
            reviewed_at=reviewed_at,
            reviewed_at_local=reviewed_at_local,
            reviewed_tz=reviewed_tz,
            repo_root=str(repo_root_path),
            repo_label=repo_label,
            commit_ref=commit_ref,
            commit_sha=commit_metadata["commit_sha"],
            commit_short_sha=commit_metadata["commit_short_sha"],
            commit_subject=commit_metadata["commit_subject"],
            summary=summary.strip(),
            applied_skill_names=_dedupe_strings(applied_skill_names or []),
            findings=_dedupe_strings(findings or []),
            candidate_notes=_dedupe_strings(candidate_notes or []),
            stats_hints=_dedupe_strings(stats_hints or []),
            mechanic_hints=_dedupe_strings(mechanic_hints or []),
            closeout_questions=_dedupe_strings(closeout_questions or []),
            evidence_refs=review_evidence_refs,
            next_owner_moves=_dedupe_strings(next_owner_moves or []),
        )
        payload = {
            "session_ref": self.peek_status(repo_root=repo_root, session_file=str(session_path)).session_ref,
            "runtime_session_id": runtime_session.session_id,
            "runtime_session_created_at": runtime_session.created_at.astimezone(UTC).isoformat().replace("+00:00", "Z"),
            "repo_root": str(repo_root_path),
            "repo_label": repo_label,
            "agent_review": review.model_dump(mode="json"),
        }
        paths.jsonl.parent.mkdir(parents=True, exist_ok=True)
        with paths.jsonl.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=True) + "\n")

        note = self.status(repo_root=repo_root, session_file=str(session_path))
        _mark_after_commit_report_reviewed(paths.post_commit_report, review=review)
        return note

    def hook_status(self, *, repo_name: str) -> CheckpointHookStatus:
        repo_root = self.workspace.repo_path(repo_name)
        hook_path = _resolve_git_hook_path(repo_root)
        template_path = _hook_template_path(self.workspace)
        rendered = _render_post_commit_hook(self.workspace)
        status: Literal["missing", "stale", "current"]
        if not hook_path.exists():
            status = "missing"
        else:
            existing = hook_path.read_text(encoding="utf-8")
            status = "current" if existing == rendered else "stale"
        return CheckpointHookStatus(
            repo=repo_name,
            repo_root=str(repo_root),
            hook_path=str(hook_path),
            template_path=str(template_path),
            template_version=POST_COMMIT_HOOK_TEMPLATE_VERSION,
            status=status,
        )

    def install_hook(
        self,
        *,
        repo_name: str,
        overwrite: bool = False,
    ) -> CheckpointHookInstallResult:
        if repo_name == "8Dionysus":
            raise ValueError("8Dionysus is read-only and excluded from checkpoint hook mutation")
        status = self.hook_status(repo_name=repo_name)
        hook_path = Path(status.hook_path)
        action: Literal["installed", "updated", "unchanged"]
        if status.status == "missing":
            hook_path.parent.mkdir(parents=True, exist_ok=True)
            hook_path.write_text(_render_post_commit_hook(self.workspace), encoding="utf-8")
            hook_path.chmod(0o755)
            action = "installed"
        elif status.status == "stale" and overwrite:
            hook_path.write_text(_render_post_commit_hook(self.workspace), encoding="utf-8")
            hook_path.chmod(0o755)
            action = "updated"
        else:
            action = "unchanged"
        return CheckpointHookInstallResult(
            repo=repo_name,
            repo_root=status.repo_root,
            hook_path=status.hook_path,
            template_path=status.template_path,
            template_version=status.template_version,
            status_before=status.status,
            action=action,
        )

    def status(self, *, repo_root: str, session_file: str | None = None) -> SessionCheckpointNote:
        runtime_session_id, _ = _ensure_checkpoint_runtime_session(
            workspace=self.workspace,
            session_file=session_file,
        )
        paths = _resolve_runtime_checkpoint_paths(
            self.workspace,
            repo_root=repo_root,
            runtime_session_id=runtime_session_id,
            migrate_legacy=True,
        )
        if not paths.jsonl.exists():
            raise SurfaceNotFound(f"no checkpoint note exists yet for {paths.repo_label}")

        note = _build_checkpoint_note(paths)
        if _should_hide_current_checkpoint_note(note, runtime_session_id=runtime_session_id):
            _archive_current_checkpoint(paths)
            raise SurfaceNotFound(f"no active checkpoint note exists yet for {paths.repo_label}")
        paths.note_json.parent.mkdir(parents=True, exist_ok=True)
        paths.note_json.write_text(note.model_dump_json(indent=2) + "\n", encoding="utf-8")
        paths.note_md.write_text(_render_checkpoint_note_markdown(note, repo_label=paths.repo_label), encoding="utf-8")
        return note

    def peek_status(self, *, repo_root: str, session_file: str | None = None) -> SessionCheckpointNote:
        runtime_session_metadata = _peek_checkpoint_runtime_session(
            workspace=self.workspace,
            session_file=session_file,
        )
        runtime_session_id = cast(str | None, runtime_session_metadata["runtime_session_id"])
        paths = _resolve_runtime_checkpoint_paths(
            self.workspace,
            repo_root=repo_root,
            runtime_session_id=runtime_session_id,
            migrate_legacy=False,
        )
        if not paths.jsonl.exists():
            raise SurfaceNotFound(f"no checkpoint note exists yet for {paths.repo_label}")

        note = _build_checkpoint_note(paths)
        if _should_hide_current_checkpoint_note(note, runtime_session_id=runtime_session_id):
            raise SurfaceNotFound(f"no active checkpoint note exists yet for {paths.repo_label}")
        return note

    def promote(
        self,
        *,
        repo_root: str,
        target: Literal["dionysus-note", "harvest-handoff"],
        session_file: str | None = None,
    ) -> SessionCheckpointPromotion:
        if target not in PROMOTION_TARGETS:
            raise ValueError(f"unsupported target {target!r}")

        note = self.status(repo_root=repo_root, session_file=session_file)
        paths = _resolve_runtime_checkpoint_paths(
            self.workspace,
            repo_root=repo_root,
            runtime_session_id=note.runtime_session_id,
            migrate_legacy=True,
        )
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
            promoted_at=(promoted_parts := _local_timestamp_parts())[0],
            promoted_at_local=promoted_parts[1],
            promoted_tz=promoted_parts[2],
            source_note_ref=str(paths.note_json),
            output_refs=output_refs,
            resulting_state=new_state,
        )

    def build_closeout_context(
        self,
        *,
        repo_root: str,
        reviewed_artifact_path: str,
        session_ref: str | None = None,
        receipt_paths: list[str] | None = None,
        receipt_dirs: list[str] | None = None,
        surface_handoff_path: str | None = None,
        session_file: str | None = None,
    ) -> CheckpointCloseoutContext:
        reviewed_artifact = Path(reviewed_artifact_path).expanduser().resolve()
        if not reviewed_artifact.exists():
            raise FileNotFoundError(f"missing reviewed artifact: {reviewed_artifact}")

        runtime_session_metadata = _load_checkpoint_runtime_session(
            workspace=self.workspace,
            session_file=session_file,
        )
        active_runtime_session_id = cast(str | None, runtime_session_metadata["runtime_session_id"])
        paths = _resolve_runtime_checkpoint_paths(
            self.workspace,
            repo_root=repo_root,
            runtime_session_id=active_runtime_session_id,
            migrate_legacy=True,
        )
        note = _load_runtime_checkpoint_note(self, repo_root=repo_root, session_file=session_file)
        handoff = _load_reviewed_surface_handoff(
            workspace=self.workspace,
            repo_root=repo_root,
            handoff_path=surface_handoff_path,
        )
        collected_receipt_paths = _collect_receipt_paths(
            receipt_paths=receipt_paths or [],
            receipt_dirs=receipt_dirs or [],
        )
        resolved_session_ref = _resolve_closeout_session_ref(
            explicit_session_ref=session_ref,
            checkpoint_note=note,
            surface_handoff=handoff,
            reviewed_artifact=reviewed_artifact,
            receipt_paths=collected_receipt_paths,
        )
        _validate_repo_root_closeout_scope(
            checkpoint_note=note,
            resolved_session_ref=resolved_session_ref,
        )
        note_records = _load_runtime_checkpoint_notes_for_closeout(
            self,
            repo_root=repo_root,
            resolved_session_ref=resolved_session_ref,
            primary_note=note,
        )
        aggregated_notes = [candidate_note for _, candidate_note in note_records]
        aggregated_note_refs = [str(candidate_paths.note_json) for candidate_paths, _ in note_records]
        runtime_session_id = next(
            (
                candidate_note.runtime_session_id
                for candidate_note in aggregated_notes
                if candidate_note.runtime_session_id is not None
            ),
            (
                note.runtime_session_id
                if note is not None and note.runtime_session_id is not None
                else cast(str | None, runtime_session_metadata["runtime_session_id"])
            ),
        )
        session_trace_ref = cast(str | None, runtime_session_metadata["session_trace_ref"])
        session_trace_thread_id = cast(str | None, runtime_session_metadata["session_trace_thread_id"])

        notes: list[str] = []
        note_ref: str | None = None
        if str(paths.note_json) in aggregated_note_refs:
            note_ref = str(paths.note_json)
        elif note is not None:
            notes.append(
                "ignored the local checkpoint note because its session_ref did not match the reviewed closeout session"
            )
        if len(aggregated_note_refs) > 1:
            notes.append(
                "aggregated runtime-session checkpoint notes across repo labels before building the reviewed closeout context"
            )

        handoff_ref: str | None = None
        if handoff is not None and handoff.session_ref == resolved_session_ref:
            handoff_ref = str(
                _surface_handoff_path(self.workspace, repo_root, override=surface_handoff_path)
            )
        elif handoff is not None:
            notes.append(
                "ignored the reviewed surface closeout handoff because its session_ref did not match the reviewed closeout session"
            )
            handoff = None

        repo_scope = _dedupe_strings(
            [
                paths.repo_label,
                *(scope for candidate_note in aggregated_notes for scope in candidate_note.repo_scope),
                *(
                    cluster.owner_hint
                    for cluster in (handoff.surviving_checkpoint_clusters if handoff is not None else [])
                ),
            ]
        )
        candidate_map = CloseoutContextCandidateMap(
            harvest_candidate_ids=_dedupe_strings(
                [
                    candidate_id
                    for candidate_note in aggregated_notes
                    for candidate_id in candidate_note.harvest_candidate_ids
                ]
            ),
            progression_candidate_ids=_dedupe_strings(
                [
                    candidate_id
                    for candidate_note in aggregated_notes
                    for candidate_id in candidate_note.progression_candidate_ids
                ]
            ),
            upgrade_candidate_ids=_dedupe_strings(
                [
                    candidate_id
                    for candidate_note in aggregated_notes
                    for candidate_id in candidate_note.upgrade_candidate_ids
                ]
            ),
        )
        ordered_skill_plan = _derive_closeout_skill_plan(notes=aggregated_notes, handoff=handoff)
        if not aggregated_notes:
            notes.append("no matching local checkpoint note was available; the reviewed artifact becomes the primary execution source")
        if handoff is None:
            notes.append("no matching reviewed surface closeout handoff was available; closeout will reread the reviewed artifact without a reviewed surface shortlist")
        if session_trace_ref is None:
            notes.append("no live Codex rollout trace was available from the active runtime session; closeout will rely on the reviewed artifact plus checkpoint evidence only")
        else:
            notes.append("bound closeout evidence to the live Codex rollout trace referenced by the active runtime session")
        if not collected_receipt_paths:
            notes.append("no prior receipt refs were supplied; closeout execution will rely on the reviewed artifact and any local checkpoint evidence only")
        notes.append(
            "checkpoint closeout bridge builds mechanical artifacts only; a Codex agent must still apply the listed skills by rereading session evidence before treating outputs as final analysis"
        )

        built_at, built_at_local, built_tz = _local_timestamp_parts()
        context = CheckpointCloseoutContext(
            session_ref=resolved_session_ref,
            built_at=built_at,
            built_at_local=built_at_local,
            built_tz=built_tz,
            repo_root=str(_resolve_context_root(self.workspace, repo_root)),
            reviewed_artifact_ref=str(reviewed_artifact),
            runtime_session_id=runtime_session_id,
            session_trace_ref=session_trace_ref,
            session_trace_thread_id=session_trace_thread_id,
            checkpoint_note_ref=note_ref,
            checkpoint_note_refs=aggregated_note_refs,
            surface_handoff_ref=handoff_ref,
            receipt_refs=[str(path) for path in collected_receipt_paths],
            repo_scope=repo_scope,
            candidate_map=candidate_map,
            progression_axis_signals=_merge_progression_axis_signals(
                [
                    signal
                    for candidate_note in aggregated_notes
                    for signal in candidate_note.progression_axis_signals
                ]
            ),
            ordered_skill_plan=ordered_skill_plan,
            notes=notes,
        )
        write_json(paths.closeout_context, context.model_dump(mode="json"))
        return context

    def execute_closeout_chain(
        self,
        *,
        repo_root: str,
        reviewed_artifact_path: str,
        session_ref: str | None = None,
        receipt_paths: list[str] | None = None,
        receipt_dirs: list[str] | None = None,
        surface_handoff_path: str | None = None,
        session_file: str | None = None,
    ) -> CheckpointCloseoutExecutionReport:
        context = self.build_closeout_context(
            repo_root=repo_root,
            reviewed_artifact_path=reviewed_artifact_path,
            session_ref=session_ref,
            receipt_paths=receipt_paths,
            receipt_dirs=receipt_dirs,
            surface_handoff_path=surface_handoff_path,
            session_file=session_file,
        )
        paths = _resolve_runtime_checkpoint_paths(
            self.workspace,
            repo_root=repo_root,
            runtime_session_id=context.runtime_session_id,
            migrate_legacy=False,
        )
        execution_dir = paths.closeout_artifacts / _safe_name(context.session_ref)
        execution_dir.mkdir(parents=True, exist_ok=True)

        reviewed_artifact_path_obj = Path(context.reviewed_artifact_ref)
        reviewed_artifact_evidence = _merge_closeout_evidence(
            primary=_read_reviewed_artifact(reviewed_artifact_path_obj),
            secondary=(
                _read_session_trace(Path(context.session_trace_ref).expanduser().resolve())
                if context.session_trace_ref is not None
                else None
            ),
        )
        notes = _load_context_checkpoint_notes(context)
        handoff = _load_context_surface_handoff(context)
        receipt_payloads = _load_receipt_payloads(context.receipt_refs)
        shortlisted_clusters = _closeout_candidate_clusters(notes=notes, handoff=handoff)

        executed_steps: list[CloseoutExecutionStep] = []
        produced_artifact_refs: list[str] = []
        produced_receipt_refs: list[str] = []

        donor_outputs = _build_donor_harvest_outputs(
            context=context,
            reviewed_artifact=reviewed_artifact_path_obj,
            reviewed_artifact_evidence=reviewed_artifact_evidence,
            shortlisted_clusters=shortlisted_clusters,
            receipt_payloads=receipt_payloads,
            output_dir=execution_dir,
        )
        executed_steps.append(
            CloseoutExecutionStep(
                skill_name="aoa-session-donor-harvest",
                status="executed",
                reason="mechanical bridge artifact build for donor-harvest-shaped output; final donor harvest analysis still requires the Codex agent to apply the skill protocol against reviewed session evidence",
                artifact_refs=donor_outputs["artifact_refs"],
                receipt_refs=donor_outputs["receipt_refs"],
            )
        )
        produced_artifact_refs.extend(donor_outputs["artifact_refs"])
        produced_receipt_refs.extend(donor_outputs["receipt_refs"])

        progression_outputs = _build_progression_lift_outputs(
            context=context,
            reviewed_artifact=reviewed_artifact_path_obj,
            reviewed_artifact_evidence=reviewed_artifact_evidence,
            donor_packet=donor_outputs["packet"],
            shortlisted_clusters=shortlisted_clusters,
            receipt_payloads=receipt_payloads,
            output_dir=execution_dir,
        )
        executed_steps.append(
            CloseoutExecutionStep(
                skill_name="aoa-session-progression-lift",
                status="executed",
                reason="mechanical bridge artifact build for progression-lift-shaped output; final progression analysis still requires the Codex agent to apply the skill protocol against reviewed session evidence",
                artifact_refs=progression_outputs["artifact_refs"],
                receipt_refs=progression_outputs["receipt_refs"],
            )
        )
        produced_artifact_refs.extend(progression_outputs["artifact_refs"])
        produced_receipt_refs.extend(progression_outputs["receipt_refs"])

        quest_outputs = _build_quest_harvest_outputs(
            context=context,
            reviewed_artifact=reviewed_artifact_path_obj,
            reviewed_artifact_evidence=reviewed_artifact_evidence,
            donor_packet=donor_outputs["packet"],
            progression_packet=progression_outputs["packet"],
            shortlisted_clusters=shortlisted_clusters,
            receipt_payloads=receipt_payloads,
            output_dir=execution_dir,
        )
        executed_steps.append(
            CloseoutExecutionStep(
                skill_name="aoa-quest-harvest",
                status="executed",
                reason="mechanical bridge artifact build for quest-harvest-shaped output; final quest triage still requires the Codex agent to apply the skill protocol against reviewed session evidence",
                artifact_refs=quest_outputs["artifact_refs"],
                receipt_refs=quest_outputs["receipt_refs"],
            )
        )
        produced_artifact_refs.extend(quest_outputs["artifact_refs"])
        produced_receipt_refs.extend(quest_outputs["receipt_refs"])

        executed_at, executed_at_local, executed_tz = _local_timestamp_parts()
        report = CheckpointCloseoutExecutionReport(
            session_ref=context.session_ref,
            executed_at=executed_at,
            executed_at_local=executed_at_local,
            executed_tz=executed_tz,
            reviewed_artifact_ref=context.reviewed_artifact_ref,
            runtime_session_id=context.runtime_session_id,
            session_trace_ref=context.session_trace_ref,
            session_trace_thread_id=context.session_trace_thread_id,
            checkpoint_note_ref=context.checkpoint_note_ref,
            checkpoint_note_refs=list(context.checkpoint_note_refs),
            surface_handoff_ref=context.surface_handoff_ref,
            context_ref=str(paths.closeout_context),
            executed_skills=executed_steps,
            skipped_skills=[],
            produced_artifact_refs=_dedupe_strings(produced_artifact_refs),
            produced_receipt_refs=_dedupe_strings(produced_receipt_refs),
            final_stop_reason=(
                "Mechanical checkpoint-closeout bridge artifacts were built; final session analysis requires agent-led skill application over reviewed evidence, and owner-local publication plus stats refresh remain downstream steps."
            ),
        )
        write_json(paths.closeout_execution_report, report.model_dump(mode="json"))
        return report


class _CheckpointPaths:
    def __init__(
        self,
        *,
        root: Path,
        repo_label: str,
        current_dir: Path,
        surface_report: Path,
        runtime_session_id: str | None,
        runtime_scope_key: str | None,
    ) -> None:
        self.root = root
        self.repo_label = repo_label
        self.current_dir = current_dir
        self.runtime_session_id = runtime_session_id
        self.runtime_scope_key = runtime_scope_key
        self.jsonl = current_dir / "checkpoint-note.jsonl"
        self.note_json = current_dir / "checkpoint-note.json"
        self.note_md = current_dir / "checkpoint-note.md"
        self.harvest_handoff = current_dir / "harvest-handoff.json"
        self.closeout_context = current_dir / "closeout-context.json"
        self.closeout_execution_report = current_dir / "closeout-execution-report.json"
        self.closeout_artifacts = current_dir / "reviewed-closeout"
        self.post_commit_report = current_dir / "post-commit-report.json"
        self.surface_report = surface_report


def _checkpoint_current_root(workspace: Workspace) -> Path:
    return workspace.repo_path("aoa-sdk") / ".aoa" / "session-growth" / "current"


def _checkpoint_post_commit_status_root(workspace: Workspace) -> Path:
    return workspace.repo_path("aoa-sdk") / ".aoa" / "session-growth" / "post-commit-status"


def _checkpoint_runtime_scope_key(runtime_session_id: str | None) -> str | None:
    if runtime_session_id is None:
        return None
    return _safe_name(runtime_session_id)


def _checkpoint_paths(
    workspace: Workspace,
    repo_root: str,
    *,
    runtime_session_id: str | None = None,
) -> _CheckpointPaths:
    repo_label = _resolve_context_label(workspace, repo_root)
    return _checkpoint_paths_for_label(workspace, repo_label, runtime_session_id=runtime_session_id)


def _checkpoint_paths_for_label(
    workspace: Workspace,
    repo_label: str,
    *,
    runtime_session_id: str | None = None,
) -> _CheckpointPaths:
    sdk_root = workspace.repo_path("aoa-sdk")
    current_root = _checkpoint_current_root(workspace)
    runtime_scope_key = _checkpoint_runtime_scope_key(runtime_session_id)
    current_dir = (
        current_root / runtime_scope_key / repo_label
        if runtime_scope_key is not None
        else current_root / repo_label
    )
    surface_report = sdk_root / ".aoa" / "surface-detection" / f"{repo_label}.checkpoint.latest.json"
    return _CheckpointPaths(
        root=sdk_root,
        repo_label=repo_label,
        current_dir=current_dir,
        surface_report=surface_report,
        runtime_session_id=runtime_session_id,
        runtime_scope_key=runtime_scope_key,
    )


def _resolve_runtime_checkpoint_paths(
    workspace: Workspace,
    *,
    repo_root: str,
    runtime_session_id: str | None,
    migrate_legacy: bool = False,
) -> _CheckpointPaths:
    repo_label = _resolve_context_label(workspace, repo_root)
    return _resolve_runtime_checkpoint_paths_for_label(
        workspace,
        repo_label=repo_label,
        runtime_session_id=runtime_session_id,
        migrate_legacy=migrate_legacy,
    )


def _resolve_runtime_checkpoint_paths_for_label(
    workspace: Workspace,
    *,
    repo_label: str,
    runtime_session_id: str | None,
    migrate_legacy: bool = False,
) -> _CheckpointPaths:
    scoped_paths = _checkpoint_paths_for_label(
        workspace,
        repo_label,
        runtime_session_id=runtime_session_id,
    )
    if runtime_session_id is None:
        return scoped_paths

    legacy_paths = _checkpoint_paths_for_label(workspace, repo_label, runtime_session_id=None)
    if scoped_paths.current_dir == legacy_paths.current_dir or scoped_paths.jsonl.exists():
        return scoped_paths
    if not legacy_paths.jsonl.exists():
        return scoped_paths

    legacy_note = _load_checkpoint_note(legacy_paths.note_json)
    if legacy_note is None:
        legacy_note = _build_checkpoint_note(legacy_paths)
    if legacy_note.runtime_session_id not in {None, runtime_session_id}:
        return scoped_paths
    if migrate_legacy:
        _move_current_checkpoint(source_paths=legacy_paths, target_paths=scoped_paths)
        return scoped_paths
    return legacy_paths


def _checkpoint_note_ref_for_capture(
    workspace: Workspace,
    repo_root: str,
    *,
    runtime_session_id: str | None,
) -> str:
    return str(
        _resolve_runtime_checkpoint_paths(
            workspace,
            repo_root=repo_root,
            runtime_session_id=runtime_session_id,
            migrate_legacy=False,
        ).note_json
    )


def _checkpoint_skill_report_path(workspace: Workspace, repo_root: str) -> Path:
    repo_label = _resolve_context_label(workspace, repo_root)
    return workspace.repo_path("aoa-sdk") / ".aoa" / "skill-dispatch" / f"{repo_label}.checkpoint.latest.json"


def _post_commit_status_path(workspace: Workspace, repo_label: str) -> Path:
    return _checkpoint_post_commit_status_root(workspace) / f"{repo_label}.latest.json"


def _hook_template_path(workspace: Workspace) -> Path:
    workspace_candidate = workspace.repo_path("aoa-sdk") / "githooks" / "post-commit"
    if workspace_candidate.exists():
        return workspace_candidate
    package_candidate = Path(__file__).resolve().parents[3] / "githooks" / "post-commit"
    if package_candidate.exists():
        return package_candidate
    return workspace_candidate


def _write_skill_detection_report(path: Path, report: object) -> None:
    write_json(
        path,
        {
            "report_path": str(path),
            "report": report,
        },
    )


def _write_after_commit_report(path: Path, report: CheckpointAfterCommitReport) -> None:
    payload = report.model_dump(mode="json")
    payload["report_path"] = str(path)
    write_json(path, payload)


def _checkpoint_capture_result_without_append(
    api: CheckpointsAPI,
    *,
    repo_root: str,
    session_file: str | None,
    reason: Literal["no_checkpoint_signal", "auto_disabled"],
    attempted: bool,
    checkpoint_kind: Literal[
        "manual",
        "commit",
        "verify_green",
        "pr_opened",
        "pr_merged",
        "pause",
        "owner_followthrough",
    ] | None,
    read_only: bool,
) -> CheckpointCaptureResult:
    captured_at, captured_at_local, captured_tz = _local_timestamp_parts()
    current_note = (
        _peek_runtime_checkpoint_note(api, repo_root=repo_root, session_file=session_file)
        if read_only
        else _load_runtime_checkpoint_note(api, repo_root=repo_root, session_file=session_file)
    )
    session_end_targets = _derive_session_end_skill_targets(current_note)
    return CheckpointCaptureResult(
        mode="auto",
        attempted=attempted,
        appended=False,
        checkpoint_kind=checkpoint_kind,
        captured_at=captured_at,
        captured_at_local=captured_at_local,
        captured_tz=captured_tz,
        reason=reason,
        note_ref=(
            _checkpoint_note_ref_for_capture(
                api.workspace,
                repo_root,
                runtime_session_id=current_note.runtime_session_id,
            )
            if current_note is not None
            else None
        ),
        session_end_skill_targets=session_end_targets,
        session_end_next_honest_move=_derive_session_end_next_honest_move(
            note=current_note,
            session_end_targets=session_end_targets,
        ),
        harvest_candidate_ids=list(current_note.harvest_candidate_ids) if current_note is not None else [],
        progression_candidate_ids=list(current_note.progression_candidate_ids) if current_note is not None else [],
        upgrade_candidate_ids=list(current_note.upgrade_candidate_ids) if current_note is not None else [],
        progression_axis_signals=list(current_note.progression_axis_signals) if current_note is not None else [],
        stats_refresh_recommended=current_note.stats_refresh_recommended if current_note is not None else False,
        note=current_note,
    )


def _resolve_context_root(workspace: Workspace, repo_root: str) -> Path:
    resolved_repo_root = Path(repo_root).expanduser()
    if not resolved_repo_root.is_absolute():
        return (workspace.root / resolved_repo_root).resolve()
    return resolved_repo_root.resolve()


def _resolve_context_label(workspace: Workspace, repo_root: str) -> str:
    resolved_repo_root = _resolve_context_root(workspace, repo_root)
    return "workspace" if resolved_repo_root == workspace.federation_root else resolved_repo_root.name


def _load_checkpoint_note(path: Path) -> SessionCheckpointNote | None:
    try:
        return SessionCheckpointNote.model_validate_json(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _ensure_checkpoint_runtime_session(
    *,
    workspace: Workspace,
    session_file: str | None,
) -> tuple[str | None, datetime | None]:
    metadata = _load_checkpoint_runtime_session(workspace=workspace, session_file=session_file)
    return (
        cast(str | None, metadata["runtime_session_id"]),
        cast(datetime | None, metadata["runtime_session_created_at"]),
    )


def _load_checkpoint_runtime_session(
    *,
    workspace: Workspace,
    session_file: str | None,
) -> dict[str, str | datetime | None]:
    try:
        session_path, runtime_session = ensure_session(workspace, session_file)
        if not session_path.exists():
            session_path.parent.mkdir(parents=True, exist_ok=True)
            save_session(session_path, runtime_session)
        return {
            "runtime_session_id": runtime_session.session_id,
            "runtime_session_created_at": runtime_session.created_at.astimezone(UTC),
            "session_trace_ref": runtime_session.codex_rollout_path,
            "session_trace_thread_id": runtime_session.codex_thread_id,
        }
    except Exception:
        return {
            "runtime_session_id": None,
            "runtime_session_created_at": None,
            "session_trace_ref": None,
            "session_trace_thread_id": None,
        }


def _probe_checkpoint_runtime_session(
    *,
    workspace: Workspace,
    session_file: str | None,
) -> tuple[Path, dict[str, str | datetime | None]]:
    session_path = resolve_session_file(workspace, session_file)
    try:
        session_path, runtime_session = probe_session(workspace, session_file)
        if runtime_session is None:
            return session_path, {
                "runtime_session_id": None,
                "runtime_session_created_at": None,
                "session_trace_ref": None,
                "session_trace_thread_id": None,
            }
        return session_path, {
            "runtime_session_id": runtime_session.session_id,
            "runtime_session_created_at": runtime_session.created_at.astimezone(UTC),
            "session_trace_ref": runtime_session.codex_rollout_path,
            "session_trace_thread_id": runtime_session.codex_thread_id,
        }
    except Exception:
        return session_path, {
            "runtime_session_id": None,
            "runtime_session_created_at": None,
            "session_trace_ref": None,
            "session_trace_thread_id": None,
        }


def _peek_checkpoint_runtime_session(
    *,
    workspace: Workspace,
    session_file: str | None,
) -> dict[str, str | datetime | None]:
    _, metadata = _probe_checkpoint_runtime_session(workspace=workspace, session_file=session_file)
    return metadata


def _should_rotate_checkpoint_note(
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


def _should_hide_current_checkpoint_note(
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


def _default_session_ref(
    paths: _CheckpointPaths,
    *,
    existing_note: SessionCheckpointNote | None,
    runtime_session_id: str | None,
) -> str:
    if existing_note is not None and existing_note.state not in {"closed", "promoted"} and existing_note.session_ref:
        return existing_note.session_ref
    timestamp = datetime.now(UTC).strftime(SESSION_REF_TIMESTAMP_FORMAT)
    runtime_suffix = f"-{_safe_name(runtime_session_id)[:12]}" if runtime_session_id else ""
    return f"session:{timestamp}-{paths.repo_label}-checkpoint-growth{runtime_suffix}"


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


def _move_current_checkpoint(*, source_paths: _CheckpointPaths, target_paths: _CheckpointPaths) -> None:
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


def _read_reviewed_artifact(path: Path) -> dict[str, object]:
    try:
        raw_text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise FileNotFoundError(f"could not read reviewed artifact: {path}") from exc
    payload: object | None = None
    if path.suffix == ".json":
        try:
            payload = load_json(path)
        except Exception:
            payload = None
    return {
        "text": raw_text,
        "payload": payload,
        "ref": str(path),
        "tokens": set(re.findall(r"[a-z0-9_:-]+", raw_text.lower())),
    }


def _read_session_trace(path: Path) -> dict[str, object]:
    if not path.exists():
        raise FileNotFoundError(f"missing Codex session trace: {path}")
    chunks: list[str] = []
    total_chars = 0
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        extracted = _extract_codex_trace_entry(payload)
        if extracted is None:
            continue
        normalized = re.sub(r"\s+", " ", extracted).strip()
        if not normalized:
            continue
        clipped = normalized[:CODEX_TRACE_MAX_CHUNK_CHARS]
        if total_chars + len(clipped) > CODEX_TRACE_MAX_CHARS:
            remaining = CODEX_TRACE_MAX_CHARS - total_chars
            if remaining <= 0:
                break
            clipped = clipped[:remaining]
        chunks.append(clipped)
        total_chars += len(clipped)
        if total_chars >= CODEX_TRACE_MAX_CHARS:
            break
    text = "\n".join(chunks)
    return {
        "text": text,
        "ref": str(path),
        "tokens": set(re.findall(r"[a-z0-9_:-]+", text.lower())),
    }


def _extract_codex_trace_entry(record: dict[str, object]) -> str | None:
    record_type = record.get("type")
    payload = record.get("payload")
    if not isinstance(payload, dict):
        return None
    if record_type == "event_msg" and payload.get("type") == "user_message":
        message = payload.get("message")
        return f"user: {message}" if isinstance(message, str) and message.strip() else None
    if record_type != "response_item":
        return None

    payload_type = payload.get("type")
    if payload_type == "message" and payload.get("role") == "assistant":
        text = _flatten_codex_content_text(payload.get("content"))
        return f"assistant: {text}" if text else None
    if payload_type == "function_call":
        name = payload.get("name")
        arguments = payload.get("arguments")
        parts = []
        if isinstance(name, str) and name.strip():
            parts.append(name.strip())
        if isinstance(arguments, str) and arguments.strip():
            parts.append(arguments.strip())
        return f"tool_call: {' '.join(parts)}" if parts else None
    if payload_type == "custom_tool_call":
        name = payload.get("name")
        input_value = payload.get("input")
        parts = []
        if isinstance(name, str) and name.strip():
            parts.append(name.strip())
        if isinstance(input_value, str) and input_value.strip():
            parts.append(input_value.strip())
        return f"tool_call: {' '.join(parts)}" if parts else None
    if payload_type in {"function_call_output", "custom_tool_call_output", "tool_search_output"}:
        output = payload.get("output")
        return f"tool_output: {output}" if isinstance(output, str) and output.strip() else None
    return None


def _flatten_codex_content_text(content: object) -> str:
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for item in content:
        if not isinstance(item, dict):
            continue
        if item.get("type") not in CODEX_TRACE_TEXT_ITEM_TYPES:
            continue
        text = item.get("text")
        if isinstance(text, str) and text.strip():
            parts.append(text.strip())
    return "\n".join(parts)


def _merge_closeout_evidence(
    *,
    primary: dict[str, object],
    secondary: dict[str, object] | None,
) -> dict[str, object]:
    if secondary is None:
        return primary
    texts = [
        text
        for text in (
            primary.get("text"),
            secondary.get("text"),
        )
        if isinstance(text, str) and text.strip()
    ]
    tokens: set[str] = set()
    for source in (primary, secondary):
        source_tokens = source.get("tokens")
        if isinstance(source_tokens, set) and all(isinstance(token, str) for token in source_tokens):
            tokens.update(source_tokens)
    refs = [
        ref
        for ref in (
            primary.get("ref"),
            secondary.get("ref"),
        )
        if isinstance(ref, str) and ref.strip()
    ]
    return {
        "text": "\n\n".join(texts),
        "payload": primary.get("payload"),
        "ref": primary.get("ref"),
        "refs": refs,
        "tokens": tokens,
    }


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


def _build_donor_harvest_outputs(
    *,
    context: CheckpointCloseoutContext,
    reviewed_artifact: Path,
    reviewed_artifact_evidence: dict[str, object],
    shortlisted_clusters: list[SessionCheckpointCluster],
    receipt_payloads: list[dict[str, object]],
    output_dir: Path,
) -> DonorHarvestOutputs:
    accepted_candidates = [
        _build_accepted_candidate(
            cluster=cluster,
            reviewed_artifact=reviewed_artifact,
            session_trace_ref=context.session_trace_ref,
        )
        for cluster in shortlisted_clusters
    ]
    deferred_candidates = (
        [
            {
                "candidate_ref": f"candidate:hold:{_safe_name(context.session_ref)}",
                "why": "no matching checkpoint or reviewed handoff candidates survived into the explicit closeout bundle",
                "evidence_anchors": _dedupe_strings(
                    [
                        str(reviewed_artifact),
                        *([context.session_trace_ref] if context.session_trace_ref is not None else []),
                    ]
                ),
            }
        ]
        if not accepted_candidates
        else []
    )
    owner_layer_distribution: dict[str, int] = {}
    extract_counts: dict[str, int] = {}
    for candidate in accepted_candidates:
        owner_repo = cast(str, candidate["owner_repo_recommendation"])
        abstraction_shape = cast(str, candidate["abstraction_shape"])
        owner_layer_distribution[owner_repo] = owner_layer_distribution.get(owner_repo, 0) + 1
        extract_counts[abstraction_shape] = extract_counts.get(abstraction_shape, 0) + 1

    packet = {
        "artifact_kind": "harvest_packet",
        "session_ref": context.session_ref,
        "route_ref": "route:checkpoint-closeout-bridge",
        "authority_contract": CHECKPOINT_CLOSEOUT_AUTHORITY_CONTRACT,
        "owner_repo": "aoa-skills",
        "reviewed_artifact_ref": str(reviewed_artifact),
        "session_trace_ref": context.session_trace_ref,
        "session_trace_thread_id": context.session_trace_thread_id,
        "checkpoint_note_ref": context.checkpoint_note_ref,
        "surface_handoff_ref": context.surface_handoff_ref,
        "accepted_candidates": accepted_candidates,
        "deferred_candidates": deferred_candidates,
        "extract_counts": extract_counts,
        "promotion_candidates": len(accepted_candidates),
        "deferrals": len(deferred_candidates),
        "owner_layer_distribution": owner_layer_distribution,
        "evidence_density": "reviewed",
    }
    packet_path = output_dir / "HARVEST_PACKET.json"
    write_json(packet_path, packet)

    run_ref = f"run-{_safe_name(context.session_ref)}-closeout-bridge"
    receipt = {
        "event_kind": "harvest_packet_receipt",
        "event_id": f"evt-{_safe_name(context.session_ref)}-harvest",
        **_observed_timestamp_fields(),
        "run_ref": run_ref,
        "session_ref": context.session_ref,
        "actor_ref": _skill_actor_ref("aoa-session-donor-harvest"),
        "object_ref": {"repo": "aoa-skills", "kind": "skill", "id": "aoa-session-donor-harvest"},
        "evidence_refs": [
            {"kind": "harvest_packet", "ref": str(packet_path), "role": "primary"},
            {"kind": "reviewed_artifact", "ref": str(reviewed_artifact), "role": "reviewed-source"},
            *(
                [{"kind": "session_trace", "ref": context.session_trace_ref, "role": "runtime-trace"}]
                if context.session_trace_ref is not None
                else []
            ),
            {
                "kind": "skill_contract",
                "ref": "repo:aoa-skills/skills/aoa-session-donor-harvest/SKILL.md",
                "role": "contract",
            },
        ],
        "payload": {
            "route_ref": "route:checkpoint-closeout-bridge",
            "authority_contract": CHECKPOINT_CLOSEOUT_AUTHORITY_CONTRACT,
            "extract_counts": extract_counts,
            "owner_layer_distribution": owner_layer_distribution,
            "promotion_candidates": len(accepted_candidates),
            "deferrals": len(deferred_candidates),
            "evidence_density": "reviewed",
        },
    }
    receipt_path = output_dir / "HARVEST_PACKET_RECEIPT.json"
    write_json(receipt_path, receipt)

    core_receipt = _build_core_skill_receipt(
        session_ref=context.session_ref,
        run_ref=run_ref,
        skill_name="aoa-session-donor-harvest",
        detail_event_kind="harvest_packet_receipt",
        detail_receipt_ref=str(receipt_path),
        route_ref="route:checkpoint-closeout-bridge",
        repo_scope=context.repo_scope,
        handoff_targets=[target.skill_name for target in context.ordered_skill_plan],
        repeated_pattern_signal=bool(shortlisted_clusters),
        promotion_discussion_required=bool(context.candidate_map.upgrade_candidate_ids),
        candidate_now=len(accepted_candidates),
        candidate_later=len(context.candidate_map.upgrade_candidate_ids),
        surface_detection_report_ref=context.surface_handoff_ref,
        detail_to_closeout_ref=context.reviewed_artifact_ref,
    )
    core_receipt_path = output_dir / "CORE_SKILL_APPLICATION_RECEIPT.harvest.json"
    write_json(core_receipt_path, core_receipt)

    reviewed_tokens_value = reviewed_artifact_evidence.get("tokens")
    reviewed_tokens = (
        reviewed_tokens_value
        if isinstance(reviewed_tokens_value, set)
        and all(isinstance(token, str) for token in reviewed_tokens_value)
        else set()
    )

    return {
        "packet": cast(dict[str, object], packet),
        "artifact_refs": [str(packet_path)],
        "receipt_refs": [str(receipt_path), str(core_receipt_path)],
        "reviewed_tokens": reviewed_tokens,
        "receipt_payloads": receipt_payloads,
    }


def _build_progression_lift_outputs(
    *,
    context: CheckpointCloseoutContext,
    reviewed_artifact: Path,
    reviewed_artifact_evidence: dict[str, object],
    donor_packet: dict[str, object],
    shortlisted_clusters: list[SessionCheckpointCluster],
    receipt_payloads: list[dict[str, object]],
    output_dir: Path,
) -> ProgressionLiftOutputs:
    base_signals = list(context.progression_axis_signals)
    derived_signals = _progression_signals_from_reviewed_artifact(
        reviewed_artifact=reviewed_artifact,
        reviewed_artifact_evidence=reviewed_artifact_evidence,
        candidate_ids=_dedupe_strings(
            [
                *context.candidate_map.harvest_candidate_ids,
                *context.candidate_map.progression_candidate_ids,
                *context.candidate_map.upgrade_candidate_ids,
            ]
        ),
    )
    merged_signals = _merge_progression_axis_signals([*base_signals, *derived_signals])
    axis_deltas = {
        signal.axis: _axis_delta_for_movement(signal.movement)
        for signal in merged_signals
    }
    verdict = _progression_verdict(
        merged_signals=merged_signals,
        accepted_candidates=donor_packet.get("accepted_candidates", []),
    )
    cautions = _progression_cautions(
        context=context,
        merged_signals=merged_signals,
        shortlisted_clusters=shortlisted_clusters,
        receipt_payloads=receipt_payloads,
    )
    packet = {
        "artifact_kind": "progression_delta",
        "session_ref": context.session_ref,
        "route_ref": "route:checkpoint-closeout-bridge",
        "authority_contract": CHECKPOINT_CLOSEOUT_AUTHORITY_CONTRACT,
        "scope": "session_scoped",
        "verdict": verdict,
        "axis_deltas": axis_deltas,
        "cautions": cautions,
        "reviewed_artifact_ref": str(reviewed_artifact),
        "session_trace_ref": context.session_trace_ref,
        "session_trace_thread_id": context.session_trace_thread_id,
        "candidate_ids": _dedupe_strings(
            [
                *context.candidate_map.progression_candidate_ids,
                *context.candidate_map.harvest_candidate_ids,
            ]
        ),
    }
    packet_path = output_dir / "PROGRESSION_DELTA.json"
    write_json(packet_path, packet)

    run_ref = f"run-{_safe_name(context.session_ref)}-closeout-bridge"
    receipt = {
        "event_kind": "progression_delta_receipt",
        "event_id": f"evt-{_safe_name(context.session_ref)}-progression",
        **_observed_timestamp_fields(),
        "run_ref": run_ref,
        "session_ref": context.session_ref,
        "actor_ref": _skill_actor_ref("aoa-session-progression-lift"),
        "object_ref": {"repo": "aoa-skills", "kind": "skill", "id": "aoa-session-progression-lift"},
        "evidence_refs": [
            {"kind": "progression_packet", "ref": str(packet_path), "role": "primary"},
            {"kind": "reviewed_artifact", "ref": str(reviewed_artifact), "role": "reviewed-source"},
            *(
                [{"kind": "session_trace", "ref": context.session_trace_ref, "role": "runtime-trace"}]
                if context.session_trace_ref is not None
                else []
            ),
            {
                "kind": "skill_contract",
                "ref": "repo:aoa-skills/skills/aoa-session-progression-lift/SKILL.md",
                "role": "contract",
            },
        ],
        "payload": {
            "route_ref": "route:checkpoint-closeout-bridge",
            "authority_contract": CHECKPOINT_CLOSEOUT_AUTHORITY_CONTRACT,
            "scope": "session_scoped",
            "verdict": verdict,
            "axis_deltas": axis_deltas,
            "cautions": cautions,
        },
    }
    receipt_path = output_dir / "PROGRESSION_DELTA_RECEIPT.json"
    write_json(receipt_path, receipt)

    core_receipt = _build_core_skill_receipt(
        session_ref=context.session_ref,
        run_ref=run_ref,
        skill_name="aoa-session-progression-lift",
        detail_event_kind="progression_delta_receipt",
        detail_receipt_ref=str(receipt_path),
        route_ref="route:checkpoint-closeout-bridge",
        repo_scope=context.repo_scope,
        handoff_targets=[target.skill_name for target in context.ordered_skill_plan],
        repeated_pattern_signal=bool(shortlisted_clusters),
        promotion_discussion_required=bool(context.candidate_map.upgrade_candidate_ids),
        candidate_now=len(context.candidate_map.progression_candidate_ids),
        candidate_later=len(context.candidate_map.upgrade_candidate_ids),
        surface_detection_report_ref=context.surface_handoff_ref,
        detail_to_closeout_ref=context.reviewed_artifact_ref,
    )
    core_receipt_path = output_dir / "CORE_SKILL_APPLICATION_RECEIPT.progression.json"
    write_json(core_receipt_path, core_receipt)

    return {
        "packet": cast(dict[str, object], packet),
        "artifact_refs": [str(packet_path)],
        "receipt_refs": [str(receipt_path), str(core_receipt_path)],
    }


def _build_quest_harvest_outputs(
    *,
    context: CheckpointCloseoutContext,
    reviewed_artifact: Path,
    reviewed_artifact_evidence: dict[str, object],
    donor_packet: dict[str, object],
    progression_packet: dict[str, object],
    shortlisted_clusters: list[SessionCheckpointCluster],
    receipt_payloads: list[dict[str, object]],
    output_dir: Path,
) -> QuestHarvestOutputs:
    accepted_candidates = _dict_records(donor_packet.get("accepted_candidates", []))
    progression_verdict_value = progression_packet.get("verdict")
    progression_verdict = (
        progression_verdict_value if isinstance(progression_verdict_value, str) else None
    )
    promotion_entries = [
        {
            "candidate_index": index,
            **_quest_promotion_fields(
                context=context,
                candidate=candidate,
                progression_verdict=progression_verdict,
            ),
        }
        for index, candidate in enumerate(accepted_candidates)
    ]
    if not promotion_entries:
        promotion_entries = [
            {
                "candidate_index": None,
                **_quest_promotion_fields(
                    context=context,
                    candidate=None,
                    progression_verdict=progression_verdict,
                ),
            }
        ]
    primary_promotion = promotion_entries[0]
    owner_repo = cast(str, primary_promotion["owner_repo"])
    next_surface = cast(str, primary_promotion["next_surface"])
    promotion_verdict = cast(str, primary_promotion["promotion_verdict"])
    nearest_wrong_target = cast(str, primary_promotion["nearest_wrong_target"])
    repeat_shape = cast(str, primary_promotion["repeat_shape"])
    bounded_unit_ref = cast(str, primary_promotion["bounded_unit_ref"])
    quest_unit_name = cast(str, primary_promotion["quest_unit_name"])
    candidate_refs = [
        cast(str, entry["bounded_unit_ref"])
        for entry in promotion_entries
        if isinstance(entry.get("bounded_unit_ref"), str)
    ]
    additional_candidate_refs = candidate_refs[1:]
    multi_candidate_followup_required = len(accepted_candidates) > 1

    triage = {
        "artifact_kind": "quest_triage",
        "session_ref": context.session_ref,
        "authority_contract": CHECKPOINT_CLOSEOUT_AUTHORITY_CONTRACT,
        "quest_unit_name": quest_unit_name,
        "reviewed_artifact_ref": str(reviewed_artifact),
        "session_trace_ref": context.session_trace_ref,
        "session_trace_thread_id": context.session_trace_thread_id,
        "candidate_ref": bounded_unit_ref,
        "candidate_refs": candidate_refs,
        "additional_candidate_refs": additional_candidate_refs,
        "accepted_candidate_count": len(accepted_candidates),
        "multi_candidate_followup_required": multi_candidate_followup_required,
        "promotion_verdict": promotion_verdict,
        "repeat_shape": repeat_shape,
        "notes": _quest_triage_notes(
            context=context,
            reviewed_artifact_evidence=reviewed_artifact_evidence,
            shortlisted_clusters=shortlisted_clusters,
            receipt_payloads=receipt_payloads,
        ),
    }
    triage_path = output_dir / "QUEST_TRIAGE.json"
    write_json(triage_path, triage)

    packet = {
        "artifact_kind": "quest_promotion",
        "session_ref": context.session_ref,
        "authority_contract": CHECKPOINT_CLOSEOUT_AUTHORITY_CONTRACT,
        "promotion_verdict": promotion_verdict,
        "owner_repo": owner_repo,
        "next_surface": next_surface,
        "nearest_wrong_target": nearest_wrong_target,
        "repeat_shape": repeat_shape,
        "bounded_unit_ref": bounded_unit_ref,
        "candidate_refs": candidate_refs,
        "additional_candidate_refs": additional_candidate_refs,
        "accepted_candidate_count": len(accepted_candidates),
        "multi_candidate_followup_required": multi_candidate_followup_required,
        "session_trace_ref": context.session_trace_ref,
        "session_trace_thread_id": context.session_trace_thread_id,
    }
    packet_path = output_dir / "QUEST_PROMOTION.json"
    write_json(packet_path, packet)

    promotion_bundle = {
        "artifact_kind": "quest_promotions",
        "session_ref": context.session_ref,
        "authority_contract": CHECKPOINT_CLOSEOUT_AUTHORITY_CONTRACT,
        "primary_bounded_unit_ref": bounded_unit_ref,
        "accepted_candidate_count": len(accepted_candidates),
        "multi_candidate_followup_required": multi_candidate_followup_required,
        "promotions": promotion_entries,
        "session_trace_ref": context.session_trace_ref,
        "session_trace_thread_id": context.session_trace_thread_id,
    }
    promotion_bundle_path = output_dir / "QUEST_PROMOTIONS.json"
    write_json(promotion_bundle_path, promotion_bundle)

    run_ref = f"run-{_safe_name(context.session_ref)}-closeout-bridge"
    receipt = {
        "event_kind": "quest_promotion_receipt",
        "event_id": f"evt-{_safe_name(context.session_ref)}-quest",
        **_observed_timestamp_fields(),
        "run_ref": run_ref,
        "session_ref": context.session_ref,
        "actor_ref": _skill_actor_ref("aoa-quest-harvest"),
        "object_ref": {"repo": "aoa-skills", "kind": "skill", "id": "aoa-quest-harvest"},
        "evidence_refs": [
            {"kind": "quest_triage", "ref": str(triage_path), "role": "primary"},
            {"kind": "quest_promotion", "ref": str(packet_path), "role": "promotion"},
            {"kind": "quest_promotions", "ref": str(promotion_bundle_path), "role": "all-candidates"},
            {"kind": "reviewed_artifact", "ref": str(reviewed_artifact), "role": "reviewed-source"},
            *(
                [{"kind": "session_trace", "ref": context.session_trace_ref, "role": "runtime-trace"}]
                if context.session_trace_ref is not None
                else []
            ),
            {
                "kind": "skill_contract",
                "ref": "repo:aoa-skills/skills/aoa-quest-harvest/SKILL.md",
                "role": "contract",
            },
        ],
        "payload": {
            "promotion_verdict": promotion_verdict,
            "authority_contract": CHECKPOINT_CLOSEOUT_AUTHORITY_CONTRACT,
            "owner_repo": owner_repo,
            "next_surface": next_surface,
            "nearest_wrong_target": nearest_wrong_target,
            "repeat_shape": repeat_shape,
            "bounded_unit_ref": bounded_unit_ref,
            "candidate_refs": candidate_refs,
            "additional_candidate_refs": additional_candidate_refs,
            "accepted_candidate_count": len(accepted_candidates),
            "multi_candidate_followup_required": multi_candidate_followup_required,
        },
    }
    receipt_path = output_dir / "QUEST_PROMOTION_RECEIPT.json"
    write_json(receipt_path, receipt)

    core_receipt = _build_core_skill_receipt(
        session_ref=context.session_ref,
        run_ref=run_ref,
        skill_name="aoa-quest-harvest",
        detail_event_kind="quest_promotion_receipt",
        detail_receipt_ref=str(receipt_path),
        route_ref="route:checkpoint-closeout-bridge",
        repo_scope=context.repo_scope,
        handoff_targets=[target.skill_name for target in context.ordered_skill_plan],
        repeated_pattern_signal=bool(shortlisted_clusters),
        promotion_discussion_required=bool(context.candidate_map.upgrade_candidate_ids),
        candidate_now=len(context.candidate_map.upgrade_candidate_ids),
        candidate_later=0,
        surface_detection_report_ref=context.surface_handoff_ref,
        detail_to_closeout_ref=context.reviewed_artifact_ref,
    )
    core_receipt_path = output_dir / "CORE_SKILL_APPLICATION_RECEIPT.quest.json"
    write_json(core_receipt_path, core_receipt)

    return {
        "packet": cast(dict[str, object], packet),
        "artifact_refs": [str(triage_path), str(packet_path), str(promotion_bundle_path)],
        "receipt_refs": [str(receipt_path), str(core_receipt_path)],
    }


def _build_accepted_candidate(
    *,
    cluster: SessionCheckpointCluster,
    reviewed_artifact: Path,
    session_trace_ref: str | None,
) -> dict[str, object]:
    owner_repo = (
        cluster.owner_hint
        if cluster.owner_hint in ALLOWED_OWNER_REPOS
        else DEFAULT_OWNER_BY_CANDIDATE_KIND.get(cluster.candidate_kind, "aoa-skills")
    )
    abstraction_shape = ABSTRACTION_SHAPE_BY_OWNER[owner_repo]
    slug = _safe_name(cluster.display_name or cluster.candidate_id)
    next_surface = DEFAULT_ARTIFACT_BY_OWNER[owner_repo].format(slug=slug)
    return {
        "candidate_ref": cluster.candidate_id,
        "unit_name": cluster.display_name,
        "abstraction_shape": abstraction_shape,
        "owner_repo_recommendation": owner_repo,
        "chosen_next_artifact": next_surface,
        "nearest_wrong_target": _nearest_wrong_target(owner_repo),
        "owner_reason": _owner_reason(cluster=cluster, owner_repo=owner_repo),
        "evidence_anchors": _dedupe_strings(
            [
                str(reviewed_artifact),
                *([session_trace_ref] if session_trace_ref is not None else []),
                *cluster.evidence_refs,
            ]
        ),
    }


def _owner_reason(*, cluster: SessionCheckpointCluster, owner_repo: str) -> str:
    reasons = {
        "aoa-playbooks": "The surviving reviewed unit is still route-shaped, so the next honest owner surface is a playbook rather than a leaf skill.",
        "aoa-skills": "The surviving reviewed unit looks like a bounded executable workflow, so the next honest owner surface is a skill contract.",
        "aoa-evals": "The surviving reviewed unit looks proof- or verdict-shaped, so the next honest owner surface is an eval contract.",
        "aoa-memo": "The surviving reviewed unit looks recall-shaped, so the next honest owner surface is a memo or writeback surface.",
        "aoa-agents": "The surviving reviewed unit looks actor- or role-shaped, so the next honest owner surface is an agent boundary contract.",
        "aoa-techniques": "The surviving reviewed unit looks like reusable practice meaning, so the next honest owner surface is a technique contract.",
    }
    return reasons.get(
        owner_repo,
        f"The reviewed checkpoint candidate {cluster.candidate_id} survived closeout with enough shape to draft the next owner artifact.",
    )


def _nearest_wrong_target(owner_repo: str) -> str:
    nearest = {
        "aoa-playbooks": "skill",
        "aoa-skills": "playbook",
        "aoa-evals": "skill",
        "aoa-memo": "eval",
        "aoa-agents": "skill",
        "aoa-techniques": "skill",
    }
    return nearest.get(owner_repo, "skill")


def _progression_signals_from_reviewed_artifact(
    *,
    reviewed_artifact: Path,
    reviewed_artifact_evidence: dict[str, object],
    candidate_ids: list[str],
) -> list[ProgressionAxisSignal]:
    text = cast(str, reviewed_artifact_evidence.get("text") or "")
    lowered = text.lower()
    templates: list[tuple[str, tuple[str, ...], str]] = [
        (
            "boundary_integrity",
            ("boundary", "scope", "owner layer", "owner-layer", "charter"),
            "the reviewed artifact explicitly revisits boundaries, scope, or ownership and should feed a final boundary-integrity reread",
        ),
        (
            "execution_reliability",
            ("implemented", "executed", "ran", "green", "verified"),
            "the reviewed artifact carries real execution or verify-green evidence that should count toward execution reliability",
        ),
        (
            "change_legibility",
            ("patch", "diff", "change", "commit", "refactor"),
            "the reviewed artifact names concrete changes clearly enough to improve change legibility at reviewed closeout",
        ),
        (
            "review_sharpness",
            ("review", "audit", "finding", "risk", "gap"),
            "the reviewed artifact preserves explicit review language that should sharpen the final progression reread",
        ),
        (
            "proof_discipline",
            ("proof", "validate", "verification", "test", "schema"),
            "the reviewed artifact cites proof or validation work that should inform final proof-discipline judgment",
        ),
        (
            "provenance_hygiene",
            ("source of truth", "authority", "provenance", "canonical"),
            "the reviewed artifact keeps provenance and authority visible, which should influence provenance hygiene at closeout",
        ),
        (
            "deep_readiness",
            ("architecture", "wave", "phase", "bridge", "kernel"),
            "the reviewed artifact shows deeper structural understanding that should be reconsidered during progression lift",
        ),
    ]
    evidence_refs = [str(reviewed_artifact)]
    signals: list[ProgressionAxisSignal] = []
    for axis, keywords, why in templates:
        if not any(keyword in lowered for keyword in keywords):
            continue
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
                movement="advance",
                why=why,
                evidence_refs=evidence_refs,
                candidate_ids=list(candidate_ids),
            )
        )
    return signals


def _axis_delta_for_movement(movement: str) -> int:
    return {
        "advance": 1,
        "hold": 0,
        "reanchor": -1,
        "downgrade": -2,
    }[movement]


def _progression_verdict(
    *,
    merged_signals: list[ProgressionAxisSignal],
    accepted_candidates: object,
) -> str:
    if not merged_signals:
        return "hold"
    movements = [signal.movement for signal in merged_signals]
    if "downgrade" in movements:
        return "downgrade"
    if "reanchor" in movements:
        return "reanchor"
    if sum(1 for movement in movements if movement == "advance") >= 2 and isinstance(accepted_candidates, list):
        return "advance" if accepted_candidates else "hold"
    return "hold"


def _progression_cautions(
    *,
    context: CheckpointCloseoutContext,
    merged_signals: list[ProgressionAxisSignal],
    shortlisted_clusters: list[SessionCheckpointCluster],
    receipt_payloads: list[dict[str, object]],
) -> list[str]:
    cautions: list[str] = []
    if context.checkpoint_note_ref is None:
        cautions.append("no checkpoint note was available, so progression relies on the reviewed artifact and any prior receipts only")
    if context.surface_handoff_ref is None:
        cautions.append("no reviewed surface handoff was available, so owner-layer shortlist cues remained minimal")
    if not shortlisted_clusters:
        cautions.append("no reviewed checkpoint candidates survived into closeout, so progression remains cautious and session-scoped")
    if not receipt_payloads:
        cautions.append("no prior receipt refs were provided to widen the reviewed evidence set")
    if not merged_signals:
        cautions.append("no durable axis movement was strong enough to survive reviewed reread, so the honest progression verdict is hold")
    return cautions


def _quest_promotion_fields(
    *,
    context: CheckpointCloseoutContext,
    candidate: dict[str, object] | None,
    progression_verdict: str | None,
) -> dict[str, object]:
    candidate_ref = _string_field(candidate, "candidate_ref") if candidate is not None else None
    owner_repo_value = (
        _string_field(candidate, "owner_repo_recommendation") if candidate is not None else None
    )
    next_surface_value = (
        _string_field(candidate, "chosen_next_artifact") if candidate is not None else None
    )
    can_promote = (
        candidate is not None
        and progression_verdict in {"advance", "hold"}
        and owner_repo_value is not None
        and next_surface_value is not None
    )
    if can_promote:
        assert candidate is not None
        assert owner_repo_value is not None
        assert next_surface_value is not None
        owner_repo = owner_repo_value
        next_surface = next_surface_value
        promotion_verdict = QUEST_PROMOTION_VERDICT_BY_OWNER.get(owner_repo, "keep_open_quest")
        nearest_wrong_target = _string_field(candidate, "nearest_wrong_target") or "promote_to_skill"
        repeat_shape = _string_field(candidate, "abstraction_shape") or "route"
        bounded_unit_ref = candidate_ref or f"quest:{_safe_name(context.session_ref)}"
        unit_name = _string_field(candidate, "unit_name")
        quest_unit_name = unit_name or f"reviewed closeout candidate {bounded_unit_ref}"
    else:
        owner_repo = "aoa-playbooks"
        next_surface = f"quests/{_safe_name(context.session_ref)}-followup/QUEST.md"
        promotion_verdict = "keep_open_quest"
        nearest_wrong_target = "promote_to_skill"
        repeat_shape = "route"
        bounded_unit_ref = (
            candidate_ref
            if isinstance(candidate_ref, str) and candidate_ref
            else f"quest:{_safe_name(context.session_ref)}"
        )
        quest_unit_name = f"reviewed closeout follow-through for {context.session_ref}"
    return {
        "source_candidate_ref": candidate_ref,
        "promotion_verdict": promotion_verdict,
        "owner_repo": owner_repo,
        "next_surface": next_surface,
        "nearest_wrong_target": nearest_wrong_target,
        "repeat_shape": repeat_shape,
        "bounded_unit_ref": bounded_unit_ref,
        "quest_unit_name": quest_unit_name,
    }


def _quest_triage_notes(
    *,
    context: CheckpointCloseoutContext,
    reviewed_artifact_evidence: dict[str, object],
    shortlisted_clusters: list[SessionCheckpointCluster],
    receipt_payloads: list[dict[str, object]],
) -> list[str]:
    notes: list[str] = []
    if shortlisted_clusters:
        notes.append("quest triage started from checkpoint and reviewed-handoff shortlists but reread the reviewed artifact before deciding any promotion target")
    else:
        notes.append("quest triage had no checkpoint shortlist and therefore relied on the reviewed artifact alone")
    if receipt_payloads:
        notes.append("prior receipt refs stayed evidence inputs, not replacement authority")
    if "repeat" in cast(set[str], reviewed_artifact_evidence.get("tokens") or set()):
        notes.append("the reviewed artifact still names repeated work, so keep-open-quest remains a meaningful option even without promotion")
    return notes


def _build_core_skill_receipt(
    *,
    session_ref: str,
    run_ref: str,
    skill_name: Literal[
        "aoa-session-donor-harvest",
        "aoa-session-progression-lift",
        "aoa-quest-harvest",
    ],
    detail_event_kind: Literal[
        "harvest_packet_receipt",
        "progression_delta_receipt",
        "quest_promotion_receipt",
    ],
    detail_receipt_ref: str,
    route_ref: str,
    repo_scope: list[str],
    handoff_targets: list[str],
    repeated_pattern_signal: bool,
    promotion_discussion_required: bool,
    candidate_now: int,
    candidate_later: int,
    surface_detection_report_ref: str | None,
    detail_to_closeout_ref: str,
) -> dict[str, object]:
    adjacent_owner_repos = [repo for repo in repo_scope if repo in ALLOWED_OWNER_REPOS]
    return {
        "event_kind": "core_skill_application_receipt",
        "event_id": f"evt-core-{_safe_name(session_ref)}-{skill_name.replace('aoa-', '')}",
        **_observed_timestamp_fields(),
        "run_ref": run_ref,
        "session_ref": session_ref,
        "actor_ref": _skill_actor_ref(skill_name),
        "object_ref": {"repo": "aoa-skills", "kind": "skill", "id": skill_name},
        "evidence_refs": [{"kind": "receipt", "ref": detail_receipt_ref}],
        "payload": {
            "kernel_id": "project-core-session-growth-v1",
            "skill_name": skill_name,
            "application_stage": "finish",
            "authority_contract": CHECKPOINT_CLOSEOUT_AUTHORITY_CONTRACT,
            "detail_event_kind": detail_event_kind,
            "detail_receipt_ref": detail_receipt_ref,
            "route_ref": route_ref,
            "surface_detection_context": {
                "activation_truth": "manual-equivalent-adjacent",
                "adjacent_owner_repos": adjacent_owner_repos,
                "owner_layer_ambiguity": len(set(adjacent_owner_repos)) > 1,
                "detail_to_closeout_ref": detail_to_closeout_ref,
                "surface_closeout_handoff_ref": surface_detection_report_ref,
                "candidate_counts": {
                    "candidate_now": candidate_now,
                    "candidate_later": candidate_later,
                },
                "suggested_handoff_targets": handoff_targets,
                "repeated_pattern_signal": repeated_pattern_signal,
                "promotion_discussion_required": promotion_discussion_required,
            },
        },
    }


def _skill_actor_ref(
    skill_name: Literal[
        "aoa-session-donor-harvest",
        "aoa-session-progression-lift",
        "aoa-quest-harvest",
    ],
) -> str:
    return f"aoa-skills:{skill_name}"


def _safe_name(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip())
    normalized = normalized.strip("-._")
    return normalized or "session"


def _build_checkpoint_note(paths: _CheckpointPaths) -> SessionCheckpointNote:
    entries: list[SessionCheckpointHistoryEntry] = []
    agent_reviews: list[SessionCheckpointAgentReview] = []
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
            runtime_session_created_at = _coerce_datetime(payload.get("runtime_session_created_at"))
        if "agent_review" in payload:
            review = SessionCheckpointAgentReview.model_validate(payload["agent_review"])
            reviewed_at_local, reviewed_tz = _with_local_timestamp_fallback(
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
            agent_reviews.append(review)
            continue
        entry = SessionCheckpointHistoryEntry.model_validate(payload["history_entry"])
        observed_at_local, observed_tz = _with_local_timestamp_fallback(
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
        session_ref = _default_session_ref(
            paths,
            existing_note=None,
            runtime_session_id=runtime_session_id,
        )

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
    reviewed_commit_keys = _agent_review_commit_keys(agent_reviews)
    normalized_entries: list[SessionCheckpointHistoryEntry] = []

    for entry in entries:
        if entry.agent_review_status == "pending" and _history_entry_review_key(entry) in reviewed_commit_keys:
            entry = entry.model_copy(
                update={
                    "agent_review_status": "reviewed",
                    "agent_review_ref": reviewed_commit_keys[_history_entry_review_key(entry)],
                }
            )
        normalized_entries.append(entry)
    entries = normalized_entries

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
            )
            all_evidence.update(merged_evidence)
            next_owner_moves.update(merged_moves)

    for review in agent_reviews:
        all_evidence.update(review.evidence_refs)
        next_owner_moves.update(review.next_owner_moves)

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
        agent_reviews=agent_reviews,
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


def _load_runtime_checkpoint_note(
    api: CheckpointsAPI,
    *,
    repo_root: str,
    session_file: str | None = None,
) -> SessionCheckpointNote | None:
    try:
        return api.status(repo_root=repo_root, session_file=session_file)
    except SurfaceNotFound:
        return None


def _peek_runtime_checkpoint_note(
    api: CheckpointsAPI,
    *,
    repo_root: str,
    session_file: str | None = None,
) -> SessionCheckpointNote | None:
    try:
        return api.peek_status(repo_root=repo_root, session_file=session_file)
    except SurfaceNotFound:
        return None


def _load_runtime_checkpoint_notes_for_closeout(
    api: CheckpointsAPI,
    *,
    repo_root: str,
    resolved_session_ref: str,
    primary_note: SessionCheckpointNote | None,
) -> list[tuple[_CheckpointPaths, SessionCheckpointNote]]:
    current_root = _checkpoint_current_root(api.workspace)
    if not current_root.exists():
        return []

    runtime_session_id = primary_note.runtime_session_id if primary_note is not None else None
    records: list[tuple[_CheckpointPaths, SessionCheckpointNote]] = []
    candidate_paths: list[_CheckpointPaths] = []
    seen_dirs: set[Path] = set()
    if runtime_session_id is not None:
        scope_root = current_root / cast(str, _checkpoint_runtime_scope_key(runtime_session_id))
        if scope_root.exists():
            for current_dir in sorted(path for path in scope_root.iterdir() if path.is_dir()):
                paths = _checkpoint_paths_for_label(
                    api.workspace,
                    current_dir.name,
                    runtime_session_id=runtime_session_id,
                )
                seen_dirs.add(paths.current_dir)
                candidate_paths.append(paths)
    for current_dir in sorted(path for path in current_root.iterdir() if path.is_dir()):
        if not (current_dir / "checkpoint-note.jsonl").exists():
            continue
        paths = _checkpoint_paths_for_label(api.workspace, current_dir.name, runtime_session_id=None)
        if paths.current_dir in seen_dirs:
            continue
        candidate_paths.append(paths)
        seen_dirs.add(paths.current_dir)

    for paths in candidate_paths:
        if not paths.jsonl.exists():
            continue
        note = _build_checkpoint_note(paths)
        if runtime_session_id is not None and note.runtime_session_id not in {None, runtime_session_id}:
            continue
        if _should_hide_current_checkpoint_note(note, runtime_session_id=runtime_session_id):
            _archive_current_checkpoint(paths)
            continue
        if not _checkpoint_note_matches_closeout_scope(
            note,
            resolved_session_ref=resolved_session_ref,
            runtime_session_id=runtime_session_id,
        ):
            continue
        paths.note_json.parent.mkdir(parents=True, exist_ok=True)
        paths.note_json.write_text(note.model_dump_json(indent=2) + "\n", encoding="utf-8")
        paths.note_md.write_text(
            _render_checkpoint_note_markdown(note, repo_label=paths.repo_label),
            encoding="utf-8",
        )
        records.append((paths, note))
    return records


def _checkpoint_note_matches_closeout_scope(
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


def _derive_session_end_skill_targets(note: SessionCheckpointNote | None) -> list[SessionEndSkillTarget]:
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


def _derive_session_end_next_honest_move(
    *,
    note: SessionCheckpointNote | None,
    session_end_targets: list[SessionEndSkillTarget],
) -> str | None:
    if note is None or not session_end_targets:
        return None

    skill_names = [target.skill_name for target in session_end_targets]
    if note.stats_refresh_recommended:
        return (
            "At reviewed closeout, run aoa-checkpoint-closeout-bridge so it raises "
            + ", ".join(skill_names)
            + " and refresh stats only after the reviewed handoff is assembled."
        )
    return "At reviewed closeout, run aoa-checkpoint-closeout-bridge and raise " + ", ".join(skill_names) + "."


def _render_checkpoint_note_markdown(note: SessionCheckpointNote, *, repo_label: str) -> str:
    lines = [
        "# Session Checkpoint Note",
        "",
        f"Session ref: `{note.session_ref}`",
        *([f"Runtime session id: `{note.runtime_session_id}`"] if note.runtime_session_id else []),
        f"Repo label: `{repo_label}`",
        f"State: `{note.state}`",
        f"Review status: `{note.review_status}`",
        f"Promotion recommendation: `{note.promotion_recommendation}`",
        f"Carry until session closeout: `{'yes' if note.carry_until_session_closeout else 'no'}`",
        f"Session-end recommendation: `{note.session_end_recommendation}`",
        f"Stats refresh recommended at closeout: `{'yes' if note.stats_refresh_recommended else 'no'}`",
        f"Agent checkpoint review: `{note.agent_review_status}`",
        "",
        "## Repo Scope",
        "",
    ]
    lines.extend(f"- `{scope}`" for scope in note.repo_scope)
    if note.harvest_candidate_ids:
        lines.extend(["", "## Harvest Candidates", ""])
        lines.extend(f"- `{candidate_id}`" for candidate_id in note.harvest_candidate_ids)
    if note.progression_candidate_ids:
        lines.extend(["", "## Progression Candidates", ""])
        lines.extend(f"- `{candidate_id}`" for candidate_id in note.progression_candidate_ids)
    if note.progression_axis_signals:
        lines.extend(["", "## Provisional Progression Axes", ""])
        for signal in note.progression_axis_signals:
            lines.append(
                f"- `{signal.axis}` -> `{signal.movement}`"
                + (
                    f" from {', '.join(f'`{candidate_id}`' for candidate_id in signal.candidate_ids)}"
                    if signal.candidate_ids
                    else ""
                )
            )
            lines.append(f"  - {signal.why}")
    if note.upgrade_candidate_ids:
        lines.extend(["", "## Upgrade Candidates", ""])
        lines.extend(f"- `{candidate_id}`" for candidate_id in note.upgrade_candidate_ids)
    if note.agent_reviews:
        lines.extend(["", "## Agent Checkpoint Reviews", ""])
        for review in note.agent_reviews:
            lines.extend(
                [
                    f"### {review.commit_short_sha or review.commit_ref}",
                    "",
                    f"- review id: `{review.review_id}`",
                    f"- summary: {review.summary}",
                    f"- applied skills: {', '.join(f'`{name}`' for name in review.applied_skill_names) or '`none`'}",
                    f"- defer until closeout: `{'yes' if review.defer_until_closeout else 'no'}`",
                ]
            )
            for label, values in (
                ("findings", review.findings),
                ("candidate notes", review.candidate_notes),
                ("stats hints", review.stats_hints),
                ("mechanic hints", review.mechanic_hints),
                ("closeout questions", review.closeout_questions),
            ):
                if values:
                    lines.append(f"- {label}:")
                    lines.extend(f"  - {value}" for value in values)
            if review.evidence_refs:
                lines.append("- evidence refs:")
                lines.extend(f"  - `{ref}`" for ref in review.evidence_refs)
            lines.append("")
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
        if cluster.progression_axis_signals:
            lines.append("- provisional progression axes:")
            lines.extend(
                f"  - `{signal.axis}` -> `{signal.movement}`: {signal.why}"
                for signal in cluster.progression_axis_signals
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
        observed_at = entry.observed_at.isoformat().replace("+00:00", "Z")
        observed_at_local, observed_tz = _with_local_timestamp_fallback(
            utc_value=entry.observed_at,
            local_value=entry.observed_at_local,
            tz_name=entry.observed_tz,
        )
        if observed_at_local:
            observed_at += f" (local {observed_at_local}"
            if observed_tz:
                observed_at += f" {observed_tz}"
            observed_at += ")"
        lines.append(
            f"- `{entry.checkpoint_kind}` at `{observed_at}` -> "
            + (", ".join(cluster.candidate_id for cluster in entry.candidate_clusters) or "no surviving candidates")
        )
        if entry.agent_review_status != "not_required":
            lines.append(f"  - agent review: `{entry.agent_review_status}`")
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
    session_slug = _safe_name(note.session_ref)
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


def _write_harvest_handoff(*, paths: _CheckpointPaths, note: SessionCheckpointNote) -> list[str]:
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


def _resolve_after_commit_checkpoint_kind(
    *,
    checkpoint_kind: Literal["auto", "commit", "owner_followthrough"],
    commit_subject: str | None,
    commit_body: str | None,
    existing_note: SessionCheckpointNote | None,
) -> Literal["commit", "owner_followthrough"]:
    if checkpoint_kind == "commit":
        return "commit"
    if checkpoint_kind == "owner_followthrough":
        return "owner_followthrough"
    if existing_note is not None and existing_note.state in {"closed", "promoted"}:
        return "owner_followthrough"
    inferred = _infer_auto_checkpoint_kind(
        intent_text="\n".join(part for part in (commit_subject, commit_body) if part)
    )
    return "owner_followthrough" if inferred == "owner_followthrough" else "commit"


def _after_commit_mutation_surface(
    checkpoint_kind: Literal["commit", "owner_followthrough"],
) -> Literal["code", "public-share"]:
    if checkpoint_kind == "owner_followthrough":
        return "public-share"
    return "code"


def _after_commit_intent(
    *,
    commit_short_sha: str | None,
    commit_subject: str | None,
    checkpoint_kind: Literal["commit", "owner_followthrough"],
) -> str:
    short_sha = (commit_short_sha or "HEAD").strip()
    subject = re.sub(r"\s+", " ", (commit_subject or "checkpoint").strip())
    if checkpoint_kind == "owner_followthrough":
        return f"owner follow-through commit {short_sha}: {subject}"
    return f"checkpoint commit {short_sha}: {subject}"


def _agent_review_command(*, repo_root: str, commit_ref: str, workspace_root: str) -> str:
    return (
        f"aoa checkpoint review-note {repo_root} --commit-ref {commit_ref} "
        f"--root {workspace_root} --summary '<agent checkpoint review>'"
    )


def _history_entry_review_key(entry: SessionCheckpointHistoryEntry) -> str:
    return entry.commit_sha or entry.commit_short_sha or entry.intent_text


def _agent_review_commit_keys(reviews: list[SessionCheckpointAgentReview]) -> dict[str, str]:
    keys: dict[str, str] = {}
    for review in reviews:
        for key in (review.commit_sha, review.commit_short_sha, review.commit_ref):
            if key:
                keys[key] = review.review_id
    return keys


def _mark_after_commit_report_reviewed(path: Path, *, review: SessionCheckpointAgentReview) -> None:
    if not path.exists():
        return
    payload = load_json(path)
    report = CheckpointAfterCommitReport.model_validate(payload)
    if report.commit_sha and review.commit_sha and report.commit_sha != review.commit_sha:
        return
    updated = report.model_copy(
        update={
            "agent_review_required": True,
            "agent_review_status": "reviewed",
            "agent_review_ref": review.review_id,
        }
    )
    _write_after_commit_report(path, updated)


def _run_git(repo_root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if check and result.returncode != 0:
        stderr = result.stderr.strip()
        stdout = result.stdout.strip()
        detail = stderr or stdout or f"git exited {result.returncode}"
        raise RuntimeError(f"git {' '.join(args)} failed for {repo_root}: {detail}")
    return result


def _read_git_commit_metadata(repo_root: Path, commit_ref: str) -> dict[str, Any]:
    show_result = _run_git(repo_root, "show", "-s", "--format=%H%x00%h%x00%s%x00%b", commit_ref)
    parts = show_result.stdout.split("\x00", 3)
    while len(parts) < 4:
        parts.append("")
    commit_sha, commit_short_sha, commit_subject, commit_body = [part.rstrip("\n") for part in parts[:4]]
    changed_result = _run_git(
        repo_root,
        "show",
        "--pretty=format:",
        "--name-only",
        "--diff-filter=ACDMRTUXB",
        commit_ref,
    )
    changed_paths = [
        line.strip()
        for line in changed_result.stdout.splitlines()
        if line.strip()
    ]
    return {
        "commit_sha": commit_sha,
        "commit_short_sha": commit_short_sha,
        "commit_subject": commit_subject,
        "commit_body": commit_body,
        "changed_paths": _dedupe_strings(changed_paths),
    }


def _resolve_git_hook_path(repo_root: Path) -> Path:
    result = _run_git(repo_root, "rev-parse", "--git-path", "hooks/post-commit")
    raw_path = result.stdout.strip()
    hook_path = Path(raw_path)
    if hook_path.is_absolute():
        return hook_path
    return (repo_root / hook_path).resolve()


def _render_post_commit_hook(workspace: Workspace) -> str:
    template = _hook_template_path(workspace).read_text(encoding="utf-8")
    if POST_COMMIT_HOOK_MARKER not in template:
        raise ValueError("post-commit hook template is missing the aoa-sdk version marker")
    return template.replace("__AOA_CHECKPOINT_WORKSPACE_ROOT__", str(workspace.federation_root))


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
