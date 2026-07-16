"""Reviewed owner-candidate handoff materialization for checkpoint closeout."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from ...loaders import load_json, write_json
from ...models import (
    CheckpointCloseoutContext,
    CheckpointOwnerHandoff,
    CheckpointOwnerHandoffItem,
    SessionCheckpointCluster,
)
from ...workspace.discovery import Workspace
from ..naming import safe_checkpoint_name as _safe_name
from .common import _dedupe_strings


ALLOWED_OWNER_REPOS = {
    "aoa-techniques",
    "aoa-skills",
    "aoa-evals",
    "aoa-memo",
    "aoa-playbooks",
    "aoa-agents",
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


def _checkpoint_closeout_handoff_root(workspace: Workspace) -> Path:
    return workspace.repo_path("aoa-sdk") / ".aoa" / "closeout" / "handoffs"


def _load_checkpoint_owner_handoff_for_session(
    workspace: Workspace,
    *,
    session_ref: str,
) -> CheckpointOwnerHandoff | None:
    handoff_root = _checkpoint_closeout_handoff_root(workspace)
    if not handoff_root.exists():
        return None
    direct_path = handoff_root / f"{_safe_name(session_ref)}.owner-handoff.json"
    candidate_paths = [direct_path] if direct_path.exists() else []
    candidate_paths.extend(
        sorted(path for path in handoff_root.glob("*.owner-handoff.json") if path != direct_path)
    )
    for path in candidate_paths:
        try:
            payload = CheckpointOwnerHandoff.model_validate(load_json(path))
        except Exception:
            continue
        if payload.session_ref == session_ref:
            return payload
    return None


def _has_reviewed_closeout_owner_handoff_for_repo(
    workspace: Workspace,
    *,
    session_ref: str | None,
    repo_label: str,
) -> bool:
    if not session_ref:
        return False
    handoff = _load_checkpoint_owner_handoff_for_session(
        workspace,
        session_ref=session_ref,
    )
    return bool(
        handoff is not None
        and handoff.reviewed
        and any(item.owner_repo == repo_label for item in handoff.items)
    )


def _write_checkpoint_owner_handoff(
    *,
    workspace: Workspace,
    closeout_context_ref: Path,
    context: CheckpointCloseoutContext,
    shortlisted_clusters: list[SessionCheckpointCluster],
    reviewed_artifact: Path,
) -> tuple[Path | None, CheckpointOwnerHandoff | None]:
    items = [
        _owner_handoff_item(
            cluster=cluster,
            context=context,
            reviewed_artifact=reviewed_artifact,
        )
        for cluster in shortlisted_clusters
    ]
    if not items:
        return None, None

    handoff = CheckpointOwnerHandoff(
        session_ref=context.session_ref,
        context_ref=str(closeout_context_ref),
        generated_at=datetime.now(UTC),
        items=items,
    )
    handoff_root = _checkpoint_closeout_handoff_root(workspace)
    handoff_root.mkdir(parents=True, exist_ok=True)
    handoff_path = handoff_root / f"{_safe_name(context.session_ref)}.owner-handoff.json"
    write_json(handoff_path, handoff.model_dump(mode="json"))
    return handoff_path, handoff


def _owner_handoff_item(
    *,
    cluster: SessionCheckpointCluster,
    context: CheckpointCloseoutContext,
    reviewed_artifact: Path,
) -> CheckpointOwnerHandoffItem:
    owner_repo = cluster.owner_hint.strip() or "unresolved-owner"
    known_owner = owner_repo in ALLOWED_OWNER_REPOS
    abstraction_shape = (
        ABSTRACTION_SHAPE_BY_OWNER[owner_repo]
        if known_owner
        else cluster.lineage_hint.owner_shape
        if cluster.lineage_hint is not None
        else "unresolved"
    )
    proposed_surface = (
        DEFAULT_ARTIFACT_BY_OWNER[owner_repo].format(
            slug=_safe_name(cluster.display_name or cluster.candidate_id)
        )
        if known_owner
        else f"owner-review:{cluster.candidate_id}"
    )
    lineage = cluster.lineage_hint
    if lineage is not None and lineage.status_posture == "reanchor":
        decision_posture: Literal[
            "review-required", "prove-first", "reanchor-owner"
        ] = "reanchor-owner"
    elif cluster.blocked_by or cluster.defer_reason or (
        lineage is not None and lineage.status_posture == "thin-evidence"
    ):
        decision_posture = "prove-first"
    else:
        decision_posture = "review-required"
    return CheckpointOwnerHandoffItem(
        candidate_ref=cluster.candidate_id,
        owner_repo=owner_repo,
        owner_ref=f"repo:{owner_repo}",
        proposed_surface=proposed_surface,
        decision_posture=decision_posture,
        abstraction_shape=abstraction_shape,
        nearest_wrong_target=(
            lineage.nearest_wrong_target
            if lineage is not None and lineage.nearest_wrong_target != owner_repo
            else None
        ),
        why=(
            f"The reviewed checkpoint candidate remains {cluster.candidate_kind}-shaped; "
            f"{owner_repo} must decide whether {proposed_surface} is warranted."
        ),
        evidence_refs=_dedupe_strings(
            [
                str(reviewed_artifact),
                *([context.session_trace_ref] if context.session_trace_ref else []),
                *context.checkpoint_review_carry.evidence_refs,
                *cluster.evidence_refs,
            ]
        ),
    )
