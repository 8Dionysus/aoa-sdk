from __future__ import annotations

import json
from pathlib import Path

from ..models import (
    ProgressionAxisSignal,
    SessionCheckpointCluster,
    SessionCheckpointNote,
    SurfaceCloseoutHandoff,
    SurfaceCloseoutHandoffTarget,
    SurfaceDetectionReport,
    SurfaceOpportunityItem,
)
from ..workspace.discovery import Workspace
from .checkpoint_candidates import checkpoint_note_ref, load_current_checkpoint_note
from .common import SurfacePhase


ACTIVE_CHECKPOINT_NOTE_STATES = {"collecting", "reviewable"}
ACTIVE_CHECKPOINT_CLUSTER_STATES = {"collecting", "reviewable"}


def build_surface_closeout_handoff(
    workspace: Workspace,
    report_or_path: SurfaceDetectionReport | str | Path,
    *,
    session_ref: str,
    reviewed: bool = True,
) -> SurfaceCloseoutHandoff:
    if not reviewed:
        raise ValueError("surface closeout handoff requires reviewed=True")

    report, report_ref = load_surface_report(report_or_path)
    surviving_items = [item for item in report.items if item.state != "activated"]
    checkpoint_note = load_current_checkpoint_note(workspace, report.repo_root)
    surviving_checkpoint_clusters = closeout_surviving_checkpoint_clusters(checkpoint_note)
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
        checkpoint_note_ref=checkpoint_note_ref(workspace, report.repo_root, checkpoint_note),
        surviving_items=surviving_items,
        surviving_checkpoint_clusters=surviving_checkpoint_clusters,
        checkpoint_harvest_candidates=checkpoint_harvest_candidates,
        checkpoint_progression_candidates=checkpoint_progression_candidates,
        checkpoint_upgrade_candidates=checkpoint_upgrade_candidates,
        checkpoint_progression_axes=checkpoint_progression_axes,
        stats_refresh_recommended=stats_refresh_recommended,
        handoff_targets=derive_closeout_handoff_targets(
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


def load_surface_report(report_or_path: SurfaceDetectionReport | str | Path) -> tuple[SurfaceDetectionReport, str]:
    if isinstance(report_or_path, SurfaceDetectionReport):
        return report_or_path, "in-memory:surface-detection-report"

    payload = json.loads(Path(report_or_path).expanduser().resolve().read_text(encoding="utf-8"))
    report_payload = payload.get("report", payload)
    return SurfaceDetectionReport.model_validate(report_payload), str(Path(report_or_path).expanduser().resolve())


def closeout_surviving_checkpoint_clusters(
    checkpoint_note: SessionCheckpointNote | None,
) -> list[SessionCheckpointCluster]:
    if checkpoint_note is None or checkpoint_note.state not in ACTIVE_CHECKPOINT_NOTE_STATES:
        return []
    return [
        cluster
        for cluster in checkpoint_note.candidate_clusters
        if cluster.review_status in ACTIVE_CHECKPOINT_CLUSTER_STATES
    ]


def derive_closeout_followups(
    *,
    items: list[SurfaceOpportunityItem],
    surface_phase: SurfacePhase,
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


def owner_layer_notes(*, items: list[SurfaceOpportunityItem]) -> list[str]:
    notes = [
        "aoa-sdk stays on the control plane; it may detect and hand off but does not become the source of truth for eval, memo, playbook, technique, or agent meaning",
        "playbook, eval, memo, agent, and technique items remain hints, candidates, or closeout handoffs in the initial boundary; they are not auto-activatable runtime objects here",
    ]
    if any(item.shortlist_hints for item in items):
        notes.append("routing shortlist hints stay advisory only; they can sharpen inspection and ambiguity reporting but never overwrite activation truth")
    if any(item.state == "manual-equivalent" for item in items):
        notes.append("manual-equivalent remains distinct from activated all the way through reporting and closeout")
    return notes


def derive_closeout_handoff_targets(
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
