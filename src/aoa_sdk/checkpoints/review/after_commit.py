"""After-commit checkpoint review helpers."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any, Literal, cast

from ...loaders import load_json, write_json
from ...models import (
    CheckpointAfterCommitReport,
    SessionCheckpointAgentReview,
    SessionCheckpointAutoObservation,
    SessionCheckpointNote,
    SurfaceDetectionReport,
)
from ..kinds import infer_auto_checkpoint_kind
from ..naming import safe_checkpoint_name


def resolve_after_commit_checkpoint_kind(
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
    inferred = infer_auto_checkpoint_kind(
        intent_text="\n".join(part for part in (commit_subject, commit_body) if part)
    )
    return "owner_followthrough" if inferred == "owner_followthrough" else "commit"


def after_commit_mutation_surface(
    checkpoint_kind: Literal["commit", "owner_followthrough"],
) -> Literal["code", "public-share"]:
    if checkpoint_kind == "owner_followthrough":
        return "public-share"
    return "code"


def after_commit_intent(
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


def build_after_commit_auto_observation(
    *,
    repo_root_path: Path,
    repo_label: str,
    commit_ref: str,
    commit_metadata: dict[str, Any],
    checkpoint_kind: Literal["commit", "owner_followthrough"],
    mutation_surface: Literal["code", "public-share"],
    surface_report: SurfaceDetectionReport,
    observed_at: datetime,
    observed_at_local: str | None,
    observed_tz: str | None,
    surface_report_path: str,
) -> SessionCheckpointAutoObservation:
    commit_sha = cast(str | None, commit_metadata.get("commit_sha"))
    commit_short_sha = cast(str | None, commit_metadata.get("commit_short_sha"))
    commit_subject = cast(str | None, commit_metadata.get("commit_subject"))
    changed_paths = [
        path
        for path in cast(list[str], commit_metadata.get("changed_paths", []))
        if isinstance(path, str) and path.strip()
    ]
    related_capability_refs = _dedupe_strings(
        [
            *(
                capability_ref
                for item in surface_report.items
                for capability_ref in item.related_capability_refs
            ),
            *(
                capability_ref
                for item in surface_report.items
                for capability_ref in item.closeout_capability_candidates
            ),
        ]
    )
    candidate_ids = [cluster.candidate_id for cluster in surface_report.candidate_clusters]
    findings: list[str] = []
    if changed_paths:
        findings.append(f"tracked paths changed: {_preview_strings(changed_paths, limit=5)}")
    if related_capability_refs:
        findings.append(
            "surface inspection linked capability candidate(s): "
            + _preview_strings(related_capability_refs, limit=6)
        )
    if surface_report.candidate_clusters:
        findings.append(
            f"surface detection preserved {len(surface_report.candidate_clusters)} checkpoint candidate(s): "
            + _preview_strings(candidate_ids, limit=4)
        )
    if surface_report.blocked_by:
        findings.append(
            "checkpoint-time promotion remains blocked by: "
            + _preview_strings(surface_report.blocked_by, limit=4)
        )

    candidate_notes = [
        cluster.candidate_id
        + f" -> owner {cluster.owner_hint}/{cluster.candidate_kind}"
        + (
            f"; blocked by {_preview_strings(cluster.blocked_by, limit=3)}"
            if cluster.blocked_by
            else ""
        )
        + (
            f"; next move {cluster.next_owner_moves[0]}"
            if cluster.next_owner_moves
            else ""
        )
        for cluster in surface_report.candidate_clusters
    ]

    stats_hints: list[str] = []
    if surface_report.candidate_clusters:
        stats_hints.append(
            "refresh stats only after reviewed closeout confirms which checkpoint candidates survive the full-session reread"
        )

    mechanic_hints = [
        "treat auto-observation output as provisional checkpoint collection rather than agent-reviewed session judgment",
        "treat related capability refs as routing context, not proof that any skill or workflow executed",
    ]
    if mutation_surface == "public-share":
        mechanic_hints.append(
            "owner-followthrough capture should preserve publish-surface evidence without reopening or rotating a closed checkpoint ledger"
        )

    closeout_questions: list[str] = []
    if any(block == "owner-ambiguity" for block in surface_report.blocked_by):
        closeout_questions.append(
            "does the full-session reread clarify the right owner layer, or should this remain only an early tracked candidate?"
        )
    if checkpoint_kind == "owner_followthrough":
        closeout_questions.append(
            "did the reviewed closeout already justify this owner follow-through, or is this commit over-claiming beyond checkpoint authority?"
        )
    else:
        closeout_questions.append(
            "does the later verify-green or reviewed session reread confirm that this commit seam still survives as a real candidate?"
        )

    next_owner_moves = _dedupe_strings(
        [
            *surface_report.closeout_followups,
            *(cluster.next_owner_moves[0] for cluster in surface_report.candidate_clusters if cluster.next_owner_moves),
            "write an explicit agent checkpoint review before treating this commit boundary as semantically understood",
        ]
    )
    evidence_refs = _dedupe_strings(
        [
            *([f"commit:{commit_sha}"] if commit_sha else []),
            *(f"path:{path}" for path in changed_paths),
            surface_report_path,
            *(f"surface-input:{source_ref}" for source_ref in surface_report.source_inputs),
            *(
                evidence.ref
                for item in surface_report.items
                for evidence in item.evidence_refs
            ),
            *(cluster.source_surface_ref for cluster in surface_report.candidate_clusters),
            *(ref for cluster in surface_report.candidate_clusters for ref in cluster.evidence_refs[:3]),
        ]
    )

    observation_kind = "owner follow-through" if checkpoint_kind == "owner_followthrough" else "commit"
    normalized_commit_subject = re.sub(r"\s+", " ", (commit_subject or "checkpoint").strip())
    summary = (
        f"Auto-captured {observation_kind} checkpoint observation for {commit_short_sha or commit_ref}: "
        f"{normalized_commit_subject}"
    )
    return SessionCheckpointAutoObservation(
        observation_id=(
            "auto-observation:"
            f"{safe_checkpoint_name(commit_short_sha or commit_ref)}:"
            f"{observed_at.strftime('%Y%m%dT%H%M%SZ')}"
        ),
        observed_at=observed_at,
        observed_at_local=observed_at_local,
        observed_tz=observed_tz,
        repo_root=str(repo_root_path),
        repo_label=repo_label,
        commit_ref=commit_ref,
        commit_sha=commit_sha,
        commit_short_sha=commit_short_sha,
        commit_subject=commit_subject,
        summary=summary,
        related_capability_refs=related_capability_refs,
        findings=findings,
        candidate_notes=candidate_notes,
        stats_hints=stats_hints,
        mechanic_hints=mechanic_hints,
        closeout_questions=closeout_questions,
        evidence_refs=evidence_refs,
        next_owner_moves=next_owner_moves,
    )


def agent_review_command(*, repo_root: str, commit_ref: str, workspace_root: str) -> str:
    return (
        f"aoa checkpoint review-note {repo_root} --commit-ref {commit_ref} "
        f"--auto --root {workspace_root}"
    )


def write_after_commit_report(path: Path, report: CheckpointAfterCommitReport) -> None:
    payload = report.model_dump(mode="json")
    payload["report_path"] = str(path)
    write_json(path, payload)


def mark_after_commit_report_reviewed(path: Path, *, review: SessionCheckpointAgentReview) -> None:
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
    write_after_commit_report(path, updated)


def _preview_strings(values: list[str], *, limit: int = 4) -> str:
    items = [value.strip() for value in values if value and value.strip()]
    if not items:
        return "none"
    preview = items[:limit]
    text = ", ".join(preview)
    if len(items) > limit:
        text += f" (+{len(items) - limit} more)"
    return text


def _dedupe_strings(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))
