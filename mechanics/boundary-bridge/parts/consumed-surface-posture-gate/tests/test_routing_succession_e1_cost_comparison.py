from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[5]
PART_ROOT = Path(__file__).resolve().parents[1]
MEASURER_PATH = PART_ROOT / "scripts" / "measure_routing_succession_e1.py"


def _load_measurer():
    spec = importlib.util.spec_from_file_location(
        "measure_routing_succession_e1",
        MEASURER_PATH,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_e1_report_is_recomputed_from_pinned_git_and_trial_evidence() -> None:
    measurer = _load_measurer()
    report = measurer.build_report()

    repository_cost = report["repository_and_ci_cost"]
    process_cost = report["agent_process_cost"]
    assert repository_cost["canonical_routing_producers"] == {
        "before": 1,
        "after": 1,
    }
    assert repository_cost["active_producer_control_planes"] == {
        "before": 2,
        "after": 1,
    }
    assert repository_cost["checkout_actions"]["before"] == 73
    assert repository_cost["checkout_actions"]["after"] == 23
    assert repository_cost["checkout_actions"]["removed"] == 50
    assert repository_cost["sdk_direct_predecessor_checkouts"] == {
        "before": 4,
        "after": 0,
    }
    assert repository_cost["active_historical_release_probes"]["after"] == []
    assert process_cost["old_contour"]["compile_ready_scenarios"] == 0
    assert process_cost["new_contour"]["compile_ready_scenarios"] == 3
    assert process_cost["new_contour"]["predecessor_checkout_present"] is False


def test_e1_keeps_unlike_latency_and_missing_telemetry_out_of_benefit_claim() -> None:
    measurer = _load_measurer()
    report = measurer.build_report()
    limits = report["agent_process_cost"]["telemetry_limits"]
    stop_lines = report["quality_and_stop_lines"]

    assert limits["direct_latency_comparison_valid"] is False
    assert limits["model_tokens"] == "unavailable in both contours"
    assert stop_lines["task_latency_reduction_claimed"] is False
    assert stop_lines["post_landing_ci_failure_rate_reduction_claimed"] is False
    assert stop_lines["central_aoa_evals_verdict_claimed"] is False
    assert stop_lines["consumer_zero_claimed"] is False
    assert stop_lines["archive_ready_claimed"] is False
    assert stop_lines["archive_authorized_claimed"] is False


@pytest.mark.parametrize(
    ("section", "field", "value"),
    [
        ("verdict", "structural_process_cost_reduced", False),
        ("verdict", "typed_agent_process_capability_increased", False),
        ("verdict", "g13_gate", "pass"),
    ],
)
def test_e1_schema_rejects_overstated_or_regressed_verdict(
    section: str,
    field: str,
    value: object,
) -> None:
    measurer = _load_measurer()
    report = measurer.build_report()
    report[section][field] = value

    with pytest.raises(RuntimeError, match="invalid E1 cost evidence"):
        measurer._validate_report(report)


def test_checked_e1_evidence_matches_builder() -> None:
    measurer = _load_measurer()
    checked = json.loads(
        measurer.EVIDENCE_PATH.read_text(encoding="utf-8")
    )

    assert checked == measurer.build_report()
    assert (
        REPO_ROOT
        / "mechanics"
        / "boundary-bridge"
        / "parts"
        / "consumed-surface-posture-gate"
        / "docs"
        / "routing-succession-e1-cost-comparison.md"
    ).is_file()
