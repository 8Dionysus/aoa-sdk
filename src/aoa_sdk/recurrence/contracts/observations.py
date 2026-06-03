from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import Field

from .base import HookEvent, HookMatchMode, HookProducerKind, ObservationCategory, StrictModel


class ObservationRecord(StrictModel):
    observation_ref: str
    component_ref: str
    owner_repo: str
    observed_at: datetime
    category: ObservationCategory
    signal: str
    source_inputs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    attributes: dict[str, Any] = Field(default_factory=dict)
    notes: str = ""


class ObservationPacket(StrictModel):
    schema_version: Literal["aoa_observation_packet_v1"] = "aoa_observation_packet_v1"
    packet_ref: str
    workspace_root: str
    signal_ref: str | None = None
    observations: list[ObservationRecord] = Field(default_factory=list)


class HookSignalRule(StrictModel):
    signal: str
    category: ObservationCategory
    match: HookMatchMode = "always"
    field: str | None = None
    value: Any | None = None
    source_inputs: list[str] = Field(default_factory=list)
    attributes_from_fields: list[str] = Field(default_factory=list)
    notes: str = ""


class HookBinding(StrictModel):
    binding_ref: str
    event: HookEvent
    producer: HookProducerKind
    component_ref: str
    owner_repo: str
    input_ref: str
    path_globs: list[str] = Field(default_factory=list)
    config: dict[str, Any] = Field(default_factory=dict)
    signal_rules: list[HookSignalRule] = Field(default_factory=list)
    notes: str = ""


class HookBindingSet(StrictModel):
    manifest_kind: Literal["hook_binding_set"] = "hook_binding_set"
    schema_version: Literal["aoa_hook_binding_set_v1"] = "aoa_hook_binding_set_v1"
    component_ref: str
    owner_repo: str
    bindings: list[HookBinding] = Field(default_factory=list)
    notes: str = ""


class HookRunWarning(StrictModel):
    binding_ref: str
    message: str
    paths: list[str] = Field(default_factory=list)


class HookRunReport(StrictModel):
    schema_version: Literal["aoa_hook_run_report_v1"] = "aoa_hook_run_report_v1"
    run_ref: str
    workspace_root: str
    event: HookEvent
    signal_ref: str | None = None
    bindings_run: list[str] = Field(default_factory=list)
    missing_paths: list[str] = Field(default_factory=list)
    warnings: list[HookRunWarning] = Field(default_factory=list)
    observations: list[ObservationRecord] = Field(default_factory=list)
