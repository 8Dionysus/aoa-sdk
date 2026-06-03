from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class WorkspaceBootstrapInstallStep(BaseModel):
    skill_name: str
    source_dir: str
    target_dir: str
    action: Literal["create", "replace", "unchanged", "conflict", "missing-source"]


class WorkspaceBootstrapAgentsFile(BaseModel):
    path: str
    action: Literal["write", "overwrite", "unchanged", "preserve-existing", "skipped"]


class WorkspaceBootstrapReport(BaseModel):
    workspace_root: str
    foundation_id: str
    canonical_install_profile: str
    mode: Literal["symlink", "copy"]
    strict_layout: bool
    execute_requested: bool
    overwrite: bool
    ready: bool
    executed: bool
    verified: bool | None = None
    required_repos: list[str] = Field(default_factory=list)
    missing_required_repos: list[str] = Field(default_factory=list)
    optional_repos_present: list[str] = Field(default_factory=list)
    optional_repos_missing: list[str] = Field(default_factory=list)
    install_root: str
    install_steps: list[WorkspaceBootstrapInstallStep] = Field(default_factory=list)
    agents_file: WorkspaceBootstrapAgentsFile | None = None
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
