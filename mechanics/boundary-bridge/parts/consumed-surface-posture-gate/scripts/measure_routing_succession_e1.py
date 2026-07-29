#!/usr/bin/env python3
"""Build the bounded E1 routing-succession process-cost comparison."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path
from statistics import median
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


PART_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PART_ROOT.parents[3]
BASELINE_PATH = PART_ROOT / "evidence" / "routing-succession-r0-baseline.json"
OBSERVATIONS_PATH = (
    PART_ROOT / "evidence" / "routing-succession-e1-process-observations.json"
)
EVIDENCE_PATH = (
    PART_ROOT / "evidence" / "routing-succession-e1-cost-comparison.json"
)
SCHEMA_PATH = (
    PART_ROOT / "schemas" / "routing-succession-e1-cost-comparison.schema.json"
)
COMPILER_TRIAL_PATH = (
    REPO_ROOT
    / "mechanics"
    / "boundary-bridge"
    / "parts"
    / "plan-compilation-control-plane"
    / "trials"
    / "fresh-context-compiler-v3-black-box-v1.json"
)
LIFECYCLE_TRIAL_PATH = (
    REPO_ROOT
    / "mechanics"
    / "boundary-bridge"
    / "parts"
    / "runner-lifecycle-control-plane"
    / "trials"
    / "isolated-runtime-lifecycle-v1.json"
)
G11_TRIAL_PATH = (
    REPO_ROOT
    / "mechanics"
    / "boundary-bridge"
    / "parts"
    / "runner-lifecycle-control-plane"
    / "trials"
    / "agent-os-g11-adversarial-corpus-v1.json"
)
HISTORICAL_PROBES = (
    "verify_routing_shadow_wheel.py",
    "verify_routing_g5_candidate_wheel.py",
    "verify_routing_g5_release_candidate_wheel.py",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--routing-root",
        type=Path,
        help=(
            "Optional aoa-routing M3 worktree. When supplied, its exact "
            "receipt, commit ancestry, and workflow counts are rechecked."
        ),
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail when checked evidence differs from the measured report.",
    )
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args()


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"expected a JSON object: {path}")
    return payload


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _duration_seconds(started_at: str, completed_at: str) -> int:
    start = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
    end = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
    return int((end - start).total_seconds())


def _git(
    repo_root: Path,
    *args: str,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=check,
        capture_output=True,
        text=True,
    )


def _require_ancestor(repo_root: Path, ref: str) -> None:
    result = _git(
        repo_root,
        "merge-base",
        "--is-ancestor",
        ref,
        "HEAD",
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"{ref} is not an ancestor of {repo_root} HEAD")


def _workflow_paths_at(repo_root: Path, ref: str) -> tuple[str, ...]:
    result = _git(
        repo_root,
        "ls-tree",
        "-r",
        "--name-only",
        ref,
        ".github/workflows",
    )
    return tuple(
        path
        for path in result.stdout.splitlines()
        if path.endswith((".yml", ".yaml"))
    )


def _workflow_texts_at(repo_root: Path, ref: str) -> tuple[str, ...]:
    return tuple(
        _git(repo_root, "show", f"{ref}:{path}").stdout
        for path in _workflow_paths_at(repo_root, ref)
    )


def _current_workflow_texts(repo_root: Path) -> tuple[str, ...]:
    workflow_root = repo_root / ".github" / "workflows"
    paths = sorted(
        (
            *workflow_root.glob("*.yml"),
            *workflow_root.glob("*.yaml"),
        )
    )
    return tuple(path.read_text(encoding="utf-8") for path in paths)


def _checkout_actions(texts: tuple[str, ...]) -> int:
    return sum(text.count("repository: 8Dionysus/") for text in texts)


def _routing_checkouts(texts: tuple[str, ...]) -> int:
    return sum(
        text.count("repository: 8Dionysus/aoa-routing") for text in texts
    )


def _active_historical_probes(
    workflow_texts: tuple[str, ...],
    release_check: str,
) -> list[str]:
    active_text = "\n".join((*workflow_texts, release_check))
    return [probe for probe in HISTORICAL_PROBES if probe in active_text]


def _validate_routing_snapshot(
    routing_root: Path,
    observations: dict[str, Any],
) -> None:
    routing_root = routing_root.resolve()
    snapshot = observations["routing_m3"]
    _require_ancestor(routing_root, snapshot["source_ref"])
    evidence_path = (
        routing_root
        / "mechanics"
        / "release-support"
        / "parts"
        / "release-gate-routing"
        / "evidence"
        / "routing-succession-m3-maintenance-only.json"
    )
    if _sha256(evidence_path) != snapshot["evidence_sha256"]:
        raise RuntimeError("routing M3 evidence differs from the E1 pin")
    current_texts = _current_workflow_texts(routing_root)
    if len(current_texts) != snapshot["workflow_contours_after"]:
        raise RuntimeError("routing M3 workflow count differs from E1")
    if _checkout_actions(current_texts) != snapshot["checkout_actions_after"]:
        raise RuntimeError("routing M3 checkout count differs from E1")


def _validate_report(report: dict[str, Any]) -> None:
    schema = _read_json(SCHEMA_PATH)
    errors = sorted(
        Draft202012Validator(
            schema,
            format_checker=FormatChecker(),
        ).iter_errors(report),
        key=lambda error: list(error.path),
    )
    if errors:
        rendered = "; ".join(
            f"{'/'.join(str(part) for part in error.path) or '<root>'}: "
            f"{error.message}"
            for error in errors
        )
        raise RuntimeError(f"invalid E1 cost evidence: {rendered}")


def build_report(routing_root: Path | None = None) -> dict[str, Any]:
    baseline = _read_json(BASELINE_PATH)
    observations = _read_json(OBSERVATIONS_PATH)
    compiler_trial = _read_json(COMPILER_TRIAL_PATH)
    lifecycle_trial = _read_json(LIFECYCLE_TRIAL_PATH)
    g11_trial = _read_json(G11_TRIAL_PATH)

    pins = observations["pins"]
    _require_ancestor(REPO_ROOT, pins["sdk_post_m3_ref"])
    if routing_root is not None:
        _validate_routing_snapshot(routing_root, observations)

    sdk_before = _workflow_texts_at(REPO_ROOT, pins["sdk_before_m3_ref"])
    sdk_after = _workflow_texts_at(REPO_ROOT, pins["sdk_post_m3_ref"])
    release_before = _git(
        REPO_ROOT,
        "show",
        f"{pins['sdk_before_m3_ref']}:scripts/release_check.py",
    ).stdout
    release_after = _git(
        REPO_ROOT,
        "show",
        f"{pins['sdk_post_m3_ref']}:scripts/release_check.py",
    ).stdout
    routing_m3 = observations["routing_m3"]
    baseline_cost = baseline["cost_baseline"]

    sdk_before_checkouts = _checkout_actions(sdk_before)
    sdk_after_checkouts = _checkout_actions(sdk_after)
    routing_before_checkouts = routing_m3["checkout_actions_before"]
    routing_after_checkouts = routing_m3["checkout_actions_after"]
    checkout_before = sdk_before_checkouts + routing_before_checkouts
    checkout_after = sdk_after_checkouts + routing_after_checkouts
    contexts = observations["process_observations"]["repository_contexts"]
    legacy_route = observations["process_observations"]["legacy_advisory_route"]
    clean_chain = observations["process_observations"]["clean_federation_chain"]
    post_ci = observations["post_landing_ci"]
    old_agent = baseline_cost["agent_process_baseline"]
    g11_runs = g11_trial["runs"]

    for run in post_ci["runs"]:
        _require_ancestor(REPO_ROOT, run["head_sha"])
        if run["conclusion"] != "success":
            raise RuntimeError("post-landing E1 CI sample contains a failed run")
        if run["runner_seconds"] != _duration_seconds(
            run["job_started_at"],
            run["job_completed_at"],
        ):
            raise RuntimeError("post-landing E1 runner duration is inconsistent")
        if run["lead_time_seconds"] != _duration_seconds(
            run["created_at"],
            run["updated_at"],
        ):
            raise RuntimeError("post-landing E1 lead time is inconsistent")

    runner_seconds = [run["runner_seconds"] for run in post_ci["runs"]]
    lead_time_seconds = [run["lead_time_seconds"] for run in post_ci["runs"]]
    sdk_baseline = next(
        item
        for item in baseline_cost["workflow_metrics"]
        if item["repo"] == "aoa-sdk" and item["workflow"] == "Repo Validation"
    )
    routing_baseline = next(
        item
        for item in baseline_cost["workflow_metrics"]
        if (
            item["repo"] == "aoa-routing"
            and item["workflow"] == "Repo Validation"
        )
    )
    paired_baseline_seconds = (
        sdk_baseline["successful_median_seconds"]
        + routing_baseline["successful_median_seconds"]
    )
    post_runner_median = median(runner_seconds)
    post_lead_median = median(lead_time_seconds)
    runner_delta = post_runner_median - paired_baseline_seconds
    runner_regression_fraction = round(
        runner_delta / paired_baseline_seconds,
        3,
    )
    expected_sample = post_ci["sample"]
    if expected_sample != {
        "run_count": len(post_ci["runs"]),
        "all_success": True,
        "runner_seconds": runner_seconds,
        "lead_time_seconds": lead_time_seconds,
        "median_runner_seconds": post_runner_median,
        "median_lead_time_seconds": post_lead_median,
        "runner_seconds_delta_from_paired_baseline": runner_delta,
        "runner_time_regression_fraction": runner_regression_fraction,
    }:
        raise RuntimeError("post-landing E1 CI sample summary is inconsistent")
    if post_ci["baseline"] != {
        "sdk_successful_median_runner_seconds": sdk_baseline[
            "successful_median_seconds"
        ],
        "predecessor_successful_median_runner_seconds": routing_baseline[
            "successful_median_seconds"
        ],
        "paired_successful_validation_runner_seconds": paired_baseline_seconds,
    }:
        raise RuntimeError("post-landing E1 CI baseline summary is inconsistent")

    report: dict[str, Any] = {
        "schema_version": "aoa_sdk_routing_succession_e1_cost_comparison_v2",
        "observed_on": observations["observed_on"],
        "status": "complete_mixed_verdict",
        "scope": {
            "comparison": (
                "R0 predecessor contour to landed SDK control-plane contour"
            ),
            "sdk_before_m3_ref": pins["sdk_before_m3_ref"],
            "sdk_post_m3_ref": pins["sdk_post_m3_ref"],
            "sdk_post_landing_observation_through_ref": post_ci["runs"][-1][
                "head_sha"
            ],
            "routing_before_m3_ref": routing_m3["baseline_ref"],
            "routing_post_m3_ref": routing_m3["source_ref"],
            "r0_evidence_sha256": _sha256(BASELINE_PATH),
            "routing_m3_evidence_sha256": routing_m3["evidence_sha256"],
            "comparison_rule": old_agent["comparison_rule"],
        },
        "repository_and_ci_cost": {
            "canonical_routing_producers": {
                "before": baseline_cost["canonical_routing_producers"],
                "after": 1,
            },
            "active_producer_control_planes": {
                "before": baseline_cost["active_repository_control_planes"],
                "after": 1,
            },
            "physical_producer_implementations": {
                "before": 1,
                "shadow_peak": 2,
                "after": 2,
                "active_after": 1,
                "retained_after": "predecessor rollback implementation",
            },
            "workflow_files_in_comparison_family": {
                "before": len(sdk_before)
                + routing_m3["workflow_contours_before"],
                "after": len(sdk_after)
                + routing_m3["workflow_contours_after"],
            },
            "routing_related_workflow_contours": {
                "before": baseline_cost["routing_related_workflow_contours"],
                "after": observations["routing_related_workflows_after"],
            },
            "checkout_actions": {
                "before": checkout_before,
                "after": checkout_after,
                "removed": checkout_before - checkout_after,
                "reduction_fraction": round(
                    (checkout_before - checkout_after) / checkout_before,
                    3,
                ),
                "sdk_before": sdk_before_checkouts,
                "sdk_after": sdk_after_checkouts,
                "predecessor_before": routing_before_checkouts,
                "predecessor_after": routing_after_checkouts,
            },
            "sdk_direct_predecessor_checkouts": {
                "before": _routing_checkouts(sdk_before),
                "after": _routing_checkouts(sdk_after),
            },
            "paired_release_streams": {
                "before": baseline_cost["paired_release_streams"],
                "after": 1,
            },
            "active_historical_release_probes": {
                "before": _active_historical_probes(
                    sdk_before,
                    release_before,
                ),
                "after": _active_historical_probes(
                    sdk_after,
                    release_after,
                ),
            },
            "sdk_requires_predecessor_workspace_repo": {
                "before": True,
                "after": False,
            },
            "historical_runner_sample": {
                "runs": baseline_cost["measured_run_sample_count"],
                "runner_minutes": baseline_cost["measured_runner_minutes"],
                "failed_runs": baseline_cost["measured_failed_runs"],
                "failure_rate": baseline_cost["measured_failure_rate"],
                "post_landing_comparable_sample_available": True,
            },
            "post_landing_runner_sample": {
                "observation_class": post_ci["observation_class"],
                "workflow": post_ci["workflow"],
                "event": post_ci["event"],
                "branch": post_ci["branch"],
                "runs": post_ci["runs"],
                "run_count": len(post_ci["runs"]),
                "all_success": True,
                "median_runner_seconds": post_runner_median,
                "median_lead_time_seconds": post_lead_median,
                "paired_predecessor_median_runner_seconds": (
                    paired_baseline_seconds
                ),
                "runner_seconds_delta_from_paired_baseline": runner_delta,
                "runner_time_regression_fraction": runner_regression_fraction,
                "failure_rate_reduction_claimable": post_ci[
                    "failure_rate_reduction_claimable"
                ],
                "growth_sources": post_ci["growth_sources"],
                "claim_limit": post_ci["claim_limit"],
            },
        },
        "agent_process_cost": {
            "scenarios": clean_chain["verified_scenarios"],
            "old_contour": {
                "free_text_intent_to_route_decision": old_agent[
                    "free_text_intent_to_route_decision"
                ],
                "route_decision_to_run_plan": old_agent[
                    "route_decision_to_run_plan"
                ],
                "run_plan_to_session_handle": old_agent[
                    "run_plan_to_session_handle"
                ],
                "session_handle_to_closeout": old_agent[
                    "session_handle_to_closeout"
                ],
                "compile_ready_scenarios": 0,
                "smallest_observed_route": legacy_route,
                "manual_transformations_lower_bound": 1,
                "artifact_maintenance_repository_contexts": old_agent[
                    "artifact_maintenance_context_lower_bound"
                ],
            },
            "new_contour": {
                "compile_ready_scenarios": len(
                    clean_chain["verified_scenarios"]
                ),
                "compile_ready_scenario_count": len(
                    clean_chain["verified_scenarios"]
                ),
                "clean_federation_repository_contexts": contexts[
                    "new_clean_federation"
                ],
                "predecessor_checkout_present": compiler_trial[
                    "pinned_inputs"
                ]["aoa_routing_checkout_present"],
                "minimum_public_transformations_per_compile_scenario": [
                    "scenario_ref",
                    "resolve",
                    "bind_scenario",
                    "compile",
                ],
                "manual_json_transformations_after_typed_input": 0,
                "clean_federation_benchmark": clean_chain,
                "compiler_repeat_observations": compiler_trial[
                    "child_observation"
                ]["successful_chain_observation_count"],
                "isolated_lifecycle_terminal_state": lifecycle_trial[
                    "lifecycle"
                ]["terminal_state"],
                "isolated_lifecycle_event_count": lifecycle_trial[
                    "lifecycle"
                ]["event_count"],
                "g11_golden_case_count": g11_trial["terminal_posture"][
                    "golden_case_count"
                ],
                "g11_adversarial_category_count": g11_trial[
                    "terminal_posture"
                ]["adversarial_category_count"],
                "g11_sdk_cases_passed": g11_runs["sdk_suite"]["passed"],
                "g11_runtime_owner_cases_passed": g11_runs[
                    "runtime_owner_suite"
                ]["passed"],
            },
            "repository_context_reduction": {
                "old_lower_bound": contexts["old_lower_bound"],
                "old_upper_bound": contexts["old_upper_bound"],
                "new": contexts["new_clean_federation"],
                "reduction_from_lower_bound_fraction": round(
                    (
                        contexts["old_lower_bound"]
                        - contexts["new_clean_federation"]
                    )
                    / contexts["old_lower_bound"],
                    3,
                ),
                "reduction_from_upper_bound_fraction": round(
                    (
                        contexts["old_upper_bound"]
                        - contexts["new_clean_federation"]
                    )
                    / contexts["old_upper_bound"],
                    3,
                ),
            },
            "telemetry_limits": {
                "model_tokens": "unavailable in both contours",
                "agent_tool_calls": (
                    "not recorded by the retained old or T1 receipts"
                ),
                "process_calls": (
                    "legacy HTTP call and SDK public transformations counted"
                ),
                "serialized_bytes": (
                    "observed but not compared as token cost because outputs "
                    "have different contracts"
                ),
                "direct_latency_comparison_valid": False,
                "reason": (
                    "the legacy sample returns advisory references while the "
                    "new sample verifies three typed route-bind-compile chains"
                ),
            },
        },
        "quality_and_stop_lines": {
            "new_chain_all_benchmark_runs_passed": clean_chain["all_passed"],
            "new_chain_scenarios_verified": len(
                clean_chain["verified_scenarios"]
            ),
            "g11_complete_to_rightful_stop_boundary": g11_trial[
                "terminal_posture"
            ]["complete_to_rightful_stop_boundary"],
            "central_aoa_evals_verdict_claimed": False,
            "structural_process_cost_reduction_claimed": True,
            "direct_ci_runner_time_reduction_claimed": False,
            "task_latency_reduction_claimed": False,
            "post_landing_ci_failure_rate_reduction_claimed": False,
            "assurance_removed_to_reduce_ci_time": False,
            "consumer_zero_claimed": False,
            "rollback_retired_claimed": False,
            "archive_ready_claimed": False,
            "archive_authorized_claimed": False,
        },
        "verdict": {
            "structural_process_cost_reduced": True,
            "direct_ci_runner_time_reduced": False,
            "direct_ci_runner_time_regression_fraction": (
                runner_regression_fraction
            ),
            "typed_agent_process_capability_increased": True,
            "bounded_no_regression_signal": True,
            "g13_gate": "pass_with_ci_runner_time_regression",
            "growth_source": (
                "The 23.1% runner-time increase is attributable to the "
                "portable multi-owner KAG audit and expanded package, trust, "
                "routing, planning, lifecycle, and runtime-adapter gates; "
                "duplicate producer scaffolding did not return."
            ),
            "claim_limit": (
                "E1 proves structural checkout, workflow, release, context, "
                "and supported-process improvement, while reporting a 23.1% "
                "median CI runner-time regression. It does not prove direct "
                "task latency or token reduction, a long-run CI failure-rate "
                "improvement, a central eval verdict, consumer-zero, rollback "
                "retirement, archive readiness, or archive authority."
            ),
        },
    }
    _validate_report(report)
    return report


def main() -> int:
    args = parse_args()
    report = build_report(args.routing_root)
    if args.check:
        checked = _read_json(EVIDENCE_PATH)
        if checked != report:
            raise SystemExit("checked E1 evidence differs from measured report")
        print(
            json.dumps(
                {
                    "status": report["status"],
                    "verdict": report["verdict"]["g13_gate"],
                    "evidence_current": True,
                },
                sort_keys=True,
            )
        )
        return 0
    print(
        json.dumps(
            report,
            indent=2 if args.pretty else None,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
