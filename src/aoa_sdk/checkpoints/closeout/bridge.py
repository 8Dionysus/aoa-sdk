"""Closeout context, evidence, execution, and owner-handoff helpers."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, TypedDict, cast

from ...loaders import load_json, write_json
from ...models import (
    CheckpointCloseoutContext,
    CheckpointLineageHint,
    CloseoutFollowthroughDecision,
    CloseoutOwnerFollowthroughHint,
    CloseoutOwnerHandoff,
    OwnerFollowThroughBrief,
    ProgressionAxisSignal,
    SessionCheckpointCluster,
    SessionCheckpointNote,
    SessionEndSkillTarget,
    SurfaceCloseoutHandoff,
    WorkflowFollowThroughBrief,
)
from ...workspace.discovery import Workspace
from ..ledger.notes import merge_checkpoint_lineage_hint as _merge_checkpoint_lineage_hint
from ..ledger.notes import merge_progression_axis_signals as _merge_progression_axis_signals
from ..naming import safe_checkpoint_name as _safe_name
from ..timestamps import observed_timestamp_fields as _observed_timestamp_fields

SESSION_REF_RE = re.compile(r'"session_ref"\s*:\s*"([^"]+)"|session_ref:\s*`?([^`\s]+)`?|Session ref:\s*`?([^`\n]+)`?')
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
FollowthroughSkillName = Literal[
    "aoa-session-route-forks",
    "aoa-session-self-diagnose",
    "aoa-session-self-repair",
    "aoa-session-progression-lift",
    "aoa-automation-opportunity-scan",
    "aoa-quest-harvest",
]
FollowthroughReasonCode = Literal[
    "multiple_plausible_next_moves",
    "repeated_friction",
    "blocked_automation_readiness",
    "reviewed_diagnosis_present",
    "smallest_repair_clear",
    "explicit_axis_movement",
    "no_repair_needed",
    "repeated_manual_route",
    "stable_output_shape",
    "checkpoint_sensitive",
    "reviewed_quest_unit",
    "promotion_pressure",
]
ApprovalPosture = Literal["not_required", "review_required", "approval_required"]
FOLLOWTHROUGH_DECISION_BY_STATUS: dict[
    Literal["early", "reanchor", "thin-evidence", "stable"],
    Literal["land_direct", "reanchor_owner", "prove_first"],
] = {
    "early": "land_direct",
    "reanchor": "reanchor_owner",
    "thin-evidence": "prove_first",
    "stable": "land_direct",
}
OWNER_STATUS_SURFACE_BY_REPO = {
    "aoa-agents": "aoa-agents:reviewed_owner_landing_bundle",
    "aoa-evals": "aoa-evals:reviewed_owner_landing_bundle",
    "aoa-memo": "aoa-memo:reviewed_owner_landing_bundle",
    "aoa-playbooks": "aoa-playbooks:reviewed_owner_landing_bundle",
    "aoa-skills": "aoa-skills:reviewed_owner_landing_bundle",
    "aoa-techniques": "aoa-techniques:reviewed_owner_landing_bundle",
}
KERNEL_SIGNAL_SKILLS: tuple[FollowthroughSkillName, ...] = (
    "aoa-session-route-forks",
    "aoa-session-self-diagnose",
    "aoa-session-self-repair",
    "aoa-session-progression-lift",
    "aoa-automation-opportunity-scan",
    "aoa-quest-harvest",
)


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


def _requested_followthrough_decision_class(
    hint: CheckpointLineageHint,
) -> Literal[
    "land_direct",
    "stage_seed",
    "reanchor_owner",
    "prove_first",
    "merge_into_existing",
    "defer",
    "drop",
]:
    if hint.merged_into:
        return "merge_into_existing"
    return FOLLOWTHROUGH_DECISION_BY_STATUS[hint.status_posture]


def _build_owner_followthrough_map(
    hints: list[CheckpointLineageHint],
) -> list[CloseoutOwnerFollowthroughHint]:
    return [
        CloseoutOwnerFollowthroughHint(
            cluster_ref=hint.cluster_ref,
            owner_hypothesis=hint.owner_hypothesis,
            owner_shape=hint.owner_shape,
            nearest_wrong_target=hint.nearest_wrong_target,
            status_posture=hint.status_posture,
            recommended_owner_status_surface=OWNER_STATUS_SURFACE_BY_REPO.get(
                hint.owner_hypothesis,
                f"{hint.owner_hypothesis}:reviewed_owner_landing_bundle",
            ),
            requested_next_decision_class=_requested_followthrough_decision_class(hint),
            evidence_refs=list(hint.evidence_refs),
        )
        for hint in hints
    ]


def _cluster_text(cluster: SessionCheckpointCluster) -> str:
    return " ".join(
        [
            cluster.candidate_kind,
            cluster.owner_hint,
            cluster.display_name,
            cluster.source_surface_ref,
            cluster.defer_reason or "",
            *cluster.blocked_by,
            *cluster.promote_if,
            *cluster.next_owner_moves,
            *(cluster.evidence_refs or []),
            cluster.lineage_hint.owner_shape if cluster.lineage_hint is not None else "",
            cluster.lineage_hint.nearest_wrong_target if cluster.lineage_hint and cluster.lineage_hint.nearest_wrong_target else "",
        ]
    ).lower()


def _is_route_cluster(cluster: SessionCheckpointCluster) -> bool:
    cluster_text = _cluster_text(cluster)
    return (
        cluster.candidate_kind == "route"
        or cluster.owner_hint == "aoa-playbooks"
        or "playbook_registry" in cluster_text
        or "playbook" in cluster_text
    )


def _is_repair_cluster(cluster: SessionCheckpointCluster) -> bool:
    cluster_text = _cluster_text(cluster)
    return "repair" in cluster_text


def _has_blocked_signal(cluster: SessionCheckpointCluster) -> bool:
    return bool(
        cluster.blocked_by
        or cluster.defer_reason
        or (cluster.lineage_hint is not None and cluster.lineage_hint.status_posture == "thin-evidence")
    )


def _has_upgrade_pressure(cluster: SessionCheckpointCluster) -> bool:
    return "upgrade" in cluster.session_end_targets and bool(cluster.promote_if)


def _primary_lineage_cluster(clusters: list[SessionCheckpointCluster]) -> SessionCheckpointCluster:
    for cluster in clusters:
        if cluster.lineage_hint is not None and cluster.candidate_kind != "route":
            return cluster
    return clusters[0]


def _closeout_followthrough_alternatives(
    *,
    clusters: list[SessionCheckpointCluster],
    has_progression_signal: bool,
    recommended_next_skill: FollowthroughSkillName,
) -> list[FollowthroughSkillName]:
    candidates: list[FollowthroughSkillName] = []
    if len(clusters) > 1 or len({cluster.owner_hint for cluster in clusters}) > 1:
        candidates.append("aoa-session-route-forks")
    if any(_has_blocked_signal(cluster) for cluster in clusters):
        candidates.append("aoa-session-self-diagnose")
    if any(_is_repair_cluster(cluster) for cluster in clusters):
        candidates.append("aoa-session-self-repair")
    if has_progression_signal:
        candidates.append("aoa-session-progression-lift")
    if any(_is_route_cluster(cluster) for cluster in clusters):
        candidates.append("aoa-automation-opportunity-scan")
    if any(_has_upgrade_pressure(cluster) for cluster in clusters):
        candidates.append("aoa-quest-harvest")
    alternatives: list[FollowthroughSkillName] = []
    seen: set[FollowthroughSkillName] = set()
    for skill in candidates:
        if skill == recommended_next_skill or skill in seen:
            continue
        alternatives.append(skill)
        seen.add(skill)
    return alternatives[:2]


def _approval_posture_for_next_skill(
    skill_name: FollowthroughSkillName,
) -> ApprovalPosture:
    if skill_name == "aoa-session-self-repair":
        return "approval_required"
    if skill_name in {"aoa-session-route-forks", "aoa-automation-opportunity-scan", "aoa-quest-harvest"}:
        return "review_required"
    return "not_required"


def _build_closeout_followthrough_decision(
    *,
    session_ref: str,
    reviewed_closeout_context_ref: str,
    clusters: list[SessionCheckpointCluster],
    progression_axis_signals: list[ProgressionAxisSignal],
) -> CloseoutFollowthroughDecision | None:
    lineage_clusters = [cluster for cluster in clusters if cluster.lineage_hint is not None]
    if not lineage_clusters:
        return None

    selected_cluster: SessionCheckpointCluster
    recommended_next_skill: FollowthroughSkillName
    reason_codes: list[FollowthroughReasonCode]
    primary_cluster = _primary_lineage_cluster(lineage_clusters)
    route_cluster = next((cluster for cluster in lineage_clusters if _is_route_cluster(cluster)), None)
    repair_cluster = next((cluster for cluster in lineage_clusters if _is_repair_cluster(cluster)), None)
    blocked_cluster = next((cluster for cluster in lineage_clusters if _has_blocked_signal(cluster)), None)
    upgrade_cluster = next((cluster for cluster in lineage_clusters if _has_upgrade_pressure(cluster)), None)
    has_progression_signal = bool(
        any(signal.movement == "advance" for signal in progression_axis_signals)
        or any(signal.movement == "advance" for cluster in lineage_clusters for signal in cluster.progression_axis_signals)
        or any(
            value > 0
            for cluster in lineage_clusters
            for value in (cluster.lineage_hint.axis_pressure.values() if cluster.lineage_hint is not None else [])
        )
    )
    if route_cluster is not None:
        selected_cluster = route_cluster
        recommended_next_skill = "aoa-automation-opportunity-scan"
        reason_codes = ["repeated_manual_route", "stable_output_shape", "checkpoint_sensitive"]
    elif repair_cluster is not None:
        selected_cluster = repair_cluster
        recommended_next_skill = "aoa-session-self-repair"
        reason_codes = ["reviewed_diagnosis_present", "smallest_repair_clear", "checkpoint_sensitive"]
    elif blocked_cluster is not None:
        selected_cluster = blocked_cluster
        recommended_next_skill = "aoa-session-self-diagnose"
        reason_codes = ["repeated_friction", "blocked_automation_readiness", "checkpoint_sensitive"]
    elif has_progression_signal:
        selected_cluster = primary_cluster
        recommended_next_skill = "aoa-session-progression-lift"
        reason_codes = ["explicit_axis_movement", "no_repair_needed", "checkpoint_sensitive"]
    elif upgrade_cluster is not None:
        selected_cluster = upgrade_cluster
        recommended_next_skill = "aoa-quest-harvest"
        reason_codes = ["reviewed_quest_unit", "promotion_pressure", "checkpoint_sensitive"]
    else:
        selected_cluster = primary_cluster
        recommended_next_skill = "aoa-session-route-forks"
        reason_codes = ["multiple_plausible_next_moves", "checkpoint_sensitive"]

    selected_hint = selected_cluster.lineage_hint
    assert selected_hint is not None
    approval_posture = _approval_posture_for_next_skill(recommended_next_skill)
    defer_allowed = bool(
        selected_cluster.blocked_by
        or selected_cluster.defer_reason
        or selected_hint.status_posture != "stable"
        or approval_posture != "not_required"
    )
    return CloseoutFollowthroughDecision(
        session_ref=session_ref,
        reviewed_closeout_context_ref=reviewed_closeout_context_ref,
        cluster_ref=selected_hint.cluster_ref,
        recommended_next_skill=recommended_next_skill,
        also_considered=_closeout_followthrough_alternatives(
            clusters=lineage_clusters,
            has_progression_signal=has_progression_signal,
            recommended_next_skill=recommended_next_skill,
        ),
        reason_codes=reason_codes,
        checkpoint_required=selected_cluster.checkpoint_hits > 0,
        approval_posture=approval_posture,
        defer_allowed=defer_allowed,
        owner_hypothesis=selected_hint.owner_hypothesis,
        nearest_wrong_target=selected_hint.nearest_wrong_target,
        status_posture=selected_hint.status_posture,
    )


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
        "checkpoint_review_carry": context.checkpoint_review_carry.model_dump(mode="json"),
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
            "checkpoint_review_refs": context.checkpoint_review_carry.review_refs,
            "checkpoint_closeout_questions": context.checkpoint_review_carry.closeout_questions,
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
        "checkpoint_review_carry": context.checkpoint_review_carry.model_dump(mode="json"),
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
            "checkpoint_review_refs": context.checkpoint_review_carry.review_refs,
            "checkpoint_closeout_questions": context.checkpoint_review_carry.closeout_questions,
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
        "checkpoint_review_carry": context.checkpoint_review_carry.model_dump(mode="json"),
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
        "checkpoint_review_carry": context.checkpoint_review_carry.model_dump(mode="json"),
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
        "checkpoint_review_carry": context.checkpoint_review_carry.model_dump(mode="json"),
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
            "checkpoint_review_refs": context.checkpoint_review_carry.review_refs,
            "checkpoint_closeout_questions": context.checkpoint_review_carry.closeout_questions,
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
            ("architecture", "stage", "phase", "bridge", "kernel"),
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


def _dedupe_strings(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))
