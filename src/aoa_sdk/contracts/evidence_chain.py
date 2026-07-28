"""Owner-safe unified evidence and closeout-chain contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator

from .control_plane import (
    CloseoutBundleRef,
    Digest,
    EvalVerdictRef,
    ExecutionEvent,
    MemoryReceiptRef,
    NonEmptyStr,
    ProvenanceRef,
    RouteDecision,
    RouteExplanation,
    RouteIntent,
    RunOutcome,
    RunPlan,
    SessionHandle,
    StrictControlPlaneModel,
)


EVIDENCE_CHAIN_SCHEMA_VERSION: Literal["aoa_evidence_chain_v1"] = (
    "aoa_evidence_chain_v1"
)
EVIDENCE_CHAIN_INDEX_SCHEMA_VERSION: Literal["aoa_evidence_chain_index_v1"] = (
    "aoa_evidence_chain_index_v1"
)


class CheckpointReceiptRef(StrictControlPlaneModel):
    """Owner-qualified checkpoint reference without importing checkpoint truth."""

    ref_id: NonEmptyStr
    artifact_kind: Literal["checkpoint_receipt"] = "checkpoint_receipt"
    provenance: ProvenanceRef
    review_status: Literal["provisional", "reviewed", "closed"]
    covered_step_ids: tuple[NonEmptyStr, ...] = ()
    covers_pause: bool = False
    covers_recoverable_failure: bool = False

    @model_validator(mode="after")
    def validate_coverage(self) -> CheckpointReceiptRef:
        if len(self.covered_step_ids) != len(set(self.covered_step_ids)):
            raise ValueError("checkpoint receipt step coverage must be unique")
        return self


class EvidenceChain(StrictControlPlaneModel):
    """Frozen SDK projection; external owner artifacts remain references only."""

    schema_version: Literal["aoa_evidence_chain_v1"] = EVIDENCE_CHAIN_SCHEMA_VERSION
    chain_id: NonEmptyStr
    session_id: NonEmptyStr
    correlation_id: NonEmptyStr
    disposition: Literal["partial", "complete"]
    intent: RouteIntent
    decision: RouteDecision
    explanation: RouteExplanation
    plan: RunPlan
    session: SessionHandle
    events: tuple[ExecutionEvent, ...]
    runtime_outcome: RunOutcome
    eval_verdict_refs: tuple[EvalVerdictRef, ...] = ()
    memory_receipt_refs: tuple[MemoryReceiptRef, ...] = ()
    checkpoint_receipt_refs: tuple[CheckpointReceiptRef, ...] = ()
    closeout_bundle_ref: CloseoutBundleRef | None = None
    missing_required_refs: tuple[NonEmptyStr, ...] = ()
    unresolved_optional_refs: tuple[NonEmptyStr, ...] = ()
    assembled_at: datetime
    assembled_by: ProvenanceRef
    chain_digest: Digest

    @field_validator("assembled_at")
    @classmethod
    def require_aware_assembled_at(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("assembled_at must be timezone-aware")
        return value

    @model_validator(mode="after")
    def validate_shape(self) -> EvidenceChain:
        if self.session_id != self.session.session_id:
            raise ValueError("evidence chain session id differs from its handle")
        if self.correlation_id != self.session.correlation_id:
            raise ValueError("evidence chain correlation id differs from its handle")
        if not self.events:
            raise ValueError("evidence chain must retain the verified event stream")
        if self.disposition == "complete":
            if self.missing_required_refs:
                raise ValueError("complete evidence chain cannot miss required refs")
            if self.closeout_bundle_ref is None:
                raise ValueError("complete evidence chain requires a closeout bundle")
        else:
            if not self.missing_required_refs:
                raise ValueError(
                    "partial evidence chain must name missing required refs"
                )
            if self.closeout_bundle_ref is not None:
                raise ValueError(
                    "partial evidence chain cannot carry a lifecycle closeout bundle"
                )
        for label, values in (
            (
                "eval verdict",
                [item.ref_id for item in self.eval_verdict_refs],
            ),
            (
                "memory receipt",
                [item.ref_id for item in self.memory_receipt_refs],
            ),
            (
                "checkpoint receipt",
                [item.ref_id for item in self.checkpoint_receipt_refs],
            ),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"evidence chain {label} refs must be unique")
        if self.assembled_by.owner_repo != "aoa-sdk":
            raise ValueError("evidence chain projection must be assembled by aoa-sdk")
        return self


class EvidenceChainIndexEntry(StrictControlPlaneModel):
    """One immutable repository revision reachable by exact lookup keys."""

    session_id: NonEmptyStr
    chain_id: NonEmptyStr
    chain_digest: Digest
    disposition: Literal["partial", "complete"]
    revision: Annotated[int, Field(ge=1)]
    object_ref: NonEmptyStr
    closeout_ref_id: str | None = None


class EvidenceChainIndex(StrictControlPlaneModel):
    """Serializable exact index; it contains no proof or memory payload."""

    schema_version: Literal["aoa_evidence_chain_index_v1"] = (
        EVIDENCE_CHAIN_INDEX_SCHEMA_VERSION
    )
    entries: tuple[EvidenceChainIndexEntry, ...] = ()

    @model_validator(mode="after")
    def validate_index(self) -> EvidenceChainIndex:
        revision_keys = [(item.session_id, item.revision) for item in self.entries]
        if len(revision_keys) != len(set(revision_keys)):
            raise ValueError("evidence chain index revisions must be unique")
        closeout_keys = [
            item.closeout_ref_id
            for item in self.entries
            if item.closeout_ref_id is not None
        ]
        if len(closeout_keys) != len(set(closeout_keys)):
            raise ValueError("closeout receipt ids must resolve to one chain")
        return self
