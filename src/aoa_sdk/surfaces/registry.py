from __future__ import annotations

from pathlib import Path

from ..models import (
    SurfaceCloseoutHandoff,
    SurfaceDetectionReport,
)
from ..checkpoints.candidate_intelligence import build_candidate_intelligence_from_surface
from ..skills.detector import detect_skills
from ..workspace.discovery import Workspace
from .checkpoint_candidates import (
    checkpoint_blocked_by,
    checkpoint_promotion_recommendation,
    dedupe_checkpoint_candidate_clusters,
    derive_checkpoint_candidate_clusters,
    derive_explicit_mutation_growth_clusters,
)
from .closeout_handoff import (
    build_surface_closeout_handoff,
    derive_closeout_followups,
    owner_layer_notes,
)
from .common import (
    MUTATION_SURFACES,
    SURFACE_PHASES,
    CheckpointKind,
    MutationSurface,
    SurfacePhase,
)
from .context import (
    enrich_surface_items,
    load_active_skill_names,
    load_core_skill_receipt_contexts,
    load_shortlist_hints,
    load_stats_regrounding_hints,
    regrounding_reason_codes,
)
from .items import derive_surface_items


class SurfacesAPI:
    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace

    def detect(
        self,
        *,
        repo_root: str,
        phase: SurfacePhase,
        intent_text: str = "",
        mutation_surface: MutationSurface = "none",
        session_file: str | None = None,
        closeout_path: str | None = None,
        skill_report_path: str | None = None,
        include_shortlist: bool = True,
        checkpoint_kind: CheckpointKind | None = None,
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
        active_skill_names = load_active_skill_names(self.workspace, session_file=session_file)
        shortlist_hints = load_shortlist_hints(self.workspace) if include_shortlist else []
        skill_receipt_contexts = load_core_skill_receipt_contexts(self.workspace)
        regrounding_hints = load_stats_regrounding_hints(
            self.workspace,
            intent_text=intent_text,
            phase=phase,
            mutation_surface=mutation_surface,
        )
        items = enrich_surface_items(
            derive_surface_items(
                skill_report=skill_report,
                surface_phase=phase,
                intent_text=intent_text,
                active_skill_names=active_skill_names,
                closeout_signal=phase == "closeout" or skill_report.closeout_chain is not None,
            ),
            shortlist_hints=shortlist_hints,
            skill_receipt_contexts=skill_receipt_contexts,
        )
        candidate_clusters = (
            derive_checkpoint_candidate_clusters(
                items=items,
                checkpoint_kind=checkpoint_kind,
            )
            if phase == "checkpoint"
            else []
        )
        if phase == "checkpoint":
            candidate_clusters = dedupe_checkpoint_candidate_clusters(
                [
                    *candidate_clusters,
                    *derive_explicit_mutation_growth_clusters(
                        workspace=self.workspace,
                        repo_root=repo_root,
                        mutation_surface=mutation_surface,
                        intent_text=intent_text,
                        checkpoint_kind=checkpoint_kind,
                        skill_report=skill_report,
                    ),
                ]
            )
        candidate_intelligence = (
            build_candidate_intelligence_from_surface(
                workspace=self.workspace,
                repo_root=repo_root,
                intent_text=intent_text,
                checkpoint_kind=checkpoint_kind,
                mutation_surface=mutation_surface,
                items=items,
                candidate_clusters=candidate_clusters,
                actionability_gaps=list(skill_report.actionability_gaps),
            )
            if phase == "checkpoint"
            else None
        )
        if candidate_intelligence is not None:
            refs_by_candidate: dict[str, list[str]] = {}
            for event in candidate_intelligence.action_events:
                if event.action_signature_ref is None:
                    continue
                for candidate_id in event.candidate_ids:
                    refs_by_candidate.setdefault(candidate_id, []).append(event.action_signature_ref)
            candidate_clusters = [
                cluster.model_copy(
                    update={
                        "action_signature_refs": sorted(
                            set(refs_by_candidate.get(cluster.candidate_id, []))
                        )
                    }
                )
                for cluster in candidate_clusters
            ]
        blocked_by = checkpoint_blocked_by(candidate_clusters) if phase == "checkpoint" else []
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
            regrounding_hints=regrounding_hints,
            regrounding_required=any(
                hint.decision == "reground_required" for hint in regrounding_hints
            ),
            regrounding_reason_codes=regrounding_reason_codes(regrounding_hints),
            checkpoint_should_capture=checkpoint_should_capture,
            candidate_clusters=candidate_clusters,
            action_events=(
                list(candidate_intelligence.action_events)
                if candidate_intelligence is not None
                else []
            ),
            action_signatures=(
                list(candidate_intelligence.action_signatures)
                if candidate_intelligence is not None
                else []
            ),
            wrapper_gap_candidates=(
                list(candidate_intelligence.wrapper_gap_candidates)
                if candidate_intelligence is not None
                else []
            ),
            promotion_recommendation=(
                checkpoint_promotion_recommendation(
                    candidate_clusters=candidate_clusters,
                    checkpoint_kind=checkpoint_kind,
                )
                if phase == "checkpoint"
                else "none"
            ),
            blocked_by=blocked_by,
            closeout_followups=derive_closeout_followups(items=items, surface_phase=phase),
            owner_layer_notes=owner_layer_notes(items=items),
            actionability_gaps=list(skill_report.actionability_gaps),
        )

    def build_closeout_handoff(
        self,
        report_or_path: SurfaceDetectionReport | str | Path,
        *,
        session_ref: str,
        reviewed: bool = True,
    ) -> SurfaceCloseoutHandoff:
        return build_surface_closeout_handoff(
            self.workspace,
            report_or_path,
            session_ref=session_ref,
            reviewed=reviewed,
        )
