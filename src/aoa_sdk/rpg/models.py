from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Rank = Literal["initiate", "adept", "specialist", "veteran", "master"]
OriginKind = Literal["local_model", "remote_model", "hybrid", "human_guided", "replay"]
Difficulty = Literal[
    "d0_probe",
    "d1_patch",
    "d2_slice",
    "d3_seam",
    "d4_architecture",
    "d5_doctrine",
]
Risk = Literal["r0_readonly", "r1_repo_local", "r2_contract", "r3_side_effect"]
RunMode = Literal["solo", "pair", "checkpoint_cohort", "orchestrated_loop", "manual"]
OrchestratorKind = Literal["codex", "local_runner", "sdk_driver", "human_supervised", "hybrid"]
QuestState = Literal["captured", "triaged", "ready", "active", "blocked", "reanchor", "done", "dropped"]
RunStatus = Literal["completed", "partial", "blocked", "reanchor_needed", "failed_safe", "aborted"]
ReputationAxis = Literal[
    "proof_trust",
    "handoff_trust",
    "provenance_trust",
    "campaign_discipline",
    "boundary_trust",
    "review_trust",
]
Freshness = Literal["hot", "warm", "cool", "cold"]
CauseKind = Literal[
    "eval_verdict",
    "quest_run",
    "manual_review",
    "campaign_review",
    "reanchor",
    "artifact_review",
]
PresentationGroup = Literal[
    "identity",
    "attribute",
    "derived_stat",
    "resource",
    "loadout",
    "quest",
    "reputation",
    "campaign",
    "action",
    "status",
]
AdapterPosture = Literal["portable_only", "local_adapter_optional", "local_adapter_expected"]
EventKind = Literal["rank_change", "unlock", "reputation_shift", "artifact_gain", "reanchor", "campaign_milestone"]
ArtifactStatus = Literal["equipped", "vaulted", "detuned", "retired"]
CampaignStatus = Literal["seed", "proven", "promoted", "canonical", "deprecated"]


class StrictModel(BaseModel):
    # RPG transport surfaces are version-gated upstream, so additive fields inside a
    # supported schema version should not break typed read paths downstream.
    model_config = ConfigDict(extra="ignore")


class DualVocabularyEntry(StrictModel):
    canonical_key: str
    canonical_label: str
    presentation_label: str
    presentation_group: PresentationGroup
    notes: str | None = None


class DualVocabularyOverlay(StrictModel):
    schema_version: Literal["dual_vocabulary_overlay_v1"]
    overlay_id: str
    theme_id: str
    language: str
    entries: list[DualVocabularyEntry] = Field(default_factory=list)
    notes: str | None = None
    public_safe: bool

    def label_for(self, canonical_key: str) -> str | None:
        for entry in self.entries:
            if entry.canonical_key == canonical_key:
                return entry.presentation_label
        return None


class ExecutionOrigin(StrictModel):
    origin_kind: OriginKind
    wrapper_class: str
    model_profile_ref: str | None = None
    orchestrator_hint: str | None = None


class MasteryAxes(StrictModel):
    boundary_integrity: int
    execution_reliability: int
    change_legibility: int
    review_sharpness: int
    proof_discipline: int
    provenance_hygiene: int
    deep_readiness: int


class CapabilityEnvelope(StrictModel):
    difficulty_ceiling: Difficulty
    risk_ceiling: Risk
    allowed_control_modes: list[str] = Field(default_factory=list)
    cohort_patterns: list[str] = Field(default_factory=list)
    authority_rights: list[str] = Field(default_factory=list)


class Loadout(StrictModel):
    equipped_ability_ids: list[str] = Field(default_factory=list)
    passive_feat_ids: list[str] = Field(default_factory=list)
    artifact_ids: list[str] = Field(default_factory=list)
    toolset_refs: list[str] = Field(default_factory=list)
    pack_profiles: list[str] = Field(default_factory=list)
    adapter_posture: AdapterPosture


class DerivedStats(StrictModel):
    handoff_accuracy: int
    reanchor_resilience: int
    campaign_stability: int


class ResourceBudget(StrictModel):
    current: int
    max: int


class ResourceBudgets(StrictModel):
    integrity_budget: ResourceBudget
    focus_budget: ResourceBudget
    deep_budget: ResourceBudget
    recall_budget: ResourceBudget
    autonomy_budget: ResourceBudget


class AgentBuildSnapshot(StrictModel):
    schema_version: Literal["agent_build_snapshot_v1"]
    snapshot_id: str
    captured_at: datetime
    agent_id: str
    role_ref: str
    class_archetype: str
    execution_origin: ExecutionOrigin
    progression_ref: str
    rank: Rank
    mastery_axes: MasteryAxes
    capability_envelope: CapabilityEnvelope
    loadout: Loadout
    derived_stats: DerivedStats
    resource_budgets: ResourceBudgets
    reputation_refs: list[str] = Field(default_factory=list)
    notes: str | None = None
    public_safe: bool


class AgentBuildSnapshotCollection(StrictModel):
    schema_version: Literal["agent_build_snapshot_collection_v1"]
    builds: list[AgentBuildSnapshot] = Field(default_factory=list)


class ReputationSlice(StrictModel):
    slice_id: str
    axis: ReputationAxis
    owner_scope: str
    standing: int
    last_delta: int
    cause_kind: CauseKind
    cause_ref: str
    evidence_refs: list[str] = Field(default_factory=list)
    freshness: Freshness
    recorded_at: datetime
    notes: str | None = None


class ReputationLedger(StrictModel):
    schema_version: Literal["reputation_ledger_v1"]
    ledger_id: str
    subject_ref: str
    subject_kind: Literal["agent", "party", "artifact", "campaign"]
    generated_at: datetime
    slices: list[ReputationSlice] = Field(default_factory=list)
    notes: str | None = None
    public_safe: bool


class ReputationLedgerCollection(StrictModel):
    schema_version: Literal["reputation_ledger_collection_v1"]
    ledgers: list[ReputationLedger] = Field(default_factory=list)


class OrchestratorRef(StrictModel):
    orchestrator_id: str
    orchestrator_kind: OrchestratorKind
    run_mode: RunMode


class QuestRunExecution(StrictModel):
    wrapper_class: str
    control_mode: str
    difficulty: Difficulty
    risk: Risk
    party: list[str] = Field(default_factory=list)
    build_snapshot_refs: list[str] = Field(default_factory=list)
    ability_ids: list[str] = Field(default_factory=list)
    feat_ids: list[str] = Field(default_factory=list)
    artifact_ids: list[str] = Field(default_factory=list)
    toolset_refs: list[str] = Field(default_factory=list)


class QuestRunOutcome(StrictModel):
    run_status: RunStatus
    quest_state_hint: QuestState | None = None
    summary: str


class AxisDeltaPreview(StrictModel):
    boundary_integrity: int
    execution_reliability: int
    change_legibility: int
    review_sharpness: int
    proof_discipline: int
    provenance_hygiene: int
    deep_readiness: int


class ProgressionEffects(StrictModel):
    evidence_refs: list[str] = Field(default_factory=list)
    axis_delta_preview: AxisDeltaPreview
    unlock_candidate_ids: list[str] = Field(default_factory=list)


class ReputationEffect(StrictModel):
    axis: ReputationAxis
    owner_scope: str
    delta: int
    cause_ref: str


class Penalty(StrictModel):
    penalty_kind: str
    summary: str
    duration_hint: str | None = None
    source_ref: str | None = None


class NextHop(StrictModel):
    action: str
    target_ref: str
    note: str | None = None


class QuestRunResult(StrictModel):
    schema_version: Literal["quest_run_result_v1"]
    run_id: str
    quest_ref: str
    owner_repo: str
    started_at: datetime
    finished_at: datetime
    orchestrator: OrchestratorRef
    execution: QuestRunExecution
    outcome: QuestRunOutcome
    artifact_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    chronicle_refs: list[str] = Field(default_factory=list)
    progression_effects: ProgressionEffects | None = None
    reputation_effects: list[ReputationEffect] = Field(default_factory=list)
    penalties: list[Penalty] = Field(default_factory=list)
    next_hops: list[NextHop] = Field(default_factory=list)
    notes: str | None = None
    public_safe: bool


class QuestRunResultCollection(StrictModel):
    schema_version: Literal["quest_run_result_collection_v1"]
    runs: list[QuestRunResult] = Field(default_factory=list)


class ProjectionSourceRefs(StrictModel):
    build_snapshots: list[str] = Field(default_factory=list)
    reputation_ledgers: list[str] = Field(default_factory=list)
    quest_run_results: list[str] = Field(default_factory=list)
    quest_board_refs: list[str] = Field(default_factory=list)
    campaign_refs: list[str] = Field(default_factory=list)


class AxisValue(StrictModel):
    axis: Literal[
        "boundary_integrity",
        "execution_reliability",
        "change_legibility",
        "review_sharpness",
        "proof_discipline",
        "provenance_hygiene",
        "deep_readiness",
    ]
    value: int


class ResourceMeter(StrictModel):
    resource: Literal[
        "integrity_budget",
        "focus_budget",
        "deep_budget",
        "recall_budget",
        "autonomy_budget",
    ]
    current: int
    max: int


class AgentSheetCard(StrictModel):
    agent_id: str
    build_snapshot_ref: str
    display_name: str
    class_archetype: str
    rank: Rank
    primary_axes: list[AxisValue] = Field(default_factory=list)
    resources: list[ResourceMeter] = Field(default_factory=list)
    equipped_ability_ids: list[str] = Field(default_factory=list)
    passive_feat_ids: list[str] = Field(default_factory=list)
    artifact_ids: list[str] = Field(default_factory=list)
    reputation_panel_refs: list[str] = Field(default_factory=list)
    active_quest_refs: list[str] = Field(default_factory=list)


class QuestBoardCard(StrictModel):
    quest_ref: str
    title: str
    owner_repo: str
    state: QuestState
    band: Literal["frontier", "near", "latent", "parked"]
    difficulty: Difficulty
    risk: Risk
    recommended_agents: list[str] = Field(default_factory=list)
    reward_hints: list[str] = Field(default_factory=list)
    penalty_hints: list[str] = Field(default_factory=list)
    source_ref: str


class CampaignLaneCard(StrictModel):
    campaign_ref: str
    title: str
    status: CampaignStatus
    stage_label: str
    anchor_refs: list[str] = Field(default_factory=list)
    recommended_build_refs: list[str] = Field(default_factory=list)
    source_ref: str


class ProgressionTimelineEntry(StrictModel):
    entry_id: str
    agent_ref: str
    event_kind: EventKind
    summary: str
    source_ref: str
    occurred_at: datetime


class ArtifactCaseCard(StrictModel):
    artifact_id: str
    label: str
    status: ArtifactStatus
    source_refs: list[str] = Field(default_factory=list)


class HighlightedReputationSlice(StrictModel):
    axis: ReputationAxis
    standing: int
    label: str | None = None


class ReputationPanel(StrictModel):
    panel_id: str
    subject_ref: str
    ledger_ref: str
    highlighted_slices: list[HighlightedReputationSlice] = Field(default_factory=list)


class FrontendViews(StrictModel):
    agent_sheet_cards: list[AgentSheetCard] = Field(default_factory=list)
    quest_board_cards: list[QuestBoardCard] = Field(default_factory=list)
    campaign_lane_cards: list[CampaignLaneCard] = Field(default_factory=list)
    progression_timeline_entries: list[ProgressionTimelineEntry] = Field(default_factory=list)
    artifact_case_cards: list[ArtifactCaseCard] = Field(default_factory=list)
    reputation_panels: list[ReputationPanel] = Field(default_factory=list)


class FrontendProjectionBundle(StrictModel):
    schema_version: Literal["frontend_projection_bundle_v1"]
    bundle_id: str
    generated_at: datetime
    vocabulary_overlay_ref: str
    source_refs: ProjectionSourceRefs = Field(default_factory=ProjectionSourceRefs)
    views: FrontendViews
    notes: str | None = None
    public_safe: bool


class FrontendProjectionBundleCollection(StrictModel):
    schema_version: Literal["frontend_projection_bundle_collection_v1"]
    bundles: list[FrontendProjectionBundle] = Field(default_factory=list)
