"""Deterministic compilation of one reviewed scenario into a RunPlan."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ...contracts.control_plane import (
    CheckpointPolicy,
    CloseoutRequirement,
    ContentRef,
    ControlPlaneContractError,
    EvalRequirement,
    EvidenceRequirement,
    PlanSnapshot,
    PlanStep,
    ProvenanceRef,
    RetentionRequirement,
    RetryPolicy,
    RollbackPolicy,
    RouteDecision,
    RunPlan,
    RuntimeProfile,
    ScenarioBinding,
    assert_run_plan_digest,
    canonical_digest,
)
from .snapshot import (
    PlanCompilationSnapshot,
    PlanContour,
    _EvalRequirement as ContourEvalRequirement,
    _EvidenceRequirement as ContourEvidenceRequirement,
    _RetentionRequirement as ContourRetentionRequirement,
)


PLAN_COMPILER_VERSION = "aoa_control_plane_plan_compiler_v2"
_ZERO_DIGEST = "sha256:" + "0" * 64


class PlanCompilationError(ControlPlaneContractError):
    """The reviewed inputs cannot compile into the selected owner contour."""


def compile_run_plan(
    decision: RouteDecision,
    scenario: ScenarioBinding,
    runtime_profile: RuntimeProfile,
    snapshot: PlanCompilationSnapshot,
    *,
    compiler_provenance: ProvenanceRef | None = None,
) -> RunPlan:
    """Compile exact owner-qualified bindings without choosing a runtime."""

    contour = snapshot.contour_for(scenario.scenario.scenario_id)
    provenance = compiler_provenance or default_compiler_provenance()
    _validate_decision_binding(decision, scenario)
    bindings = _validate_scenario_binding(
        contour,
        scenario,
        owner_source_ref=snapshot.source_lock.owner_source_ref,
    )
    active_conditions = {
        item.condition_id: item.value for item in scenario.condition_bindings
    }
    active_steps = tuple(
        step
        for step in contour.steps
        if step.guard_condition_id is None or active_conditions[step.guard_condition_id]
    )
    active_step_ids = {step.step_id for step in active_steps}
    approval_ids = tuple(
        requirement.requirement_id for requirement in decision.approval_requirements
    )
    if len(approval_ids) != len(set(approval_ids)):
        raise PlanCompilationError(
            "route approval requirement ids must be unique before compilation"
        )
    for approval_requirement in decision.approval_requirements:
        missing = set(approval_requirement.applies_to_step_ids) - active_step_ids
        if missing:
            raise PlanCompilationError(
                "route approval "
                f"{approval_requirement.requirement_id!r} references "
                f"inactive contour steps: {sorted(missing)}"
            )

    agents = {item.agent_id: item for item in scenario.agent_refs}
    capabilities = (
        {
            item.requirement_id: item.capability
            for item in scenario.capability_bindings
        }
        if scenario.capability_bindings
        else {item.capability_id: item for item in scenario.capability_refs}
    )
    plan_steps = tuple(
        PlanStep(
            step_id=step.step_id,
            operation_kind=step.operation_kind,
            effect_class=step.effect_class,
            depends_on=tuple(
                dependency
                for dependency in step.depends_on
                if dependency in active_step_ids
            ),
            agent_refs=tuple(agents[item] for item in step.agent_ids),
            capability_refs=tuple(capabilities[item] for item in step.capability_ids),
            input_refs=_step_input_refs(
                step.input_binding,
                step.input_artifact_kinds,
                scenario,
                bindings,
            ),
            expected_output_kinds=step.expected_output_kinds,
            approval_requirement_ids=tuple(
                requirement.requirement_id
                for requirement in decision.approval_requirements
                if (
                    step.step_id in requirement.applies_to_step_ids
                    or (
                        not requirement.applies_to_step_ids
                        and step.approval_binding == "all_route_requirements"
                    )
                )
            ),
        )
        for step in active_steps
    )
    bound_approval_ids = {
        requirement_id
        for step in plan_steps
        for requirement_id in step.approval_requirement_ids
    }
    unbound_approval_ids = set(approval_ids) - bound_approval_ids
    if unbound_approval_ids:
        raise PlanCompilationError(
            "route approvals have no active contour step binding: "
            f"{sorted(unbound_approval_ids)}"
        )
    evidence_requirements = tuple(
        _compile_evidence(requirement, bindings, runtime_profile)
        for requirement in contour.evidence_requirements
        if _guard_is_active(
            requirement.guard_condition_id,
            active_conditions,
        )
    )
    active_evidence_ids = {
        requirement.requirement_id for requirement in evidence_requirements
    }
    for evidence_requirement in evidence_requirements:
        if (
            evidence_requirement.required_after_step_id is not None
            and evidence_requirement.required_after_step_id not in active_step_ids
        ):
            raise PlanCompilationError(
                "active evidence "
                f"{evidence_requirement.requirement_id!r} references "
                "an inactive contour step"
            )
    requirement_refs = {
        (item.owner_repo, item.artifact_ref): item for item in scenario.requirement_refs
    }
    eval_requirements = tuple(
        _compile_eval(requirement, requirement_refs, active_evidence_ids)
        for requirement in contour.eval_requirements
        if _guard_is_active(
            requirement.guard_condition_id,
            active_conditions,
        )
    )
    retention_requirements = tuple(
        _compile_retention(requirement, requirement_refs)
        for requirement in contour.retention_requirements
        if _guard_is_active(
            requirement.guard_condition_id,
            active_conditions,
        )
    )
    rollback_artifact = None
    if contour.rollback_policy.rollback_artifact_input_ref is not None:
        rollback_artifact = _require_owner_ref(
            requirement_refs,
            contour.rollback_policy.rollback_artifact_input_ref.owner_repo,
            contour.rollback_policy.rollback_artifact_input_ref.artifact_ref,
        )
    rollback_owner = _bound_owner(
        contour.rollback_policy.owner_binding,
        scenario,
        runtime_profile,
    )
    checkpoint_steps = tuple(
        step_id
        for step_id in contour.checkpoint_policy.required_after_step_ids
        if step_id in active_step_ids
    )
    snapshot_refs = _snapshot_source_refs(
        decision=decision,
        scenario=scenario,
        runtime_profile=runtime_profile,
        owner_snapshot=snapshot,
        compiler_provenance=provenance,
    )
    plan_snapshot = PlanSnapshot(
        snapshot_id="plan-snapshot:"
        + _hex_digest(
            {
                "compiler_version": PLAN_COMPILER_VERSION,
                "owner_snapshot_digest": snapshot.input_snapshot_digest,
                "source_refs": [item.model_dump(mode="json") for item in snapshot_refs],
                "abi_refs": [snapshot.contour_abi.model_dump(mode="json")],
            }
        ),
        source_refs=snapshot_refs,
        abi_refs=(snapshot.contour_abi,),
        snapshot_digest=_ZERO_DIGEST,
    )
    plan_snapshot = plan_snapshot.model_copy(
        update={
            "snapshot_digest": canonical_digest(
                plan_snapshot,
                exclude={"snapshot_digest"},
            )
        }
    )
    decision_digest = canonical_digest(decision)
    decision_ref = ContentRef(
        object_id=decision.decision_id,
        owner_repo=decision.provenance.owner_repo,
        schema_version=decision.schema_version,
        digest=decision_digest,
    )
    plan = RunPlan(
        plan_id="run-plan:"
        + _hex_digest(
            {
                "compiler_version": PLAN_COMPILER_VERSION,
                "decision_digest": decision_digest,
                "scenario_binding_digest": canonical_digest(scenario),
                "runtime_profile_digest": canonical_digest(runtime_profile),
                "snapshot_digest": plan_snapshot.snapshot_digest,
            }
        ),
        correlation_id=decision.correlation_id,
        decision_ref=decision_ref,
        scenario_binding=scenario,
        runtime_profile=runtime_profile,
        snapshot=plan_snapshot,
        steps=plan_steps,
        approval_requirements=decision.approval_requirements,
        checkpoint_policy=CheckpointPolicy(
            owner=scenario.scenario.provenance,
            required_after_step_ids=checkpoint_steps,
            required_on_pause=(contour.checkpoint_policy.required_on_pause),
            required_on_recoverable_failure=(
                contour.checkpoint_policy.required_on_recoverable_failure
            ),
        ),
        retry_policy=RetryPolicy(
            max_attempts=contour.retry_policy.max_attempts,
            retryable_failure_codes=(contour.retry_policy.retryable_failure_codes),
        ),
        rollback_policy=RollbackPolicy(
            required=contour.rollback_policy.required,
            owner=rollback_owner,
            trigger_codes=contour.rollback_policy.trigger_codes,
            rollback_artifact_ref=rollback_artifact,
        ),
        evidence_requirements=evidence_requirements,
        eval_requirements=eval_requirements,
        retention_requirements=retention_requirements,
        closeout_requirements=tuple(
            CloseoutRequirement(
                requirement_id=requirement.requirement_id,
                owner_ref=_bound_owner(
                    requirement.owner_binding,
                    scenario,
                    runtime_profile,
                ),
                required_ref_kinds=requirement.required_ref_kinds,
            )
            for requirement in contour.closeout_requirements
        ),
        plan_digest=_ZERO_DIGEST,
        provenance=provenance,
    )
    plan = plan.model_copy(
        update={
            "plan_digest": canonical_digest(
                plan,
                exclude={"plan_digest"},
            )
        }
    )
    assert_run_plan_digest(plan)
    return plan


def default_compiler_provenance() -> ProvenanceRef:
    source_file = Path(__file__).resolve()
    module_digest = hashlib.sha256(source_file.read_bytes()).hexdigest()
    return ProvenanceRef(
        owner_repo="aoa-sdk",
        artifact_ref="src/aoa_sdk/control_plane/planning/compiler.py",
        source_ref=f"{PLAN_COMPILER_VERSION}@sha256:{module_digest}",
        artifact_digest=f"sha256:{module_digest}",
        schema_ref=(
            "docs/decisions/"
            "AOA-SDK-D-0085-resolve-scenario-capabilities-before-compilation.md"
        ),
        schema_version=PLAN_COMPILER_VERSION,
    )


def _validate_decision_binding(
    decision: RouteDecision,
    scenario: ScenarioBinding,
) -> None:
    if decision.status == "blocked" or decision.selected_candidate_id is None:
        raise PlanCompilationError(
            "a blocked route decision cannot compile into a run plan"
        )
    expected_ref = ContentRef(
        object_id=decision.decision_id,
        owner_repo=decision.provenance.owner_repo,
        schema_version=decision.schema_version,
        digest=canonical_digest(decision),
    )
    if scenario.decision_ref != expected_ref:
        raise PlanCompilationError(
            "scenario binding does not reference the exact route decision"
        )
    if scenario.correlation_id != decision.correlation_id:
        raise PlanCompilationError(
            "scenario binding correlation does not match the route decision"
        )
    selected = next(
        candidate
        for candidate in decision.candidates
        if candidate.candidate_id == decision.selected_candidate_id
    )
    if selected.scenario != scenario.scenario:
        raise PlanCompilationError(
            "scenario binding must match an explicit selected scenario"
        )


def _validate_scenario_binding(
    contour: PlanContour,
    scenario: ScenarioBinding,
    *,
    owner_source_ref: str,
) -> dict[str, ProvenanceRef]:
    scenario_provenance = scenario.scenario.provenance
    if (
        scenario_provenance.owner_repo != "aoa-playbooks"
        or scenario_provenance.artifact_ref != contour.source_playbook_ref
        or scenario_provenance.source_ref != owner_source_ref
    ):
        raise PlanCompilationError(
            "scenario provenance must match the exact admitted aoa-playbooks source"
        )
    expected_agents = contour.required_agent_ids
    actual_agents = tuple(item.agent_id for item in scenario.agent_refs)
    if actual_agents != expected_agents:
        raise PlanCompilationError(
            "scenario agents must match the owner contour exactly and in order"
        )
    if any(item.provenance.owner_repo != "aoa-agents" for item in scenario.agent_refs):
        raise PlanCompilationError("scenario agents must remain owned by aoa-agents")
    expected_capabilities = contour.required_capability_ids
    actual_capabilities = (
        tuple(item.requirement_id for item in scenario.capability_bindings)
        if scenario.capability_bindings
        else tuple(item.capability_id for item in scenario.capability_refs)
    )
    if actual_capabilities != expected_capabilities:
        raise PlanCompilationError(
            "scenario capabilities must match the owner contour exactly and in order"
        )
    if not scenario.capability_bindings and any(
        item.provenance.owner_repo != "aoa-skills"
        for item in scenario.capability_refs
    ):
        raise PlanCompilationError(
            "scenario capabilities must remain owned by aoa-skills"
        )
    if scenario.capability_bindings and any(
        item.capability.provenance.owner_repo != "aoa-skills"
        or item.migration_provenance.owner_repo != "aoa-skills"
        for item in scenario.capability_bindings
    ):
        raise PlanCompilationError(
            "resolved capability bindings must remain pinned aoa-skills projections"
        )
    if scenario.expected_artifact_kinds != contour.expected_artifact_kinds:
        raise PlanCompilationError(
            "scenario expected artifacts must match the owner contour exactly"
        )
    expected_conditions = tuple(
        item.condition_id for item in contour.scenario_conditions
    )
    actual_conditions = tuple(item.condition_id for item in scenario.condition_bindings)
    if actual_conditions != expected_conditions:
        raise PlanCompilationError(
            "scenario conditions must match the owner contour exactly and in order"
        )
    expected_input_kinds = contour.input_artifact_kinds
    actual_input_kinds = tuple(
        item.artifact_kind for item in scenario.input_artifact_bindings
    )
    if expected_input_kinds:
        if scenario.input_refs:
            raise PlanCompilationError(
                "typed scenario inputs cannot also use generic input refs"
            )
        if actual_input_kinds != expected_input_kinds:
            raise PlanCompilationError(
                "typed scenario inputs must match owner artifact kinds "
                "exactly and in order"
            )
    else:
        if scenario.input_artifact_bindings:
            raise PlanCompilationError(
                "generic scenario contours cannot accept typed input artifacts"
            )
        if (
            any(step.input_binding == "all_scenario_inputs" for step in contour.steps)
            and not scenario.input_refs
        ):
            raise PlanCompilationError(
                "owner contour requires at least one exact generic scenario input"
            )
    generic_keys = [
        (item.owner_repo, item.artifact_ref) for item in scenario.input_refs
    ]
    if len(generic_keys) != len(set(generic_keys)):
        raise PlanCompilationError(
            "generic scenario input refs must be owner-path unique"
        )
    expected_requirement_keys = {
        (item.input_ref.owner_repo, item.input_ref.artifact_ref)
        for item in contour.eval_requirements
    }
    expected_requirement_keys.update(
        (item.input_ref.owner_repo, item.input_ref.artifact_ref)
        for item in contour.retention_requirements
    )
    if contour.rollback_policy.rollback_artifact_input_ref is not None:
        rollback_ref = contour.rollback_policy.rollback_artifact_input_ref
        expected_requirement_keys.add(
            (rollback_ref.owner_repo, rollback_ref.artifact_ref)
        )
    actual_requirement_keys = {
        (item.owner_repo, item.artifact_ref) for item in scenario.requirement_refs
    }
    if actual_requirement_keys != expected_requirement_keys:
        raise PlanCompilationError(
            "scenario requirement refs must cover owner contour refs exactly; "
            f"missing={sorted(expected_requirement_keys - actual_requirement_keys)}, "
            f"extra={sorted(actual_requirement_keys - expected_requirement_keys)}"
        )
    return {
        item.artifact_kind: item.artifact_ref
        for item in scenario.input_artifact_bindings
    }


def _step_input_refs(
    input_binding: str,
    input_artifact_kinds: tuple[str, ...],
    scenario: ScenarioBinding,
    bindings: dict[str, ProvenanceRef],
) -> tuple[ProvenanceRef, ...]:
    if input_binding == "none":
        return ()
    if input_binding == "all_scenario_inputs":
        return scenario.input_refs
    if input_binding == "selected_scenario_inputs":
        try:
            return tuple(bindings[kind] for kind in input_artifact_kinds)
        except KeyError as exc:
            raise PlanCompilationError(
                f"missing typed scenario input {exc.args[0]!r}"
            ) from exc
    raise PlanCompilationError(f"unsupported scenario input binding {input_binding!r}")


def _compile_evidence(
    requirement: ContourEvidenceRequirement,
    bindings: dict[str, ProvenanceRef],
    runtime_profile: RuntimeProfile,
) -> EvidenceRequirement:
    artifact_binding = requirement.artifact_binding
    artifact_kind = requirement.artifact_kind
    if artifact_binding == "scenario_input":
        if artifact_kind not in bindings:
            raise PlanCompilationError(
                f"scenario-input evidence lacks binding for {artifact_kind!r}"
            )
        producer_owner = bindings[artifact_kind].owner_repo
    else:
        producer_owner = runtime_profile.runtime_owner
    return EvidenceRequirement(
        requirement_id=requirement.requirement_id,
        artifact_kind=artifact_kind,
        artifact_binding=artifact_binding,
        producer_owner=producer_owner,
        required_after_step_id=requirement.required_after_step_id,
        terminal_required=requirement.terminal_required,
    )


def _compile_eval(
    requirement: ContourEvalRequirement,
    requirement_refs: dict[tuple[str, str], ProvenanceRef],
    active_evidence_ids: set[str],
) -> EvalRequirement:
    input_ref = requirement.input_ref
    owner_ref = _require_owner_ref(
        requirement_refs,
        input_ref.owner_repo,
        input_ref.artifact_ref,
    )
    required_evidence_ids = requirement.required_evidence_ids
    missing = set(required_evidence_ids) - active_evidence_ids
    if missing:
        raise PlanCompilationError(
            f"active eval {requirement.requirement_id!r} "
            f"references inactive evidence: {sorted(missing)}"
        )
    return EvalRequirement(
        requirement_id=requirement.requirement_id,
        eval_anchor=requirement.eval_anchor,
        eval_owner_ref=owner_ref,
        eval_contract_ref=owner_ref,
        required_evidence_ids=required_evidence_ids,
        verdict_required_for_closeout=(requirement.verdict_required_for_closeout),
    )


def _compile_retention(
    requirement: ContourRetentionRequirement,
    requirement_refs: dict[tuple[str, str], ProvenanceRef],
) -> RetentionRequirement:
    input_ref = requirement.input_ref
    owner_ref = _require_owner_ref(
        requirement_refs,
        input_ref.owner_repo,
        input_ref.artifact_ref,
    )
    return RetentionRequirement(
        requirement_id=requirement.requirement_id,
        memory_owner_ref=owner_ref,
        retention_contract_ref=owner_ref,
        receipt_required_for_closeout=(requirement.receipt_required_for_closeout),
    )


def _require_owner_ref(
    requirement_refs: dict[tuple[str, str], ProvenanceRef],
    owner_repo: str,
    artifact_ref: str,
) -> ProvenanceRef:
    try:
        return requirement_refs[(owner_repo, artifact_ref)]
    except KeyError as exc:
        raise PlanCompilationError(
            f"missing exact owner ref {owner_repo}:{artifact_ref}"
        ) from exc


def _bound_owner(
    owner_binding: str,
    scenario: ScenarioBinding,
    runtime_profile: RuntimeProfile,
) -> ProvenanceRef:
    if owner_binding == "scenario_owner":
        return scenario.scenario.provenance
    if owner_binding == "runtime_owner":
        return runtime_profile.provenance
    raise PlanCompilationError(f"unsupported owner binding {owner_binding!r}")


def _guard_is_active(
    condition_id: str | None,
    active_conditions: dict[str, bool],
) -> bool:
    return condition_id is None or active_conditions[condition_id]


def _snapshot_source_refs(
    *,
    decision: RouteDecision,
    scenario: ScenarioBinding,
    runtime_profile: RuntimeProfile,
    owner_snapshot: PlanCompilationSnapshot,
    compiler_provenance: ProvenanceRef,
) -> tuple[ProvenanceRef, ...]:
    refs = [
        owner_snapshot.contour_provenance,
        owner_snapshot.schema_provenance,
        owner_snapshot.admission_provenance,
        decision.provenance,
        scenario.scenario.provenance,
        scenario.provenance,
        runtime_profile.provenance,
        compiler_provenance,
        *(item.provenance for item in scenario.agent_refs),
        *(item.provenance for item in scenario.capability_refs),
        *(
            item.migration_provenance
            for item in scenario.capability_bindings
        ),
        *scenario.input_refs,
        *(item.artifact_ref for item in scenario.input_artifact_bindings),
        *(item.provenance for item in scenario.condition_bindings),
        *scenario.requirement_refs,
        *runtime_profile.constraint_refs,
        *(requirement.approval_owner for requirement in decision.approval_requirements),
        *(
            evidence
            for requirement in decision.approval_requirements
            for evidence in requirement.required_evidence_refs
        ),
    ]
    by_key: dict[tuple[str, str], ProvenanceRef] = {}
    for ref in refs:
        key = (ref.owner_repo, ref.artifact_ref)
        prior = by_key.get(key)
        if prior is not None and prior != ref:
            raise PlanCompilationError(
                f"conflicting provenance for {ref.owner_repo}:{ref.artifact_ref}"
            )
        by_key[key] = ref
    return tuple(by_key[key] for key in sorted(by_key))


def _hex_digest(payload: object) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
