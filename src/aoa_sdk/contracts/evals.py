from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class EvalCard(BaseModel):
    baseline_mode: str
    category: str
    claim_type: str
    eval_path: str
    export_ready: bool
    maturity_score: int
    name: str
    object_under_evaluation: str
    portability_level: str
    repeatability: str
    report_format: str
    review_required: bool
    rigor_level: str
    skill_dependencies: list[str] = Field(default_factory=list)
    status: str
    summary: str
    technique_dependencies: list[str] = Field(default_factory=list)
    validation_strength: str
    verdict_shape: str


class EvalCapsule(BaseModel):
    blind_spot_short: str
    bounded_claim_short: str
    category: str
    comparison_surface: dict[str, Any] | None = None
    do_not_use_short: str
    eval_path: str
    name: str
    proof_artifact_short: str
    skill_dependencies: list[str] = Field(default_factory=list)
    status: str
    summary: str
    technique_dependencies: list[str] = Field(default_factory=list)
    use_when_short: str
    verdict_shape: str
    what_this_does_not_prove: str


class EvalSection(BaseModel):
    heading: str
    key: str
    content_markdown: str


class EvalSectionBundle(BaseModel):
    category: str
    eval_path: str
    name: str
    sections: list[EvalSection] = Field(default_factory=list)
    status: str
    verdict_shape: str


class ComparisonEntry(BaseModel):
    baseline_mode: str
    comparison_surface: dict[str, Any]
    eval_path: str
    interpretation_boundary: str
    name: str
    proof_artifacts: dict[str, Any] = Field(default_factory=dict)
    relations: list[dict[str, Any]] = Field(default_factory=list)
    selection_summary: str
    status: str


class EvalRuntimeCandidateTemplate(BaseModel):
    template_kind: Literal["runtime_evidence_selection", "artifact_to_verdict_hook"]
    template_name: str
    playbook_id: str | None = None
    eval_anchor: str | None = None
    verdict_bundle_ref: str | None = None
    required_runtime_artifacts: list[str] = Field(default_factory=list)
    review_required: bool
    source_example_ref: str


class EvalRuntimeCandidateIntake(BaseModel):
    template_kind: Literal["runtime_evidence_selection", "artifact_to_verdict_hook"]
    template_name: str
    playbook_id: str | None = None
    eval_anchor: str | None = None
    verdict_bundle_ref: str | None = None
    required_runtime_artifacts: list[str] = Field(default_factory=list)
    review_required: bool
    review_guide_ref: str
    owner_review_refs: list[str] = Field(default_factory=list)
    candidate_acceptance_posture: str
