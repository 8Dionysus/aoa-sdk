from __future__ import annotations

from .models import (
    EvidenceRef,
    MemoExportPlan,
    RemoteTaskResult,
    ReturnPlan,
    ReviewedExportCandidate,
    StressBundle,
)
from .utils import unique_preserve_order


def _base_evidence(
    remote_task: RemoteTaskResult, reviewed_artifact_path: str | None
) -> list[EvidenceRef]:
    evidence = [
        EvidenceRef(
            kind="remote_task", ref=f"a2a:task:{remote_task.task_id}", role="child_task"
        )
    ]
    if reviewed_artifact_path:
        evidence.append(
            EvidenceRef(
                kind="reviewed_artifact", ref=reviewed_artifact_path, role="closeout"
            )
        )
    for ref in remote_task.artifact_refs:
        evidence.append(
            EvidenceRef(kind="remote_artifact", ref=ref, role="returned_artifact")
        )
    return unique_preserve_order(evidence)


def build_memo_export_plan(
    remote_task: RemoteTaskResult,
    *,
    reviewed_artifact_path: str | None = None,
    stress_bundle: StressBundle | None = None,
    return_plan: ReturnPlan | None = None,
    checkpoint_note_ref: str | None = None,
    recovery_window: bool = False,
) -> MemoExportPlan:
    evidence = _base_evidence(remote_task, reviewed_artifact_path)
    writeback: list[ReviewedExportCandidate] = []
    candidates: list[ReviewedExportCandidate] = []
    adjuncts: list[ReviewedExportCandidate] = []

    for artifact in remote_task.returned_artifacts:
        if artifact in {"bounded_plan", "inquiry_checkpoint"}:
            writeback.append(
                ReviewedExportCandidate(
                    kind="state_capsule",
                    review_status="reviewed_candidate",
                    summary="Remote child returned bounded working state that may become a state capsule after review.",
                    evidence_refs=evidence,
                    metadata={"source_artifact": artifact},
                )
            )
        elif artifact in {"route_decision", "transition_decision"}:
            writeback.append(
                ReviewedExportCandidate(
                    kind="decision",
                    review_status="reviewed_candidate",
                    summary="Remote child returned a route or transition decision that may survive recall after review.",
                    evidence_refs=evidence,
                    metadata={"source_artifact": artifact},
                )
            )
        elif artifact == "work_result":
            writeback.append(
                ReviewedExportCandidate(
                    kind="episode",
                    review_status="reviewed_candidate",
                    summary="Remote child returned bounded execution output that may be retained as an episode.",
                    evidence_refs=evidence,
                    metadata={"source_artifact": artifact},
                )
            )
        elif artifact == "verification_result":
            writeback.append(
                ReviewedExportCandidate(
                    kind="audit_event",
                    review_status="reviewed_candidate",
                    summary="Remote verification may be retained as a review-facing audit event.",
                    evidence_refs=evidence,
                    metadata={"source_artifact": artifact},
                )
            )
        elif artifact == "deep_synthesis_note":
            candidates.append(
                ReviewedExportCandidate(
                    kind="claim",
                    review_status="reviewed_candidate",
                    summary="Deep synthesis may yield a claim candidate after provenance and review checks.",
                    evidence_refs=evidence,
                    metadata={"source_artifact": artifact},
                )
            )
        elif artifact == "distillation_pack":
            for candidate_kind in ("claim", "pattern", "bridge"):
                candidates.append(
                    ReviewedExportCandidate(
                        kind=candidate_kind,
                        review_status="reviewed_candidate",
                        summary=f"Distillation produced a {candidate_kind} candidate that still needs memo-side review.",
                        evidence_refs=evidence,
                        metadata={"source_artifact": artifact},
                    )
                )

    if return_plan is not None:
        writeback.append(
            ReviewedExportCandidate(
                kind="decision",
                review_status="reviewed_candidate",
                summary="The child route returned through a governed transition decision.",
                evidence_refs=evidence,
                metadata={
                    "decision": "return",
                    "anchor_artifact": return_plan.anchor_artifact,
                    "reentry_mode": return_plan.reentry_mode,
                },
            )
        )
        candidates.append(
            ReviewedExportCandidate(
                kind="anchor",
                review_status="reviewed_candidate",
                summary="The return anchor may survive as a stable memo-side anchor after review.",
                evidence_refs=evidence,
                metadata={"anchor_artifact": return_plan.anchor_artifact},
            )
        )

    if checkpoint_note_ref:
        writeback.append(
            ReviewedExportCandidate(
                kind="state_capsule",
                review_status="reviewed_candidate",
                summary="Checkpoint-shaped working state may survive as a state capsule after review.",
                evidence_refs=evidence,
                metadata={"checkpoint_note_ref": checkpoint_note_ref},
            )
        )

    if stress_bundle and stress_bundle.selected_posture in {
        "reground_first",
        "human_review_first",
        "stop_before_mutation",
    }:
        adjuncts.append(
            ReviewedExportCandidate(
                kind="failure_lesson_memory_v1",
                review_status="draft",
                summary="Reviewed stress context suggests a portable failure-lesson memory candidate.",
                evidence_refs=unique_preserve_order(
                    evidence + stress_bundle.evidence_refs
                ),
                metadata={
                    "selected_posture": stress_bundle.selected_posture,
                    "dominant_source_family": stress_bundle.dominant_source_family,
                },
            )
        )

    if recovery_window:
        adjuncts.append(
            ReviewedExportCandidate(
                kind="recovery_pattern_memory_v1",
                review_status="draft",
                summary="Ordered reviewed recovery context suggests a portable recovery-pattern memory candidate.",
                evidence_refs=unique_preserve_order(
                    evidence + (stress_bundle.evidence_refs if stress_bundle else [])
                ),
                metadata={"recovery_window": True},
            )
        )

    return MemoExportPlan(
        writeback_targets=unique_preserve_order(writeback),
        candidate_targets=unique_preserve_order(candidates),
        adjunct_targets=unique_preserve_order(adjuncts),
        contains_raw_trace=False,
    )
