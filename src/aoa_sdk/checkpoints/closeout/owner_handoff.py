"""Owner follow-through handoff helpers for checkpoint reviewed closeout."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from ...loaders import load_json, write_json
from ...models import (
    CheckpointCloseoutContext,
    CloseoutOwnerHandoff,
    OwnerFollowThroughBrief,
    SessionCheckpointCluster,
    WorkflowFollowThroughBrief,
)
from ...workspace.discovery import Workspace
from ..naming import safe_checkpoint_name as _safe_name
from .common import _dedupe_strings, _dict_records, _string_field
from .contracts import ALLOWED_OWNER_REPOS, DonorHarvestOutputs, QuestHarvestOutputs

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


def _checkpoint_closeout_handoff_root(workspace: Workspace) -> Path:
    return workspace.repo_path("aoa-sdk") / ".aoa" / "closeout" / "handoffs"


def _load_closeout_owner_handoff_for_session(
    workspace: Workspace,
    *,
    session_ref: str,
) -> CloseoutOwnerHandoff | None:
    handoff_root = _checkpoint_closeout_handoff_root(workspace)
    if not handoff_root.exists():
        return None
    direct_path = handoff_root / f"{_safe_name(session_ref)}.owner-handoff.json"
    candidate_paths: list[Path] = []
    if direct_path.exists():
        candidate_paths.append(direct_path)
    candidate_paths.extend(
        sorted(path for path in handoff_root.glob("*.owner-handoff.json") if path != direct_path)
    )
    for path in candidate_paths:
        try:
            payload = CloseoutOwnerHandoff.model_validate(load_json(path))
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
    handoff = _load_closeout_owner_handoff_for_session(workspace, session_ref=session_ref)
    if handoff is None:
        return False
    return any(item.owner_repo == repo_label for item in handoff.items)


def _checkpoint_owner_follow_through_key(brief: OwnerFollowThroughBrief) -> str:
    return brief.unit_ref or brief.next_surface


def _load_checkpoint_quest_unit_name(artifact_refs: list[str]) -> str | None:
    triage_ref = next((ref for ref in artifact_refs if ref.endswith("QUEST_TRIAGE.json")), None)
    if triage_ref is None:
        return None
    try:
        payload = load_json(Path(triage_ref).expanduser().resolve())
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        return None
    if not isinstance(payload, dict):
        return None
    quest_unit_name = payload.get("quest_unit_name")
    return quest_unit_name if isinstance(quest_unit_name, str) and quest_unit_name else None


def _write_checkpoint_owner_handoff(
    *,
    workspace: Workspace,
    closeout_context_ref: Path,
    context: CheckpointCloseoutContext,
    donor_outputs: DonorHarvestOutputs,
    quest_outputs: QuestHarvestOutputs,
    reviewed_artifact: Path,
) -> tuple[Path | None, list[OwnerFollowThroughBrief], list[WorkflowFollowThroughBrief]]:
    reviewed_ref = str(reviewed_artifact)
    session_trace_ref = context.session_trace_ref
    review_evidence_refs = list(context.checkpoint_review_carry.evidence_refs)
    harvest_packet_ref = next(
        (ref for ref in donor_outputs["artifact_refs"] if ref.endswith("HARVEST_PACKET.json")),
        None,
    )
    quest_packet_ref = next(
        (ref for ref in quest_outputs["artifact_refs"] if ref.endswith("QUEST_PROMOTION.json")),
        None,
    )
    briefs_by_key: dict[str, OwnerFollowThroughBrief] = {}

    for candidate in _dict_records(donor_outputs["packet"].get("accepted_candidates", [])):
        owner_repo = _string_field(candidate, "owner_repo_recommendation")
        next_surface = _string_field(candidate, "chosen_next_artifact")
        unit_ref = _string_field(candidate, "candidate_ref")
        if not all(value is not None and value for value in (owner_repo, next_surface, unit_ref)):
            continue
        evidence_anchors = candidate.get("evidence_anchors")
        evidence_refs = _dedupe_strings(
            [
                *([harvest_packet_ref] if harvest_packet_ref is not None else []),
                reviewed_ref,
                *([session_trace_ref] if session_trace_ref is not None else []),
                *review_evidence_refs,
                *(
                    anchor
                    for anchor in (evidence_anchors if isinstance(evidence_anchors, list) else [])
                    if isinstance(anchor, str) and anchor
                ),
            ]
        )
        brief = OwnerFollowThroughBrief(
            source_kind="harvest-candidate",
            unit_ref=cast(str, unit_ref),
            unit_name=_string_field(candidate, "unit_name"),
            owner_repo=cast(str, owner_repo),
            next_surface=cast(str, next_surface),
            suggested_action="draft-owner-artifact",
            abstraction_shape=_string_field(candidate, "abstraction_shape"),
            nearest_wrong_target=_string_field(candidate, "nearest_wrong_target"),
            reason=(
                _string_field(candidate, "owner_reason")
                or "Harvest named this as a reusable owner-layer candidate, so the next honest move is a bounded owner-surface draft."
            ),
            evidence_refs=evidence_refs,
        )
        briefs_by_key[_checkpoint_owner_follow_through_key(brief)] = brief

    quest_packet = quest_outputs["packet"]
    owner_repo = _string_field(quest_packet, "owner_repo")
    next_surface = _string_field(quest_packet, "next_surface")
    promotion_verdict = _string_field(quest_packet, "promotion_verdict")
    bounded_unit_ref = _string_field(quest_packet, "bounded_unit_ref") or context.session_ref
    if all(value is not None and value for value in (owner_repo, next_surface, promotion_verdict)):
        evidence_refs = _dedupe_strings(
            [
                *([quest_packet_ref] if quest_packet_ref is not None else []),
                *quest_outputs["artifact_refs"],
                reviewed_ref,
                *([session_trace_ref] if session_trace_ref is not None else []),
                *review_evidence_refs,
            ]
        )
        brief = OwnerFollowThroughBrief(
            source_kind="quest-promotion",
            unit_ref=bounded_unit_ref,
            unit_name=_load_checkpoint_quest_unit_name(quest_outputs["artifact_refs"]),
            owner_repo=cast(str, owner_repo),
            next_surface=cast(str, next_surface),
            suggested_action="author-owner-artifact",
            promotion_verdict=cast(str, promotion_verdict),
            nearest_wrong_target=_string_field(quest_packet, "nearest_wrong_target"),
            reason=(
                f"Quest promotion closed with {promotion_verdict}, so the next honest move is to author the owner-layer artifact."
            ),
            evidence_refs=evidence_refs,
        )
        briefs_by_key[_checkpoint_owner_follow_through_key(brief)] = brief

    owner_briefs = sorted(
        briefs_by_key.values(),
        key=lambda item: (item.owner_repo, item.next_surface, item.unit_ref),
    )
    workflow_briefs: list[WorkflowFollowThroughBrief] = []
    if not owner_briefs and not workflow_briefs:
        return None, owner_briefs, workflow_briefs

    handoff_dir = _checkpoint_closeout_handoff_root(workspace)
    handoff_dir.mkdir(parents=True, exist_ok=True)
    handoff_path = handoff_dir / f"{_safe_name(context.session_ref)}.owner-handoff.json"
    payload = CloseoutOwnerHandoff(
        schema_version=1,
        closeout_id=f"checkpoint-closeout-{_safe_name(context.session_ref)}",
        session_ref=context.session_ref,
        manifest_path=str(closeout_context_ref),
        generated_at=datetime.now(UTC),
        items=owner_briefs,
        workflow_items=workflow_briefs,
    )
    write_json(handoff_path, payload.model_dump(mode="json"))
    return handoff_path, owner_briefs, workflow_briefs


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
        next_surface = f"quests/checkpoint/captured/{_safe_name(context.session_ref)}-followup.md"
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
