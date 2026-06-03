from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class CodexProjectionLiveRolloutStatusSnapshot(BaseModel):
    schema_version: Literal["aoa_sdk_codex_projection_live_rollout_status_snapshot_v1"] = (
        "aoa_sdk_codex_projection_live_rollout_status_snapshot_v1"
    )
    workspace_root: str
    trust_posture: Literal[
        "unknown",
        "root_mismatch",
        "config_inactive",
        "trusted_ready",
        "rollout_active",
        "rollback_recommended",
    ]
    latest_trust_state_ref: str
    latest_rollout_receipt_ref: str
    project_config_active: bool
    hooks_active: bool
    active_mcp_servers: list[str] = Field(default_factory=list)
    rollout_state: Literal[
        "render_only",
        "dry_run_ready",
        "applied",
        "verified",
        "drifted",
        "rollback_recommended",
    ]
    drift_detected: bool
    next_action: Literal["none", "run_doctor", "rerender", "rerollout", "rollback"]
    observed_at: datetime
