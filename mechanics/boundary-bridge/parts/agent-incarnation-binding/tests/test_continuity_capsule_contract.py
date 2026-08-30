from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from aoa_sdk.contracts.control_plane import (
    ContinuityCapsuleRef,
    ResumeCommand,
    RunPlan,
    assert_run_plan_digest,
    canonical_digest,
)
from aoa_sdk.control_plane.runner import AoARunner
from aoa_sdk.control_plane.runner.core import _assert_command_scope


PLAN_PATH = (
    Path(__file__).resolve().parents[5]
    / "mechanics"
    / "boundary-bridge"
    / "parts"
    / "plan-compilation-control-plane"
    / "examples"
    / "bounded-preview-pruned.run-plan.json"
)


def _plan_with_capsule() -> tuple[RunPlan, ContinuityCapsuleRef]:
    original = RunPlan.model_validate_json(PLAN_PATH.read_text(encoding="utf-8"))
    capsule_ref = ContinuityCapsuleRef(
        object_id="continuity-capsule:goal-d3-case-001",
        digest="sha256:" + "1" * 64,
    )
    plan = original.model_copy(
        update={
            "continuity_capsule_ref": capsule_ref,
            "plan_digest": "sha256:" + "0" * 64,
        }
    )
    plan = plan.model_copy(
        update={"plan_digest": canonical_digest(plan, exclude={"plan_digest"})}
    )
    return plan, capsule_ref


def test_capsule_reference_is_optional_and_exactly_carried_by_session() -> None:
    legacy_plan = RunPlan.model_validate_json(PLAN_PATH.read_text(encoding="utf-8"))
    assert legacy_plan.continuity_capsule_ref is None

    plan, capsule_ref = _plan_with_capsule()
    assert_run_plan_digest(plan)
    session = AoARunner().prepare(plan)

    assert session.continuity_capsule_ref == capsule_ref
    assert session.plan_digest == plan.plan_digest


def test_resume_command_must_match_the_plan_capsule_reference() -> None:
    plan, capsule_ref = _plan_with_capsule()
    runner = AoARunner()
    session = runner.prepare(plan)
    wrong_ref = capsule_ref.model_copy(update={"digest": "sha256:" + "2" * 64})
    command = ResumeCommand(
        command_id="resume:wrong-capsule",
        idempotency_key="resume:wrong-capsule",
        session_id=session.session_id,
        correlation_id=session.correlation_id,
        plan_digest=plan.plan_digest,
        continuity_capsule_ref=wrong_ref,
        expected_revision=0,
        issued_at=datetime.now(timezone.utc),
        issued_by=plan.provenance,
        reason="resume exact continuation",
        resume_after_sequence=-1,
    )

    record = runner._sessions[session.session_id]

    with pytest.raises(ValueError, match="outside the session"):
        _assert_command_scope(record, command)
