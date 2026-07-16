from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Literal, cast

from ..errors import RepoNotFound
from ..models import (
    CheckpointCandidateCluster,
    CheckpointLineageHint,
    ProgressionAxisSignal,
    SessionCheckpointNote,
    SurfaceOpportunityItem,
)
from ..workspace.discovery import Workspace
from .common import (
    CheckpointKind,
    ExplicitGrowthCheckpointKind,
    MutationSurface,
    context_label,
    dedupe_strings,
    session_scope_name,
    slugify,
)
from .progression import (
    axis_pressure_from_signals,
    progression_axis_signals_for_explicit_growth,
    progression_axis_signals_for_item,
)


OWNER_SHAPE_BY_REPO = {
    "aoa-techniques": "technique",
    "aoa-skills": "skill",
    "aoa-evals": "eval",
    "aoa-memo": "memo",
    "aoa-playbooks": "playbook",
    "aoa-agents": "agent",
    "aoa-sdk": "runtime_surface",
    "aoa-stats": "summary_surface",
    "Dionysus": "seed",
}
NEAREST_WRONG_TARGET_BY_REPO = {
    "aoa-playbooks": "aoa-skills",
    "aoa-skills": "aoa-playbooks",
    "aoa-evals": "aoa-skills",
    "aoa-memo": "aoa-evals",
    "aoa-agents": "aoa-skills",
    "aoa-techniques": "aoa-skills",
    "aoa-sdk": "aoa-skills",
    "aoa-stats": "aoa-evals",
    "Dionysus": "aoa-skills",
}


def derive_explicit_mutation_growth_clusters(
    *,
    workspace: Workspace,
    repo_root: str,
    mutation_surface: MutationSurface,
    intent_text: str,
    checkpoint_kind: CheckpointKind | None,
    source_refs: list[str],
) -> list[CheckpointCandidateCluster]:
    if checkpoint_kind not in {
        "commit",
        "verify_green",
        "pr_opened",
        "pr_merged",
        "owner_followthrough",
    }:
        return []
    explicit_checkpoint_kind = cast(
        ExplicitGrowthCheckpointKind,
        checkpoint_kind,
    )
    if mutation_surface == "none":
        return []
    if not intent_explicitly_requests_checkpoint_kind(
        intent_text=intent_text,
        checkpoint_kind=explicit_checkpoint_kind,
    ):
        return []

    label = context_label(workspace, repo_root)
    evidence_refs = explicit_mutation_growth_evidence_refs(
        source_refs=source_refs,
        mutation_surface=mutation_surface,
        context_label=label,
    )
    if len(evidence_refs) < 2:
        return []

    blocked_by: list[str] = []
    defer_reason: str | None = None
    if label == "workspace":
        blocked_by.append("owner-ambiguity")
        defer_reason = "workspace-wide mutation growth still needs owner review before promotion beyond the local note"

    display_name_by_kind = {
        "commit": "Commit growth seam",
        "verify_green": "Verify-green growth seam",
        "pr_opened": "PR-opened growth seam",
        "pr_merged": "PR-merged growth seam",
        "owner_followthrough": "Owner follow-through growth seam",
    }
    review_move_by_kind = {
        "commit": "review the same bounded mutation again after verify-green before promoting it",
        "verify_green": "confirm the verify-green seam still points to the same bounded owner context",
        "pr_opened": "keep the opened PR tied to the reviewed closeout evidence before promotion",
        "pr_merged": "confirm the merged PR state is reflected in the final reviewed closeout",
        "owner_followthrough": "route owner follow-through through the reviewed closeout handoff before promotion",
    }
    promote_if = [
        promote_hint_for_explicit_checkpoint_kind(explicit_checkpoint_kind),
        "repeat the same bounded mutation seam across another reviewed checkpoint before promoting beyond the local note",
    ]
    next_owner_moves = [
        "append the explicit mutation seam into the local checkpoint note",
        "carry the explicit mutation seam through reviewed session closeout before moving candidates or stats",
        review_move_by_kind[explicit_checkpoint_kind],
    ]
    candidate_id = f"candidate:growth:{slugify(f'{label}-{explicit_checkpoint_kind}-{mutation_surface}')}"
    confidence: Literal["low", "medium", "high"] = (
        "high"
        if explicit_checkpoint_kind in {"verify_green", "pr_merged", "owner_followthrough"}
        else "medium"
    )
    progression_axis_signals = progression_axis_signals_for_explicit_growth(
        candidate_id=candidate_id,
        checkpoint_kind=explicit_checkpoint_kind,
        blocked_by=blocked_by,
        evidence_refs=evidence_refs,
    )

    return [
        CheckpointCandidateCluster(
            candidate_id=candidate_id,
            candidate_kind="growth",
            owner_hint=label,
            display_name=display_name_by_kind[explicit_checkpoint_kind],
            source_surface_ref=f"aoa-sdk:checkpoint_auto_capture.{explicit_checkpoint_kind}",
            evidence_refs=evidence_refs,
            confidence=confidence,
            session_end_targets=["harvest", "progression"],
            progression_axis_signals=progression_axis_signals,
            promote_if=promote_if,
            defer_reason=defer_reason,
            blocked_by=blocked_by,
            next_owner_moves=next_owner_moves,
            lineage_hint=build_checkpoint_lineage_hint(
                candidate_id=candidate_id,
                candidate_kind="growth",
                owner_hint=label,
                source_surface_ref=f"aoa-sdk:checkpoint_auto_capture.{explicit_checkpoint_kind}",
                evidence_refs=evidence_refs,
                confidence=confidence,
                blocked_by=blocked_by,
                progression_axis_signals=progression_axis_signals,
                defer_reason=defer_reason,
            ),
        )
    ]


def dedupe_checkpoint_candidate_clusters(
    clusters: list[CheckpointCandidateCluster],
) -> list[CheckpointCandidateCluster]:
    deduped: dict[tuple[str, str], CheckpointCandidateCluster] = {}
    for cluster in clusters:
        deduped[(cluster.candidate_id, cluster.owner_hint)] = cluster
    return list(deduped.values())


def build_checkpoint_lineage_hint(
    *,
    candidate_id: str,
    candidate_kind: str,
    owner_hint: str,
    source_surface_ref: str,
    evidence_refs: list[str],
    confidence: Literal["low", "medium", "high"],
    blocked_by: list[str],
    progression_axis_signals: list[ProgressionAxisSignal],
    defer_reason: str | None,
) -> CheckpointLineageHint:
    return CheckpointLineageHint(
        cluster_ref=f"cluster:{candidate_kind}:{slugify(candidate_id)}",
        owner_hypothesis=owner_hint,
        owner_shape=owner_shape(owner_hint=owner_hint, candidate_kind=candidate_kind),
        nearest_wrong_target=nearest_wrong_target_repo(owner_hint=owner_hint),
        status_posture=lineage_status_posture(blocked_by=blocked_by, confidence=confidence),
        evidence_refs=list(evidence_refs),
        axis_pressure=axis_pressure_from_signals(progression_axis_signals),
        supersedes=[],
        merged_into=None,
        drop_reason=defer_reason if "thin-evidence" in blocked_by else None,
    )


def owner_shape(*, owner_hint: str, candidate_kind: str) -> str:
    if owner_hint in OWNER_SHAPE_BY_REPO:
        return OWNER_SHAPE_BY_REPO[owner_hint]
    shape_by_candidate_kind = {
        "route": "playbook",
        "pattern": "technique",
        "proof": "eval",
        "recall": "memo",
        "role": "agent",
        "risk": "skill",
        "growth": "runtime_surface",
    }
    return shape_by_candidate_kind.get(candidate_kind, "runtime_surface")


def nearest_wrong_target_repo(*, owner_hint: str) -> str:
    return NEAREST_WRONG_TARGET_BY_REPO.get(owner_hint, "aoa-skills")


def lineage_status_posture(
    *,
    blocked_by: list[str],
    confidence: Literal["low", "medium", "high"],
) -> Literal["early", "reanchor", "thin-evidence", "stable"]:
    if "owner-ambiguity" in blocked_by:
        return "reanchor"
    if "thin-evidence" in blocked_by:
        return "thin-evidence"
    if confidence == "high" and not blocked_by:
        return "stable"
    return "early"


def promote_hint_for_explicit_checkpoint_kind(
    checkpoint_kind: ExplicitGrowthCheckpointKind,
) -> str:
    if checkpoint_kind == "verify_green":
        return "keep the same bounded mutation seam stable through a reviewed verify-green pass"
    if checkpoint_kind == "pr_opened":
        return "pair this opened PR seam with green checks or merge evidence before promotion"
    if checkpoint_kind == "pr_merged":
        return "pair this merged PR seam with reviewed closeout evidence before promotion"
    if checkpoint_kind == "owner_followthrough":
        return "owner follow-through already exists; keep promotion gated by reviewed closeout evidence"
    return "pair this explicit commit seam with one reviewed verify-green checkpoint before promotion"


def intent_explicitly_requests_checkpoint_kind(
    *,
    intent_text: str,
    checkpoint_kind: ExplicitGrowthCheckpointKind,
) -> bool:
    normalized = re.sub(r"[\s_-]+", " ", intent_text.strip().lower())
    if checkpoint_kind == "verify_green":
        return any(
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
        )
    if checkpoint_kind == "pr_opened":
        padded = f" {normalized} "
        return (
            "pull request" in normalized
            or "review thread" in normalized
            or (" pr " in padded and any(token in normalized for token in ("open", "opened", "created", "draft")))
        )
    if checkpoint_kind == "pr_merged":
        return any(
            token in normalized
            for token in (
                "pull request merged",
                "merged pull request",
                "pr merged",
                "merged pr",
                "merge complete",
            )
        )
    if checkpoint_kind == "owner_followthrough":
        return any(
            token in normalized
            for token in (
                "owner follow through",
                "owner followthrough",
                "owner handoff",
                "follow through",
                "followthrough",
            )
        )
    return "checkpoint" in normalized or "commit" in normalized


def explicit_mutation_growth_evidence_refs(
    *,
    source_refs: list[str],
    mutation_surface: MutationSurface,
    context_label: str,
) -> list[str]:
    refs = [
        f"context:{context_label}",
        f"mutation_surface:{mutation_surface}",
    ]
    refs.extend(source_refs)
    return dedupe_strings(refs)


def derive_checkpoint_candidate_clusters(
    *,
    items: list[SurfaceOpportunityItem],
    checkpoint_kind: CheckpointKind | None,
) -> list[CheckpointCandidateCluster]:
    clusters: list[CheckpointCandidateCluster] = []
    for item in items:
        evidence_refs = dedupe_strings(
            [
                *[ref.ref for ref in item.family_entry_refs],
                *[ref.ref for ref in item.evidence_refs],
                item.surface_ref,
            ]
        )
        blocked_by: list[str] = []
        if item.owner_layer_ambiguity_note:
            blocked_by.append("owner-ambiguity")
        if len(evidence_refs) < 2 or item.confidence == "low":
            blocked_by.append("thin-evidence")
        candidate_kind = candidate_kind_for_item(item)
        defer_reason = None
        if "owner-ambiguity" in blocked_by:
            defer_reason = "owner ambiguity still exceeds checkpoint-note promotion authority"
        elif "thin-evidence" in blocked_by:
            defer_reason = "thin evidence should stay local until another checkpoint confirms the same candidate"
        promote_if = dedupe_strings(
            [
                item.promotion_hint or "",
                "repeat the same owner hint across another reviewed checkpoint",
                *(
                    ["owner follow-through already exists"]
                    if checkpoint_kind == "owner_followthrough"
                    else []
                ),
            ]
        )
        next_owner_moves = dedupe_strings(
            [
                "append the candidate into the local checkpoint note",
                "carry the candidate through reviewed session closeout before moving candidates or stats",
                *(
                    ["promote the reviewed note into Dionysus when the evidence stays stable"]
                    if "owner-ambiguity" not in blocked_by
                    else []
                ),
            ]
        )
        candidate_id = f"candidate:{candidate_kind}:{slugify(item.surface_ref)}"
        progression_axis_signals = progression_axis_signals_for_item(
            item,
            candidate_kind=candidate_kind,
            blocked_by=blocked_by,
            evidence_refs=evidence_refs,
        )
        clusters.append(
            CheckpointCandidateCluster(
                candidate_id=candidate_id,
                candidate_kind=candidate_kind,
                owner_hint=item.owner_repo,
                display_name=item.display_name,
                source_surface_ref=item.surface_ref,
                evidence_refs=evidence_refs,
                confidence=item.confidence,
                session_end_targets=session_end_targets_for_candidate_kind(candidate_kind),
                progression_axis_signals=progression_axis_signals,
                promote_if=promote_if,
                defer_reason=defer_reason,
                blocked_by=blocked_by,
                next_owner_moves=next_owner_moves,
                lineage_hint=build_checkpoint_lineage_hint(
                    candidate_id=candidate_id,
                    candidate_kind=candidate_kind,
                    owner_hint=item.owner_repo,
                    source_surface_ref=item.surface_ref,
                    evidence_refs=evidence_refs,
                    confidence=item.confidence,
                    blocked_by=blocked_by,
                    progression_axis_signals=progression_axis_signals,
                    defer_reason=defer_reason,
                ),
            )
        )
    return clusters


def candidate_kind_for_item(item: SurfaceOpportunityItem) -> str:
    if item.object_kind == "playbook":
        return "route"
    if item.object_kind == "technique":
        return "pattern"
    if item.object_kind == "eval":
        return "proof"
    if item.object_kind == "memo":
        return "recall"
    if item.object_kind == "agent":
        return "role"
    if item.object_kind == "skill":
        return "risk"
    return item.object_kind


def session_end_targets_for_candidate_kind(
    candidate_kind: str,
) -> list[Literal["harvest", "progression", "upgrade"]]:
    targets: list[Literal["harvest", "progression", "upgrade"]] = ["harvest", "progression"]
    if candidate_kind in {"route", "pattern", "proof", "recall", "role"}:
        targets.append("upgrade")
    return targets


def checkpoint_blocked_by(clusters: list[CheckpointCandidateCluster]) -> list[str]:
    return dedupe_strings([blocked for cluster in clusters for blocked in cluster.blocked_by])


def checkpoint_promotion_recommendation(
    *,
    candidate_clusters: list[CheckpointCandidateCluster],
    checkpoint_kind: CheckpointKind | None,
) -> Literal["none", "local_note", "dionysus_note", "harvest_handoff"]:
    if not candidate_clusters:
        return "none"
    if checkpoint_kind == "owner_followthrough" and any("owner-ambiguity" not in cluster.blocked_by for cluster in candidate_clusters):
        return "harvest_handoff"
    if any(len(cluster.evidence_refs) >= 3 and "owner-ambiguity" not in cluster.blocked_by for cluster in candidate_clusters):
        return "dionysus_note"
    return "local_note"


def load_current_checkpoint_note(workspace: Workspace, repo_root: str) -> SessionCheckpointNote | None:
    for note_path in candidate_checkpoint_note_paths(workspace, repo_root):
        if not note_path.exists():
            continue
        try:
            return SessionCheckpointNote.model_validate_json(note_path.read_text(encoding="utf-8"))
        except Exception:
            continue
    return None


def checkpoint_note_ref(workspace: Workspace, repo_root: str, note: SessionCheckpointNote | None) -> str | None:
    if note is None:
        return None
    for note_path in candidate_checkpoint_note_paths(
        workspace,
        repo_root,
        runtime_session_id=note.runtime_session_id,
    ):
        if note_path.exists():
            return str(note_path)
    return None


def candidate_checkpoint_note_paths(
    workspace: Workspace,
    repo_root: str,
    *,
    runtime_session_id: str | None = None,
) -> list[Path]:
    try:
        sdk_root = workspace.repo_path("aoa-sdk")
    except RepoNotFound:
        return []
    current_root = sdk_root / ".aoa" / "session-growth" / "current"
    label = context_label(workspace, repo_root)
    resolved_runtime_session_id = runtime_session_id or active_runtime_session_id(workspace)
    paths: list[Path] = []
    if isinstance(resolved_runtime_session_id, str) and resolved_runtime_session_id.strip():
        scope_name = session_scope_name(resolved_runtime_session_id)
        paths.append(current_root / scope_name / label / "checkpoint-note.json")
    paths.append(current_root / label / "checkpoint-note.json")
    return paths


def active_runtime_session_id(workspace: Workspace) -> str | None:
    del workspace
    for env_name in ("AOA_SESSION_ID", "CODEX_THREAD_ID"):
        value = os.environ.get(env_name)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None
