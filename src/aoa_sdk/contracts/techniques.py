from __future__ import annotations

from pydantic import BaseModel, Field


class TechniquePromotionReadinessEntry(BaseModel):
    technique_id: str
    technique_name: str
    status: str
    export_ready: bool
    review_required: bool
    has_canonical_readiness_note: bool
    has_adverse_effects_review: bool
    readiness_passed: bool
    blockers: list[str] = Field(default_factory=list)
