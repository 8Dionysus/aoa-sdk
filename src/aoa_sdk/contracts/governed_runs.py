from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from .evals import EvalRuntimeCandidateIntake
from .memo import MemoWritebackIntakeTarget
from .playbooks import PlaybookReviewIntake


class GovernedRunReviewPacketManifest(BaseModel):
    artifact_kind: str
    schema_version: str
    run_id: str
    generated_at: str
    selected_playbook: dict[str, Any] | None = None
    matched_playbook_packet_contract: dict[str, Any] | None = None
    matched_eval_template_entries: list[dict[str, Any]] = Field(default_factory=list)
    matched_memo_writeback_targets: list[dict[str, Any]] = Field(default_factory=list)
    advisory_trace_ref: str | None = None
    emitted_candidate_artifact_refs: list[dict[str, Any]] = Field(default_factory=list)
    skipped_packet_kinds: list[dict[str, Any]] = Field(default_factory=list)


class GovernedRunPacketStatus(BaseModel):
    packet_kind: str
    status: Literal["emitted", "skipped", "missing", "stale"]
    artifact_refs: list[str] = Field(default_factory=list)
    reason: str | None = None


class GovernedRunReviewPacketAudit(BaseModel):
    schema_version: int
    run_id: str
    playbook_id: str
    audit_verdict: Literal["ready", "partial", "blocked"]
    review_packet_manifest_ref: str
    advisory_trace_ref: str | None = None
    packet_statuses: list[GovernedRunPacketStatus] = Field(default_factory=list)
    contract_refs: list[str] = Field(default_factory=list)
    recommended_review_targets: list[dict[str, str]] = Field(default_factory=list)
    replayable: bool
    safe_replay_command: str | None = None


class GovernedRunReviewHandoffBundle(BaseModel):
    schema_version: int
    run_id: str
    playbook_id: str
    audit_verdict: Literal["ready", "partial", "blocked"]
    replayable: bool
    playbook_intake: PlaybookReviewIntake | None = None
    eval_intake_entries: list[EvalRuntimeCandidateIntake] = Field(default_factory=list)
    memo_intake_entries: list[MemoWritebackIntakeTarget] = Field(default_factory=list)
    emitted_candidate_artifact_refs: list[dict[str, Any]] = Field(default_factory=list)
    recommended_review_targets: dict[str, list[dict[str, str]]] = Field(default_factory=dict)
    missing_or_blocked_packet_kinds: list[dict[str, Any]] = Field(default_factory=list)
    operator_next_steps: list[str] = Field(default_factory=list)
