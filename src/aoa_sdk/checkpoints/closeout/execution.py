"""Mechanical closeout packet and receipt builders."""

from __future__ import annotations

from pathlib import Path
from typing import Literal, cast

from ...loaders import write_json
from ...models import (
    CheckpointCloseoutContext,
    ProgressionAxisSignal,
    SessionCheckpointCluster,
)
from ..ledger.notes import merge_progression_axis_signals as _merge_progression_axis_signals
from ..naming import safe_checkpoint_name as _safe_name
from ..timestamps import observed_timestamp_fields as _observed_timestamp_fields
from .common import _dedupe_strings, _dict_records
from .contracts import (
    ALLOWED_OWNER_REPOS,
    CHECKPOINT_CLOSEOUT_AUTHORITY_CONTRACT,
    DonorHarvestOutputs,
    ProgressionLiftOutputs,
    QuestHarvestOutputs,
)
from .owner_handoff import _build_accepted_candidate, _quest_promotion_fields

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
