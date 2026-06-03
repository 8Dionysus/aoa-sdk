from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class MemoSurface(BaseModel):
    id: str
    name: str
    surface_kind: str
    summary: str
    primary_focus: str
    recall_modes: list[str] = Field(default_factory=list)
    status: str
    temperature: str
    inspect_surface: str
    expand_surface: str
    source_path: str


class MemoCapsule(BaseModel):
    id: str
    name: str
    summary: str
    one_line_intent: str
    use_when_short: str
    do_not_use_short: str
    inputs_short: str
    outputs_short: str
    core_contract_short: str
    main_risk_short: str
    validation_short: str
    source_path: str


class MemoSection(BaseModel):
    section_id: str
    heading: str
    ordinal: int
    summary: str
    body: str


class MemoSectionBundle(BaseModel):
    id: str
    name: str
    source_path: str
    sections: list[MemoSection] = Field(default_factory=list)


class MemoObjectCard(BaseModel):
    id: str
    kind: str
    title: str
    summary: str
    temperature: str
    review_state: str
    current_recall_status: str
    authority_kind: str
    primary_recall_modes: list[str] = Field(default_factory=list)
    source_path: str
    inspect_key: str
    expand_key: str


class MemoObjectCapsule(BaseModel):
    id: str
    kind: str
    title: str
    summary: str
    recall_posture_short: str
    trust_posture_short: str
    use_when_short: str
    do_not_use_short: str
    strongest_next_source: str
    source_path: str


class MemoObjectSectionBundle(BaseModel):
    id: str
    kind: str
    title: str
    source_path: str
    sections: list[MemoSection] = Field(default_factory=list)


class MemoWritebackRule(BaseModel):
    runtime_surface: str
    runtime_refs: list[str] = Field(default_factory=list)
    target_kind: str
    writeback_class: str
    temperature_hint: str
    review_state_default: str
    requires_human_review: bool
    notes: str


class MemoWritebackMap(BaseModel):
    runtime_surface: str
    contract_type: str
    contract_id: str
    runtime_boundary: dict[str, Any] = Field(default_factory=dict)
    mapping: MemoWritebackRule
    source_files: list[str] = Field(default_factory=list)


class MemoWritebackTarget(BaseModel):
    runtime_surface: str
    target_kind: str
    writeback_class: str
    requires_human_review: bool
    review_state_default: str
    runtime_refs: list[str] = Field(default_factory=list)
    notes: str

class MemoWritebackIntakeTarget(BaseModel):
    runtime_surface: str
    target_kind: str
    writeback_class: str
    requires_human_review: bool
    review_state_default: str
    runtime_refs: list[str] = Field(default_factory=list)
    owner_review_refs: list[str] = Field(default_factory=list)
    intake_posture: str


class MemoWritebackGovernanceTarget(BaseModel):
    runtime_surface: str
    target_kind: str | None = None
    writeback_class: str | None = None
    requires_human_review: bool | None = None
    review_state_default: str | None = None
    intake_posture: str | None = None
    in_writeback_targets: bool
    in_writeback_intake: bool
    governance_passed: bool
    blockers: list[str] = Field(default_factory=list)
