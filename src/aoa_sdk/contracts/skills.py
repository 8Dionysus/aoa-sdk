from __future__ import annotations

from pathlib import PurePosixPath
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


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
    """Legacy v1 projection model; its public constructor stays compatible."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["aoa_skill_home_port_v1"]
    contract_ref: str
    owner_repo: str
    owner_ref: str
    bundles: list[SkillHomeBundle] = Field(default_factory=list)
    projection: SkillHomeProjection


SkillHomeName = Annotated[str, Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")]


def _skill_home_relative_path(value: str) -> str:
    path = PurePosixPath(value)
    if not value or "\x00" in value or path.is_absolute() or ".." in path.parts:
        raise ValueError("skill-home path must be nonempty and owner-relative")
    return value


class SkillHomeAdmittedBundle(SkillHomeBundle):
    name: SkillHomeName
    version: Annotated[
        str,
        Field(
            pattern=r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-[0-9A-Za-z.-]+)?$"
        ),
    ]
    lifecycle: Literal["admitted"]
    visibility: Literal["advertised"]

    @field_validator("admission_ref")
    @classmethod
    def validate_admission_ref(cls, value: str) -> str:
        return _skill_home_relative_path(value)

    @model_validator(mode="after")
    def validate_source_path(self) -> SkillHomeAdmittedBundle:
        if self.path != f"skills/{self.name}":
            raise ValueError("bundle path must equal skills/<name>")
        return self


class SkillHomeExposureV2(BaseModel):
    model_config = ConfigDict(extra="forbid")

    runtime: Literal["codex"]
    scope: Literal["user"]
    profile: Literal["os-user-default"]
    mode: Literal["profile-selected"]
    skills: list[SkillHomeName] = Field(min_length=1)


class SkillHomeExposureV3(BaseModel):
    model_config = ConfigDict(extra="forbid")

    runtime: SkillHomeName
    scope: SkillHomeName
    profile: SkillHomeName
    mode: Literal["profile-eligible"]
    skills: list[SkillHomeName] = Field(min_length=1)

    @field_validator("skills")
    @classmethod
    def validate_unique_skills(cls, value: list[str]) -> list[str]:
        if len(set(value)) != len(value):
            raise ValueError("exposure skills must be unique")
        return value


class _SkillHomeOwnerManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract_ref: Literal["aoa-skills:schemas/skill-home-port.schema.json"]
    owner_repo: Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$")]
    owner_ref: str
    bundles: list[SkillHomeAdmittedBundle] = Field(min_length=1)

    @field_validator("owner_ref")
    @classmethod
    def validate_owner_ref(cls, value: str) -> str:
        return _skill_home_relative_path(value)

    @field_validator("bundles")
    @classmethod
    def validate_unique_bundles(
        cls, value: list[SkillHomeAdmittedBundle]
    ) -> list[SkillHomeAdmittedBundle]:
        if len({bundle.name for bundle in value}) != len(value):
            raise ValueError("bundle names must be unique")
        return value


class SkillHomePortManifestV2(_SkillHomeOwnerManifest):
    schema_version: Literal["aoa_skill_home_port_v2"]
    exposure: SkillHomeExposureV2

    @model_validator(mode="after")
    def validate_complete_exposure(self) -> SkillHomePortManifestV2:
        if self.exposure.skills != [bundle.name for bundle in self.bundles]:
            raise ValueError("v2 exposure skills must exactly match bundles order")
        return self


class SkillHomePortManifestV3(_SkillHomeOwnerManifest):
    schema_version: Literal["aoa_skill_home_port_v3"]
    exposures: list[SkillHomeExposureV3]

    @model_validator(mode="after")
    def validate_exposures(self) -> SkillHomePortManifestV3:
        names = {bundle.name for bundle in self.bundles}
        targets: set[tuple[str, str, str]] = set()
        for exposure in self.exposures:
            if not set(exposure.skills) <= names:
                raise ValueError("exposure skills must refer to declared bundles")
            target = (exposure.runtime, exposure.scope, exposure.profile)
            if target in targets:
                raise ValueError("exposure targets must be unique")
            targets.add(target)
        return self


AnySkillHomePortManifest = Annotated[
    SkillHomePortManifest | SkillHomePortManifestV2 | SkillHomePortManifestV3,
    Field(discriminator="schema_version"),
]


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
        "owner-source",
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
        "owner-source",
    ]
    scope: Literal["user", "repo", "workspace", "source"]
    path: str
    exists: bool
    authority: Literal[
        "host-projection",
        "owner-projection",
        "legacy-unowned",
        "portable-export",
        "owner-source",
    ]
    owner_repo: str | None = None
    manifest_path: str | None = None
    source_schema_version: str | None = None
    exposures: list[SkillHomeExposureV2 | SkillHomeExposureV3] = Field(
        default_factory=list
    )
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
