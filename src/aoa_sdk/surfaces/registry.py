from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Literal, cast

from ..errors import RepoNotFound, SurfaceNotFound
from ..models import (
    CheckpointCandidateCluster,
    ProgressionAxisSignal,
    RoutingOwnerLayerShortlistHint,
    SessionCheckpointCluster,
    SessionCheckpointNote,
    SkillDetectionReport,
    SurfaceCloseoutHandoff,
    SurfaceCloseoutHandoffTarget,
    SurfaceDetectionReport,
    SurfaceOpportunityExecutionHint,
    SurfaceOpportunityItem,
    SurfaceOpportunityReference,
)
from ..routing.hints import load_owner_layer_shortlist_hints
from ..skills.detector import detect_skills
from ..skills.session import load_session
from ..workspace.discovery import Workspace
from .heuristics import EXPLICIT_LAYER_RULES_BY_TOKEN, HEURISTIC_RULES


TOKEN_RE = re.compile(r"[a-z0-9_-]+")
SURFACE_PHASES = {"ingress", "in-flight", "pre-mutation", "checkpoint", "closeout"}
MUTATION_SURFACES = {"none", "code", "repo-config", "infra", "runtime", "public-share"}
SurfaceSignal = Literal[
    "explicit-request",
    "risk-gate",
    "router-match",
    "repeated-pattern",
    "proof-need",
    "recall-need",
    "scenario-recurring",
    "role-posture",
    "closeout-chain",
]
STATE_RANK = {
    "activated": 4,
    "manual-equivalent": 3,
    "candidate-now": 2,
    "candidate-later": 1,
}
CONFIDENCE_RANK = {"high": 3, "medium": 2, "low": 1}
SIGNAL_ORDER: list[SurfaceSignal] = [
    "explicit-request",
    "risk-gate",
    "router-match",
    "repeated-pattern",
    "proof-need",
    "recall-need",
    "scenario-recurring",
    "role-posture",
    "closeout-chain",
]
ACTIVE_CHECKPOINT_NOTE_STATES = {"collecting", "reviewable"}
ACTIVE_CHECKPOINT_CLUSTER_STATES = {"collecting", "reviewable"}


class SurfacesAPI:
    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace

    def detect(
        self,
        *,
        repo_root: str,
        phase: Literal["ingress", "in-flight", "pre-mutation", "checkpoint", "closeout"],
        intent_text: str = "",
        mutation_surface: Literal["none", "code", "repo-config", "infra", "runtime", "public-share"] = "none",
        session_file: str | None = None,
        closeout_path: str | None = None,
        skill_report_path: str | None = None,
        include_shortlist: bool = True,
        checkpoint_kind: Literal[
            "manual",
            "commit",
            "verify_green",
            "pr_opened",
            "pr_merged",
            "pause",
            "owner_followthrough",
        ] | None = None,
    ) -> SurfaceDetectionReport:
        if phase not in SURFACE_PHASES:
            raise ValueError(f"unsupported phase {phase!r}")
        if mutation_surface not in MUTATION_SURFACES:
            raise ValueError(f"unsupported mutation_surface {mutation_surface!r}")

        skill_phase = phase if phase != "in-flight" else "ingress"
        skill_report = detect_skills(
            self.workspace,
            repo_root=repo_root,
            phase=skill_phase,  # type: ignore[arg-type]
            intent_text=intent_text,
            mutation_surface=mutation_surface,
            closeout_path=closeout_path,
        )
        active_skill_names = _load_active_skill_names(self.workspace, session_file=session_file)
        shortlist_hints = _load_shortlist_hints(self.workspace) if include_shortlist else []
        skill_receipt_contexts = _load_core_skill_receipt_contexts(self.workspace)
        items = _derive_surface_items(
            skill_report=skill_report,
            surface_phase=phase,
            intent_text=intent_text,
            active_skill_names=active_skill_names,
            closeout_signal=phase == "closeout" or skill_report.closeout_chain is not None,
            shortlist_hints=shortlist_hints,
            skill_receipt_contexts=skill_receipt_contexts,
        )
        candidate_clusters = _derive_checkpoint_candidate_clusters(
            items=items,
            checkpoint_kind=checkpoint_kind,
        ) if phase == "checkpoint" else []
        if phase == "checkpoint" and not candidate_clusters:
            candidate_clusters = _derive_explicit_mutation_growth_clusters(
                workspace=self.workspace,
                repo_root=repo_root,
                mutation_surface=mutation_surface,
                intent_text=intent_text,
                checkpoint_kind=checkpoint_kind,
                skill_report=skill_report,
            )
        blocked_by = _checkpoint_blocked_by(candidate_clusters) if phase == "checkpoint" else []
        checkpoint_should_capture = bool(candidate_clusters) or (
            phase == "checkpoint" and checkpoint_kind in {"manual", "pause"} and bool(items)
        )
        return SurfaceDetectionReport(
            repo_root=skill_report.repo_root,
            workspace_root=str(self.workspace.federation_root),
            phase=phase,
            intent_text=intent_text,
            mutation_surface=mutation_surface,
            checkpoint_kind=checkpoint_kind,
            skill_report_path=skill_report_path,
            skill_report_included=True,
            shortlist_included=bool(shortlist_hints),
            active_skill_names=active_skill_names,
            immediate_skill_dispatch=[item.skill_name for item in skill_report.activate_now],
            items=items,
            checkpoint_should_capture=checkpoint_should_capture,
            candidate_clusters=candidate_clusters,
            promotion_recommendation=_checkpoint_promotion_recommendation(
                candidate_clusters=candidate_clusters,
                checkpoint_kind=checkpoint_kind,
            ) if phase == "checkpoint" else "none",
            blocked_by=blocked_by,
            closeout_followups=_derive_closeout_followups(items=items, surface_phase=phase),
            owner_layer_notes=_owner_layer_notes(items=items),
            actionability_gaps=list(skill_report.actionability_gaps),
        )

    def build_closeout_handoff(
        self,
        report_or_path: SurfaceDetectionReport | str | Path,
        *,
        session_ref: str,
        reviewed: bool = True,
    ) -> SurfaceCloseoutHandoff:
        if not reviewed:
            raise ValueError("surface closeout handoff requires reviewed=True")

        report, report_ref = _load_surface_report(report_or_path)
        surviving_items = [item for item in report.items if item.state != "activated"]
        checkpoint_note = _load_current_checkpoint_note(self.workspace, report.repo_root)
        surviving_checkpoint_clusters = _closeout_surviving_checkpoint_clusters(checkpoint_note)
        checkpoint_progression_axes = (
            list(checkpoint_note.progression_axis_signals)
            if checkpoint_note is not None and checkpoint_note.state in ACTIVE_CHECKPOINT_NOTE_STATES
            else []
        )
        stats_refresh_recommended = (
            checkpoint_note.stats_refresh_recommended
            if checkpoint_note is not None and checkpoint_note.state in ACTIVE_CHECKPOINT_NOTE_STATES
            else False
        )
        checkpoint_harvest_candidates = [
            cluster for cluster in surviving_checkpoint_clusters if "harvest" in cluster.session_end_targets
        ]
        checkpoint_progression_candidates = [
            cluster for cluster in surviving_checkpoint_clusters if "progression" in cluster.session_end_targets
        ]
        checkpoint_upgrade_candidates = [
            cluster for cluster in surviving_checkpoint_clusters if "upgrade" in cluster.session_end_targets
        ]
        return SurfaceCloseoutHandoff(
            session_ref=session_ref,
            reviewed=reviewed,
            surface_detection_report_ref=report_ref,
            checkpoint_note_ref=_checkpoint_note_ref(self.workspace, report.repo_root, checkpoint_note),
            surviving_items=surviving_items,
            surviving_checkpoint_clusters=surviving_checkpoint_clusters,
            checkpoint_harvest_candidates=checkpoint_harvest_candidates,
            checkpoint_progression_candidates=checkpoint_progression_candidates,
            checkpoint_upgrade_candidates=checkpoint_upgrade_candidates,
            checkpoint_progression_axes=checkpoint_progression_axes,
            stats_refresh_recommended=stats_refresh_recommended,
            handoff_targets=_derive_closeout_handoff_targets(
                surviving_items=surviving_items,
                surviving_checkpoint_clusters=surviving_checkpoint_clusters,
                checkpoint_harvest_candidates=checkpoint_harvest_candidates,
                checkpoint_progression_candidates=checkpoint_progression_candidates,
                checkpoint_progression_axes=checkpoint_progression_axes,
                checkpoint_upgrade_candidates=checkpoint_upgrade_candidates,
                actionability_gaps=report.actionability_gaps,
            ),
            notes=[
                "use the session-growth kernel only after reviewed run, closure, or pause",
                "do not let donor-harvest or automation scan become hidden live routing authority",
                *(
                    ["checkpoint candidates stayed local until reviewed closeout; move candidates and stats only from the final handoff"]
                    if checkpoint_note is not None and checkpoint_note.carry_until_session_closeout
                    else []
                ),
                *(
                    ["preserve the checkpoint note as reviewed pre-harvest context instead of replaying raw append history"]
                    if checkpoint_note is not None
                    else []
                ),
            ],
        )


def _load_surface_report(report_or_path: SurfaceDetectionReport | str | Path) -> tuple[SurfaceDetectionReport, str]:
    if isinstance(report_or_path, SurfaceDetectionReport):
        return report_or_path, "in-memory:surface-detection-report"

    payload = json.loads(Path(report_or_path).expanduser().resolve().read_text(encoding="utf-8"))
    report_payload = payload.get("report", payload)
    return SurfaceDetectionReport.model_validate(report_payload), str(Path(report_or_path).expanduser().resolve())


def _load_active_skill_names(workspace: Workspace, *, session_file: str | None) -> list[str]:
    try:
        session = load_session(workspace, session_file)
    except SurfaceNotFound:
        return []
    return [record.name for record in session.active_skills]


def _derive_surface_items(
    *,
    skill_report: SkillDetectionReport,
    surface_phase: Literal["ingress", "in-flight", "pre-mutation", "checkpoint", "closeout"],
    intent_text: str,
    active_skill_names: list[str],
    closeout_signal: bool,
    shortlist_hints: list[RoutingOwnerLayerShortlistHint],
    skill_receipt_contexts: dict[str, dict[str, object]],
) -> list[SurfaceOpportunityItem]:
    items: list[SurfaceOpportunityItem] = []
    items.extend(
        _derive_skill_surface_items(
            skill_report=skill_report,
            surface_phase=surface_phase,
            closeout_signal=closeout_signal,
        )
    )
    items.extend(
        _derive_heuristic_items(
            intent_text=intent_text,
            surface_phase=surface_phase,
            active_skill_names=active_skill_names,
            closeout_signal=closeout_signal,
        )
    )
    deduped = _dedupe_surface_items(items)
    enriched = [
        _enrich_item_with_shortlist(item, shortlist_hints=shortlist_hints)
        for item in deduped
    ]
    return [
        _enrich_item_with_skill_receipt_context(item, skill_receipt_contexts=skill_receipt_contexts)
        for item in enriched
    ]


def _derive_skill_surface_items(
    *,
    skill_report: SkillDetectionReport,
    surface_phase: Literal["ingress", "in-flight", "pre-mutation", "checkpoint", "closeout"],
    closeout_signal: bool,
) -> list[SurfaceOpportunityItem]:
    items: list[SurfaceOpportunityItem] = []
    for item in skill_report.activate_now:
        signals: list[SurfaceSignal] = ["router-match"]
        if closeout_signal:
            signals.append("closeout-chain")
        items.append(
            SurfaceOpportunityItem(
                surface_ref=f"aoa-skills:{item.skill_name}",
                display_name=_display_name(item.skill_name),
                object_kind="skill",
                owner_repo="aoa-skills",
                state="activated",
                phase_detected=surface_phase,
                reason=item.reason,
                signals=_ordered_signals(signals),
                confidence="high",
                execution=SurfaceOpportunityExecutionHint(
                    lane="skill-dispatch",
                    executable_now=True,
                    requires_confirmation=False,
                    existing_command="aoa skills dispatch",
                    existing_surface=f".agents/skills/{item.skill_name}/SKILL.md",
                    manual_fallback_allowed=False,
                    manual_fallback_note=None,
                    host_availability_status=item.host_availability.status,
                ),
                related_skill_names=[],
                closeout_family_candidates=["aoa-session-donor-harvest"],
                promotion_hint=None,
                family_entry_refs=_default_family_entry_refs(
                    owner_repo="aoa-skills",
                    surface_ref=None,
                    inspect_surface=f".agents/skills/{item.skill_name}/SKILL.md",
                ),
            )
        )

    fallback_items = [*skill_report.must_confirm, *skill_report.suggest_next]
    for item in fallback_items:
        if item.host_availability.status != "router-only" or not item.host_availability.manual_fallback_allowed:
            continue
        fallback_signals: list[SurfaceSignal] = ["router-match"]
        if item in skill_report.must_confirm:
            fallback_signals.append("risk-gate")
        if closeout_signal:
            fallback_signals.append("closeout-chain")
        items.append(
            SurfaceOpportunityItem(
                surface_ref=f"aoa-skills:{item.skill_name}",
                display_name=_display_name(item.skill_name),
                object_kind="skill",
                owner_repo="aoa-skills",
                state="manual-equivalent",
                phase_detected=surface_phase,
                reason=item.reason,
                signals=_ordered_signals(fallback_signals),
                confidence="high" if item in skill_report.must_confirm else "medium",
                execution=SurfaceOpportunityExecutionHint(
                    lane="manual-fallback",
                    executable_now=False,
                    requires_confirmation=item in skill_report.must_confirm,
                    existing_command=(
                        "aoa skills guard"
                        if surface_phase == "pre-mutation"
                        else "aoa skills detect --phase checkpoint"
                        if surface_phase == "checkpoint"
                        else "aoa skills detect"
                    ),
                    existing_surface=None,
                    manual_fallback_allowed=True,
                    manual_fallback_note="keep the distinction visible: the same discipline was followed manually, not claimed as a real activation",
                    host_availability_status=item.host_availability.status,
                ),
                related_skill_names=_related_skill_names(skill_report, item.skill_name),
                closeout_family_candidates=["aoa-session-donor-harvest"],
                promotion_hint=None,
                family_entry_refs=[],
            )
        )

    return items


def _derive_heuristic_items(
    *,
    intent_text: str,
    surface_phase: Literal["ingress", "in-flight", "pre-mutation", "checkpoint", "closeout"],
    active_skill_names: list[str],
    closeout_signal: bool,
) -> list[SurfaceOpportunityItem]:
    items: list[SurfaceOpportunityItem] = []
    tokens = set(TOKEN_RE.findall(intent_text.casefold()))

    for rule in HEURISTIC_RULES:
        if rule.id == "repeated-pattern":
            if not _repeated_pattern_detected(tokens=tokens, active_skill_names=active_skill_names, phase=surface_phase):
                continue
        elif not tokens.intersection(rule.tokens):
            continue
        rule_signals: list[SurfaceSignal] = [rule.signal]
        if closeout_signal:
            rule_signals.append("closeout-chain")
        items.append(
            SurfaceOpportunityItem(
                surface_ref=rule.surface_ref,
                display_name=rule.display_name,
                object_kind=rule.object_kind,
                owner_repo=rule.owner_repo,
                state=rule.default_state,
                phase_detected=surface_phase,
                reason=rule.reason_template,
                signals=_ordered_signals(rule_signals),
                confidence=rule.confidence,
                execution=SurfaceOpportunityExecutionHint(
                    lane=rule.execution_lane,
                    executable_now=False,
                    requires_confirmation=False,
                    existing_command=None,
                    existing_surface=rule.existing_surface,
                    manual_fallback_allowed=False,
                    manual_fallback_note=None,
                    host_availability_status=None,
                ),
                related_skill_names=[],
                closeout_family_candidates=list(rule.closeout_family_candidates),
                promotion_hint=rule.promotion_hint,
                family_entry_refs=_default_family_entry_refs(
                    owner_repo=rule.owner_repo,
                    surface_ref=rule.surface_ref,
                    inspect_surface=rule.existing_surface,
                ),
            )
        )

    for token in sorted(tokens):
        explicit_rule = EXPLICIT_LAYER_RULES_BY_TOKEN.get(token)
        if explicit_rule is None:
            continue
        explicit_signals: list[SurfaceSignal] = ["explicit-request"]
        if closeout_signal:
            explicit_signals.append("closeout-chain")
        items.append(
            SurfaceOpportunityItem(
                surface_ref=explicit_rule.surface_ref,
                display_name=explicit_rule.display_name,
                object_kind=explicit_rule.object_kind,
                owner_repo=explicit_rule.owner_repo,
                state="candidate-now",
                phase_detected=surface_phase,
                reason=f"intent names the {explicit_rule.owner_repo} layer directly; prefer owner-layer-aware routing over silent guessing",
                signals=_ordered_signals(explicit_signals),
                confidence="high",
                execution=SurfaceOpportunityExecutionHint(
                    lane="inspect-expand-use",
                    executable_now=False,
                    requires_confirmation=False,
                    existing_command=None,
                    existing_surface=explicit_rule.existing_surface,
                    manual_fallback_allowed=False,
                    manual_fallback_note=None,
                    host_availability_status=None,
                ),
                related_skill_names=[],
                closeout_family_candidates=[],
                promotion_hint=None,
                family_entry_refs=_default_family_entry_refs(
                    owner_repo=explicit_rule.owner_repo,
                    surface_ref=None if explicit_rule.surface_ref.startswith("aoa-skills:") else explicit_rule.surface_ref,
                    inspect_surface=explicit_rule.existing_surface,
                ),
            )
        )

    return items


def _derive_explicit_mutation_growth_clusters(
    *,
    workspace: Workspace,
    repo_root: str,
    mutation_surface: Literal["none", "code", "repo-config", "infra", "runtime", "public-share"],
    intent_text: str,
    checkpoint_kind: Literal[
        "manual",
        "commit",
        "verify_green",
        "pr_opened",
        "pr_merged",
        "pause",
        "owner_followthrough",
    ] | None,
    skill_report: SkillDetectionReport,
) -> list[CheckpointCandidateCluster]:
    if checkpoint_kind not in {"commit", "verify_green"}:
        return []
    explicit_checkpoint_kind = cast(Literal["commit", "verify_green"], checkpoint_kind)
    if mutation_surface == "none":
        return []
    if not _intent_explicitly_requests_checkpoint_kind(
        intent_text=intent_text,
        checkpoint_kind=explicit_checkpoint_kind,
    ):
        return []

    context_label = _surface_context_label(workspace, repo_root)
    evidence_refs = _explicit_mutation_growth_evidence_refs(
        skill_report=skill_report,
        mutation_surface=mutation_surface,
        context_label=context_label,
    )
    if len(evidence_refs) < 2:
        return []

    blocked_by: list[str] = []
    defer_reason: str | None = None
    if context_label == "workspace":
        blocked_by.append("owner-ambiguity")
        defer_reason = "workspace-wide mutation growth still needs owner review before promotion beyond the local note"

    display_name = (
        "Verify-green growth seam"
        if explicit_checkpoint_kind == "verify_green"
        else "Commit growth seam"
    )
    promote_if = [
        (
            "keep the same bounded mutation seam stable through a reviewed verify-green pass"
            if explicit_checkpoint_kind == "verify_green"
            else "pair this explicit commit seam with one reviewed verify-green checkpoint before promotion"
        ),
        "repeat the same bounded mutation seam across another reviewed checkpoint before promoting beyond the local note",
    ]
    next_owner_moves = [
        "append the explicit mutation seam into the local checkpoint note",
        "carry the explicit mutation seam through reviewed session closeout before moving candidates or stats",
        (
            "review the same bounded mutation again after verify-green before promoting it"
            if explicit_checkpoint_kind == "commit"
            else "confirm the verify-green seam still points to the same bounded owner context"
        ),
    ]

    return [
        CheckpointCandidateCluster(
            candidate_id=f"candidate:growth:{_slugify(f'{context_label}-{explicit_checkpoint_kind}-{mutation_surface}')}",
            candidate_kind="growth",
            owner_hint=context_label,
            display_name=display_name,
            source_surface_ref=f"aoa-sdk:checkpoint_auto_capture.{explicit_checkpoint_kind}",
            evidence_refs=evidence_refs,
            confidence="high" if explicit_checkpoint_kind == "verify_green" else "medium",
            session_end_targets=["harvest", "progression"],
            progression_axis_signals=_progression_axis_signals_for_explicit_growth(
                candidate_id=f"candidate:growth:{_slugify(f'{context_label}-{explicit_checkpoint_kind}-{mutation_surface}')}",
                checkpoint_kind=explicit_checkpoint_kind,
                blocked_by=blocked_by,
                evidence_refs=evidence_refs,
            ),
            promote_if=promote_if,
            defer_reason=defer_reason,
            blocked_by=blocked_by,
            next_owner_moves=next_owner_moves,
        )
    ]


def _intent_explicitly_requests_checkpoint_kind(
    *,
    intent_text: str,
    checkpoint_kind: Literal["commit", "verify_green"],
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
    return "checkpoint" in normalized or "commit" in normalized


def _explicit_mutation_growth_evidence_refs(
    *,
    skill_report: SkillDetectionReport,
    mutation_surface: Literal["none", "code", "repo-config", "infra", "runtime", "public-share"],
    context_label: str,
) -> list[str]:
    refs = [
        f"context:{context_label}",
        f"mutation_surface:{mutation_surface}",
    ]
    for item in [*skill_report.activate_now, *skill_report.must_confirm, *skill_report.suggest_next]:
        refs.append(f"aoa-skills:{item.skill_name}")
    return _dedupe_strings(refs)


def _progression_axis_signals_for_explicit_growth(
    *,
    candidate_id: str,
    checkpoint_kind: Literal["commit", "verify_green"],
    blocked_by: list[str],
    evidence_refs: list[str],
) -> list[ProgressionAxisSignal]:
    templates: list[tuple[str, str, str]] = [
        (
            "execution_reliability",
            "advance",
            "bounded mutation evidence suggests the session improved execution reliability, pending reviewed closeout",
        ),
        (
            "change_legibility",
            "advance",
            "the explicit checkpoint seam makes the change easier to narrate and verify later",
        ),
    ]
    if checkpoint_kind == "verify_green":
        templates.append(
            (
                "proof_discipline",
                "advance",
                "verify-green evidence strengthens proof discipline for the bounded mutation seam",
            )
        )
    signals: list[ProgressionAxisSignal] = []
    for axis, movement, why in templates:
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
                movement=cast(
                    Literal["advance", "hold", "reanchor", "downgrade"],
                    _adjust_progression_movement(movement=movement, blocked_by=blocked_by),
                ),
                why=why,
                evidence_refs=list(evidence_refs),
                candidate_ids=[candidate_id],
            )
        )
    return signals


def _repeated_pattern_detected(
    *,
    tokens: set[str],
    active_skill_names: list[str],
    phase: Literal["ingress", "in-flight", "pre-mutation", "checkpoint", "closeout"],
) -> bool:
    repeated_tokens = {"repeat", "repeated", "again", "pattern", "recurring"}
    return bool(tokens.intersection(repeated_tokens)) and (phase in {"closeout", "checkpoint"} or bool(active_skill_names))


def _surface_context_label(workspace: Workspace, repo_root: str) -> str:
    resolved = Path(repo_root).expanduser()
    if not resolved.is_absolute():
        resolved = (workspace.root / resolved).resolve()
    else:
        resolved = resolved.resolve()
    return "workspace" if resolved == workspace.federation_root else resolved.name


def _derive_closeout_followups(
    *,
    items: list[SurfaceOpportunityItem],
    surface_phase: Literal["ingress", "in-flight", "pre-mutation", "checkpoint", "closeout"],
) -> list[str]:
    followups: list[str] = []
    if items:
        if surface_phase == "checkpoint":
            followups.append("append the surviving checkpoint candidates into the local reviewed note before any promotion decision")
        else:
            followups.append("bundle surviving notes into a reviewed closeout handoff before any promotion decision")
    if any(item.object_kind == "playbook" for item in items):
        followups.append("route recurring-route evidence through aoa-automation-opportunity-scan before naming automation authority")
    if any(item.object_kind in {"playbook", "technique"} and item.promotion_hint for item in items):
        followups.append("use aoa-quest-harvest only for the final promote-or-defer decision after repeated reviewed evidence exists")
    return followups


def _owner_layer_notes(*, items: list[SurfaceOpportunityItem]) -> list[str]:
    notes = [
        "aoa-sdk stays on the control plane; it may detect and hand off but does not become the source of truth for eval, memo, playbook, technique, or agent meaning",
        "playbook, eval, memo, agent, and technique items remain hints, candidates, or closeout handoffs in wave one; they are not auto-activatable runtime objects here",
    ]
    if any(item.shortlist_hints for item in items):
        notes.append("routing shortlist hints stay advisory only; they can sharpen inspection and ambiguity reporting but never overwrite activation truth")
    if any(item.state == "manual-equivalent" for item in items):
        notes.append("manual-equivalent remains distinct from activated all the way through reporting and closeout")
    return notes


def _derive_closeout_handoff_targets(
    *,
    surviving_items: list[SurfaceOpportunityItem],
    surviving_checkpoint_clusters: list[SessionCheckpointCluster],
    checkpoint_harvest_candidates: list[SessionCheckpointCluster],
    checkpoint_progression_candidates: list[SessionCheckpointCluster],
    checkpoint_progression_axes: list[ProgressionAxisSignal],
    checkpoint_upgrade_candidates: list[SessionCheckpointCluster],
    actionability_gaps: list[str],
) -> list[SurfaceCloseoutHandoffTarget]:
    targets: list[SurfaceCloseoutHandoffTarget] = []
    checkpoint_triggered_by = [f"checkpoint:{cluster.candidate_id}" for cluster in surviving_checkpoint_clusters]
    if surviving_items or surviving_checkpoint_clusters:
        targets.append(
            SurfaceCloseoutHandoffTarget(
                skill_name="aoa-session-donor-harvest",
                why="bundle the surviving bounded notes into a reviewable harvest packet instead of leaving them as session residue",
                triggered_by=[*([item.surface_ref for item in surviving_items]), *checkpoint_triggered_by],
            )
        )
    if checkpoint_progression_candidates or checkpoint_progression_axes:
        targets.append(
            SurfaceCloseoutHandoffTarget(
                skill_name="aoa-session-progression-lift",
                why="reviewed closeout should turn provisional checkpoint axis movement into one explicit progression delta before any final quest verdict",
                triggered_by=[
                    *[f"checkpoint-progression:{cluster.candidate_id}" for cluster in checkpoint_progression_candidates],
                    *[f"checkpoint-axis:{signal.axis}" for signal in checkpoint_progression_axes],
                ],
            )
        )
    playbook_items = [
        item
        for item in surviving_items
        if item.object_kind == "playbook" and "scenario-recurring" in item.signals
    ]
    if playbook_items:
        targets.append(
            SurfaceCloseoutHandoffTarget(
                skill_name="aoa-automation-opportunity-scan",
                why="the recurring-route candidate is about repeated manual process and owner-layer routing, not immediate activation",
                triggered_by=[item.surface_ref for item in playbook_items],
            )
        )
    diagnose_items = [
        item
        for item in surviving_items
        if item.state == "manual-equivalent" and "risk-gate" in item.signals
    ]
    if diagnose_items or actionability_gaps:
        targets.append(
            SurfaceCloseoutHandoffTarget(
                skill_name="aoa-session-self-diagnose",
                why="router-only risk-gate or actionability-gap notes should become explicit diagnosis rather than hidden route residue",
                triggered_by=[item.surface_ref for item in diagnose_items] or [f"skill-gap:{name}" for name in actionability_gaps],
            )
        )
    promotion_items = [
        item
        for item in surviving_items
        if item.object_kind in {"playbook", "technique"} and item.state == "candidate-later" and item.promotion_hint
    ]
    if promotion_items:
        targets.append(
            SurfaceCloseoutHandoffTarget(
                skill_name="aoa-quest-harvest",
                why="playbook-versus-technique promotion questions should stay reviewed closeout decisions rather than live-session guesses",
                triggered_by=[item.surface_ref for item in promotion_items],
            )
        )
    elif checkpoint_upgrade_candidates:
        targets.append(
            SurfaceCloseoutHandoffTarget(
                skill_name="aoa-quest-harvest",
                why="checkpoint-marked upgrade candidates should be reviewed after progression lift, not promoted during the session",
                triggered_by=[f"checkpoint-upgrade:{cluster.candidate_id}" for cluster in checkpoint_upgrade_candidates],
            )
        )
    return targets


def _dedupe_surface_items(items: list[SurfaceOpportunityItem]) -> list[SurfaceOpportunityItem]:
    deduped: dict[str, SurfaceOpportunityItem] = {}
    order: list[str] = []
    for item in items:
        existing = deduped.get(item.surface_ref)
        if existing is None:
            deduped[item.surface_ref] = item
            order.append(item.surface_ref)
            continue
        deduped[item.surface_ref] = _merge_surface_items(existing, item)
    return [deduped[key] for key in order]


def _merge_surface_items(left: SurfaceOpportunityItem, right: SurfaceOpportunityItem) -> SurfaceOpportunityItem:
    chosen = left
    if STATE_RANK[right.state] > STATE_RANK[left.state]:
        chosen = right
    elif STATE_RANK[right.state] == STATE_RANK[left.state] and CONFIDENCE_RANK[right.confidence] > CONFIDENCE_RANK[left.confidence]:
        chosen = right

    merged_reason = left.reason if left.reason == right.reason else f"{left.reason}; {right.reason}"
    chosen_execution = chosen.execution
    other_execution = right.execution if chosen is left else left.execution
    if chosen_execution.existing_surface is None and other_execution.existing_surface is not None:
        chosen_execution = chosen_execution.model_copy(update={"existing_surface": other_execution.existing_surface})
    if chosen_execution.existing_command is None and other_execution.existing_command is not None:
        chosen_execution = chosen_execution.model_copy(update={"existing_command": other_execution.existing_command})

    return chosen.model_copy(
        update={
            "reason": merged_reason,
            "signals": _ordered_signals([*left.signals, *right.signals]),
            "related_skill_names": list(dict.fromkeys([*left.related_skill_names, *right.related_skill_names])),
            "closeout_family_candidates": list(
                dict.fromkeys([*left.closeout_family_candidates, *right.closeout_family_candidates])
            ),
            "promotion_hint": left.promotion_hint or right.promotion_hint,
            "execution": chosen_execution,
            "shortlist_hints": _dedupe_shortlist_hints([*left.shortlist_hints, *right.shortlist_hints]),
            "owner_layer_ambiguity_note": left.owner_layer_ambiguity_note or right.owner_layer_ambiguity_note,
            "family_entry_refs": _dedupe_refs([*left.family_entry_refs, *right.family_entry_refs]),
            "evidence_refs": _dedupe_refs([*left.evidence_refs, *right.evidence_refs]),
        }
    )


def _ordered_signals(signals: list[SurfaceSignal]) -> list[SurfaceSignal]:
    unique = list(dict.fromkeys(signal for signal in signals if signal))
    return sorted(unique, key=lambda signal: SIGNAL_ORDER.index(signal) if signal in SIGNAL_ORDER else len(SIGNAL_ORDER))


def _display_name(skill_name: str) -> str:
    words = [part for part in skill_name.replace("aoa-", "").split("-") if part]
    return "AoA " + " ".join(word.capitalize() for word in words)


def _related_skill_names(skill_report: SkillDetectionReport, skill_name: str) -> list[str]:
    related = [
        item.skill_name
        for item in [*skill_report.must_confirm, *skill_report.suggest_next]
        if item.skill_name != skill_name and item.host_availability.status == "router-only"
    ]
    return list(dict.fromkeys(related))


def _load_shortlist_hints(workspace: Workspace) -> list[RoutingOwnerLayerShortlistHint]:
    try:
        return load_owner_layer_shortlist_hints(workspace)
    except (RepoNotFound, SurfaceNotFound):
        return []


def _load_core_skill_receipt_contexts(workspace: Workspace) -> dict[str, dict[str, object]]:
    try:
        receipt_path = workspace.repo_path("aoa-skills") / ".aoa" / "live_receipts" / "core-skill-applications.jsonl"
    except RepoNotFound:
        return {}
    if not receipt_path.exists():
        return {}

    latest_by_skill: dict[str, dict[str, object]] = {}
    for line_number, raw_line in enumerate(receipt_path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        try:
            receipt = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(receipt, dict) or receipt.get("event_kind") != "core_skill_application_receipt":
            continue
        payload = receipt.get("payload")
        if not isinstance(payload, dict) or payload.get("application_stage") != "finish":
            continue
        skill_name = payload.get("skill_name")
        if not isinstance(skill_name, str) or not skill_name:
            continue
        sort_key = (str(receipt.get("observed_at") or ""), str(receipt.get("event_id") or ""), line_number)
        existing = latest_by_skill.get(skill_name)
        existing_sort_key = existing.get("_sort_key") if existing is not None else None
        if (
            isinstance(existing_sort_key, tuple)
            and len(existing_sort_key) == 3
            and isinstance(existing_sort_key[0], str)
            and isinstance(existing_sort_key[1], str)
            and isinstance(existing_sort_key[2], int)
            and existing_sort_key >= sort_key
        ):
            continue
        context = payload.get("surface_detection_context")
        latest_by_skill[skill_name] = {
            "_sort_key": sort_key,
            "event_id": receipt.get("event_id"),
            "detail_receipt_ref": payload.get("detail_receipt_ref"),
            "surface_detection_context": context if isinstance(context, dict) else {},
        }
    return latest_by_skill


def _default_family_entry_refs(
    *,
    owner_repo: str,
    surface_ref: str | None,
    inspect_surface: str | None,
) -> list[SurfaceOpportunityReference]:
    refs: list[SurfaceOpportunityReference] = []
    if inspect_surface:
        refs.append(
            SurfaceOpportunityReference(
                role="inspect",
                ref=inspect_surface,
                owner_repo=owner_repo,
                note="stable inspect surface",
            )
        )
    if surface_ref:
        refs.append(
            SurfaceOpportunityReference(
                role="family-entry",
                ref=surface_ref,
                owner_repo=owner_repo,
                note="canonical family entry surface",
            )
        )
    return refs


def _enrich_item_with_shortlist(
    item: SurfaceOpportunityItem,
    *,
    shortlist_hints: list[RoutingOwnerLayerShortlistHint],
) -> SurfaceOpportunityItem:
    matching = [
        hint
        for hint in shortlist_hints
        if hint.signal in item.signals
    ]
    if not matching:
        return item

    ambiguity_note: str | None = item.owner_layer_ambiguity_note
    matching_repos = {hint.owner_repo for hint in matching}
    if ambiguity_note is None and (len(matching_repos) > 1 or any(hint.ambiguity == "ambiguous" for hint in matching)):
        ambiguity_note = (
            "routing shortlist keeps "
            + ", ".join(sorted(matching_repos))
            + " visible as adjacent owner-layer options until reviewed evidence resolves the ambiguity"
        )

    shortlist_refs = [
        *item.family_entry_refs,
        *[
            SurfaceOpportunityReference(
                role="inspect",
                ref=hint.inspect_surface,
                owner_repo=hint.owner_repo,
                note=hint.hint_reason,
            )
            for hint in matching
            if hint.inspect_surface
        ],
        *[
            SurfaceOpportunityReference(
                role="family-entry",
                ref=hint.target_surface,
                owner_repo=hint.owner_repo,
                note=hint.hint_reason,
            )
            for hint in matching
        ],
        *[
            SurfaceOpportunityReference(
                role="inspect",
                ref=hint.target_surface,
                owner_repo=hint.owner_repo,
                note=hint.hint_reason,
            )
            for hint in matching
            if hint.inspect_surface and hint.inspect_surface != hint.target_surface
        ],
    ]
    return item.model_copy(
        update={
            "shortlist_hints": _dedupe_shortlist_hints([*item.shortlist_hints, *matching]),
            "owner_layer_ambiguity_note": ambiguity_note,
            "family_entry_refs": _dedupe_refs(shortlist_refs),
        }
    )


def _enrich_item_with_skill_receipt_context(
    item: SurfaceOpportunityItem,
    *,
    skill_receipt_contexts: dict[str, dict[str, object]],
) -> SurfaceOpportunityItem:
    if item.object_kind != "skill" or not item.surface_ref.startswith("aoa-skills:"):
        return item
    skill_name = item.surface_ref.split(":", 1)[1]
    receipt_info = skill_receipt_contexts.get(skill_name)
    if receipt_info is None:
        return item

    evidence_refs = list(item.evidence_refs)
    event_id = receipt_info.get("event_id")
    if isinstance(event_id, str) and event_id:
        evidence_refs.append(
            SurfaceOpportunityReference(
                role="runtime-receipt",
                ref=f"repo:aoa-skills/.aoa/live_receipts/core-skill-applications.jsonl#{event_id}",
                owner_repo="aoa-skills",
                note="latest finish-stage core skill receipt",
            )
        )
    detail_receipt_ref = receipt_info.get("detail_receipt_ref")
    if isinstance(detail_receipt_ref, str) and detail_receipt_ref:
        evidence_refs.append(
            SurfaceOpportunityReference(
                role="runtime-receipt",
                ref=detail_receipt_ref,
                owner_repo="aoa-skills",
                note="detail receipt linked from the latest finish-stage core skill receipt",
            )
        )

    context = receipt_info.get("surface_detection_context")
    if not isinstance(context, dict):
        context = {}
    if isinstance(context.get("surface_detection_report_ref"), str) and context["surface_detection_report_ref"]:
        evidence_refs.append(
            SurfaceOpportunityReference(
                role="skill-report",
                ref=context["surface_detection_report_ref"],
                owner_repo="aoa-sdk",
                note="reviewed surface detection report captured by the skill-side receipt",
            )
        )
    if isinstance(context.get("surface_closeout_handoff_ref"), str) and context["surface_closeout_handoff_ref"]:
        evidence_refs.append(
            SurfaceOpportunityReference(
                role="closeout-handoff",
                ref=context["surface_closeout_handoff_ref"],
                owner_repo="aoa-sdk",
                note="reviewed surface closeout handoff captured by the skill-side receipt",
            )
        )

    family_entry_refs = list(item.family_entry_refs)
    family_entry_refs.extend(
        SurfaceOpportunityReference(
            role="family-entry",
            ref=ref,
            note="adjacent owner-layer family entry preserved in the latest core skill receipt",
        )
        for ref in context.get("family_entry_refs", [])
        if isinstance(ref, str) and ref
    )

    ambiguity_note = item.owner_layer_ambiguity_note
    if ambiguity_note is None and bool(context.get("owner_layer_ambiguity")):
        adjacent_owner_repos = [
            repo
            for repo in context.get("adjacent_owner_repos", [])
            if isinstance(repo, str) and repo
        ]
        if adjacent_owner_repos:
            ambiguity_note = (
                "skill receipt preserved adjacent owner-layer relevance for "
                + ", ".join(adjacent_owner_repos)
            )

    return item.model_copy(
        update={
            "owner_layer_ambiguity_note": ambiguity_note,
            "family_entry_refs": _dedupe_refs(family_entry_refs),
            "evidence_refs": _dedupe_refs(evidence_refs),
        }
    )


def _dedupe_shortlist_hints(
    hints: list[RoutingOwnerLayerShortlistHint],
) -> list[RoutingOwnerLayerShortlistHint]:
    deduped: dict[str, RoutingOwnerLayerShortlistHint] = {}
    for hint in hints:
        deduped[hint.shortlist_id] = hint
    return list(deduped.values())


def _dedupe_refs(refs: list[SurfaceOpportunityReference]) -> list[SurfaceOpportunityReference]:
    deduped: dict[tuple[str, str], SurfaceOpportunityReference] = {}
    for ref in refs:
        deduped[(ref.role, ref.ref)] = ref
    return list(deduped.values())


def _derive_checkpoint_candidate_clusters(
    *,
    items: list[SurfaceOpportunityItem],
    checkpoint_kind: Literal[
        "manual",
        "commit",
        "verify_green",
        "pr_opened",
        "pr_merged",
        "pause",
        "owner_followthrough",
    ] | None,
) -> list[CheckpointCandidateCluster]:
    clusters: list[CheckpointCandidateCluster] = []
    for item in items:
        if item.state == "activated":
            continue
        evidence_refs = _dedupe_strings(
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
        if item.state == "manual-equivalent" and "risk-gate" in item.signals:
            blocked_by.append("requires-reviewed-route")
        candidate_kind = _candidate_kind_for_item(item)
        defer_reason = None
        if "owner-ambiguity" in blocked_by:
            defer_reason = "owner ambiguity still exceeds checkpoint-note promotion authority"
        elif "thin-evidence" in blocked_by:
            defer_reason = "thin evidence should stay local until another checkpoint confirms the same candidate"
        promote_if = _dedupe_strings(
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
        next_owner_moves = _dedupe_strings(
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
        clusters.append(
            CheckpointCandidateCluster(
                candidate_id=f"candidate:{candidate_kind}:{_slugify(item.surface_ref)}",
                candidate_kind=candidate_kind,
                owner_hint=item.owner_repo,
                display_name=item.display_name,
                source_surface_ref=item.surface_ref,
                evidence_refs=evidence_refs,
                confidence=item.confidence,
                session_end_targets=_session_end_targets_for_candidate_kind(candidate_kind),
                progression_axis_signals=_progression_axis_signals_for_item(
                    item,
                    candidate_kind=candidate_kind,
                    blocked_by=blocked_by,
                    evidence_refs=evidence_refs,
                ),
                promote_if=promote_if,
                defer_reason=defer_reason,
                blocked_by=blocked_by,
                next_owner_moves=next_owner_moves,
            )
        )
    return clusters


def _candidate_kind_for_item(item: SurfaceOpportunityItem) -> str:
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


def _session_end_targets_for_candidate_kind(candidate_kind: str) -> list[Literal["harvest", "progression", "upgrade"]]:
    targets: list[Literal["harvest", "progression", "upgrade"]] = ["harvest", "progression"]
    if candidate_kind in {"route", "pattern", "proof", "recall", "role"}:
        targets.append("upgrade")
    return targets


def _progression_axis_signals_for_item(
    item: SurfaceOpportunityItem,
    *,
    candidate_kind: str,
    blocked_by: list[str],
    evidence_refs: list[str],
) -> list[ProgressionAxisSignal]:
    templates: list[tuple[str, str, str]]
    if candidate_kind == "route":
        templates = [
            (
                "change_legibility",
                "advance",
                "recurring-route evidence makes this session easier to hand off and review honestly",
            ),
            (
                "deep_readiness",
                "advance",
                "repeated route evidence hints that the route may be ready for a stronger reusable shape later",
            ),
        ]
    elif candidate_kind == "pattern":
        templates = [
            (
                "deep_readiness",
                "advance",
                "pattern-shaped evidence suggests the route is approaching reusable technique form",
            ),
            (
                "review_sharpness",
                "advance",
                "named pattern evidence sharpens later reviewed interpretation",
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
                "explicit proof artifacts sharpen later closeout judgment",
            ),
        ]
    elif candidate_kind == "recall":
        templates = [
            (
                "provenance_hygiene",
                "advance",
                "recall surfaces preserve route memory and attribution for later review",
            ),
            (
                "change_legibility",
                "advance",
                "memo-shaped recall makes the route easier to narrate without replaying raw history",
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
                "role evidence may reflect deeper readiness once it is reviewed in owner context",
            ),
        ]
    elif candidate_kind == "risk":
        templates = [
            (
                "boundary_integrity",
                "reanchor",
                "risk-gated evidence says progression must stay bounded and reviewed",
            ),
            (
                "proof_discipline",
                "hold",
                "risk-shaped signals should hold until reviewed proof confirms the same concern",
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
                movement=cast(
                    Literal["advance", "hold", "reanchor", "downgrade"],
                    _adjust_progression_movement(movement=movement, blocked_by=blocked_by),
                ),
                why=why,
                evidence_refs=list(evidence_refs),
                candidate_ids=[f"candidate:{candidate_kind}:{_slugify(item.surface_ref)}"],
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


def _checkpoint_blocked_by(clusters: list[CheckpointCandidateCluster]) -> list[str]:
    return _dedupe_strings([blocked for cluster in clusters for blocked in cluster.blocked_by])


def _checkpoint_promotion_recommendation(
    *,
    candidate_clusters: list[CheckpointCandidateCluster],
    checkpoint_kind: Literal[
        "manual",
        "commit",
        "verify_green",
        "pr_opened",
        "pr_merged",
        "pause",
        "owner_followthrough",
    ] | None,
) -> Literal["none", "local_note", "dionysus_note", "harvest_handoff"]:
    if not candidate_clusters:
        return "none"
    if checkpoint_kind == "owner_followthrough" and any("owner-ambiguity" not in cluster.blocked_by for cluster in candidate_clusters):
        return "harvest_handoff"
    if any(len(cluster.evidence_refs) >= 3 and "owner-ambiguity" not in cluster.blocked_by for cluster in candidate_clusters):
        return "dionysus_note"
    return "local_note"


def _load_current_checkpoint_note(workspace: Workspace, repo_root: str) -> SessionCheckpointNote | None:
    for note_path in _candidate_checkpoint_note_paths(workspace, repo_root):
        if not note_path.exists():
            continue
        try:
            return SessionCheckpointNote.model_validate_json(note_path.read_text(encoding="utf-8"))
        except Exception:
            continue
    return None


def _closeout_surviving_checkpoint_clusters(
    checkpoint_note: SessionCheckpointNote | None,
) -> list[SessionCheckpointCluster]:
    if checkpoint_note is None or checkpoint_note.state not in ACTIVE_CHECKPOINT_NOTE_STATES:
        return []
    return [
        cluster
        for cluster in checkpoint_note.candidate_clusters
        if cluster.review_status in ACTIVE_CHECKPOINT_CLUSTER_STATES
    ]


def _checkpoint_note_ref(workspace: Workspace, repo_root: str, note: SessionCheckpointNote | None) -> str | None:
    if note is None:
        return None
    for note_path in _candidate_checkpoint_note_paths(
        workspace,
        repo_root,
        runtime_session_id=note.runtime_session_id,
    ):
        if note_path.exists():
            return str(note_path)
    return None


def _candidate_checkpoint_note_paths(
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
    label = _context_label(workspace, repo_root)
    resolved_runtime_session_id = runtime_session_id or _active_runtime_session_id(workspace)
    paths: list[Path] = []
    if isinstance(resolved_runtime_session_id, str) and resolved_runtime_session_id.strip():
        scope_name = _session_scope_name(resolved_runtime_session_id)
        paths.append(current_root / scope_name / label / "checkpoint-note.json")
    paths.append(current_root / label / "checkpoint-note.json")
    return paths


def _active_runtime_session_id(workspace: Workspace) -> str | None:
    try:
        return load_session(workspace, None).session_id
    except Exception:
        return None


def _session_scope_name(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip()).strip("-._") or "session"


def _context_label(workspace: Workspace, repo_root: str) -> str:
    resolved = Path(repo_root).expanduser()
    if not resolved.is_absolute():
        resolved = (workspace.root / resolved).resolve()
    else:
        resolved = resolved.resolve()
    return "workspace" if resolved == workspace.federation_root else resolved.name


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")


def _dedupe_strings(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))
