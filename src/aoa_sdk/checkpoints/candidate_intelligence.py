"""Checkpoint candidate-intelligence route evidence.

This module derives action signatures below legacy checkpoint candidate kinds.
It is a classifier/navigation layer only; reviewed memory, proof, promotion,
and wrapper acceptance stay with their owner routes.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Sequence
from typing import Literal, TypeAlias, cast

from ..models import (
    ActionFacetSet,
    ActionSignature,
    CandidateIntelligenceReport,
    CandidateIntelligenceSample,
    CheckpointActionEvent,
    CheckpointCandidateCluster,
    ExistingWrapperFit,
    RepetitionCluster,
    SessionCheckpointCluster,
    SurfaceOpportunityItem,
    WrapperGapCandidate,
    WrapperReadiness,
)
from ..workspace.discovery import Workspace
from .naming import safe_checkpoint_name
from .timestamps import local_timestamp_parts

WrapperFamily = Literal[
    "skill",
    "playbook",
    "technique",
    "eval",
    "memo",
    "sdk_mechanic",
    "owner_local",
    "unknown",
]

Family = Literal[
    "communication",
    "command_execution",
    "workspace_mutation",
    "context_memory",
    "verification",
    "owner_routing",
    "risk",
    "wrapper_gap",
    "unknown",
]

CandidateCluster: TypeAlias = CheckpointCandidateCluster | SessionCheckpointCluster


@dataclass(frozen=True)
class ActionProfile:
    event_type: str
    family: Family
    action: str
    object: str
    wrapper_family: WrapperFamily
    route_signals: tuple[str, ...]
    steps: tuple[str, ...]
    outputs: tuple[str, ...]
    verification: tuple[str, ...]
    failure_modes: tuple[str, ...]
    stop_lines: tuple[str, ...]


DEFAULT_STOP_LINES = (
    "no_reviewed_memory_claim",
    "no_owner_verdict",
    "no_single_event_promotion",
    "no_hidden_automation",
)

SIGNAL_PROFILES: dict[str, ActionProfile] = {
    "scenario-recurring": ActionProfile(
        event_type="repeated_manual_workflow_candidate",
        family="command_execution",
        action="repeat_manual_workflow",
        object="multi_surface_route",
        wrapper_family="playbook",
        route_signals=("session_act:manual_sequence", "route_signal:recurrence"),
        steps=("inspect route surfaces", "perform repeated sequence", "record evidence refs"),
        outputs=("route candidate", "handoff-ready action signature"),
        verification=("same trigger and output shape recur",),
        failure_modes=("route copied without owner review",),
        stop_lines=DEFAULT_STOP_LINES,
    ),
    "repeated-pattern": ActionProfile(
        event_type="repeated_practice_candidate",
        family="command_execution",
        action="repeat_bounded_practice",
        object="operator_or_agent_discipline",
        wrapper_family="technique",
        route_signals=("session_act:practice_repeat", "route_signal:technique_pressure"),
        steps=("identify bounded discipline", "compare repeat evidence", "defer promotion"),
        outputs=("technique-shaped candidate",),
        verification=("practice repeats across reviewed contexts",),
        failure_modes=("practice mistaken for accepted technique",),
        stop_lines=DEFAULT_STOP_LINES,
    ),
    "proof-need": ActionProfile(
        event_type="verification_surface_candidate",
        family="verification",
        action="define_bounded_verification",
        object="proof_or_invariant",
        wrapper_family="eval",
        route_signals=("session_act:verification", "route_signal:proof_need"),
        steps=("name claim under test", "identify invariant", "route to proof owner"),
        outputs=("eval-shaped candidate",),
        verification=("verification target is repeatable and bounded",),
        failure_modes=("green check treated as proof verdict",),
        stop_lines=DEFAULT_STOP_LINES,
    ),
    "recall-need": ActionProfile(
        event_type="memory_recall_route_candidate",
        family="context_memory",
        action="retrieve_prior_context",
        object="provenance_aware_memory",
        wrapper_family="memo",
        route_signals=("session_act:memory_read", "route_signal:memory_provenance"),
        steps=("identify prior context need", "preserve refs", "avoid memory truth claim"),
        outputs=("memo-shaped recall candidate",),
        verification=("future agent can find the same provenance route",),
        failure_modes=("summary promoted as durable memory",),
        stop_lines=DEFAULT_STOP_LINES,
    ),
    "role-posture": ActionProfile(
        event_type="owner_or_role_route_candidate",
        family="owner_routing",
        action="clarify_owner_or_agent_role",
        object="owner_boundary",
        wrapper_family="owner_local",
        route_signals=("session_act:owner_route", "route_signal:authority_surface"),
        steps=("name owner pressure", "record ambiguity", "defer verdict"),
        outputs=("owner-review candidate",),
        verification=("owner route is stable after reviewed closeout",),
        failure_modes=("agent assigns owner verdict",),
        stop_lines=DEFAULT_STOP_LINES,
    ),
    "risk-gate": ActionProfile(
        event_type="risk_gate_candidate",
        family="risk",
        action="gate_risky_action",
        object="automation_or_mutation_risk",
        wrapper_family="skill",
        route_signals=("session_act:risk_gate", "route_signal:failure_mode"),
        steps=("name risk", "require explicit review", "avoid hidden action"),
        outputs=("preflight-skill candidate",),
        verification=("risk gate catches repeated failure mode",),
        failure_modes=("risk gate silently executes mutation",),
        stop_lines=DEFAULT_STOP_LINES,
    ),
}

GENERIC_PROFILES: tuple[tuple[tuple[str, ...], ActionProfile], ...] = (
    (
        ("verify", "proof", "test", "invariant", "regression", "quality"),
        SIGNAL_PROFILES["proof-need"],
    ),
    (
        ("memory", "recall", "previous", "prior", "history", "provenance"),
        SIGNAL_PROFILES["recall-need"],
    ),
    (
        ("owner", "ambiguity", "route", "handoff", "boundary"),
        SIGNAL_PROFILES["role-posture"],
    ),
    (
        ("repeat", "again", "workflow", "sequence", "manual", "routine"),
        SIGNAL_PROFILES["scenario-recurring"],
    ),
)

KIND_TO_PROFILE = {
    "route": SIGNAL_PROFILES["scenario-recurring"],
    "pattern": SIGNAL_PROFILES["repeated-pattern"],
    "proof": SIGNAL_PROFILES["proof-need"],
    "recall": SIGNAL_PROFILES["recall-need"],
    "role": SIGNAL_PROFILES["role-posture"],
    "risk": SIGNAL_PROFILES["risk-gate"],
}

OBJECT_KIND_TO_WRAPPER: dict[str, WrapperFamily] = {
    "skill": "skill",
    "playbook": "playbook",
    "technique": "technique",
    "eval": "eval",
    "memo": "memo",
    "agent": "owner_local",
}


def build_candidate_intelligence_from_surface(
    *,
    workspace: Workspace,
    repo_root: str,
    intent_text: str,
    checkpoint_kind: str | None,
    mutation_surface: str,
    items: list[SurfaceOpportunityItem],
    candidate_clusters: Sequence[CandidateCluster],
    actionability_gaps: list[str],
    sample_limit: int = 0,
) -> CandidateIntelligenceReport:
    repo_root_path = _resolve_repo_root(workspace, repo_root)
    repo_label = _repo_label(workspace, repo_root)
    generated_at, generated_at_local, generated_tz = local_timestamp_parts()
    events = _derive_action_events(
        repo_label=repo_label,
        intent_text=intent_text,
        checkpoint_kind=checkpoint_kind,
        mutation_surface=mutation_surface,
        items=items,
        candidate_clusters=candidate_clusters,
        actionability_gaps=actionability_gaps,
    )
    occurrence_counts = _signature_occurrence_counts(events)
    signatures = _signatures_for_events(events, occurrence_counts=occurrence_counts)
    gaps = _wrapper_gaps_for_signatures(
        signatures=signatures,
        events=events,
        candidate_clusters=candidate_clusters,
        intent_text=intent_text,
    )
    clusters = _repetition_clusters(
        signatures=signatures,
        events=events,
        wrapper_gaps=gaps,
        runtime_session_ids=[],
        candidate_clusters=candidate_clusters,
        occurrence_counts=occurrence_counts,
    )
    samples = _sample_audit(signatures=signatures, gaps=gaps, clusters=clusters, limit=sample_limit)
    return CandidateIntelligenceReport(
        repo_root=str(repo_root_path),
        repo_label=repo_label,
        generated_at=generated_at,
        generated_at_local=generated_at_local,
        generated_tz=generated_tz,
        source="surface_detection",
        action_events=events,
        action_signatures=signatures,
        repetition_clusters=clusters,
        wrapper_gap_candidates=gaps,
        existing_wrapper_fits=[cluster.existing_wrapper_fit for cluster in clusters],
        sample_audit=samples,
    )


def build_candidate_intelligence_from_note(
    *,
    workspace: Workspace,
    repo_root: str,
    action_events: list[CheckpointActionEvent],
    action_signatures: list[ActionSignature],
    candidate_clusters: Sequence[CandidateCluster] | None = None,
    runtime_session_ids: list[str],
    sample_limit: int = 0,
) -> CandidateIntelligenceReport:
    repo_root_path = _resolve_repo_root(workspace, repo_root)
    repo_label = _repo_label(workspace, repo_root)
    generated_at, generated_at_local, generated_tz = local_timestamp_parts()
    raw_events = list(action_events)
    raw_signatures = list(action_signatures)
    if not raw_events and not raw_signatures and candidate_clusters:
        raw_events = _events_from_candidate_clusters(
            repo_label=repo_label,
            candidate_clusters=candidate_clusters,
        )
    occurrence_counts = _signature_occurrence_counts(raw_events)
    occurrence_counts = _merge_occurrence_counts(
        occurrence_counts,
        _candidate_cluster_occurrence_counts(
            events=raw_events,
            candidate_clusters=candidate_clusters or [],
        ),
    )
    occurrence_counts = _merge_occurrence_counts(
        occurrence_counts,
        _signature_saved_event_counts(raw_signatures),
    )
    if raw_events:
        raw_signatures = [
            *raw_signatures,
            *_signatures_for_events(raw_events, occurrence_counts=occurrence_counts),
        ]
    signatures = _merge_signatures(raw_signatures, occurrence_counts=occurrence_counts)
    events = _merge_events(raw_events)
    gaps = _wrapper_gaps_for_signatures(
        signatures=signatures,
        events=events,
        candidate_clusters=candidate_clusters or [],
        intent_text="",
    )
    clusters = _repetition_clusters(
        signatures=signatures,
        events=events,
        wrapper_gaps=gaps,
        runtime_session_ids=runtime_session_ids,
        candidate_clusters=candidate_clusters or [],
        occurrence_counts=occurrence_counts,
    )
    samples = _sample_audit(signatures=signatures, gaps=gaps, clusters=clusters, limit=sample_limit)
    return CandidateIntelligenceReport(
        repo_root=str(repo_root_path),
        repo_label=repo_label,
        generated_at=generated_at,
        generated_at_local=generated_at_local,
        generated_tz=generated_tz,
        source="checkpoint_note",
        action_events=events,
        action_signatures=signatures,
        repetition_clusters=clusters,
        wrapper_gap_candidates=gaps,
        existing_wrapper_fits=[cluster.existing_wrapper_fit for cluster in clusters],
        sample_audit=samples,
    )


def _derive_action_events(
    *,
    repo_label: str,
    intent_text: str,
    checkpoint_kind: str | None,
    mutation_surface: str,
    items: list[SurfaceOpportunityItem],
    candidate_clusters: Sequence[CandidateCluster],
    actionability_gaps: list[str],
) -> list[CheckpointActionEvent]:
    events: list[CheckpointActionEvent] = []
    for item in items:
        profile = _profile_for_item(item)
        if profile is None:
            continue
        events.append(
            _event_from_profile(
                profile=profile,
                source_ref=item.surface_ref,
                trigger_text=intent_text,
                candidate_ids=[
                    cluster.candidate_id
                    for cluster in candidate_clusters
                    if cluster.source_surface_ref == item.surface_ref
                ],
                surface_refs=[item.surface_ref],
                evidence_refs=_item_evidence_refs(item),
                confidence=item.confidence,
                extra_route_signals=tuple(item.signals),
            )
        )
    for cluster in candidate_clusters:
        if any(cluster.candidate_id in event.candidate_ids for event in events):
            continue
        profile = KIND_TO_PROFILE.get(cluster.candidate_kind) or _profile_for_cluster(cluster)
        events.append(
            _event_from_profile(
                profile=profile,
                source_ref=cluster.source_surface_ref,
                trigger_text=intent_text,
                candidate_ids=[cluster.candidate_id],
                surface_refs=[cluster.source_surface_ref],
                evidence_refs=list(cluster.evidence_refs),
                confidence=cluster.confidence,
                extra_route_signals=(f"candidate_kind:{cluster.candidate_kind}",),
            )
        )
    generic = _generic_profile(intent_text=intent_text, actionability_gaps=actionability_gaps)
    if generic is not None and not events:
        events.append(
            _event_from_profile(
                profile=generic,
                source_ref=f"intent:{safe_checkpoint_name(intent_text)[:64] or 'checkpoint'}",
                trigger_text=intent_text,
                candidate_ids=[],
                surface_refs=[],
                evidence_refs=[f"context:{repo_label}", f"mutation_surface:{mutation_surface}"],
                confidence="low",
                extra_route_signals=("route_signal:wrapper_gap",),
            )
        )
    if mutation_surface != "none" and checkpoint_kind in {"commit", "verify_green", "pr_opened", "pr_merged"}:
        profile = ActionProfile(
            event_type=f"{checkpoint_kind}_mutation_action",
            family="workspace_mutation",
            action=f"record_{checkpoint_kind}_mutation",
            object=mutation_surface,
            wrapper_family="sdk_mechanic",
            route_signals=("session_act:workspace_mutation", "route_signal:mutation_surface"),
            steps=("record checkpoint boundary", "preserve mutation evidence", "defer promotion"),
            outputs=("checkpoint mutation action signature",),
            verification=("bounded mutation evidence remains inspectable",),
            failure_modes=("mutation boundary treated as owner approval",),
            stop_lines=DEFAULT_STOP_LINES,
        )
        events.append(
            _event_from_profile(
                profile=profile,
                source_ref=f"checkpoint_kind:{checkpoint_kind}",
                trigger_text=intent_text,
                candidate_ids=[
                    cluster.candidate_id for cluster in candidate_clusters if cluster.candidate_kind == "growth"
                ],
                surface_refs=[f"aoa-sdk:checkpoint_auto_capture.{checkpoint_kind}"],
                evidence_refs=[f"context:{repo_label}", f"mutation_surface:{mutation_surface}"],
                confidence="medium",
                extra_route_signals=(f"checkpoint_kind:{checkpoint_kind}",),
            )
        )
    return _merge_events(events)


def _events_from_candidate_clusters(
    *,
    repo_label: str,
    candidate_clusters: Sequence[CandidateCluster],
) -> list[CheckpointActionEvent]:
    return _merge_events(
        [
            _event_from_profile(
                profile=KIND_TO_PROFILE.get(cluster.candidate_kind) or _profile_for_cluster(cluster),
                source_ref=cluster.source_surface_ref,
                trigger_text=f"legacy checkpoint candidate {cluster.candidate_id}",
                candidate_ids=[cluster.candidate_id],
                surface_refs=[cluster.source_surface_ref],
                evidence_refs=list(cluster.evidence_refs) or [f"context:{repo_label}"],
                confidence=cluster.confidence,
                extra_route_signals=(f"candidate_kind:{cluster.candidate_kind}", "route_signal:legacy_backfill"),
            )
            for cluster in candidate_clusters
        ]
    )


def _profile_for_item(item: SurfaceOpportunityItem) -> ActionProfile | None:
    for signal in item.signals:
        if signal in SIGNAL_PROFILES:
            return SIGNAL_PROFILES[signal]
    wrapper = OBJECT_KIND_TO_WRAPPER.get(item.object_kind, "unknown")
    family: Family = "wrapper_gap" if wrapper == "unknown" else "command_execution"
    return ActionProfile(
        event_type=f"{item.object_kind}_surface_candidate",
        family=family,
        action=f"route_{item.object_kind}_candidate",
        object=item.surface_ref,
        wrapper_family=wrapper,
        route_signals=(f"route_signal:{item.object_kind}",),
        steps=("inspect existing surface", "preserve candidate evidence", "defer owner verdict"),
        outputs=(f"{item.object_kind} candidate",),
        verification=("candidate survives reviewed closeout",),
        failure_modes=("surface resemblance treated as acceptance",),
        stop_lines=DEFAULT_STOP_LINES,
    )


def _profile_for_cluster(cluster: CandidateCluster) -> ActionProfile:
    wrapper: WrapperFamily = "unknown"
    if cluster.owner_hint == "aoa-sdk":
        wrapper = "sdk_mechanic"
    return ActionProfile(
        event_type=f"{cluster.candidate_kind}_candidate",
        family="unknown",
        action=f"classify_{cluster.candidate_kind}",
        object=cluster.source_surface_ref,
        wrapper_family=wrapper,
        route_signals=(f"candidate_kind:{cluster.candidate_kind}",),
        steps=("preserve candidate evidence", "defer classification review"),
        outputs=("checkpoint candidate route evidence",),
        verification=("review confirms candidate shape",),
        failure_modes=("legacy candidate kind hides real action",),
        stop_lines=DEFAULT_STOP_LINES,
    )


def _generic_profile(*, intent_text: str, actionability_gaps: list[str]) -> ActionProfile | None:
    normalized = " ".join([intent_text, *actionability_gaps]).lower()
    for tokens, profile in GENERIC_PROFILES:
        if any(token in normalized for token in tokens):
            return profile
    if any(token in normalized for token in ("risk", "gate", "hidden", "automation", "confirm", "danger")):
        return SIGNAL_PROFILES["risk-gate"]
    if any(
        token in normalized
        for token in (
            "gap",
            "missing",
            "new wrapper",
            "no existing",
            "not covered",
            "нет похож",
            "нет существ",
            "новый aoa",
            "обернуть",
        )
    ):
        return ActionProfile(
            event_type="wrapper_gap_candidate",
            family="wrapper_gap",
            action="identify_missing_wrapper",
            object="unknown_repeated_action",
            wrapper_family="unknown",
            route_signals=("route_signal:wrapper_gap",),
            steps=("name missing wrapper pressure", "collect evidence refs", "defer owner review"),
            outputs=("wrapper gap candidate",),
            verification=("review decides whether to split or add rule",),
            failure_modes=("novel action forced into existing aoa surface",),
            stop_lines=DEFAULT_STOP_LINES,
        )
    return None


def _event_from_profile(
    *,
    profile: ActionProfile,
    source_ref: str,
    trigger_text: str,
    candidate_ids: list[str],
    surface_refs: list[str],
    evidence_refs: list[str],
    confidence: Literal["low", "medium", "high"],
    extra_route_signals: tuple[str, ...],
) -> CheckpointActionEvent:
    event_id = _event_id(profile=profile, source_ref=source_ref, trigger_text=trigger_text)
    signature_id = _signature_id(profile)
    facets = ActionFacetSet(
        event_type=profile.event_type,
        family=profile.family,
        phase="checkpoint",
        actor="assistant",
        action=profile.action,
        object=profile.object,
        outcome="candidate",
        session_act=profile.action,
        route_signals=_dedupe(
            [*profile.route_signals, f"wrapper_family:{profile.wrapper_family}", *extra_route_signals]
        ),
        relationships=[*(f"candidate:{candidate_id}" for candidate_id in candidate_ids)],
        confidence=confidence,
    )
    return CheckpointActionEvent(
        event_id=event_id,
        source_ref=source_ref,
        facets=facets,
        trigger_text=trigger_text,
        evidence_refs=_dedupe(evidence_refs),
        candidate_ids=_dedupe(candidate_ids),
        surface_refs=_dedupe(surface_refs),
        action_signature_ref=signature_id,
    )


def _signatures_for_events(
    events: list[CheckpointActionEvent],
    *,
    occurrence_counts: Counter[str] | None = None,
) -> list[ActionSignature]:
    grouped: dict[str, list[CheckpointActionEvent]] = defaultdict(list)
    for event in events:
        if event.action_signature_ref is None:
            continue
        grouped[event.action_signature_ref].append(event)
    signatures: list[ActionSignature] = []
    for signature_id, group in sorted(grouped.items()):
        first = group[0]
        profile = _profile_from_event(first)
        evidence_refs = _dedupe(ref for event in group for ref in event.evidence_refs)
        surface_refs = _dedupe(ref for event in group for ref in event.surface_refs)
        route_signals = _dedupe(signal for event in group for signal in event.facets.route_signals)
        repeat_count = occurrence_counts.get(signature_id, len(group)) if occurrence_counts else len(group)
        signatures.append(
            ActionSignature(
                signature_id=signature_id,
                family=first.facets.family,
                action=first.facets.action,
                object=first.facets.object,
                trigger=_trigger_summary(first.trigger_text),
                inputs=surface_refs,
                steps=list(profile.steps),
                outputs=list(profile.outputs),
                verification=list(profile.verification),
                failure_modes=list(profile.failure_modes),
                stop_lines=list(profile.stop_lines),
                owner_pressure=_owner_pressure(surface_refs=surface_refs, evidence_refs=evidence_refs),
                event_types=_dedupe(event.facets.event_type for event in group),
                route_signals=route_signals,
                mutation_surfaces=_mutation_surfaces(evidence_refs=evidence_refs, route_signals=route_signals),
                authority_surfaces=_authority_surfaces(evidence_refs=evidence_refs, route_signals=route_signals),
                memory_provenance_refs=_memory_provenance_refs(evidence_refs=evidence_refs, route_signals=route_signals),
                negative_evidence=_negative_evidence(
                    signature_id=signature_id,
                    profile=profile,
                    events=group,
                    repeat_count=repeat_count,
                ),
                evidence_refs=evidence_refs,
                action_event_ids=[event.event_id for event in group],
                wrapper_family_hint=profile.wrapper_family,
                confidence=_max_confidence([event.facets.confidence for event in group]),
            )
        )
    return signatures


def _profile_from_event(event: CheckpointActionEvent) -> ActionProfile:
    for profile in SIGNAL_PROFILES.values():
        if profile.event_type == event.facets.event_type:
            return profile
    return ActionProfile(
        event_type=event.facets.event_type,
        family=event.facets.family,
        action=event.facets.action,
        object=event.facets.object,
        wrapper_family=_wrapper_family_from_event(event),
        route_signals=tuple(event.facets.route_signals),
        steps=("preserve action event", "defer review"),
        outputs=("candidate route evidence",),
        verification=("review confirms this action signature",),
        failure_modes=("classifier output mistaken for truth",),
        stop_lines=DEFAULT_STOP_LINES,
    )


def _wrapper_family_from_event(event: CheckpointActionEvent) -> WrapperFamily:
    for signal in event.facets.route_signals:
        if not signal.startswith("wrapper_family:"):
            continue
        value = signal.removeprefix("wrapper_family:")
        if value in {
            "skill",
            "playbook",
            "technique",
            "eval",
            "memo",
            "sdk_mechanic",
            "owner_local",
            "unknown",
        }:
            return cast(WrapperFamily, value)
    return "unknown"


def _wrapper_gaps_for_signatures(
    *,
    signatures: list[ActionSignature],
    events: list[CheckpointActionEvent],
    candidate_clusters: Sequence[CandidateCluster],
    intent_text: str,
) -> list[WrapperGapCandidate]:
    novelty = _novelty_markers(intent_text)
    by_signature = {signature.signature_id: signature for signature in signatures}
    fit_by_signature = _existing_fits(signatures=signatures, events=events, candidate_clusters=candidate_clusters)
    gaps: list[WrapperGapCandidate] = []
    for signature_id, fit in fit_by_signature.items():
        signature = by_signature[signature_id]
        if fit.fit_status == "strong" and not novelty:
            continue
        if signature.wrapper_family_hint == "sdk_mechanic" and not novelty:
            continue
        evidence_refs = list(signature.evidence_refs)
        draftability: Literal["observe", "reviewable", "draftable", "blocked"] = "observe"
        if novelty:
            draftability = "reviewable"
        gaps.append(
            WrapperGapCandidate(
                candidate_id=f"wrapper-gap:{safe_checkpoint_name(signature_id)[:96]}",
                signature_id=signature_id,
                proposed_wrapper_family=signature.wrapper_family_hint,
                nearest_existing_wrapper=fit.nearest_existing_wrapper,
                novelty_reason=_novelty_reason(fit=fit, novelty=novelty),
                draftability=draftability,
                evidence_refs=evidence_refs,
            )
        )
    return gaps


def _repetition_clusters(
    *,
    signatures: list[ActionSignature],
    events: list[CheckpointActionEvent],
    wrapper_gaps: list[WrapperGapCandidate],
    runtime_session_ids: list[str],
    candidate_clusters: Sequence[CandidateCluster] | None = None,
    occurrence_counts: Counter[str] | None = None,
) -> list[RepetitionCluster]:
    events_by_signature: dict[str, list[CheckpointActionEvent]] = defaultdict(list)
    for event in events:
        if event.action_signature_ref:
            events_by_signature[event.action_signature_ref].append(event)
    gaps_by_signature = {gap.signature_id: gap for gap in wrapper_gaps}
    fits = _existing_fits(
        signatures=signatures,
        events=events,
        candidate_clusters=candidate_clusters or [],
    )
    clusters: list[RepetitionCluster] = []
    for signature in signatures:
        group = events_by_signature.get(signature.signature_id, [])
        repeat_count = max(
            occurrence_counts.get(signature.signature_id, 0) if occurrence_counts else 0,
            len(group),
            len(signature.action_event_ids),
            1,
        )
        cross_session_count = max(len(set(runtime_session_ids)), 1 if runtime_session_ids else 0)
        owner_clarity = _stability(signature.owner_pressure)
        automation_risk = _automation_risk(signature)
        readiness = _wrapper_readiness(
            signature=signature,
            repeat_count=repeat_count,
            cross_session_count=cross_session_count,
            owner_clarity=owner_clarity,
            automation_risk=automation_risk,
            wrapper_gap=gaps_by_signature.get(signature.signature_id),
        )
        clusters.append(
            RepetitionCluster(
                cluster_id=f"repetition:{safe_checkpoint_name(signature.signature_id)[:96]}",
                signature_id=signature.signature_id,
                repeat_count=repeat_count,
                cross_session_count=cross_session_count,
                trigger_stability=_count_stability(repeat_count),
                step_stability="high" if signature.steps else "low",
                verification_stability="high" if signature.verification else "low",
                failure_recurrence="medium" if signature.failure_modes and repeat_count >= 2 else "low" if signature.failure_modes else "none",
                owner_clarity=owner_clarity,
                novelty_pressure="high" if signature.signature_id in gaps_by_signature else "low",
                automation_risk=automation_risk,
                review_debt="high" if readiness.draftability in {"reviewable", "draftable"} else "medium",
                action_event_ids=[event.event_id for event in group],
                runtime_session_ids=_dedupe(runtime_session_ids),
                evidence_refs=list(signature.evidence_refs),
                existing_wrapper_fit=fits[signature.signature_id],
                wrapper_readiness=readiness,
                wrapper_gap=gaps_by_signature.get(signature.signature_id),
            )
        )
    return sorted(clusters, key=lambda item: (-item.repeat_count, item.signature_id))


def _wrapper_readiness(
    *,
    signature: ActionSignature,
    repeat_count: int,
    cross_session_count: int,
    owner_clarity: Literal["low", "medium", "high"],
    automation_risk: Literal["low", "medium", "high"],
    wrapper_gap: WrapperGapCandidate | None,
) -> WrapperReadiness:
    score = 0
    score += min(repeat_count, 3)
    score += min(cross_session_count, 2)
    score += 1 if owner_clarity == "high" else 0
    score += 1 if signature.verification else 0
    if automation_risk == "high":
        score -= 1
    blockers: list[str] = []
    if automation_risk == "high":
        blockers.append("automation_risk_requires_review")
    if owner_clarity == "low":
        blockers.append("owner_unclear")
    draftability: Literal["observe", "reviewable", "draftable", "blocked"] = "observe"
    if blockers and repeat_count < 2:
        draftability = "blocked" if automation_risk == "high" else "observe"
    elif repeat_count >= 3 and score >= 5:
        draftability = "draftable"
    elif repeat_count >= 2:
        draftability = "reviewable"
    return WrapperReadiness(
        proposed_wrapper_family=signature.wrapper_family_hint,
        draftability=draftability,
        score=max(score, 0),
        reasons=[
            f"repeat_count={repeat_count}",
            f"cross_session_count={cross_session_count}",
            f"owner_clarity={owner_clarity}",
            f"automation_risk={automation_risk}",
        ],
        blockers=blockers,
        stop_lines=list(DEFAULT_STOP_LINES),
    )


def _existing_fits(
    *,
    signatures: list[ActionSignature],
    events: list[CheckpointActionEvent],
    candidate_clusters: Sequence[CandidateCluster],
) -> dict[str, ExistingWrapperFit]:
    clusters_by_candidate = {cluster.candidate_id: cluster for cluster in candidate_clusters}
    result: dict[str, ExistingWrapperFit] = {}
    for signature in signatures:
        signature_events = [
            event for event in events if event.action_signature_ref == signature.signature_id
        ]
        candidate_ids = _dedupe(candidate for event in signature_events for candidate in event.candidate_ids)
        matched_clusters = [clusters_by_candidate[candidate_id] for candidate_id in candidate_ids if candidate_id in clusters_by_candidate]
        existing_surface = next((cluster.source_surface_ref for cluster in matched_clusters if cluster.source_surface_ref), None)
        blocked = {blocked for cluster in matched_clusters for blocked in cluster.blocked_by}
        if existing_surface and not blocked:
            fit_status: Literal["strong", "weak", "none"] = "strong"
            reason = "legacy candidate has an existing surface and no classifier blocker"
        elif existing_surface:
            fit_status = "weak"
            reason = "legacy candidate exists, but blockers keep this as route evidence"
        else:
            fit_status = "none"
            reason = "no existing wrapper surface matched this action signature"
        result[signature.signature_id] = ExistingWrapperFit(
            wrapper_family=signature.wrapper_family_hint,
            fit_status=fit_status,
            existing_surface_ref=existing_surface,
            nearest_existing_wrapper=existing_surface,
            fit_reason=reason,
            evidence_refs=list(signature.evidence_refs),
        )
    return result


def _sample_audit(
    *,
    signatures: list[ActionSignature],
    gaps: list[WrapperGapCandidate],
    clusters: list[RepetitionCluster],
    limit: int,
) -> list[CandidateIntelligenceSample]:
    if limit <= 0:
        return []
    samples: list[CandidateIntelligenceSample] = []
    for gap in gaps[:limit]:
        samples.append(
            CandidateIntelligenceSample(
                sample_id=f"sample:{safe_checkpoint_name(gap.candidate_id)[:96]}",
                target_ref=gap.candidate_id,
                sample_kind="wrapper_gap",
                reason="review whether this gap should be accepted, weakened, split, or converted into a rule",
                evidence_refs=list(gap.evidence_refs),
            )
        )
    remaining = max(limit - len(samples), 0)
    for cluster in clusters[:remaining]:
        samples.append(
            CandidateIntelligenceSample(
                sample_id=f"sample:{safe_checkpoint_name(cluster.cluster_id)[:96]}",
                target_ref=cluster.cluster_id,
                sample_kind="repetition_cluster",
                reason="review classifier quality; sample remains unreviewed until explicit verdict",
                evidence_refs=list(cluster.evidence_refs),
            )
        )
    remaining = max(limit - len(samples), 0)
    for signature in signatures[:remaining]:
        samples.append(
            CandidateIntelligenceSample(
                sample_id=f"sample:{safe_checkpoint_name(signature.signature_id)[:96]}",
                target_ref=signature.signature_id,
                sample_kind="signature",
                reason="review action signature quality before changing rules",
                evidence_refs=list(signature.evidence_refs),
            )
        )
    return samples


def _signature_occurrence_counts(events: list[CheckpointActionEvent]) -> Counter[str]:
    return Counter(
        event.action_signature_ref
        for event in events
        if event.action_signature_ref is not None
    )


def _candidate_cluster_occurrence_counts(
    *,
    events: list[CheckpointActionEvent],
    candidate_clusters: Sequence[CandidateCluster],
) -> Counter[str]:
    event_signature_by_candidate = {
        candidate_id: event.action_signature_ref
        for event in events
        for candidate_id in event.candidate_ids
        if event.action_signature_ref is not None
    }
    counts: Counter[str] = Counter()
    for cluster in candidate_clusters:
        signature_id = event_signature_by_candidate.get(cluster.candidate_id)
        if signature_id is None:
            continue
        counts[signature_id] += max(int(getattr(cluster, "checkpoint_hits", 1)), 1)
    return counts


def _signature_saved_event_counts(signatures: list[ActionSignature]) -> Counter[str]:
    refs_by_signature: dict[str, set[str]] = defaultdict(set)
    for signature in signatures:
        refs_by_signature[signature.signature_id].update(signature.action_event_ids)
    counts: Counter[str] = Counter()
    for signature_id, refs in refs_by_signature.items():
        counts[signature_id] = len(refs)
    return counts


def _merge_occurrence_counts(left: Counter[str], right: Counter[str]) -> Counter[str]:
    merged: Counter[str] = Counter(left)
    for key, value in right.items():
        merged[key] = max(merged.get(key, 0), value)
    return merged


def _merge_signatures(
    signatures: list[ActionSignature],
    *,
    occurrence_counts: Counter[str] | None = None,
) -> list[ActionSignature]:
    merged: dict[str, ActionSignature] = {}
    for signature in signatures:
        existing = merged.get(signature.signature_id)
        if existing is None:
            merged[signature.signature_id] = signature
            continue
        merged[signature.signature_id] = existing.model_copy(
            update={
                "evidence_refs": _dedupe([*existing.evidence_refs, *signature.evidence_refs]),
                "action_event_ids": _dedupe([*existing.action_event_ids, *signature.action_event_ids]),
                "inputs": _dedupe([*existing.inputs, *signature.inputs]),
                "steps": _dedupe([*existing.steps, *signature.steps]),
                "outputs": _dedupe([*existing.outputs, *signature.outputs]),
                "verification": _dedupe([*existing.verification, *signature.verification]),
                "failure_modes": _dedupe([*existing.failure_modes, *signature.failure_modes]),
                "stop_lines": _dedupe([*existing.stop_lines, *signature.stop_lines]),
                "owner_pressure": _dedupe([*existing.owner_pressure, *signature.owner_pressure]),
                "event_types": _dedupe([*existing.event_types, *signature.event_types]),
                "route_signals": _dedupe([*existing.route_signals, *signature.route_signals]),
                "mutation_surfaces": _dedupe(
                    [*existing.mutation_surfaces, *signature.mutation_surfaces]
                ),
                "authority_surfaces": _dedupe(
                    [*existing.authority_surfaces, *signature.authority_surfaces]
                ),
                "memory_provenance_refs": _dedupe(
                    [*existing.memory_provenance_refs, *signature.memory_provenance_refs]
                ),
                "negative_evidence": _dedupe(
                    [*existing.negative_evidence, *signature.negative_evidence]
                ),
                "confidence": _max_confidence([existing.confidence, signature.confidence]),
            }
        )
    normalized = [
        _normalize_signature_negative_evidence(
            signature,
            repeat_count=(
                occurrence_counts.get(signature.signature_id, len(signature.action_event_ids))
                if occurrence_counts
                else len(signature.action_event_ids)
            ),
        )
        for signature in merged.values()
    ]
    return sorted(normalized, key=lambda item: item.signature_id)


def _normalize_signature_negative_evidence(
    signature: ActionSignature,
    *,
    repeat_count: int,
) -> ActionSignature:
    if repeat_count > 1 and "single_event_cannot_promote" in signature.negative_evidence:
        return signature.model_copy(
            update={
                "negative_evidence": [
                    item
                    for item in signature.negative_evidence
                    if item != "single_event_cannot_promote"
                ]
            }
        )
    return signature


def _merge_events(events: list[CheckpointActionEvent]) -> list[CheckpointActionEvent]:
    merged: dict[str, CheckpointActionEvent] = {}
    for event in events:
        existing = merged.get(event.event_id)
        if existing is None:
            merged[event.event_id] = event
            continue
        merged[event.event_id] = existing.model_copy(
            update={
                "evidence_refs": _dedupe([*existing.evidence_refs, *event.evidence_refs]),
                "candidate_ids": _dedupe([*existing.candidate_ids, *event.candidate_ids]),
                "surface_refs": _dedupe([*existing.surface_refs, *event.surface_refs]),
            }
        )
    return sorted(merged.values(), key=lambda item: item.event_id)


def _item_evidence_refs(item: SurfaceOpportunityItem) -> list[str]:
    return _dedupe(
        [
            item.surface_ref,
            *(ref.ref for ref in item.family_entry_refs),
            *(ref.ref for ref in item.evidence_refs),
            *(f"skill:{name}" for name in item.related_skill_names),
        ]
    )


def _event_id(*, profile: ActionProfile, source_ref: str, trigger_text: str) -> str:
    return "action-event:" + safe_checkpoint_name(
        f"{profile.event_type}:{source_ref}:{_trigger_summary(trigger_text)}"
    )[:120]


def _signature_id(profile: ActionProfile) -> str:
    return "action-signature:" + safe_checkpoint_name(
        f"{profile.family}:{profile.action}:{profile.object}:{profile.wrapper_family}"
    )[:120]


def _trigger_summary(value: str) -> str:
    normalized = " ".join(value.strip().split())
    return normalized[:120] if normalized else "checkpoint"


def _owner_pressure(*, surface_refs: list[str], evidence_refs: list[str]) -> list[str]:
    refs = [*surface_refs, *evidence_refs]
    owners = []
    for ref in refs:
        if ref.startswith("aoa-"):
            owners.append(ref.split(":", 1)[0].split(".", 1)[0])
        elif ref.startswith("context:"):
            owners.append(ref.removeprefix("context:"))
    return _dedupe(owners)


def _mutation_surfaces(*, evidence_refs: list[str], route_signals: list[str]) -> list[str]:
    return _prefixed_values([*evidence_refs, *route_signals], "mutation_surface:")


def _authority_surfaces(*, evidence_refs: list[str], route_signals: list[str]) -> list[str]:
    authority_refs = []
    for value in [*evidence_refs, *route_signals]:
        if value.startswith("authority_surface:"):
            authority_refs.append(value.removeprefix("authority_surface:"))
        elif value.startswith("context:"):
            authority_refs.append(value.removeprefix("context:"))
        elif value.startswith("aoa-") and ":" in value:
            authority_refs.append(value.split(":", 1)[0])
    return _dedupe(authority_refs)


def _memory_provenance_refs(*, evidence_refs: list[str], route_signals: list[str]) -> list[str]:
    refs = []
    for value in [*evidence_refs, *route_signals]:
        lowered = value.lower()
        if (
            value.startswith(("session_memory:", "raw:", "memory:", "memo:"))
            or "session-memory" in lowered
            or "raw_ref" in lowered
            or "provenance" in lowered
        ):
            refs.append(value)
    return _dedupe(refs)


def _negative_evidence(
    *,
    signature_id: str,
    profile: ActionProfile,
    events: list[CheckpointActionEvent],
    repeat_count: int,
) -> list[str]:
    negatives = list(profile.failure_modes)
    if repeat_count <= 1:
        negatives.append("single_event_cannot_promote")
    if profile.wrapper_family == "unknown":
        negatives.append("wrapper_family_unknown")
    if "risk" in signature_id or any("risk" in signal for event in events for signal in event.facets.route_signals):
        negatives.append("risk_signal_requires_review")
    return _dedupe(negatives)


def _prefixed_values(values: list[str], prefix: str) -> list[str]:
    return _dedupe(
        value.removeprefix(prefix)
        for value in values
        if isinstance(value, str) and value.startswith(prefix)
    )


def _novelty_markers(intent_text: str) -> bool:
    normalized = intent_text.lower()
    return any(
        marker in normalized
        for marker in (
            "no existing",
            "missing wrapper",
            "wrapper gap",
            "new wrapper",
            "not covered",
            "нет похож",
            "нет существ",
            "новый aoa",
        )
    )


def _novelty_reason(*, fit: ExistingWrapperFit, novelty: bool) -> str:
    if novelty and fit.fit_status == "strong":
        return "operator intent names novelty pressure despite a strong existing wrapper resemblance"
    if novelty:
        return "operator intent names missing-wrapper pressure"
    if fit.fit_status == "none":
        return "no existing wrapper surface matched this action signature"
    return "existing wrapper fit is weak and should stay candidate-only until review"


def _count_stability(count: int) -> Literal["low", "medium", "high"]:
    if count >= 3:
        return "high"
    if count >= 2:
        return "medium"
    return "low"


def _stability(values: list[str]) -> Literal["low", "medium", "high"]:
    if len(values) == 1:
        return "high"
    if len(values) == 2:
        return "medium"
    return "low"


def _automation_risk(signature: ActionSignature) -> Literal["low", "medium", "high"]:
    text = " ".join([signature.action, signature.object, *signature.stop_lines, *signature.failure_modes]).lower()
    if "hidden" in text or "automation" in text or signature.wrapper_family_hint == "skill":
        return "high" if "risk" in text else "medium"
    if signature.wrapper_family_hint in {"memo", "eval"}:
        return "low"
    return "medium"


def _max_confidence(values: list[str]) -> Literal["low", "medium", "high"]:
    if "high" in values:
        return "high"
    if "medium" in values:
        return "medium"
    return "low"


def _dedupe(values) -> list[str]:  # type: ignore[no-untyped-def]
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if not isinstance(value, str) or not value:
            continue
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _resolve_repo_root(workspace: Workspace, repo_root: str) -> Path:
    path = Path(repo_root).expanduser()
    if path.is_absolute():
        return path.resolve()
    if workspace.has_repo(repo_root):
        return workspace.repo_path(repo_root)
    return (workspace.federation_root / repo_root).resolve()


def _repo_label(workspace: Workspace, repo_root: str) -> str:
    resolved = Path(repo_root).expanduser()
    if not resolved.is_absolute():
        resolved = (workspace.root / resolved).resolve()
    else:
        resolved = resolved.resolve()
    return "workspace" if resolved == workspace.federation_root else resolved.name
