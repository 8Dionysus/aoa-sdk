from aoa_sdk.a2a.rebase import (
    ProgressionOverlay,
    QuestPassport,
    SummonIntent,
    assess_summon,
)


def test_codex_local_leaf_is_default_for_bounded_local_work() -> None:
    passport = QuestPassport(
        difficulty="d1_patch",
        risk="r1_repo_local",
        control_mode="codex_supervised",
        delegate_tier="executor",
        wrapper_class="codex_primary",
        route_anchor="bounded_plan",
        expected_artifacts=["work_result"],
    )
    intent = SummonIntent(
        desired_role="coder",
        expected_outputs=["work_result"],
        transport_preference="codex_local",
    )

    decision = assess_summon(passport, intent)

    assert decision.allowed is True
    assert decision.lane == "codex_local_leaf"
    assert decision.execution_surface == "codex_local"
    assert decision.codex_projection_required is True


def test_progression_gate_blocks_when_required_overlay_is_missing() -> None:
    passport = QuestPassport(
        difficulty="d2_slice",
        risk="r1_repo_local",
        control_mode="codex_supervised",
        delegate_tier="executor",
        route_anchor="bounded_plan",
        expected_artifacts=["verification_result"],
    )
    intent = SummonIntent(
        desired_role="reviewer",
        expected_outputs=["verification_result"],
        require_progression=True,
    )

    decision = assess_summon(passport, intent)

    assert decision.allowed is False
    assert decision.progression_required is True
    assert "missing_progression_overlay" in decision.reason_codes


def test_progression_gate_passes_with_unlocks() -> None:
    passport = QuestPassport(
        difficulty="d2_slice",
        risk="r1_repo_local",
        control_mode="codex_supervised",
        delegate_tier="executor",
        route_anchor="bounded_plan",
        expected_artifacts=["verification_result"],
    )
    intent = SummonIntent(
        desired_role="reviewer",
        expected_outputs=["verification_result"],
        require_progression=True,
    )
    progression = ProgressionOverlay(
        agent_id="reviewer",
        unlocked_difficulties=["d0_probe", "d1_patch", "d2_slice"],
        unlocked_risks=["r0_readonly", "r1_repo_local"],
        unlocked_cohorts=["solo", "pair"],
    )

    decision = assess_summon(passport, intent, progression=progression)

    assert decision.allowed is True
    assert (
        decision.lane == "codex_local_leaf" or decision.lane == "codex_local_reviewed"
    )
