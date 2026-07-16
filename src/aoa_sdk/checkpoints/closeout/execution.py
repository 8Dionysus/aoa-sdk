"""Materialize reviewed checkpoint evidence without executing capabilities."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from ...loaders import write_json
from ...models import CheckpointCloseoutContext, SessionCheckpointCluster
from ..naming import safe_checkpoint_name as _safe_name
from ..timestamps import observed_timestamp_fields as _observed_timestamp_fields
from .contracts import (
    CHECKPOINT_CLOSEOUT_AUTHORITY_CONTRACT,
    ReviewedEvidenceBundleOutputs,
)


def _materialize_reviewed_evidence_bundle(
    *,
    context: CheckpointCloseoutContext,
    reviewed_artifact: Path,
    reviewed_artifact_evidence: dict[str, object],
    shortlisted_clusters: list[SessionCheckpointCluster],
    receipt_payloads: list[dict[str, object]],
    output_dir: Path,
) -> ReviewedEvidenceBundleOutputs:
    evidence_text = reviewed_artifact_evidence.get("text")
    evidence_refs = reviewed_artifact_evidence.get("refs")
    packet = {
        "schema_version": 2,
        "artifact_kind": "checkpoint_closeout_reviewed_evidence_bundle",
        "session_ref": context.session_ref,
        "authority_contract": CHECKPOINT_CLOSEOUT_AUTHORITY_CONTRACT,
        "capability_execution_claimed": False,
        "related_workflow_ref": context.related_workflow_ref,
        "reviewed_artifact_ref": str(reviewed_artifact),
        "reviewed_evidence_refs": (
            [ref for ref in evidence_refs if isinstance(ref, str)]
            if isinstance(evidence_refs, list)
            else [str(reviewed_artifact)]
        ),
        "reviewed_evidence_char_count": (
            len(evidence_text) if isinstance(evidence_text, str) else 0
        ),
        "runtime_session_id": context.runtime_session_id,
        "session_trace_ref": context.session_trace_ref,
        "session_trace_thread_id": context.session_trace_thread_id,
        "session_memory_ref": (
            context.session_memory_ref.model_dump(mode="json")
            if context.session_memory_ref is not None
            else None
        ),
        "session_memory_freshness": context.session_memory_freshness.model_dump(
            mode="json"
        ),
        "checkpoint_note_refs": list(context.checkpoint_note_refs),
        "surface_handoff_ref": context.surface_handoff_ref,
        "receipt_refs": list(context.receipt_refs),
        "receipt_payload_count": len(receipt_payloads),
        "candidate_map": context.candidate_map.model_dump(mode="json"),
        "checkpoint_review_carry": context.checkpoint_review_carry.model_dump(mode="json"),
        "candidate_lineage_map": [
            item.model_dump(mode="json") for item in context.candidate_lineage_map
        ],
        "owner_followthrough_map": [
            item.model_dump(mode="json") for item in context.owner_followthrough_map
        ],
        "capability_candidates": [
            item.model_dump(mode="json") for item in context.capability_candidates
        ],
        "checkpoint_candidates": [
            {
                "candidate_ref": cluster.candidate_id,
                "candidate_kind": cluster.candidate_kind,
                "owner_hint": cluster.owner_hint,
                "review_status": cluster.review_status,
                "blocked_by": list(cluster.blocked_by),
                "defer_reason": cluster.defer_reason,
                "evidence_refs": list(cluster.evidence_refs),
            }
            for cluster in shortlisted_clusters
        ],
        "stop_line": (
            "This bundle is navigation evidence. It does not execute capabilities, "
            "promote candidates, author owner artifacts, or refresh stats."
        ),
    }
    packet_path = output_dir / "CHECKPOINT_CLOSEOUT_EVIDENCE_BUNDLE.json"
    write_json(packet_path, packet)

    run_ref = f"run-{_safe_name(context.session_ref)}-checkpoint-closeout-materialization"
    receipt = {
        "schema_version": 2,
        "event_kind": "checkpoint_closeout_materialization_receipt",
        "event_id": f"evt-{_safe_name(context.session_ref)}-checkpoint-closeout",
        **_observed_timestamp_fields(),
        "run_ref": run_ref,
        "session_ref": context.session_ref,
        "actor_ref": "aoa-sdk:checkpoint-closeout-materializer",
        "object_ref": {
            "repo": "aoa-sdk",
            "kind": "adapter",
            "id": "checkpoint-closeout-materializer",
        },
        "evidence_refs": [
            {"kind": "reviewed_evidence_bundle", "ref": str(packet_path), "role": "primary"},
            {
                "kind": "reviewed_artifact",
                "ref": str(reviewed_artifact),
                "role": "reviewed-source",
            },
            *(
                [
                    {
                        "kind": "session_trace",
                        "ref": context.session_trace_ref,
                        "role": "runtime-trace",
                    }
                ]
                if context.session_trace_ref is not None
                else []
            ),
        ],
        "payload": {
            "authority_contract": CHECKPOINT_CLOSEOUT_AUTHORITY_CONTRACT,
            "capability_execution_claimed": False,
            "related_workflow_ref": context.related_workflow_ref,
            "candidate_count": len(shortlisted_clusters),
            "capability_candidate_refs": [
                target.target_ref for target in context.capability_candidates
            ],
            "owner_review_required": bool(shortlisted_clusters),
        },
    }
    receipt_path = output_dir / "CHECKPOINT_CLOSEOUT_MATERIALIZATION_RECEIPT.json"
    write_json(receipt_path, receipt)
    return {
        "packet": cast(dict[str, object], packet),
        "artifact_refs": [str(packet_path)],
        "receipt_refs": [str(receipt_path)],
    }
