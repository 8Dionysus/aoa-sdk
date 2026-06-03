from __future__ import annotations

from typing import Literal

from pydantic import Field

from .base import StrictModel


WiringScope = Literal[
    "session_start",
    "user_prompt_submit",
    "session_stop",
    "pre_commit",
    "pre_push",
    "ci",
]

RolloutPhase = Literal[
    "prepared",
    "activated",
    "monitoring",
    "repairing",
    "rollback_open",
    "rolled_back",
]


class WiringSnippet(StrictModel):
    snippet_ref: str
    scope: WiringScope
    title: str
    target_path: str
    commands: list[str] = Field(default_factory=list)
    notes: str = ""


class WiringPlan(StrictModel):
    schema_version: Literal["aoa_wiring_plan_v1"] = "aoa_wiring_plan_v1"
    plan_ref: str
    workspace_root: str
    snippets: list[WiringSnippet] = Field(default_factory=list)


class DriftTrigger(StrictModel):
    signal: str
    severity: Literal["low", "medium", "high"]
    source: str
    notes: str = ""


class RolloutWindow(StrictModel):
    window_ref: str
    campaign_ref: str
    phase: RolloutPhase
    title: str
    wiring_scopes: list[WiringScope] = Field(default_factory=list)
    review_surfaces: list[str] = Field(default_factory=list)
    guard_commands: list[str] = Field(default_factory=list)
    drift_triggers: list[DriftTrigger] = Field(default_factory=list)
    rollback_anchors: list[str] = Field(default_factory=list)
    notes: str = ""


class RolloutWindowBundle(StrictModel):
    schema_version: Literal["aoa_rollout_window_bundle_v1"] = (
        "aoa_rollout_window_bundle_v1"
    )
    bundle_ref: str
    workspace_root: str
    wiring_plan_ref: str
    campaign_window: RolloutWindow
    drift_review_window: RolloutWindow
    rollback_followthrough_window: RolloutWindow
