from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

from ..errors import SurfaceNotFound
from ..loaders import load_json
from ..models import (
    SkillDetectionReport,
    SurfaceCloseoutHandoff,
    SurfaceCloseoutHandoffTarget,
    SurfaceDetectionReport,
    SurfaceOpportunityExecutionHint,
    SurfaceOpportunityItem,
)
from ..skills.detector import detect_skills
from ..skills.session import load_session
from ..workspace.discovery import Workspace
from .heuristics import EXPLICIT_LAYER_RULES_BY_TOKEN, HEURISTIC_RULES


TOKEN_RE = re.compile(r"[a-z0-9_-]+")
SURFACE_PHASES = {"ingress", "in-flight", "pre-mutation", "closeout"}
MUTATION_SURFACES = {"none", "code", "repo-config", "infra", "runtime", "public-share"}
STATE_RANK = {
    "activated": 4,
    "manual-equivalent": 3,
    "candidate-now": 2,
    "candidate-later": 1,
}
CONFIDENCE_RANK = {"high": 3, "medium": 2, "low": 1}
SIGNAL_ORDER = [
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


class SurfacesAPI:
    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace

    def detect(
        self,
        *,
        repo_root: str,
        phase: Literal["ingress", "in-flight", "pre-mutation", "closeout"],
        intent_text: str = "",
        mutation_surface: Literal["none", "code", "repo-config", "infra", "runtime", "public-share"] = "none",
        session_file: str | None = None,
        closeout_path: str | None = None,
        skill_report_path: str | None = None,
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
        items = _derive_surface_items(
            skill_report=skill_report,
            surface_phase=phase,
            intent_text=intent_text,
            active_skill_names=active_skill_names,
            closeout_signal=phase == "closeout" or skill_report.closeout_chain is not None,
        )
        return SurfaceDetectionReport(
            repo_root=skill_report.repo_root,
            workspace_root=str(self.workspace.federation_root),
            phase=phase,
            intent_text=intent_text,
            mutation_surface=mutation_surface,
            skill_report_path=skill_report_path,
            skill_report_included=True,
            active_skill_names=active_skill_names,
            immediate_skill_dispatch=[item.skill_name for item in skill_report.activate_now],
            items=items,
            closeout_followups=_derive_closeout_followups(items=items),
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
        return SurfaceCloseoutHandoff(
            session_ref=session_ref,
            reviewed=reviewed,
            surface_detection_report_ref=report_ref,
            surviving_items=surviving_items,
            handoff_targets=_derive_closeout_handoff_targets(
                surviving_items=surviving_items,
                actionability_gaps=report.actionability_gaps,
            ),
            notes=[
                "use the session-growth kernel only after reviewed run, closure, or pause",
                "do not let donor-harvest or automation scan become hidden live routing authority",
            ],
        )


def _load_surface_report(report_or_path: SurfaceDetectionReport | str | Path) -> tuple[SurfaceDetectionReport, str]:
    if isinstance(report_or_path, SurfaceDetectionReport):
        return report_or_path, "in-memory:surface-detection-report"

    payload = load_json(Path(report_or_path).expanduser().resolve())
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
    surface_phase: Literal["ingress", "in-flight", "pre-mutation", "closeout"],
    intent_text: str,
    active_skill_names: list[str],
    closeout_signal: bool,
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
    return _dedupe_surface_items(items)


def _derive_skill_surface_items(
    *,
    skill_report: SkillDetectionReport,
    surface_phase: Literal["ingress", "in-flight", "pre-mutation", "closeout"],
    closeout_signal: bool,
) -> list[SurfaceOpportunityItem]:
    items: list[SurfaceOpportunityItem] = []
    for item in skill_report.activate_now:
        signals = ["router-match", *(("closeout-chain",) if closeout_signal else ())]
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
            )
        )

    fallback_items = [*skill_report.must_confirm, *skill_report.suggest_next]
    for item in fallback_items:
        if item.host_availability.status != "router-only" or not item.host_availability.manual_fallback_allowed:
            continue
        signals = ["router-match"]
        if item in skill_report.must_confirm:
            signals.append("risk-gate")
        if closeout_signal:
            signals.append("closeout-chain")
        items.append(
            SurfaceOpportunityItem(
                surface_ref=f"aoa-skills:{item.skill_name}",
                display_name=_display_name(item.skill_name),
                object_kind="skill",
                owner_repo="aoa-skills",
                state="manual-equivalent",
                phase_detected=surface_phase,
                reason=item.reason,
                signals=_ordered_signals(signals),
                confidence="high" if item in skill_report.must_confirm else "medium",
                execution=SurfaceOpportunityExecutionHint(
                    lane="manual-fallback",
                    executable_now=False,
                    requires_confirmation=item in skill_report.must_confirm,
                    existing_command="aoa skills guard" if surface_phase == "pre-mutation" else "aoa skills detect",
                    existing_surface=None,
                    manual_fallback_allowed=True,
                    manual_fallback_note="keep the distinction visible: the same discipline was followed manually, not claimed as a real activation",
                    host_availability_status=item.host_availability.status,
                ),
                related_skill_names=_related_skill_names(skill_report, item.skill_name),
                closeout_family_candidates=["aoa-session-donor-harvest"],
                promotion_hint=None,
            )
        )

    return items


def _derive_heuristic_items(
    *,
    intent_text: str,
    surface_phase: Literal["ingress", "in-flight", "pre-mutation", "closeout"],
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
        items.append(
            SurfaceOpportunityItem(
                surface_ref=rule.surface_ref,
                display_name=rule.display_name,
                object_kind=rule.object_kind,
                owner_repo=rule.owner_repo,
                state=rule.default_state,
                phase_detected=surface_phase,
                reason=rule.reason_template,
                signals=_ordered_signals([rule.signal, *(("closeout-chain",) if closeout_signal else ())]),
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
            )
        )

    for token in tokens:
        explicit_rule = EXPLICIT_LAYER_RULES_BY_TOKEN.get(token)
        if explicit_rule is None:
            continue
        items.append(
            SurfaceOpportunityItem(
                surface_ref=explicit_rule.surface_ref,
                display_name=explicit_rule.display_name,
                object_kind=explicit_rule.object_kind,
                owner_repo=explicit_rule.owner_repo,
                state="candidate-now",
                phase_detected=surface_phase,
                reason=f"intent names the {explicit_rule.owner_repo} layer directly; prefer owner-layer-aware routing over silent guessing",
                signals=_ordered_signals(["explicit-request", *(("closeout-chain",) if closeout_signal else ())]),
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
            )
        )

    return items


def _repeated_pattern_detected(
    *,
    tokens: set[str],
    active_skill_names: list[str],
    phase: Literal["ingress", "in-flight", "pre-mutation", "closeout"],
) -> bool:
    repeated_tokens = {"repeat", "repeated", "again", "pattern", "recurring"}
    return bool(tokens.intersection(repeated_tokens)) and (phase == "closeout" or bool(active_skill_names))


def _derive_closeout_followups(*, items: list[SurfaceOpportunityItem]) -> list[str]:
    followups: list[str] = []
    if items:
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
    if any(item.state == "manual-equivalent" for item in items):
        notes.append("manual-equivalent remains distinct from activated all the way through reporting and closeout")
    return notes


def _derive_closeout_handoff_targets(
    *,
    surviving_items: list[SurfaceOpportunityItem],
    actionability_gaps: list[str],
) -> list[SurfaceCloseoutHandoffTarget]:
    targets: list[SurfaceCloseoutHandoffTarget] = []
    if surviving_items:
        targets.append(
            SurfaceCloseoutHandoffTarget(
                skill_name="aoa-session-donor-harvest",
                why="bundle the surviving bounded notes into a reviewable harvest packet instead of leaving them as session residue",
                triggered_by=[item.surface_ref for item in surviving_items],
            )
        )
    playbook_items = [item for item in surviving_items if item.object_kind == "playbook"]
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
        }
    )


def _ordered_signals(signals: list[str]) -> list[str]:
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
