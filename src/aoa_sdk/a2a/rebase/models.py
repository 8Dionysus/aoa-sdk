from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


Difficulty = Literal[
    "d0_probe",
    "d1_patch",
    "d2_slice",
    "d3_seam",
    "d4_architecture",
    "d5_doctrine",
]
Risk = Literal["r0_readonly", "r1_repo_local", "r2_contract", "r3_side_effect"]
ControlMode = Literal[
    "codex_supervised", "human_gate", "human_codex_copilot", "blocked"
]
CohortPattern = Literal[
    "solo", "pair", "checkpoint_cohort", "orchestrated_loop", "alpha_curated"
]
StressPosture = Literal[
    "reground_first",
    "degrade_preferred",
    "human_review_first",
    "stop_before_mutation",
    "route_around_unhealthy_surface",
]
SignalSourceFamily = Literal[
    "owner_receipt", "runtime_receipt", "eval", "stats", "route_hint", "memo"
]
Severity = Literal["low", "medium", "high", "critical"]
TransportPreference = Literal["codex_local", "a2a_remote", "either"]
ExecutionSurface = Literal["codex_local", "a2a_remote", "human_gate", "split"]
ReturnReentryMode = Literal[
    "same_phase",
    "previous_phase",
    "router_reentry",
    "checkpoint_relaunch",
    "review_gate",
    "rollback_gate",
    "safe_stop",
]
MemoryScope = Literal["thread", "session", "repo", "project", "workspace", "ecosystem"]
RankLabel = Literal["initiate", "adept", "specialist", "veteran", "master"]


CANONICAL_RUNTIME_EVENT_KINDS = {"runtime_return_closeout_receipt"}


@dataclass(slots=True)
class EvidenceRef:
    kind: str
    ref: str
    role: str | None = None


@dataclass(slots=True)
class QuestPassport:
    difficulty: Difficulty
    risk: Risk
    control_mode: ControlMode
    delegate_tier: str
    secondary_tier: str | None = None
    wrapper_class: str | None = None
    route_anchor: str | None = None
    expected_artifacts: list[str] = field(default_factory=list)
    self_agent: bool = False


@dataclass(slots=True)
class SummonIntent:
    desired_role: str | None = None
    child_agent_id: str | None = None
    capability_refs: list[str] = field(default_factory=list)
    expected_outputs: list[str] = field(default_factory=list)
    parent_task_id: str | None = None
    session_ref: str | None = None
    reviewed_artifact_path: str | None = None
    audit_refs: list[str] = field(default_factory=list)
    playbook_ref: str | None = None
    review_required: bool = True
    transport_preference: TransportPreference = "codex_local"
    require_progression: bool = False
    workspace_root: str = "/srv/AbyssOS"


@dataclass(slots=True)
class StressSignal:
    source_family: SignalSourceFamily
    posture: StressPosture
    severity: Severity = "medium"
    family: str | None = None
    evidence_refs: list[EvidenceRef] = field(default_factory=list)
    blocked_actions: list[str] = field(default_factory=list)
    reentry_conditions: list[str] = field(default_factory=list)
    note: str | None = None


@dataclass(slots=True)
class StressBundle:
    selected_posture: StressPosture | None
    dominant_source_family: SignalSourceFamily | None
    suppression: Literal["active", "low_evidence", "disabled"] = "disabled"
    blocked_actions: list[str] = field(default_factory=list)
    evidence_refs: list[EvidenceRef] = field(default_factory=list)
    reentry_conditions: list[str] = field(default_factory=list)
    considered_sources: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ProgressionOverlay:
    agent_id: str
    rank: RankLabel | None = None
    unlocked_difficulties: list[Difficulty] = field(default_factory=list)
    unlocked_risks: list[Risk] = field(default_factory=list)
    unlocked_cohorts: list[CohortPattern] = field(default_factory=list)
    authority_rights: list[str] = field(default_factory=list)
    evidence_refs: list[EvidenceRef] = field(default_factory=list)


@dataclass(slots=True)
class SelfAgentCheckpoint:
    agent_id: str
    approval_mode: str
    rollback_marker: str | None
    health_check: str | None
    memory_scope: MemoryScope = "session"
    max_iterations: int = 1
    approved: bool = False
    evidence_refs: list[EvidenceRef] = field(default_factory=list)


@dataclass(slots=True)
class SummonDecision:
    allowed: bool
    lane: str
    execution_surface: ExecutionSurface
    cohort_pattern: CohortPattern
    require_split: bool = False
    closeout_required: bool = True
    checkpoint_required: bool = False
    progression_required: bool = False
    codex_projection_required: bool = False
    requested_posture: StressPosture | None = None
    reason_codes: list[str] = field(default_factory=list)
    blocked_actions: list[str] = field(default_factory=list)
    expected_outputs: list[str] = field(default_factory=list)


@dataclass(slots=True)
class CodexLocalAgentTarget:
    agent_id: str
    role: str
    workspace_root: str
    workspace_marker: str
    project_codex_root: str
    config_path: str
    install_surface: str
    sandbox_mode: str
    mcp_servers: list[str] = field(default_factory=list)
    nickname_candidates: list[str] = field(default_factory=list)
    projection_chain: list[str] = field(default_factory=list)


@dataclass(slots=True)
class RemoteTaskResult:
    task_id: str
    state: str
    agent_id: str
    endpoint: str
    returned_artifacts: list[str] = field(default_factory=list)
    context_id: str | None = None
    parent_task_id: str | None = None
    artifact_refs: list[str] = field(default_factory=list)
    message_refs: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ReturnPlan:
    decision: Literal["return"] = "return"
    anchor_artifact: str = "bounded_plan"
    reentry_mode: ReturnReentryMode = "router_reentry"
    next_hop: str = "aoa-routing/generated/return_navigation_hints.min.json"
    reentry_note: str = ""
    reason_codes: list[str] = field(default_factory=list)
    checkpoint_note_ref: str | None = None
    codex_trace_ref: str | None = None
    navigation_target: str | None = None


@dataclass(slots=True)
class ReviewedExportCandidate:
    kind: str
    review_status: str
    summary: str
    evidence_refs: list[EvidenceRef] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class MemoExportPlan:
    writeback_targets: list[ReviewedExportCandidate] = field(default_factory=list)
    candidate_targets: list[ReviewedExportCandidate] = field(default_factory=list)
    adjunct_targets: list[ReviewedExportCandidate] = field(default_factory=list)
    contains_raw_trace: bool = False


@dataclass(slots=True)
class OwnerEvidenceHandoff:
    owner_ref: str
    candidate_kind: str
    reason: str
    evidence_refs: list[str] = field(default_factory=list)
    capability_ref: str | None = None
    review_required: bool = True


@dataclass(slots=True)
class CheckpointEvidenceHandoffPlan:
    mode: Literal["reviewed-evidence-handoff"] = "reviewed-evidence-handoff"
    session_ref: str = ""
    reviewed_artifact_path: str = ""
    checkpoint_note_ref: str | None = None
    codex_trace_ref: str | None = None
    surviving_checkpoint_clusters: list[str] = field(default_factory=list)
    capability_candidates: list[str] = field(
        default_factory=lambda: ["workflow.operations.checkpoint-closeout"]
    )
    authority_contract: str = (
        "reviewed_artifact_primary_capability_candidates_are_routing_only"
    )
    capability_execution_claimed: bool = False
    return_anchor_artifact: str | None = None
