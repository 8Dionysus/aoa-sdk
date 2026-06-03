from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class KagRegistrySurface(BaseModel):
    id: str
    name: str
    status: str
    summary: str
    source_class: str
    derived_kind: str
    provenance_mode: str
    normalization_scope: str
    framework_readiness: str
    source_repos: list[str] = Field(default_factory=list)


class KagFederationRepoEntry(BaseModel):
    repo: str
    pilot_posture: str
    export_ref: str
    kind: str
    object_id: str
    entry_surface_ref: str
    adjunct_surfaces: list[dict[str, Any]] = Field(default_factory=list)
    summary_50: str
    provenance_note: str
    non_identity_boundary: str


class KagFederationSpine(BaseModel):
    pack_version: int
    pack_type: str
    source_manifest_ref: str
    source_inputs: list[dict[str, Any]] = Field(default_factory=list)
    repo_count: int
    repos: list[KagFederationRepoEntry] = Field(default_factory=list)
    bounded_output_contract: dict[str, Any] = Field(default_factory=dict)


class KagTinyBundleItem(BaseModel):
    order: int
    name: str
    role: str
    ref: str


class KagTinyConsumerBundle(BaseModel):
    bundle_version: int
    bundle_type: str
    source_manifest_ref: str
    source_inputs: list[dict[str, Any]] = Field(default_factory=list)
    bundle_item_count: int
    bundle_items: list[KagTinyBundleItem] = Field(default_factory=list)
    deferred_counterpart: dict[str, Any] = Field(default_factory=dict)


class KagRegroundingMode(BaseModel):
    mode_id: str
    used_when: str
    query_mode_hint: str
    trigger_surface_refs: list[str] = Field(default_factory=list)
    stronger_refs: list[str] = Field(default_factory=list)
    supporting_surface_refs: list[str] = Field(default_factory=list)
    preserved_fields: list[str] = Field(default_factory=list)
    reentry_note: str
    non_identity_boundary: str
    prohibited_promotions: list[str] = Field(default_factory=list)


class KagInspectResult(BaseModel):
    ok: bool = True
    surface_id: str
    registry_entry: KagRegistrySurface
    pack: dict[str, Any] = Field(default_factory=dict)
    source_files: list[str] = Field(default_factory=list)


class KagQueryModeResult(BaseModel):
    ok: bool = True
    mode: Literal["local_search", "global_search", "drift_search"]
    reasoning_scenarios: list[dict[str, Any]] = Field(default_factory=list)
    regrounding_modes: list[KagRegroundingMode] = Field(default_factory=list)
    source_files: list[str] = Field(default_factory=list)


class KagRepoEntry(BaseModel):
    repo: Literal["Tree-of-Sophia", "aoa-techniques"]
    pilot_posture: str
    export_ref: str
    kind: str
    object_id: str
    entry_surface_ref: str
    adjunct_surfaces: list[dict[str, Any]] = Field(default_factory=list)
    summary_50: str
    provenance_note: str
    non_identity_boundary: str
