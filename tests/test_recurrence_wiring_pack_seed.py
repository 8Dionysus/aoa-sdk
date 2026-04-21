from __future__ import annotations

# ruff: noqa: E402

import importlib.util
import sys
import types
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parents[1] / "src" / "aoa_sdk"
TEST_PACKAGE = "_test_aoa_sdk"
TEST_RECURRENCE_PACKAGE = f"{TEST_PACKAGE}.recurrence"
TEST_WORKSPACE_PACKAGE = f"{TEST_PACKAGE}.workspace"
TEST_DISCOVERY_MODULE = f"{TEST_WORKSPACE_PACKAGE}.discovery"
TEST_ROOTS_MODULE = f"{TEST_WORKSPACE_PACKAGE}.roots"


def _install_workspace_stub() -> None:
    if TEST_DISCOVERY_MODULE in sys.modules:
        return

    base_pkg = types.ModuleType(TEST_PACKAGE)
    base_pkg.__path__ = [str(SRC_ROOT)]
    recurrence_pkg = types.ModuleType(TEST_RECURRENCE_PACKAGE)
    recurrence_pkg.__path__ = [str(SRC_ROOT / "recurrence")]
    workspace_pkg = types.ModuleType(TEST_WORKSPACE_PACKAGE)
    workspace_pkg.__path__ = []
    discovery = types.ModuleType(TEST_DISCOVERY_MODULE)
    roots = types.ModuleType(TEST_ROOTS_MODULE)
    roots.KNOWN_REPOS = ()

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

    base_pkg.recurrence = recurrence_pkg
    base_pkg.workspace = workspace_pkg
    workspace_pkg.discovery = discovery
    workspace_pkg.roots = roots
    discovery.Workspace = Workspace
    sys.modules[TEST_PACKAGE] = base_pkg
    sys.modules[TEST_RECURRENCE_PACKAGE] = recurrence_pkg
    sys.modules[TEST_WORKSPACE_PACKAGE] = workspace_pkg
    sys.modules[TEST_DISCOVERY_MODULE] = discovery
    sys.modules[TEST_ROOTS_MODULE] = roots


_install_workspace_stub()


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


models = _load_module(
    f"{TEST_RECURRENCE_PACKAGE}.models", SRC_ROOT / "recurrence" / "models.py"
)
rollout = _load_module(
    f"{TEST_RECURRENCE_PACKAGE}.rollout", SRC_ROOT / "recurrence" / "rollout.py"
)
wiring = _load_module(
    f"{TEST_RECURRENCE_PACKAGE}.wiring", SRC_ROOT / "recurrence" / "wiring.py"
)

ConnectivityGap = models.ConnectivityGap
ConnectivityGapReport = models.ConnectivityGapReport
OwnerReviewSummary = models.OwnerReviewSummary
OwnerReviewSummaryItem = models.OwnerReviewSummaryItem
build_rollout_window_bundle = rollout.build_rollout_window_bundle
build_wiring_plan = wiring.build_wiring_plan
Workspace = sys.modules[TEST_DISCOVERY_MODULE].Workspace


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


def test_wiring_plan_ci_commands_use_repo_root_test_paths(tmp_path: Path) -> None:
    workspace = Workspace.discover(tmp_path)
    plan = build_wiring_plan(workspace)
    ci_snippet = next(item for item in plan.snippets if item.scope == "ci")

    assert ci_snippet.commands[1].startswith("pytest -q tests/test_recurrence_seed.py")
    assert "aoa-sdk/tests/" not in ci_snippet.commands[1]


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
