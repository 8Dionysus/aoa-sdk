from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

class SurfaceRef(BaseModel):
    repo: str
    path: str
    kind: str

class SkillCard(BaseModel):
    name: str
    display_name: str
    description: str
    short_description: str
    path: str
    trust_posture: Literal["explicit-risk", "portable-core", "project-overlay"]
    invocation_mode: Literal["explicit-only", "explicit-preferred"]
    allow_implicit_invocation: bool
    mutation_surface: Literal["none", "repo", "runtime", "sharing"]

class PhaseBinding(BaseModel):
    phase: Literal["route", "plan", "do", "verify", "transition", "deep", "distill"]
    tier_id: str
    role_names: list[str]
    artifact_type: str

class ArtifactEnvelope(BaseModel):
    artifact_type: str
    phase: str
    produced_at: datetime
    payload: dict[str, Any] = Field(default_factory=dict)
    refs: list[SurfaceRef] = Field(default_factory=list)
