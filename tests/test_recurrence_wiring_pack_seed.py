from __future__ import annotations

# ruff: noqa: E402

import sys
import types
from pathlib import Path


def _install_workspace_stub() -> None:
    if "aoa_sdk.workspace.discovery" in sys.modules:
        return
    workspace_pkg = types.ModuleType("aoa_sdk.workspace")
    discovery = types.ModuleType("aoa_sdk.workspace.discovery")

    class Workspace:
        def __init__(self, root=None, repo_roots=None):
            self.root = root
            self.repo_roots = repo_roots or {}

        @classmethod
        def discover(cls, root="."):
            root_path = Path(root)
            repo_roots = (
                {item.name: item for item in root_path.iterdir() if item.is_dir()}
                if root_path.exists()
                else {}
            )
            return cls(root=root_path, repo_roots=repo_roots)

    discovery.Workspace = Workspace
    workspace_pkg.discovery = discovery
    sys.modules["aoa_sdk.workspace"] = workspace_pkg
    sys.modules["aoa_sdk.workspace.discovery"] = discovery


_install_workspace_stub()

from aoa_sdk.recurrence.models import (
    ConnectivityGap,
    ConnectivityGapReport,
    OwnerReviewSummary,
    OwnerReviewSummaryItem,
)
from aoa_sdk.recurrence.rollout import build_rollout_window_bundle
from aoa_sdk.recurrence.wiring import build_wiring_plan
from aoa_sdk.workspace.discovery import Workspace


def test_wiring_plan_emits_expected_scopes(tmp_path: Path) -> None:
    workspace = Workspace.discover(tmp_path)
    plan = build_wiring_plan(workspace)
    scopes = [item.scope for item in plan.snippets]
    assert scopes == [
        "session_start",
        "user_prompt_submit",
        "session_stop",
        "pre_commit",
        "pre_push",
        "ci",
    ]


def test_rollout_bundle_opens_rollback_on_high_gap(tmp_path: Path) -> None:
    workspace = Workspace.discover(tmp_path)
    plan = build_wiring_plan(workspace)
    summary = OwnerReviewSummary(
        summary_ref="summary:test",
        workspace_root=str(tmp_path),
        signal_ref="signal:test",
        owners=[
            OwnerReviewSummaryItem(
                target_repo="aoa-evals", total_items=1, by_kind={"overclaim_alarm": 1}
            )
        ],
    )
    doctor = ConnectivityGapReport(
        report_ref="doctor:test",
        workspace_root=str(tmp_path),
        signal_ref="signal:test",
        components_checked=["component:evals:portable-proof-beacons"],
        gaps=[
            ConnectivityGap(
                gap_ref="gap:0001",
                severity="high",
                gap_kind="unresolved_edge",
                component_ref="component:evals:portable-proof-beacons",
                owner_repo="aoa-evals",
                evidence_refs=["beacon:001"],
                recommendation="repair the unresolved edge before widening rollout",
            )
        ],
    )
    bundle = build_rollout_window_bundle(
        workspace,
        wiring_plan=plan,
        review_summary=summary,
        doctor_report=doctor,
    )
    assert bundle.drift_review_window.phase == "repairing"
    assert bundle.rollback_followthrough_window.phase == "rollback_open"
    assert any(
        item.signal == "overclaim_alarm_present"
        for item in bundle.drift_review_window.drift_triggers
    )
