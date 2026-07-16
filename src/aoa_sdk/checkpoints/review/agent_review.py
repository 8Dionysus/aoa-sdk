"""Agent-authored checkpoint review helpers."""

from __future__ import annotations

import re

from ...models import (
    CheckpointCloseoutReviewCarry,
    SessionCheckpointAgentReview,
    SessionCheckpointAutoObservation,
    SessionCheckpointHistoryEntry,
    SessionCheckpointNote,
)


def auto_review_summary(
    *,
    auto_observation: SessionCheckpointAutoObservation | None,
    history_entry: SessionCheckpointHistoryEntry | None,
    commit_ref: str,
    commit_subject: str | None,
    commit_short_sha: str | None,
) -> str:
    subject = re.sub(
        r"\s+",
        " ",
        (
            commit_subject
            or (auto_observation.commit_subject if auto_observation is not None else None)
            or (history_entry.intent_text if history_entry is not None else None)
            or "checkpoint"
        ).strip(),
    )
    if auto_observation is not None:
        observation_kind = (
            "owner follow-through checkpoint"
            if "owner follow-through" in auto_observation.summary.lower()
            else "commit checkpoint"
        )
    else:
        observation_kind = (
            "owner follow-through checkpoint"
            if history_entry is not None and history_entry.checkpoint_kind == "owner_followthrough"
            else "commit checkpoint"
        )
    derivation = "auto-captured" if auto_observation is not None else "auto-derived"
    return (
        f"Agent reviewed the {derivation} {observation_kind} for "
        f"{commit_short_sha or (auto_observation.commit_short_sha if auto_observation is not None else None) or (history_entry.commit_short_sha if history_entry is not None else None) or commit_ref}: {subject}"
    )


def merge_auto_review_items(
    *,
    explicit_items: list[str] | None,
    auto_items: list[str],
) -> list[str]:
    return _dedupe_strings([*(explicit_items or []), *auto_items])


def matching_checkpoint_history_entry(
    *,
    note: SessionCheckpointNote,
    commit_ref: str,
    commit_sha: str | None,
    commit_short_sha: str | None,
) -> SessionCheckpointHistoryEntry | None:
    for entry in reversed(note.checkpoint_history):
        if commit_sha and entry.commit_sha == commit_sha:
            return entry
        if commit_short_sha and entry.commit_short_sha == commit_short_sha:
            return entry
        if entry.intent_text and commit_ref in entry.intent_text:
            return entry
    return None


def history_auto_review_evidence_refs(entry: SessionCheckpointHistoryEntry) -> list[str]:
    refs = [
        *([entry.report_ref] if entry.report_ref is not None else []),
        *([f"commit:{entry.commit_sha}"] if entry.commit_sha else []),
        *(cluster.source_surface_ref for cluster in entry.candidate_clusters),
        *(ref for cluster in entry.candidate_clusters for ref in cluster.evidence_refs[:3]),
    ]
    return _dedupe_strings([ref for ref in refs if isinstance(ref, str) and ref])


def auto_review_findings(
    *,
    auto_observation: SessionCheckpointAutoObservation | None,
    history_entry: SessionCheckpointHistoryEntry | None,
    auto_fill: bool,
) -> list[str]:
    if not auto_fill:
        return []
    if auto_observation is not None:
        return auto_observation.findings
    if history_entry is not None:
        return _history_auto_review_findings(history_entry)
    return []


def auto_review_candidate_notes(
    *,
    auto_observation: SessionCheckpointAutoObservation | None,
    history_entry: SessionCheckpointHistoryEntry | None,
    auto_fill: bool,
) -> list[str]:
    if not auto_fill:
        return []
    if auto_observation is not None:
        return auto_observation.candidate_notes
    if history_entry is not None:
        return _history_auto_review_candidate_notes(history_entry)
    return []


def auto_review_stats_hints(
    *,
    auto_observation: SessionCheckpointAutoObservation | None,
    history_entry: SessionCheckpointHistoryEntry | None,
    auto_fill: bool,
) -> list[str]:
    if not auto_fill:
        return []
    if auto_observation is not None:
        return auto_observation.stats_hints
    if history_entry is not None:
        return _history_auto_review_stats_hints(history_entry)
    return []


def auto_review_mechanic_hints(
    *,
    auto_observation: SessionCheckpointAutoObservation | None,
    history_entry: SessionCheckpointHistoryEntry | None,
    auto_fill: bool,
) -> list[str]:
    if not auto_fill:
        return []
    if auto_observation is not None:
        return auto_observation.mechanic_hints
    if history_entry is not None:
        return _history_auto_review_mechanic_hints(history_entry)
    return []


def auto_review_closeout_questions(
    *,
    auto_observation: SessionCheckpointAutoObservation | None,
    history_entry: SessionCheckpointHistoryEntry | None,
    auto_fill: bool,
) -> list[str]:
    if not auto_fill:
        return []
    if auto_observation is not None:
        return auto_observation.closeout_questions
    if history_entry is not None:
        return _history_auto_review_closeout_questions(history_entry)
    return []


def auto_review_next_owner_moves(
    *,
    auto_observation: SessionCheckpointAutoObservation | None,
    history_entry: SessionCheckpointHistoryEntry | None,
    auto_fill: bool,
) -> list[str]:
    if not auto_fill:
        return []
    if auto_observation is not None:
        return auto_observation.next_owner_moves
    if history_entry is not None:
        return _history_auto_review_next_owner_moves(history_entry)
    return []


def matching_auto_observation(
    *,
    note: SessionCheckpointNote,
    commit_ref: str,
    commit_sha: str | None,
    commit_short_sha: str | None,
) -> SessionCheckpointAutoObservation | None:
    for entry in reversed(note.checkpoint_history):
        observation = entry.auto_observation
        if observation is None:
            continue
        if commit_sha and observation.commit_sha == commit_sha:
            return observation
        if commit_short_sha and observation.commit_short_sha == commit_short_sha:
            return observation
        if observation.commit_ref == commit_ref:
            return observation
    return None


def closeout_pending_agent_review_refs(notes: list[SessionCheckpointNote]) -> list[str]:
    pending_refs: list[str] = []
    for note in notes:
        pending_refs.extend(note.agent_review_pending_refs)
    return _dedupe_strings(pending_refs)


def collect_review_carry(reviews: list[SessionCheckpointAgentReview]) -> CheckpointCloseoutReviewCarry:
    return CheckpointCloseoutReviewCarry(
        review_refs=_dedupe_strings([review.review_id for review in reviews]),
        auto_observation_refs=_dedupe_strings(
            [
                review.auto_observation_ref
                for review in reviews
                if review.auto_observation_ref is not None
            ]
        ),
        related_capability_refs=_dedupe_strings(
            [
                capability_ref
                for review in reviews
                for capability_ref in review.related_capability_refs
            ]
        ),
        summaries=_dedupe_strings([review.summary for review in reviews]),
        findings=_dedupe_strings([item for review in reviews for item in review.findings]),
        candidate_notes=_dedupe_strings([item for review in reviews for item in review.candidate_notes]),
        stats_hints=_dedupe_strings([item for review in reviews for item in review.stats_hints]),
        mechanic_hints=_dedupe_strings([item for review in reviews for item in review.mechanic_hints]),
        closeout_questions=_dedupe_strings(
            [item for review in reviews for item in review.closeout_questions]
        ),
        evidence_refs=_dedupe_strings([item for review in reviews for item in review.evidence_refs]),
        next_owner_moves=_dedupe_strings([item for review in reviews for item in review.next_owner_moves]),
    )


def collect_closeout_review_carry(notes: list[SessionCheckpointNote]) -> CheckpointCloseoutReviewCarry:
    return collect_review_carry([review for note in notes for review in note.agent_reviews])


def history_entry_review_key(entry: SessionCheckpointHistoryEntry) -> str:
    return entry.commit_sha or entry.commit_short_sha or entry.intent_text


def agent_review_key(review: SessionCheckpointAgentReview) -> str:
    return review.commit_sha or review.commit_short_sha or review.commit_ref or review.review_id


def agent_review_commit_keys(reviews: list[SessionCheckpointAgentReview]) -> dict[str, str]:
    keys: dict[str, str] = {}
    for review in reviews:
        for key in (
            review.commit_sha,
            review.commit_short_sha,
            review.commit_ref,
            agent_review_key(review),
        ):
            if key:
                keys[key] = review.review_id
    return keys


def _history_auto_review_findings(entry: SessionCheckpointHistoryEntry) -> list[str]:
    candidate_kinds = sorted({cluster.candidate_kind for cluster in entry.candidate_clusters if cluster.candidate_kind})
    findings = []
    if entry.candidate_clusters:
        findings.append(
            "what: checkpoint history already preserved "
            f"{len(entry.candidate_clusters)} candidate cluster(s) across {', '.join(candidate_kinds) or 'reviewable seams'}; "
            "why: semantic review should stay attached to the original commit boundary"
        )
    if entry.blocked_by:
        findings.append(
            "what: checkpoint history still carries blockers "
            f"({', '.join(entry.blocked_by)}); why: reviewed closeout should revisit them explicitly instead of skipping ahead"
        )
    if not findings:
        findings.append(
            "what: checkpoint history preserved a pending review boundary; why: this commit still needs semantic review before closeout or promotion"
        )
    return findings


def _history_auto_review_candidate_notes(entry: SessionCheckpointHistoryEntry) -> list[str]:
    notes: list[str] = []
    for cluster in entry.candidate_clusters[:3]:
        notes.append(
            f"candidate: {cluster.display_name} -> {cluster.owner_hint} ({cluster.candidate_kind}) via {cluster.source_surface_ref}"
        )
    return notes


def _history_auto_review_stats_hints(entry: SessionCheckpointHistoryEntry) -> list[str]:
    if entry.candidate_clusters or entry.blocked_by:
        return [
            "stats: refresh only after reviewed closeout confirms which checkpoint candidates and blockers still survive from this commit boundary"
        ]
    return []


def _history_auto_review_mechanic_hints(entry: SessionCheckpointHistoryEntry) -> list[str]:
    hints = [
        "mechanic: older pending checkpoint reviews without auto_observation should still be resolved from checkpoint history before closeout"
    ]
    if entry.manual_review_requested:
        hints.append(
            "mechanic: keep semantic checkpoint review coupled to the commit boundary before promotion or reviewed closeout"
        )
    return hints


def _history_auto_review_closeout_questions(entry: SessionCheckpointHistoryEntry) -> list[str]:
    candidate_targets = ", ".join(cluster.display_name for cluster in entry.candidate_clusters[:2])
    if candidate_targets:
        return [
            f"closeout: does the full session still support the same owner hints and blockers around {candidate_targets}?"
        ]
    return [
        "closeout: does the full session still support the same checkpoint boundary judgment recorded for this commit?"
    ]


def _history_auto_review_next_owner_moves(entry: SessionCheckpointHistoryEntry) -> list[str]:
    return _dedupe_strings(
        [move for cluster in entry.candidate_clusters for move in cluster.next_owner_moves]
    )


def _dedupe_strings(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))
