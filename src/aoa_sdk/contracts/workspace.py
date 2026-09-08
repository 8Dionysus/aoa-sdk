from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


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


OS_PROFILE_REPORT_SCHEMA = "aoa_sdk_os_skill_profile_report_v1"
OS_PROFILE_MAX_DIAGNOSTICS = 8
OS_PROFILE_MAX_DIAGNOSTIC_CHARS = 2048


class OSSkillProfileBootstrapReport(BaseModel):
    """Strict SDK transport report for the aoa-skills OS profile owner command.

    ``owner_payload`` deliberately remains opaque.  The SDK transports the
    owner plan and receipt vocabulary but does not turn it into SDK skill
    entries or infer readiness/admission from a preview.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["aoa_sdk_os_skill_profile_report_v1"] = (
        "aoa_sdk_os_skill_profile_report_v1"
    )
    discovery_root: str
    source_repo_root: str
    profile_name: str
    install_root: str
    target_scope_root: str
    owner_script: str
    owner_command: list[str] = Field(default_factory=list)
    source_roots: dict[str, str] = Field(default_factory=dict)
    execute_requested: bool
    check_requested: bool
    execution_state: Literal["not-requested", "succeeded", "failed", "unknown"]
    verification_state: Literal["not-requested", "passed", "failed", "unknown"]
    executed: bool | None = None
    verified: bool | None = None
    exit_code: int | None = None
    owner_payload: dict[str, Any] = Field(default_factory=dict)
    diagnostics: list[str] = Field(default_factory=list)
    claim_limit: str

    @field_validator("diagnostics")
    @classmethod
    def _diagnostics_are_bounded(cls, value: list[str]) -> list[str]:
        if len(value) > OS_PROFILE_MAX_DIAGNOSTICS:
            raise ValueError(
                f"diagnostics may contain at most {OS_PROFILE_MAX_DIAGNOSTICS} entries"
            )
        if any(len(item) > OS_PROFILE_MAX_DIAGNOSTIC_CHARS for item in value):
            raise ValueError(
                "each diagnostic must be at most "
                f"{OS_PROFILE_MAX_DIAGNOSTIC_CHARS} characters"
            )
        return value
