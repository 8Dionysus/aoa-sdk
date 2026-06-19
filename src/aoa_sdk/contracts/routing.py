from __future__ import annotations

from typing import Any, Literal

from pydantic import AliasChoices, BaseModel, Field


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


class RoutingOwnerLayerShortlistHint(BaseModel):
    shortlist_id: str
    signal: Literal[
        "explicit-request",
        "proof-need",
        "recall-need",
        "scenario-recurring",
        "role-posture",
        "repeated-pattern",
        "risk-gate",
    ]
    owner_repo: Literal[
        "aoa-techniques",
        "aoa-skills",
        "aoa-evals",
        "aoa-memo",
        "aoa-playbooks",
        "aoa-agents",
        "aoa-sdk",
        "aoa-stats",
        "Dionysus",
        "8Dionysus",
        "abyss-stack",
    ]
    object_kind: Literal[
        "technique",
        "skill",
        "eval",
        "memo",
        "playbook",
        "agent",
        "seed",
        "source_route",
        "runtime_surface",
        "orientation_surface",
    ]
    target_surface: str
    inspect_surface: str | None = None
    hint_reason: str
    confidence: Literal["low", "medium", "high"] = "medium"
    ambiguity: Literal["clear", "ambiguous"] = "clear"


class RoutingStatsRegroundingAction(BaseModel):
    verb: str
    target_repo: str
    target_ref: str


class RoutingStatsRegroundingHint(BaseModel):
    model_config = {"populate_by_name": True}

    hint_id: str
    surface_name: str
    surface_ref: str | None = None
    recommended_action: Literal["reground_before_using_stats"]
    reason_codes: list[str] = Field(default_factory=list)
    owner_truth_inputs: list[str] = Field(default_factory=list)
    primary_action: RoutingStatsRegroundingAction
    secondary_actions: list[RoutingStatsRegroundingAction] = Field(
        default_factory=list,
        validation_alias=AliasChoices("secondary_actions", "fallback_actions"),
    )
    advisory_only: bool
    authority_note: str


class RoutingStatsRegroundingHintsPayload(BaseModel):
    schema_version: Literal["aoa_routing_stats_regrounding_hints_v1"]
    schema_ref: str
    owner_repo: Literal["aoa-routing"]
    surface_kind: Literal["stats_regrounding_hints"]
    source_inputs: list[dict[str, Any]] = Field(default_factory=list)
    coverage_thin_signal_flags: list[str] = Field(default_factory=list)
    hints: list[RoutingStatsRegroundingHint] = Field(default_factory=list)
    boundary_notes: list[str] = Field(default_factory=list)


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


class SurfaceCompatibilityRule(BaseModel):
    surface_id: str
    repo: str
    relative_path: str
    preferred_relative_paths: list[str] = Field(default_factory=list)
    version_field: str | None = None
    legacy_version_fields: list[str] = Field(default_factory=list)
    supported_versions: list[int | str] = Field(default_factory=list)
    expected_json_kind: Literal["object", "array", "any"] = "object"
    required_top_level_keys: list[str] = Field(default_factory=list)
    required_top_level_object_keys: list[str] = Field(default_factory=list)
    notes: str = ""


class SurfaceCompatibilityCheck(BaseModel):
    surface_id: str
    repo: str
    relative_path: str
    resolved_relative_path: str | None = None
    exists: bool = True
    compatibility_mode: Literal["versioned", "unversioned"]
    version_field: str | None = None
    supported_versions: list[int | str] = Field(default_factory=list)
    detected_version: int | str | None = None
    compatible: bool
    reason: str
