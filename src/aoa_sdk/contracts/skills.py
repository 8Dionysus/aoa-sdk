from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import AliasChoices, BaseModel, Field

from .closeout import KernelNextStepBrief


class SkillCard(BaseModel):
    name: str
    display_name: str
    description: str
    short_description: str
    path: str
    trust_posture: Literal["explicit-risk", "portable-core", "project-overlay"]
    invocation_mode: Literal["explicit-only", "explicit-preferred"]
    allow_implicit_invocation: bool
    mutation_surface: Literal["none", "repo", "runtime", "sharing"]
    keywords: list[str] = Field(default_factory=list)
    recommended_install_scopes: list[str] = Field(default_factory=list)
    explicit_handles: dict[str, Any] = Field(default_factory=dict)


class SkillDisclosure(BaseModel):
    name: str
    display_name: str
    description: str
    short_description: str
    path: str
    skill_dir: str
    compatibility: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    headings_available: list[str] = Field(default_factory=list)
    section_summaries: dict[str, str] = Field(default_factory=dict)
    resource_inventory: dict[str, list[str]] = Field(default_factory=dict)
    policy: dict[str, Any] = Field(default_factory=dict)
    interface: dict[str, Any] = Field(default_factory=dict)
    runtime_contract_ref: str | None = None
    context_retention_ref: str | None = None
    trust_policy_ref: str | None = None
    collision_family: str | None = None


class SkillHostAvailability(BaseModel):
    model_config = {"populate_by_name": True}

    status: Literal["host-executable", "router-only", "unknown"]
    source: Literal[
        "host-manifest",
        "host-skill-list",
        "repo-install",
        "workspace-install",
        "user-install",
        "not-provided",
    ]
    manual_equivalence_allowed: bool = Field(
        validation_alias=AliasChoices("manual_equivalence_allowed", "manual_fallback_allowed")
    )
    reason: str


class SkillActivationRequest(BaseModel):
    skill_name: str
    session_file: str | None = None
    explicit_handle: str | None = None
    include_frontmatter: bool = False
    wrap_mode: Literal["structured", "markdown", "raw"] = "structured"


class ActiveSkillRecord(BaseModel):
    name: str
    activated_at: datetime
    activation_count: int
    protected_from_compaction: bool
    allowlist_paths: list[str] = Field(default_factory=list)
    compact_summary: str
    must_keep: list[str] = Field(default_factory=list)
    rehydration_hint: str


class SkillSession(BaseModel):
    schema_version: int
    profile: str
    session_id: str
    created_at: datetime
    updated_at: datetime
    codex_thread_id: str | None = None
    codex_rollout_path: str | None = None
    codex_thread_title: str | None = None
    codex_first_user_message: str | None = None
    codex_thread_updated_at: datetime | None = None
    active_skills: list[ActiveSkillRecord] = Field(default_factory=list)
    activation_log: list[dict[str, Any]] = Field(default_factory=list)

class SkillDispatchItem(BaseModel):
    skill_name: str
    layer: Literal["kernel", "outer-ring", "risk-ring"]
    collision_family: str | None = None
    reason: str
    host_availability: SkillHostAvailability = Field(
        default_factory=lambda: SkillHostAvailability(
            status="unknown",
            source="not-provided",
            manual_equivalence_allowed=False,
            reason="no host skill inventory was supplied",
        )
    )


class SkillDetectionReport(BaseModel):
    phase: Literal["ingress", "pre-mutation", "checkpoint", "closeout"]
    repo_root: str
    foundation_id: str
    activate_now: list[SkillDispatchItem] = Field(default_factory=list)
    must_confirm: list[SkillDispatchItem] = Field(default_factory=list)
    suggest_next: list[SkillDispatchItem] = Field(default_factory=list)
    host_inventory_provided: bool = False
    actionability_gaps: list[str] = Field(default_factory=list)
    blocked_actions: list[str] = Field(default_factory=list)
    closeout_chain: KernelNextStepBrief | None = None
    reasoning: list[str] = Field(default_factory=list)
