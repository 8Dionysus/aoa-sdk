from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class KernelNextStepBrief(BaseModel):
    kernel_id: str
    current_session_skill_names: list[str] = Field(default_factory=list)
    current_session_detail_event_kinds: list[str] = Field(default_factory=list)
    missing_kernel_skill_names: list[str] = Field(default_factory=list)
    kernel_usage_counts: dict[str, int] = Field(default_factory=dict)
    suggested_action: Literal["invoke-core-skill", "shift-to-owner-layer", "hold"]
    suggested_skill_name: str | None = None
    suggested_owner_repo: str | None = None
    reason: str
    stats_surface_ref: str


class OwnerFollowThroughBrief(BaseModel):
    source_kind: Literal["harvest-candidate", "quest-promotion"]
    unit_ref: str
    unit_name: str | None = None
    owner_repo: str
    next_surface: str
    suggested_action: Literal["draft-owner-artifact", "author-owner-artifact"]
    abstraction_shape: str | None = None
    promotion_verdict: str | None = None
    nearest_wrong_target: str | None = None
    reason: str
    evidence_refs: list[str] = Field(default_factory=list)


class WorkflowFollowThroughBrief(BaseModel):
    source_kind: Literal["kernel-next-step", "progression-caution", "diagnosis-gap"]
    skill_name: str
    suggested_action: Literal["invoke-core-skill"]
    phase: Literal["post-closeout"] = "post-closeout"
    reason: str
    evidence_refs: list[str] = Field(default_factory=list)


class CloseoutOwnerHandoff(BaseModel):
    schema_version: int
    closeout_id: str
    session_ref: str
    manifest_path: str
    generated_at: datetime
    items: list[OwnerFollowThroughBrief] = Field(default_factory=list)
    workflow_items: list[WorkflowFollowThroughBrief] = Field(default_factory=list)


class CloseoutPublisherBatch(BaseModel):
    publisher: str
    input_paths: list[str] = Field(default_factory=list)


class CloseoutManifest(BaseModel):
    schema_version: int
    closeout_id: str
    session_ref: str
    reviewed: bool
    audit_only: bool = False
    trigger: str
    batches: list[CloseoutPublisherBatch] = Field(default_factory=list)
    audit_refs: list[str] = Field(default_factory=list)
    notes: str | None = None


class CloseoutBuildRequest(BaseModel):
    schema_version: int
    closeout_id: str
    session_ref: str
    reviewed: bool
    audit_only: bool = False
    reviewed_artifact_path: str
    trigger: str
    batches: list[CloseoutPublisherBatch] = Field(default_factory=list)
    audit_refs: list[str] = Field(default_factory=list)
    notes: str | None = None


class CloseoutBuildReport(BaseModel):
    schema_version: int
    closeout_id: str
    session_ref: str
    request_path: str
    manifest_path: str
    built_at: datetime
    reviewed_artifact_path: str
    audit_only: bool = False
    enqueue_report: CloseoutEnqueueReport | None = None


class CloseoutSubmitReviewedReport(BaseModel):
    schema_version: int
    closeout_id: str
    session_ref: str
    request_path: str
    submitted_at: datetime
    reviewed_artifact_path: str
    audit_only: bool = False
    receipt_paths: list[str] = Field(default_factory=list)
    detected_publishers: list[str] = Field(default_factory=list)
    build_report: CloseoutBuildReport


class CloseoutEnqueueReport(BaseModel):
    schema_version: int
    closeout_id: str
    session_ref: str
    source_manifest_path: str
    queued_manifest_path: str
    enqueued_at: datetime
    queue_depth: int
    overwritten: bool = False


class CloseoutPublisherRun(BaseModel):
    publisher: str
    repo: str
    input_paths: list[str] = Field(default_factory=list)
    log_path: str
    command: list[str] = Field(default_factory=list)
    appended_count: int | None = None
    duplicate_skip_count: int | None = None
    stdout: str = ""


class CloseoutStatsRefresh(BaseModel):
    command: list[str] = Field(default_factory=list)
    source_count: int | None = None
    receipt_count: int | None = None
    cleared: bool = False
    feed_output: str | None = None
    summary_output_dir: str | None = None
    stdout: str = ""


class CloseoutRunReport(BaseModel):
    schema_version: int
    closeout_id: str
    session_ref: str
    manifest_path: str
    processed_at: datetime
    trigger: str
    reviewed: bool
    audit_only: bool = False
    audit_refs: list[str] = Field(default_factory=list)
    notes: str | None = None
    publisher_runs: list[CloseoutPublisherRun] = Field(default_factory=list)
    stats_refresh: CloseoutStatsRefresh
    kernel_next_step_brief: KernelNextStepBrief | None = None
    owner_handoff_path: str | None = None
    owner_follow_through_briefs: list[OwnerFollowThroughBrief] = Field(default_factory=list)
    workflow_follow_through_briefs: list[WorkflowFollowThroughBrief] = Field(default_factory=list)


class CloseoutInboxItemResult(BaseModel):
    manifest_path: str
    archived_manifest_path: str | None = None
    report_path: str | None = None
    status: Literal["processed", "failed"]
    closeout_id: str | None = None
    session_ref: str | None = None
    error: str | None = None
    kernel_next_step_brief: KernelNextStepBrief | None = None
    owner_handoff_path: str | None = None
    owner_follow_through_briefs: list[OwnerFollowThroughBrief] = Field(default_factory=list)
    workflow_follow_through_briefs: list[WorkflowFollowThroughBrief] = Field(default_factory=list)


class CloseoutInboxReport(BaseModel):
    schema_version: int
    inbox_dir: str
    processed_dir: str
    failed_dir: str
    report_dir: str
    processed_count: int
    failed_count: int
    items: list[CloseoutInboxItemResult] = Field(default_factory=list)


class CloseoutStatusReport(BaseModel):
    schema_version: int
    root_dir: str
    request_dir: str
    manifest_dir: str
    inbox_dir: str
    processed_dir: str
    failed_dir: str
    report_dir: str
    handoff_dir: str
    request_count: int
    manifest_count: int
    pending_manifest_count: int
    processed_manifest_count: int
    failed_manifest_count: int
    report_count: int
    handoff_count: int
    pending_manifest_paths: list[str] = Field(default_factory=list)
    latest_request_path: str | None = None
    latest_manifest_path: str | None = None
    latest_report_path: str | None = None
    latest_handoff_path: str | None = None
    latest_processed_manifest_path: str | None = None
    latest_failed_manifest_path: str | None = None
