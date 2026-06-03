from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from .routing import SurfaceRef


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
