from __future__ import annotations

from pathlib import Path

from ..models import (
    SurfaceCloseoutHandoff,
    SurfaceDetectionReport,
)
from ..checkpoints.candidate_intelligence import build_candidate_intelligence_from_surface
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
    load_shortlist_hints,
    load_stats_regrounding_hints,
    partition_current_shortlist_hints,
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
        closeout_path: str | None = None,
        include_shortlist: bool = True,
        checkpoint_kind: CheckpointKind | None = None,
    ) -> SurfaceDetectionReport:
        if phase not in SURFACE_PHASES:
            raise ValueError(f"unsupported phase {phase!r}")
        if mutation_surface not in MUTATION_SURFACES:
            raise ValueError(f"unsupported mutation_surface {mutation_surface!r}")

        all_shortlist_hints = (
            load_shortlist_hints(self.workspace) if include_shortlist else []
        )
        shortlist_hints, inspection_gaps = partition_current_shortlist_hints(
            all_shortlist_hints
        )
        regrounding_hints = load_stats_regrounding_hints(
            self.workspace,
            intent_text=intent_text,
            phase=phase,
            mutation_surface=mutation_surface,
        )
        items = enrich_surface_items(
            derive_surface_items(
                surface_phase=phase,
                intent_text=intent_text,
                closeout_signal=phase == "closeout" or closeout_path is not None,
            ),
            shortlist_hints=shortlist_hints,
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
                        source_refs=[item.surface_ref for item in items],
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
                inspection_gaps=inspection_gaps,
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
            repo_root=str(_resolve_repo_root(self.workspace, repo_root)),
            workspace_root=str(self.workspace.federation_root),
            phase=phase,
            intent_text=intent_text,
            mutation_surface=mutation_surface,
            checkpoint_kind=checkpoint_kind,
            source_inputs=[
                *(["aoa-routing.owner_layer_shortlist.min"] if all_shortlist_hints else []),
                *(["aoa-stats.regrounding-signals"] if regrounding_hints else []),
            ],
            shortlist_included=bool(shortlist_hints),
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
            inspection_gaps=inspection_gaps,
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


def _resolve_repo_root(workspace: Workspace, repo_root: str) -> Path:
    candidate = Path(repo_root).expanduser()
    if candidate.is_absolute():
        return candidate.resolve(strict=False)
    if repo_root in workspace.repo_roots:
        return workspace.repo_path(repo_root)
    return (workspace.root / candidate).resolve(strict=False)
