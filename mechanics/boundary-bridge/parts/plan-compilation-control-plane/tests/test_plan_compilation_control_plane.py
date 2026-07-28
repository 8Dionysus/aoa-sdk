from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
from pathlib import Path
from types import ModuleType

import pytest
from typer.testing import CliRunner

from aoa_sdk import AoASDK
from aoa_sdk.cli.main import app
from aoa_sdk.contracts.control_plane import (
    ProvenanceRef,
    RouteDecision,
    RunPlan,
    RuntimeProfile,
    ScenarioArtifactBinding,
    ScenarioBinding,
    ScenarioCapabilityBinding,
    assert_run_plan_digest,
    canonical_digest,
)
from aoa_sdk.control_plane.planning import (
    PlanCompilationError,
    PlanCompilationSnapshotError,
    compile_run_plan,
    load_plan_compilation_snapshot,
)


REPO_ROOT = Path(__file__).resolve().parents[5]
PART_ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = PART_ROOT / "scripts" / "generate_plan_compilation_examples.py"
PIN_GENERATOR_PATH = PART_ROOT / "scripts" / "pin_playbook_plan_contours.py"
DATA_ROOT = REPO_ROOT / "src" / "aoa_sdk" / "control_plane" / "planning" / "data"
ZERO_DIGEST = "sha256:" + "0" * 64


def _load_generator() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "plan_compilation_example_generator",
        GENERATOR_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load plan compilation example generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_pin_generator() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "plan_contour_pin_generator",
        PIN_GENERATOR_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load plan-contour pin generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _compiler_provenance() -> ProvenanceRef:
    return ProvenanceRef(
        owner_repo="aoa-sdk",
        artifact_ref="src/aoa_sdk/control_plane/planning/compiler.py",
        source_ref="fixture-source-ref",
        artifact_digest=ZERO_DIGEST,
        schema_ref="schemas/fixture.schema.json",
        schema_version="fixture-v1",
    )


def _inputs(
    scenario_id: str,
    conditions: dict[str, bool],
):
    return _load_generator()._fixture_inputs(scenario_id, conditions)


def test_snapshot_pins_exact_admitted_owner_projection() -> None:
    snapshot = load_plan_compilation_snapshot()

    assert (
        snapshot.source_lock.owner_source_ref
        == "056cac249a353ae94abedbd4048e6730f70c064d"
    )
    assert snapshot.source_lock.trust_admission.verdict == "allow"
    assert (
        snapshot.source_lock.trust_admission.record_id
        == snapshot.source_lock.trust_admission.latest_record_id
    )
    assert (
        snapshot.admission_provenance.source_ref
        == snapshot.source_lock.trust_admission.record_id
    )
    assert (
        snapshot.admission_provenance.artifact_digest
        == snapshot.source_lock.trust_admission.record_artifact_digest
    )
    assert (
        snapshot.admission_provenance.artifact_digest
        != snapshot.admission_provenance.source_ref
    )
    assert snapshot.source_lock.trust_admission.subject_store_ok is True
    assert {
        "abi_signature",
        "slsa_in_toto",
    }.issubset(snapshot.source_lock.trust_admission.verified_controls)
    assert snapshot.contour_abi.owner_repo == "aoa-playbooks"
    assert snapshot.contour_abi.abi_id == "aoa_playbook_plan_contour_v1"
    assert [contour.scenario for contour in snapshot.contours] == [
        "bounded_change_safe",
        "a2a_summon_return_checkpoint",
        "runtime_chaos_recovery",
    ]


def test_pin_reader_rejects_escape_and_symlink_inputs(tmp_path: Path) -> None:
    generator = _load_pin_generator()
    owner_root = tmp_path / "owner"
    owner_root.mkdir()
    nested = owner_root / "generated"
    nested.mkdir()
    source = nested / "contours.json"
    source.write_text("{}\n", encoding="utf-8")

    assert (
        generator._read_bounded_regular_file(
            owner_root,
            "generated/contours.json",
            "fixture contours",
        )
        == b"{}\n"
    )
    with pytest.raises(generator.PinError, match="bounded relative"):
        generator._read_bounded_regular_file(
            owner_root,
            "../outside.json",
            "fixture contours",
        )

    outside = tmp_path / "outside.json"
    outside.write_text("{}\n", encoding="utf-8")
    linked = nested / "linked.json"
    linked.symlink_to(outside)
    with pytest.raises(generator.PinError, match="symlink"):
        generator._read_bounded_regular_file(
            owner_root,
            "generated/linked.json",
            "fixture contours",
        )


def test_three_golden_branch_fixtures_match_deterministic_rebuild() -> None:
    generator = _load_generator()
    outputs = generator.build_examples()

    assert len(outputs) == 3
    for path, expected in outputs.items():
        assert path.read_bytes() == expected
        plan = RunPlan.model_validate_json(expected)
        assert_run_plan_digest(plan)

    bounded = RunPlan.model_validate_json(
        (PART_ROOT / "examples" / "bounded-preview-pruned.run-plan.json").read_bytes()
    )
    assert [step.step_id for step in bounded.steps] == [
        "orient",
        "mutate",
        "verify",
        "closeout",
    ]
    assert bounded.steps[1].depends_on == ()

    a2a = RunPlan.model_validate_json(
        (PART_ROOT / "examples" / "a2a-eval-only.run-plan.json").read_bytes()
    )
    assert "evaluate-return" in {step.step_id for step in a2a.steps}
    assert "retain-return" not in {step.step_id for step in a2a.steps}
    assert a2a.steps[-1].depends_on == (
        "checkpoint-return",
        "evaluate-return",
    )

    runtime = RunPlan.model_validate_json(
        (
            PART_ROOT / "examples" / "runtime-proof-without-reground.run-plan.json"
        ).read_bytes()
    )
    assert "reground-source" not in {step.step_id for step in runtime.steps}
    assert "evaluate-reentry" in {step.step_id for step in runtime.steps}
    evaluate = next(
        step for step in runtime.steps if step.step_id == "evaluate-reentry"
    )
    assert evaluate.depends_on == ("validate-degraded-lane",)


def test_installed_wheel_smoke_inputs_reproduce_bounded_golden() -> None:
    generator = _load_generator()
    fixture_path = PART_ROOT / "examples" / "installed-wheel-smoke.inputs.json"

    assert fixture_path.read_bytes() == generator.build_wheel_smoke_fixture()
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    snapshot = load_plan_compilation_snapshot()
    plan = compile_run_plan(
        RouteDecision.model_validate(fixture["decision"]),
        ScenarioBinding.model_validate(fixture["scenario_binding"]),
        RuntimeProfile.model_validate(fixture["runtime_profile"]),
        snapshot,
        compiler_provenance=ProvenanceRef.model_validate(
            fixture["compiler_provenance"]
        ),
    )
    expected = RunPlan.model_validate_json(
        (PART_ROOT / "examples" / fixture["expected_plan"]).read_bytes()
    )

    assert plan == expected
    assert_run_plan_digest(plan)


def test_compile_is_repeatable_and_preserves_owner_typed_inputs() -> None:
    snapshot = load_plan_compilation_snapshot()
    decision, binding, runtime = _inputs(
        "a2a_summon_return_checkpoint",
        {
            "a2a_eval_packet_earned": True,
            "memo_writeback_earned": True,
        },
    )

    first = compile_run_plan(
        decision,
        binding,
        runtime,
        snapshot,
        compiler_provenance=_compiler_provenance(),
    )
    second = compile_run_plan(
        decision,
        binding,
        runtime,
        snapshot,
        compiler_provenance=_compiler_provenance(),
    )

    assert first == second
    assert first.model_dump_json() == second.model_dump_json()
    target = next(
        step for step in first.steps if step.step_id == "inspect-child-target"
    )
    assert [item.artifact_ref for item in target.input_refs] == [
        "artifacts/summon_request.json",
        "artifacts/summon_decision.json",
    ]
    review = next(step for step in first.steps if step.step_id == "review-return")
    assert [item.artifact_ref for item in review.input_refs] == [
        "artifacts/child_task_result.json"
    ]
    approval_ids = {
        requirement.requirement_id for requirement in first.approval_requirements
    }
    assert target.approval_requirement_ids == tuple(approval_ids)
    assert first.snapshot.abi_refs == (snapshot.contour_abi,)
    assert snapshot.admission_provenance in first.snapshot.source_refs


def test_public_api_compiles_without_loading_the_routing_snapshot() -> None:
    decision, binding, runtime = _inputs(
        "bounded_change_safe",
        {"preview_required": False},
    )
    sdk = AoASDK.from_workspace(REPO_ROOT)

    first = sdk.control_plane.compile(decision, binding, runtime)
    second = sdk.control_plane.compile(decision, binding, runtime)

    assert first == second
    assert [step.step_id for step in first.steps] == [
        "orient",
        "mutate",
        "verify",
        "closeout",
    ]


def test_explicit_route_approval_step_bindings_are_preserved() -> None:
    decision, binding, runtime = _inputs(
        "bounded_change_safe",
        {"preview_required": False},
    )
    unscoped = decision.approval_requirements[0]
    explicit = unscoped.model_copy(
        update={
            "requirement_id": "approval:fixture:verify",
            "operation": "verify",
            "applies_to_step_ids": ("verify",),
        }
    )
    decision = decision.model_copy(
        update={"approval_requirements": (unscoped, explicit)}
    )
    binding = binding.model_copy(
        update={
            "decision_ref": binding.decision_ref.model_copy(
                update={"digest": canonical_digest(decision)}
            )
        }
    )

    plan = compile_run_plan(
        decision,
        binding,
        runtime,
        load_plan_compilation_snapshot(),
        compiler_provenance=_compiler_provenance(),
    )

    steps = {step.step_id: step for step in plan.steps}
    assert steps["mutate"].approval_requirement_ids == (
        unscoped.requirement_id,
    )
    assert steps["verify"].approval_requirement_ids == (
        explicit.requirement_id,
    )

    contradictory = plan.model_dump(mode="json")
    contradictory["steps"][1]["approval_requirement_ids"].append(
        explicit.requirement_id
    )
    with pytest.raises(ValueError, match="explicit step bindings"):
        RunPlan.model_validate(contradictory)


def test_runtime_profile_approval_projection_is_bound_without_rewriting_route() -> None:
    decision, binding, runtime = _inputs(
        "bounded_change_safe",
        {"preview_required": False},
    )
    route_requirement = decision.approval_requirements[0]
    runtime_requirement = route_requirement.model_copy(
        update={
            "requirement_id": "approval:abyss-stack:landing",
            "approval_owner": runtime.provenance,
            "operation": "abyss-stack:governed-execution:landing",
            "risk_class": "repo_mutation",
            "applies_to_step_ids": ("mutate",),
        }
    )
    runtime = runtime.model_copy(
        update={
            "runtime_approval_requirements": (runtime_requirement,),
        }
    )

    plan = compile_run_plan(
        decision,
        binding,
        runtime,
        load_plan_compilation_snapshot(),
        compiler_provenance=_compiler_provenance(),
    )

    assert plan.decision_ref.digest == canonical_digest(decision)
    assert plan.approval_requirements == (
        route_requirement,
        runtime_requirement,
    )
    mutate = next(step for step in plan.steps if step.step_id == "mutate")
    assert mutate.approval_requirement_ids == (
        route_requirement.requirement_id,
        runtime_requirement.requirement_id,
    )
    assert runtime_requirement.approval_owner in plan.snapshot.source_refs


def test_runtime_profile_rejects_an_approval_from_another_owner() -> None:
    decision, _, runtime = _inputs(
        "bounded_change_safe",
        {"preview_required": False},
    )
    foreign_requirement = decision.approval_requirements[0].model_copy(
        update={
            "approval_owner": runtime.provenance.model_copy(
                update={"owner_repo": "foreign-runtime-owner"}
            )
        }
    )
    payload = runtime.model_dump(mode="python")
    payload["runtime_approval_requirements"] = [
        foreign_requirement.model_dump(mode="python")
    ]

    with pytest.raises(
        ValueError,
        match="must retain runtime-owner provenance",
    ):
        RuntimeProfile.model_validate(payload)


def test_runtime_profile_cannot_shadow_a_route_approval_id() -> None:
    decision, binding, runtime = _inputs(
        "bounded_change_safe",
        {"preview_required": False},
    )
    route_requirement = decision.approval_requirements[0]
    runtime_requirement = route_requirement.model_copy(
        update={"approval_owner": runtime.provenance}
    )
    runtime = runtime.model_copy(
        update={
            "runtime_approval_requirements": (runtime_requirement,),
        }
    )

    with pytest.raises(
        PlanCompilationError,
        match="route and runtime approval requirement ids must be unique",
    ):
        compile_run_plan(
            decision,
            binding,
            runtime,
            load_plan_compilation_snapshot(),
            compiler_provenance=_compiler_provenance(),
        )


@pytest.mark.parametrize(
    ("scenario_id", "conditions"),
    (
        ("bounded_change_safe", {"preview_required": True}),
        (
            "a2a_summon_return_checkpoint",
            {
                "a2a_eval_packet_earned": False,
                "memo_writeback_earned": False,
            },
        ),
        (
            "runtime_chaos_recovery",
            {
                "derived_surface_recovery_required": True,
                "proof_handoff_earned": False,
            },
        ),
    ),
)
def test_each_owner_contour_compiles(
    scenario_id: str,
    conditions: dict[str, bool],
) -> None:
    decision, binding, runtime = _inputs(scenario_id, conditions)
    plan = compile_run_plan(
        decision,
        binding,
        runtime,
        load_plan_compilation_snapshot(),
        compiler_provenance=_compiler_provenance(),
    )

    assert plan.scenario_binding.scenario.scenario_id == scenario_id
    assert plan.steps
    assert_run_plan_digest(plan)


def test_missing_or_extra_condition_bindings_fail_closed() -> None:
    decision, binding, runtime = _inputs(
        "a2a_summon_return_checkpoint",
        {
            "a2a_eval_packet_earned": True,
            "memo_writeback_earned": False,
        },
    )
    snapshot = load_plan_compilation_snapshot()

    with pytest.raises(PlanCompilationError, match="conditions must match"):
        compile_run_plan(
            decision,
            binding.model_copy(
                update={
                    "condition_bindings": binding.condition_bindings[:1],
                }
            ),
            runtime,
            snapshot,
        )
    extra = binding.condition_bindings[0].model_copy(
        update={"condition_id": "unreviewed-extra"}
    )
    with pytest.raises(PlanCompilationError, match="conditions must match"):
        compile_run_plan(
            decision,
            binding.model_copy(
                update={
                    "condition_bindings": (
                        *binding.condition_bindings,
                        extra,
                    )
                }
            ),
            runtime,
            snapshot,
        )


def test_typed_inputs_reject_positional_guessing_missing_and_extra_kinds() -> None:
    decision, binding, runtime = _inputs(
        "runtime_chaos_recovery",
        {
            "derived_surface_recovery_required": False,
            "proof_handoff_earned": False,
        },
    )
    snapshot = load_plan_compilation_snapshot()
    typed_ref = binding.input_artifact_bindings[0].artifact_ref

    with pytest.raises(
        PlanCompilationError,
        match="cannot also use generic",
    ):
        compile_run_plan(
            decision,
            binding.model_copy(
                update={
                    "input_refs": (typed_ref,),
                }
            ),
            runtime,
            snapshot,
        )
    with pytest.raises(PlanCompilationError, match="must match owner"):
        compile_run_plan(
            decision,
            binding.model_copy(update={"input_artifact_bindings": ()}),
            runtime,
            snapshot,
        )
    extra = ScenarioArtifactBinding(
        artifact_kind="unreviewed-extra",
        artifact_ref=typed_ref.model_copy(
            update={"artifact_ref": "artifacts/unreviewed-extra.json"}
        ),
    )
    with pytest.raises(PlanCompilationError, match="must match owner"):
        compile_run_plan(
            decision,
            binding.model_copy(
                update={
                    "input_artifact_bindings": (
                        *binding.input_artifact_bindings,
                        extra,
                    )
                }
            ),
            runtime,
            snapshot,
        )


def test_generic_contour_rejects_empty_or_typed_substitution() -> None:
    decision, binding, runtime = _inputs(
        "bounded_change_safe",
        {"preview_required": False},
    )
    snapshot = load_plan_compilation_snapshot()

    with pytest.raises(PlanCompilationError, match="at least one exact generic"):
        compile_run_plan(
            decision,
            binding.model_copy(update={"input_refs": ()}),
            runtime,
            snapshot,
        )
    typed = ScenarioArtifactBinding(
        artifact_kind="request",
        artifact_ref=binding.input_refs[0],
    )
    with pytest.raises(PlanCompilationError, match="cannot accept typed"):
        compile_run_plan(
            decision,
            binding.model_copy(update={"input_artifact_bindings": (typed,)}),
            runtime,
            snapshot,
        )


def test_blocked_decision_and_wrong_parent_binding_fail_closed() -> None:
    decision, binding, runtime = _inputs(
        "bounded_change_safe",
        {"preview_required": False},
    )
    snapshot = load_plan_compilation_snapshot()

    with pytest.raises(PlanCompilationError, match="blocked route"):
        compile_run_plan(
            decision.model_copy(
                update={"status": "blocked", "selected_candidate_id": None}
            ),
            binding,
            runtime,
            snapshot,
        )
    with pytest.raises(PlanCompilationError, match="exact route decision"):
        compile_run_plan(
            decision,
            binding.model_copy(
                update={
                    "decision_ref": binding.decision_ref.model_copy(
                        update={"digest": ZERO_DIGEST}
                    )
                }
            ),
            runtime,
            snapshot,
        )


def test_resolved_contour_capabilities_are_distinct_from_route_entry() -> None:
    decision, binding, runtime = _inputs(
        "bounded_change_safe",
        {"preview_required": False},
    )
    snapshot = load_plan_compilation_snapshot()
    resolved_bindings = tuple(
        ScenarioCapabilityBinding(
            requirement_id=capability.capability_id,
            capability=capability.model_copy(
                update={
                    "capability_id": (
                        "resolved." + capability.capability_id.removeprefix("aoa-")
                    )
                }
            ),
            semantic_owner_repo="fixture-owner",
            binding_action="migration-alias",
            compatibility="migration-alias",
            availability="available",
            lifecycle_state="active",
            lifecycle_health="healthy",
            migration_provenance=capability.provenance,
        )
        for capability in binding.capability_refs
    )
    selected = decision.candidates[0].model_copy(
        update={
            "capability": decision.candidates[0].capability.model_copy(
                update={"capability_id": "skill.route-entry"}
            ),
            "agent": binding.agent_refs[0].model_copy(
                update={"agent_id": "route-requester"}
            ),
        }
    )
    decision = decision.model_copy(update={"candidates": (selected,)})
    binding = binding.model_copy(
        update={
            "decision_ref": binding.decision_ref.model_copy(
                update={"digest": canonical_digest(decision)}
            ),
            "capability_refs": tuple(
                item.capability for item in resolved_bindings
            ),
            "capability_bindings": resolved_bindings,
        }
    )

    plan = compile_run_plan(decision, binding, runtime, snapshot)

    assert plan.steps
    assert all(
        capability.capability_id.startswith("resolved.")
        for step in plan.steps
        for capability in step.capability_refs
    )
    assert selected.capability not in plan.scenario_binding.capability_refs
    assert selected.agent not in plan.scenario_binding.agent_refs


def test_plan_compilation_requires_an_explicit_selected_scenario() -> None:
    decision, binding, runtime = _inputs(
        "bounded_change_safe",
        {"preview_required": False},
    )
    snapshot = load_plan_compilation_snapshot()
    selected = decision.candidates[0].model_copy(update={"scenario": None})
    decision = decision.model_copy(update={"candidates": (selected,)})
    binding = binding.model_copy(
        update={
            "decision_ref": binding.decision_ref.model_copy(
                update={"digest": canonical_digest(decision)}
            )
        }
    )

    with pytest.raises(
        PlanCompilationError,
        match="explicit selected scenario",
    ):
        compile_run_plan(decision, binding, runtime, snapshot)


def test_owner_identity_order_and_requirement_refs_fail_closed() -> None:
    decision, binding, runtime = _inputs(
        "runtime_chaos_recovery",
        {
            "derived_surface_recovery_required": False,
            "proof_handoff_earned": False,
        },
    )
    snapshot = load_plan_compilation_snapshot()

    with pytest.raises(PlanCompilationError, match="agents must match"):
        compile_run_plan(
            decision,
            binding.model_copy(
                update={"agent_refs": tuple(reversed(binding.agent_refs))}
            ),
            runtime,
            snapshot,
        )
    wrong_scenario = binding.scenario.model_copy(
        update={
            "provenance": binding.scenario.provenance.model_copy(
                update={"source_ref": "wrong-owner-source-ref"}
            )
        }
    )
    wrong_decision = decision.model_copy(
        update={
            "candidates": (
                decision.candidates[0].model_copy(update={"scenario": wrong_scenario}),
            )
        }
    )
    wrong_binding = binding.model_copy(
        update={
            "scenario": wrong_scenario,
            "decision_ref": binding.decision_ref.model_copy(
                update={"digest": canonical_digest(wrong_decision)}
            ),
        }
    )
    with pytest.raises(PlanCompilationError, match="exact admitted"):
        compile_run_plan(
            wrong_decision,
            wrong_binding,
            runtime,
            snapshot,
        )
    wrong_agents = list(binding.agent_refs)
    wrong_agents[-1] = wrong_agents[-1].model_copy(
        update={
            "provenance": wrong_agents[-1].provenance.model_copy(
                update={"owner_repo": "fixture-agent-copy"}
            )
        }
    )
    with pytest.raises(PlanCompilationError, match="owned by aoa-agents"):
        compile_run_plan(
            decision,
            binding.model_copy(update={"agent_refs": tuple(wrong_agents)}),
            runtime,
            snapshot,
        )
    wrong_capabilities = list(binding.capability_refs)
    wrong_capabilities[-1] = wrong_capabilities[-1].model_copy(
        update={
            "provenance": wrong_capabilities[-1].provenance.model_copy(
                update={"owner_repo": "fixture-capability-copy"}
            )
        }
    )
    with pytest.raises(PlanCompilationError, match="owned by aoa-skills"):
        compile_run_plan(
            decision,
            binding.model_copy(update={"capability_refs": tuple(wrong_capabilities)}),
            runtime,
            snapshot,
        )
    with pytest.raises(PlanCompilationError, match="cover owner contour"):
        compile_run_plan(
            decision,
            binding.model_copy(update={"requirement_refs": ()}),
            runtime,
            snapshot,
        )


def test_runtime_effect_support_is_checked_by_run_plan_contract() -> None:
    decision, binding, runtime = _inputs(
        "bounded_change_safe",
        {"preview_required": False},
    )

    with pytest.raises(ValueError, match="does not support effect class"):
        compile_run_plan(
            decision,
            binding,
            runtime.model_copy(update={"supported_effect_classes": ("read_only",)}),
            load_plan_compilation_snapshot(),
        )


def test_packaged_contour_or_lock_tampering_fails_closed(
    tmp_path: Path,
) -> None:
    resource_root = tmp_path / "data"
    shutil.copytree(DATA_ROOT, resource_root)
    contour_path = resource_root / "playbook-plan-contours.v1.json"
    contour_path.write_bytes(contour_path.read_bytes() + b" ")

    with pytest.raises(
        PlanCompilationSnapshotError,
        match="digest mismatch",
    ):
        load_plan_compilation_snapshot(resource_root=resource_root)

    shutil.rmtree(resource_root)
    shutil.copytree(DATA_ROOT, resource_root)
    lock_path = resource_root / "playbook-plan-contours-source-lock.v1.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    lock["trust_admission"]["latest_record_id"] = ZERO_DIGEST
    lock_path.write_text(
        json.dumps(lock, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(
        PlanCompilationSnapshotError,
        match="not the selected latest",
    ):
        load_plan_compilation_snapshot(resource_root=resource_root)

    shutil.rmtree(resource_root)
    shutil.copytree(DATA_ROOT, resource_root)
    lock_path = resource_root / "playbook-plan-contours-source-lock.v1.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    lock["abi"]["artifact_digest"] = ZERO_DIGEST
    lock_path.write_text(
        json.dumps(lock, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(
        PlanCompilationSnapshotError,
        match="ABI identity",
    ):
        load_plan_compilation_snapshot(resource_root=resource_root)

    shutil.rmtree(resource_root)
    shutil.copytree(DATA_ROOT, resource_root)
    contour_path = resource_root / "playbook-plan-contours.v1.json"
    contour = json.loads(contour_path.read_text(encoding="utf-8"))
    contour["contours"][0]["steps"][0]["agent_ids"][0] = "unknown-agent"
    contour_path.write_text(
        json.dumps(contour, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    contour_digest = "sha256:" + hashlib.sha256(contour_path.read_bytes()).hexdigest()
    lock_path = resource_root / "playbook-plan-contours-source-lock.v1.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    lock["abi"]["artifact_digest"] = contour_digest
    lock["contours"]["artifact_digest"] = contour_digest
    lock_path.write_text(
        json.dumps(lock, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(
        PlanCompilationSnapshotError,
        match="unknown agent",
    ):
        load_plan_compilation_snapshot(resource_root=resource_root)


def test_route_cli_compile_and_validate_run_plan(tmp_path: Path) -> None:
    decision, binding, runtime = _inputs(
        "bounded_change_safe",
        {"preview_required": False},
    )
    paths = {
        "decision": tmp_path / "decision.json",
        "binding": tmp_path / "binding.json",
        "runtime": tmp_path / "runtime.json",
    }
    for name, model in (
        ("decision", decision),
        ("binding", binding),
        ("runtime", runtime),
    ):
        paths[name].write_text(
            model.model_dump_json(indent=2),
            encoding="utf-8",
        )
    runner = CliRunner()
    compiled = runner.invoke(
        app,
        [
            "route",
            "compile",
            str(paths["decision"]),
            str(paths["binding"]),
            str(paths["runtime"]),
            "--root",
            str(REPO_ROOT),
        ],
    )

    assert compiled.exit_code == 0, compiled.output
    plan = RunPlan.model_validate_json(compiled.output)
    assert_run_plan_digest(plan)
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(compiled.output, encoding="utf-8")
    validated = runner.invoke(
        app,
        [
            "route",
            "validate",
            str(plan_path),
            "--against",
            str(paths["decision"]),
        ],
    )
    assert validated.exit_code == 0, validated.output
    payload = json.loads(validated.output)
    assert payload["kind"] == "RunPlan"
    assert payload["execution_authorized"] is False

    mismatched_binding = plan.scenario_binding.model_copy(
        update={
            "decision_ref": plan.scenario_binding.decision_ref.model_copy(
                update={"object_id": "decision:other"}
            )
        }
    )
    mismatched = plan.model_copy(
        update={
            "scenario_binding": mismatched_binding,
            "plan_digest": ZERO_DIGEST,
        }
    )
    mismatched = mismatched.model_copy(
        update={
            "plan_digest": canonical_digest(
                mismatched,
                exclude={"plan_digest"},
            )
        }
    )
    mismatched_path = tmp_path / "mismatched-plan.json"
    mismatched_path.write_text(
        mismatched.model_dump_json(indent=2),
        encoding="utf-8",
    )
    rejected = runner.invoke(
        app,
        [
            "route",
            "validate",
            str(mismatched_path),
        ],
    )
    assert rejected.exit_code == 1
    assert "decision refs must match" in rejected.output
