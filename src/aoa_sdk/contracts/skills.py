from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class AgentSkillResourceInventory(BaseModel):
    model_config = ConfigDict(extra="allow")

    scripts: list[str] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)
    assets: list[str] = Field(default_factory=list)
    checks: list[str] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)


class AgentSkillCatalogEntry(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str
    display_name: str
    description: str
    short_description: str
    path: str
    openai_config_path: str | None = None
    scope: str
    status: str
    invocation_mode: str
    implicit_activation_policy: str
    allow_implicit_invocation: bool
    manual_invocation_required: bool
    candidate_only: bool
    source_skill_path: str
    trust_posture: str
    mutation_surface: str
    recommended_install_scopes: list[str] = Field(default_factory=list)
    resource_inventory: AgentSkillResourceInventory = Field(
        default_factory=AgentSkillResourceInventory
    )
    ui: dict[str, Any] = Field(default_factory=dict)


class AgentSkillCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid")

    catalog_version: Literal[2]
    profile: str
    root: str
    source_repo: str
    source_of_truth: dict[str, str]
    skills: list[AgentSkillCatalogEntry] = Field(default_factory=list)


class SkillPackEntry(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str
    source_path: str
    target_path: str
    openai_config_path: str | None = None
    allow_implicit_invocation: bool
    implicit_activation_policy: str
    trust_posture: str


class SkillPackProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: str
    scope: Literal["user", "repo"]
    install_mode: Literal["copy"]
    install_root: str
    skills: list[SkillPackEntry] = Field(default_factory=list)


class SkillPackProfiles(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[2]
    profile: str
    source_config: str
    profiles: dict[str, SkillPackProfile] = Field(default_factory=dict)


class CapabilityGraphSourceFile(BaseModel):
    path: str
    sha256: str


class CapabilityGraphSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    root: str
    family_files: list[CapabilityGraphSourceFile] = Field(default_factory=list)
    referenced_files: list[CapabilityGraphSourceFile] = Field(default_factory=list)
    content_hash: str


class CapabilityOwner(BaseModel):
    model_config = ConfigDict(extra="allow")

    authority: str
    repo: str
    surface: str


class CapabilityLifecycle(BaseModel):
    model_config = ConfigDict(extra="allow")

    state: str
    visibility: str
    evidence_state: str | None = None
    health: str | None = None
    version: str | int | None = None


class CapabilityNode(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    kind: str
    contract_level: Literal["navigation", "executable"]
    primary_parent: str | None
    source_family: str
    source_path: str
    owner: CapabilityOwner
    lifecycle: CapabilityLifecycle
    title: str | None = None
    description: str | None = None
    keywords: list[str] = Field(default_factory=list)
    abi: dict[str, Any] = Field(default_factory=dict)
    applicability: dict[str, Any] = Field(default_factory=dict)
    execution: dict[str, Any] = Field(default_factory=dict)
    binding: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)
    trust: dict[str, Any] = Field(default_factory=dict)


class CapabilityRelation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: str
    source: str
    target: str
    source_path: str
    condition: str | None = None


class CapabilityRetrievalDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    kind: str
    visibility: str
    title: str
    description: str
    search_text: str
    positive_text: str
    negative_text: str
    negative_phrases: list[str] = Field(default_factory=list)
    routing_tokens: list[str] = Field(default_factory=list)
    positive_tokens: list[str] = Field(default_factory=list)
    negative_tokens: list[str] = Field(default_factory=list)
    tokens: list[str] = Field(default_factory=list)


class CapabilityGraph(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["aoa-capability-graph-v1"]
    authority: Literal[False]
    source: CapabilityGraphSource
    roots: list[str]
    nodes: list[CapabilityNode]
    relations: list[CapabilityRelation] = Field(default_factory=list)
    retrieval_documents: list[CapabilityRetrievalDocument]


class CapabilityNeighborhood(BaseModel):
    node: CapabilityNode
    incoming: list[CapabilityRelation] = Field(default_factory=list)
    outgoing: list[CapabilityRelation] = Field(default_factory=list)


class PortableSkillExport(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str
    source_skill_path: str
    target_dir: str
    target_skill_path: str
    target_openai_config_path: str | None = None
    invocation_mode: str
    implicit_activation_policy: str
    allow_implicit_invocation: bool
    candidate_only: bool
    resource_inventory: AgentSkillResourceInventory = Field(
        default_factory=AgentSkillResourceInventory
    )


class PortableExportMap(BaseModel):
    model_config = ConfigDict(extra="forbid")

    export_version: Literal[2]
    profile: str
    root: str
    source_repo: str
    source_of_truth: dict[str, str]
    exports: list[PortableSkillExport] = Field(default_factory=list)


class McpSkillDependency(BaseModel):
    name: str
    tools: list[str] = Field(default_factory=list)


class McpDependencyManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[2]
    profile: str
    skills: list[McpSkillDependency] = Field(default_factory=list)


class SkillHomeBundle(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    path: str
    version: str
    lifecycle: str
    visibility: str
    admission_ref: str


class SkillHomeProjection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    runtime: str
    scope: Literal["repo"]
    root: str
    mode: Literal["generated-copy"]
    skills: list[str] = Field(default_factory=list)


class SkillHomePortManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["aoa_skill_home_port_v1"]
    contract_ref: str
    owner_repo: str
    owner_ref: str
    bundles: list[SkillHomeBundle] = Field(default_factory=list)
    projection: SkillHomeProjection


class InstalledSkill(BaseModel):
    name: str
    skill_dir: str
    skill_file: str
    status: Literal[
        "current",
        "drift",
        "missing",
        "unmanaged",
        "source-export",
        "legacy-unowned",
    ]
    admitted: bool = False
    expected_source_dir: str | None = None


class SkillRootInspection(BaseModel):
    root_kind: Literal[
        "user",
        "repo-projection",
        "repo-unowned",
        "workspace-legacy",
        "source-export",
    ]
    scope: Literal["user", "repo", "workspace", "source"]
    path: str
    exists: bool
    authority: Literal[
        "host-projection",
        "owner-projection",
        "legacy-unowned",
        "portable-export",
    ]
    owner_repo: str | None = None
    manifest_path: str | None = None
    admitted_names: list[str] = Field(default_factory=list)
    entries: list[InstalledSkill] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)


class SkillEnvironmentReport(BaseModel):
    repo_root: str
    federation_root: str
    source_repo_root: str
    user_skill_root: str
    roots: list[SkillRootInspection] = Field(default_factory=list)
    duplicate_names: dict[str, list[str]] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
