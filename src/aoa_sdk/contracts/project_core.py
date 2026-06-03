from __future__ import annotations

from pydantic import BaseModel, Field


class ProjectCoreKernelGovernanceContract(BaseModel):
    core_receipt_kind: str
    core_receipt_schema_ref: str
    detail_publisher: str
    core_publisher: str
    stats_surface: str
    application_stage: str


class ProjectCoreKernelSkillContract(BaseModel):
    skill_name: str
    detail_event_kind: str
    detail_receipt_schema_ref: str


class ProjectCoreSkillKernelSurface(BaseModel):
    schema_version: int
    source_config: str | None = None
    kernel_id: str
    owner_repo: str
    description: str | None = None
    canonical_install_profile: str
    backward_compatible_aliases: list[str] = Field(default_factory=list)
    skill_count: int | None = None
    skills: list[str] = Field(default_factory=list)
    governance_contract: ProjectCoreKernelGovernanceContract
    skill_contracts: list[ProjectCoreKernelSkillContract] = Field(default_factory=list)


class ProjectCoreOuterRingCluster(BaseModel):
    cluster_id: str
    skill_count: int | None = None
    skills: list[str] = Field(default_factory=list)


class ProjectCoreOuterRingSurface(BaseModel):
    schema_version: int
    source_config: str | None = None
    ring_id: str
    owner_repo: str
    description: str | None = None
    canonical_install_profile: str
    adjacent_kernel_id: str
    skill_count: int | None = None
    skills: list[str] = Field(default_factory=list)
    clusters: list[ProjectCoreOuterRingCluster] = Field(default_factory=list)


class ProjectCoreOuterRingReadinessEntry(BaseModel):
    skill_name: str
    cluster_id: str
    scope: str
    status: str
    invocation_mode: str
    in_repo_core_only: bool
    in_repo_project_core_outer_ring: bool
    in_user_curated_core: bool
    collision_family: str | None = None
    readiness_passed: bool
    blockers: list[str] = Field(default_factory=list)


class ProjectCoreOuterRingReadinessSurface(BaseModel):
    schema_version: int
    source_config: str | None = None
    ring_id: str
    canonical_install_profile: str
    repo_core_only_profile: str
    user_curated_core_profile: str
    skills: list[ProjectCoreOuterRingReadinessEntry] = Field(default_factory=list)


class ProjectRiskGuardRingCluster(BaseModel):
    cluster_id: str
    skill_count: int | None = None
    skills: list[str] = Field(default_factory=list)


class ProjectRiskGuardRingAdjacentOverlay(BaseModel):
    base_skill_name: str
    overlay_skill_name: str


class ProjectRiskGuardRingSurface(BaseModel):
    schema_version: int
    source_config: str | None = None
    ring_id: str
    owner_repo: str
    description: str | None = None
    canonical_install_profile: str
    backcompat_alias_profile: str
    adjacent_kernel_id: str
    adjacent_outer_ring_id: str
    skill_count: int | None = None
    skills: list[str] = Field(default_factory=list)
    clusters: list[ProjectRiskGuardRingCluster] = Field(default_factory=list)
    adjacent_overlays: list[ProjectRiskGuardRingAdjacentOverlay] = Field(default_factory=list)


class ProjectRiskGuardRingGovernanceEntry(BaseModel):
    skill_name: str
    cluster_id: str
    scope: str
    status: str
    invocation_mode: str
    in_repo_project_risk_guard_ring: bool
    in_repo_risk_explicit: bool
    in_repo_default: bool
    collision_family: str | None = None
    adjacent_overlay_skill_name: str | None = None
    adjacent_overlay_present: bool
    governance_passed: bool
    blockers: list[str] = Field(default_factory=list)


class ProjectRiskGuardRingGovernanceSurface(BaseModel):
    schema_version: int
    source_config: str | None = None
    ring_id: str
    canonical_install_profile: str
    backcompat_alias_profile: str
    repo_default_profile: str
    skills: list[ProjectRiskGuardRingGovernanceEntry] = Field(default_factory=list)


class ProjectFoundationProfileSurface(BaseModel):
    schema_version: int
    source_config: str | None = None
    foundation_id: str
    owner_repo: str
    description: str | None = None
    canonical_install_profile: str
    kernel_id: str
    outer_ring_id: str
    risk_ring_id: str
    skill_count: int | None = None
    skills: list[str] = Field(default_factory=list)
    kernel_skills: list[str] = Field(default_factory=list)
    outer_ring_skills: list[str] = Field(default_factory=list)
    risk_ring_skills: list[str] = Field(default_factory=list)
