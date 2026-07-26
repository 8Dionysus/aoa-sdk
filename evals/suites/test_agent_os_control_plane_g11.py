"""Run the exact aoa-sdk cases that constrain the local G11 claim."""

from __future__ import annotations

import subprocess
import sys

import pytest


CASES = (
    (
        "golden-plan-repeatability",
        "mechanics/boundary-bridge/parts/plan-compilation-control-plane/"
        "tests/test_plan_compilation_control_plane.py::"
        "test_compile_is_repeatable_and_preserves_owner_typed_inputs",
    ),
    (
        "golden-runner-lifecycle",
        "mechanics/boundary-bridge/parts/runner-lifecycle-control-plane/"
        "tests/test_runner_lifecycle_control_plane.py::"
        "test_normal_completion_and_evidence_complete_closeout",
    ),
    (
        "missing-capability",
        "mechanics/boundary-bridge/parts/route-resolution-control-plane/"
        "tests/test_route_resolution_control_plane.py::"
        "test_required_capability_is_a_hard_constraint",
    ),
    (
        "ambiguous-intent",
        "mechanics/boundary-bridge/parts/route-resolution-control-plane/"
        "tests/test_route_resolution_control_plane.py::"
        "test_equal_top_scores_block_without_lexical_fallback",
    ),
    (
        "conflicting-routes",
        "mechanics/boundary-bridge/parts/route-resolution-control-plane/"
        "tests/test_route_resolution_control_plane.py::"
        "test_conflicting_effect_ceilings_block_deterministically",
    ),
    (
        "forbidden-action",
        "mechanics/boundary-bridge/parts/route-resolution-control-plane/"
        "tests/test_route_resolution_control_plane.py::"
        "test_blank_owner_effect_is_forbidden_without_an_effect_ceiling",
    ),
    (
        "runtime-approval-owner",
        "mechanics/boundary-bridge/parts/plan-compilation-control-plane/"
        "tests/test_plan_compilation_control_plane.py::"
        "test_runtime_profile_rejects_an_approval_from_another_owner",
    ),
    (
        "runtime-approval-id-collision",
        "mechanics/boundary-bridge/parts/plan-compilation-control-plane/"
        "tests/test_plan_compilation_control_plane.py::"
        "test_runtime_profile_cannot_shadow_a_route_approval_id",
    ),
    (
        "multiple-approval-reconciliation",
        "mechanics/boundary-bridge/parts/runner-lifecycle-control-plane/"
        "tests/test_runner_lifecycle_control_plane.py::"
        "test_multiple_approvals_reconcile_one_decision_at_a_time",
    ),
    (
        "stale-route-snapshot",
        "mechanics/boundary-bridge/parts/runner-lifecycle-control-plane/"
        "tests/test_runner_lifecycle_control_plane.py::"
        "test_snapshot_drift_blocks_before_dispatch",
    ),
    (
        "stale-runtime-observation",
        "mechanics/boundary-bridge/parts/runner-lifecycle-control-plane/"
        "tests/test_runner_lifecycle_control_plane.py::"
        "test_stale_runtime_observation_blocks_before_dispatch",
    ),
    (
        "missing-event-slice",
        "mechanics/boundary-bridge/parts/runner-lifecycle-control-plane/"
        "tests/test_runner_lifecycle_control_plane.py::"
        "test_restore_rejects_a_receipt_without_its_verified_event_slice",
    ),
    (
        "reordered-event-slice",
        "mechanics/boundary-bridge/parts/runner-lifecycle-control-plane/"
        "tests/test_runner_lifecycle_control_plane.py::"
        "test_restore_rejects_reordered_durable_receipt_slices",
    ),
    (
        "invalid-runtime-event",
        "mechanics/boundary-bridge/parts/runner-lifecycle-control-plane/"
        "tests/test_runner_lifecycle_control_plane.py::"
        "test_out_of_order_or_invalid_runtime_event_fails_closed",
    ),
    (
        "duplicate-execution",
        "mechanics/boundary-bridge/parts/runner-lifecycle-control-plane/"
        "tests/test_runner_lifecycle_control_plane.py::"
        "test_duplicate_start_and_approval_create_no_new_effect",
    ),
    (
        "runtime-disconnect",
        "mechanics/boundary-bridge/parts/runner-lifecycle-control-plane/"
        "tests/test_runner_lifecycle_control_plane.py::"
        "test_disconnect_after_ack_reconciles_to_recoverable_failure",
    ),
)


@pytest.mark.parametrize(("case_id", "node_id"), CASES, ids=[case[0] for case in CASES])
def test_g11_case(case_id: str, node_id: str) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            node_id,
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert completed.returncode == 0, (
        f"{case_id} failed with exit {completed.returncode}\n"
        f"stdout:\n{completed.stdout}\n"
        f"stderr:\n{completed.stderr}"
    )
