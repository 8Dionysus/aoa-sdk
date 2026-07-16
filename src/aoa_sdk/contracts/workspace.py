from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class SkillProfileBootstrapStep(BaseModel):
    skill_name: str
    source_dir: str
    target_dir: str
    action: Literal["create", "replace", "unchanged", "conflict", "missing-source"]


class SkillProfileBootstrapReport(BaseModel):
    discovery_root: str
    source_repo_root: str
    profile_name: str
    profile_scope: Literal["user", "repo"]
    install_mode: Literal["copy"]
    install_root: str
    target_scope_root: str
    execute_requested: bool
    overwrite: bool
    ready: bool
    executed: bool
    verified: bool | None = None
    steps: list[SkillProfileBootstrapStep] = Field(default_factory=list)
    legacy_workspace_root: str | None = None
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
