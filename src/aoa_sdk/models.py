from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

class SurfaceRef(BaseModel):
    repo: str
    path: str
    kind: str


class RouterAction(BaseModel):
    enabled: bool
    surface_repo: str | None = None
    surface_file: str | None = None
    match_field: str | None = None
    section_key_field: str | None = None
    default_sections: list[str] = Field(default_factory=list)
    supported_sections: list[str] = Field(default_factory=list)


class RoutingHint(BaseModel):
    kind: str
    enabled: bool = True
    source_repo: str
    use_when: str
    actions: dict[str, RouterAction]


class RegistryEntry(BaseModel):
    kind: str
    id: str
    name: str
    repo: str
    path: str
    status: str
    summary: str
    source_type: str
    attributes: dict[str, Any] = Field(default_factory=dict)


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
    active_skills: list[ActiveSkillRecord] = Field(default_factory=list)
    activation_log: list[dict[str, Any]] = Field(default_factory=list)

class PhaseBinding(BaseModel):
    phase: Literal["route", "plan", "do", "verify", "transition", "deep", "distill"]
    tier_id: str
    role_names: list[str]
    artifact_type: str

class ArtifactEnvelope(BaseModel):
    artifact_type: str
    phase: str
    produced_by_role: str | None = None
    produced_at: datetime
    payload: dict[str, Any] = Field(default_factory=dict)
    refs: list[SurfaceRef] = Field(default_factory=list)
