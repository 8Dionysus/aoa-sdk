"""Deterministic construction and validation of AgentIncarnationBinding."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Literal

from ..contracts.control_plane import (
    ABIRef,
    AgentRef,
    CapabilityRef,
    CheckpointPolicy,
    CloseoutRequirement,
    ContentRef,
    EvidenceRequirement,
    PlanSnapshot,
    PlanStep,
    ProvenanceRef,
    RetryPolicy,
    RollbackPolicy,
    RunPlan,
    RuntimeProfile,
    ScenarioArtifactBinding,
    ScenarioBinding,
    ScenarioRef,
    assert_plan_snapshot_digest,
    assert_run_plan_digest,
    canonical_digest,
)
from ..contracts.incarnation import (
    AgentIncarnationBinding,
    AgentIncarnationBindingV2,
    ContinuationObligation,
    IncarnationPermissionPosture,
    IncarnationStopCondition,
    IncarnationToolProfile,
    IncarnationUsageMetering,
    WakeEscalationPolicy,
)
from ..errors import AoASDKError


_ZERO_DIGEST = "sha256:" + "0" * 64


class IncarnationBindingError(AoASDKError, ValueError):
    """One exact owner or plan invariant in an incarnation binding failed."""


def _unique_provenance_refs(
    values: tuple[ProvenanceRef, ...],
) -> tuple[ProvenanceRef, ...]:
    """Preserve order while rejecting conflicting owner/path identities."""

    unique: list[ProvenanceRef] = []
    by_key: dict[tuple[str, str], ProvenanceRef] = {}
    for value in values:
        key = (value.owner_repo, value.artifact_ref)
        existing = by_key.get(key)
        if existing is not None:
            if existing != value:
                raise IncarnationBindingError(
                    "one owner artifact path has conflicting provenance"
                )
            continue
        by_key[key] = value
        unique.append(value)
    return tuple(unique)


def build_obligation_actor_run_plan(
    *,
    plan_id: str,
    correlation_id: str,
    decision_ref: ContentRef,
    scenario_binding_id: str,
    scenario_id: str,
    task_local_dag_ref: ProvenanceRef,
    role: AgentRef,
    task_request_ref: ProvenanceRef,
    input_refs: tuple[ProvenanceRef, ...],
    expected_output_kinds: tuple[str, ...],
    runtime_profile: RuntimeProfile,
    snapshot_id: str,
    abi_refs: tuple[ABIRef, ...],
    step_id: str,
    effect_class: Literal["read_only", "repo_mutation"],
    producer_owner: str,
    checkpoint_owner: ProvenanceRef,
    rollback_owner: ProvenanceRef,
    closeout_owner: ProvenanceRef,
    provenance: ProvenanceRef,
    capability_refs: tuple[CapabilityRef, ...] = (),
) -> RunPlan:
    """Compile one already-decided obligation actor into a runtime-neutral plan.

    Every role, model-fit, runtime, workspace, procedure, responsibility, and
    task-DAG choice remains an exact caller-supplied owner reference.  This
    helper only removes repeated hand assembly of the SDK plan objects; it does
    not detect an obligation, select a role/model/runtime, grant an effect, or
    launch a process.
    """

    if effect_class not in {"read_only", "repo_mutation"}:
        raise IncarnationBindingError(
            "obligation actor plan supports only bounded read_only or repo_mutation effects"
        )
    if not expected_output_kinds or len(expected_output_kinds) != len(
        set(expected_output_kinds)
    ):
        raise IncarnationBindingError(
            "obligation actor expected output identities must be non-empty and unique"
        )
    if task_request_ref not in input_refs:
        raise IncarnationBindingError(
            "obligation actor task request must be an exact input ref"
        )
    if role.provenance not in input_refs:
        raise IncarnationBindingError(
            "obligation actor role provenance must be an exact input ref"
        )
    if task_local_dag_ref not in input_refs:
        raise IncarnationBindingError(
            "obligation actor task-local DAG must be an exact input ref"
        )
    if effect_class not in runtime_profile.supported_effect_classes:
        raise IncarnationBindingError(
            "selected runtime profile does not support the obligation effect class"
        )

    snapshot_sources = _unique_provenance_refs(
        (
            *input_refs,
            runtime_profile.provenance,
            checkpoint_owner,
            rollback_owner,
            closeout_owner,
            provenance,
        )
    )
    scenario = ScenarioBinding(
        binding_id=scenario_binding_id,
        correlation_id=correlation_id,
        scenario=ScenarioRef(
            scenario_id=scenario_id,
            provenance=task_local_dag_ref,
        ),
        decision_ref=decision_ref,
        agent_refs=(role,),
        capability_refs=capability_refs,
        input_refs=input_refs,
        input_artifact_bindings=(
            ScenarioArtifactBinding(
                artifact_kind="summon_request",
                artifact_ref=task_request_ref,
            ),
        ),
        expected_artifact_kinds=expected_output_kinds,
        provenance=provenance,
    )
    snapshot = PlanSnapshot(
        snapshot_id=snapshot_id,
        source_refs=snapshot_sources,
        abi_refs=abi_refs,
        snapshot_digest=_ZERO_DIGEST,
    )
    snapshot = snapshot.model_copy(
        update={
            "snapshot_digest": canonical_digest(
                snapshot,
                exclude={"snapshot_digest"},
            )
        }
    )
    step = PlanStep(
        step_id=step_id,
        operation_kind="inspect" if effect_class == "read_only" else "mutate",
        effect_class=effect_class,
        agent_refs=(role,),
        capability_refs=capability_refs,
        input_refs=input_refs,
        expected_output_kinds=expected_output_kinds,
    )
    plan = RunPlan(
        plan_id=plan_id,
        correlation_id=correlation_id,
        decision_ref=decision_ref,
        scenario_binding=scenario,
        runtime_profile=runtime_profile,
        snapshot=snapshot,
        steps=(step,),
        checkpoint_policy=CheckpointPolicy(
            owner=checkpoint_owner,
            required_after_step_ids=(step_id,),
        ),
        retry_policy=RetryPolicy(max_attempts=1),
        rollback_policy=RollbackPolicy(required=False, owner=rollback_owner),
        evidence_requirements=tuple(
            EvidenceRequirement(
                requirement_id=f"output:{name}",
                artifact_kind=name,
                producer_owner=producer_owner,
                required_after_step_id=step_id,
                terminal_required=True,
            )
            for name in expected_output_kinds
        ),
        closeout_requirements=(
            CloseoutRequirement(
                requirement_id=f"closeout:{plan_id}",
                owner_ref=closeout_owner,
                required_ref_kinds=expected_output_kinds
                + ("external_codex_agent_result",),
            ),
        ),
        plan_digest=_ZERO_DIGEST,
        provenance=provenance,
    )
    return plan.model_copy(
        update={
            "plan_digest": canonical_digest(
                plan,
                exclude={"plan_digest"},
            )
        }
    )


def load_model_realization_ref(
    path: str | Path,
    *,
    artifact_ref: str,
    source_ref: str,
) -> ProvenanceRef:
    """Hash one exact aoa-models realization without interpreting its fit claims."""

    location = Path(path)
    if not location.is_absolute():
        raise IncarnationBindingError("model realization path must be absolute")
    try:
        raw = location.read_bytes()
        payload = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise IncarnationBindingError(
            "model realization is unavailable or invalid JSON"
        ) from exc
    if (
        not isinstance(payload, dict)
        or payload.get("kind") != "ModelRealization"
        or payload.get("schema_version") != "aoa_model_realization_v1"
        or payload.get("$schema")
        != "https://schemas.aoa.local/models/model-realization.schema.json"
        or not isinstance(payload.get("model_realization_id"), str)
        or not payload["model_realization_id"]
        or not isinstance(payload.get("configuration_fingerprint"), str)
    ):
        raise IncarnationBindingError("model realization identity is invalid")
    return ProvenanceRef(
        owner_repo="aoa-models",
        artifact_ref=artifact_ref,
        source_ref=source_ref,
        artifact_digest="sha256:" + hashlib.sha256(raw).hexdigest(),
        schema_ref="schemas/model-realization.schema.json",
        schema_version="aoa_model_realization_v1",
    )


def build_agent_incarnation_binding(
    plan: RunPlan,
    *,
    binding_id: str,
    incarnation_id: str,
    causation_id: str,
    trace_id: str,
    task_request_ref: ProvenanceRef,
    role_id: str,
    role_contract_ref: ProvenanceRef,
    model_realization_ref: ProvenanceRef,
    workspace_source_ref: ProvenanceRef,
    permission_posture: IncarnationPermissionPosture,
    tool_profile: IncarnationToolProfile,
    usage_metering: IncarnationUsageMetering,
    stop_conditions: tuple[IncarnationStopCondition, ...],
    expected_result_schema_ref: ProvenanceRef,
    continuation: ContinuationObligation,
    wake_policy: WakeEscalationPolicy,
    provenance: ProvenanceRef,
) -> AgentIncarnationBinding:
    """Bind caller-selected owner refs; this function never selects a model."""

    binding = AgentIncarnationBinding(
        binding_id=binding_id,
        incarnation_id=incarnation_id,
        correlation_id=plan.correlation_id,
        causation_id=causation_id,
        trace_id=trace_id,
        run_plan_ref=ContentRef(
            object_id=plan.plan_id,
            owner_repo=plan.provenance.owner_repo,
            schema_version=plan.schema_version,
            digest=plan.plan_digest,
        ),
        task_request_ref=task_request_ref,
        role_id=role_id,
        role_contract_ref=role_contract_ref,
        model_realization_ref=model_realization_ref,
        runtime_profile_ref=plan.runtime_profile.provenance,
        workspace_source_ref=workspace_source_ref,
        permission_posture=permission_posture,
        tool_profile=tool_profile,
        usage_metering=usage_metering,
        stop_conditions=stop_conditions,
        expected_result_schema_ref=expected_result_schema_ref,
        continuation=continuation,
        wake_policy=wake_policy,
        binding_digest=_ZERO_DIGEST,
        provenance=provenance,
    )
    binding = binding.model_copy(
        update={
            "binding_digest": canonical_digest(
                binding,
                exclude={"binding_digest"},
            )
        }
    )
    assert_agent_incarnation_binding_matches_plan(binding, plan)
    return binding


def build_agent_incarnation_binding_v2(
    plan: RunPlan,
    *,
    binding_id: str,
    incarnation_id: str,
    causation_id: str,
    trace_id: str,
    task_request_ref: ProvenanceRef,
    role_id: str,
    role_contract_ref: ProvenanceRef,
    model_realization_ref: ProvenanceRef,
    workspace_source_ref: ProvenanceRef,
    permission_posture: IncarnationPermissionPosture,
    tool_profile: IncarnationToolProfile,
    usage_metering: IncarnationUsageMetering,
    stop_conditions: tuple[IncarnationStopCondition, ...],
    expected_result_schema_ref: ProvenanceRef,
    continuation: ContinuationObligation,
    wake_policy: WakeEscalationPolicy,
    agent_obligation_ref: ContentRef,
    actor_mandate_ref: ContentRef,
    role_resolution_ref: ContentRef,
    model_fit_query_result_ref: ContentRef,
    model_fit_projection_ref: ProvenanceRef,
    provenance: ProvenanceRef,
) -> AgentIncarnationBindingV2:
    """Build a new evidence-complete binding without weakening v1 receipts."""

    legacy = build_agent_incarnation_binding(
        plan,
        binding_id=binding_id,
        incarnation_id=incarnation_id,
        causation_id=causation_id,
        trace_id=trace_id,
        task_request_ref=task_request_ref,
        role_id=role_id,
        role_contract_ref=role_contract_ref,
        model_realization_ref=model_realization_ref,
        workspace_source_ref=workspace_source_ref,
        permission_posture=permission_posture,
        tool_profile=tool_profile,
        usage_metering=usage_metering,
        stop_conditions=stop_conditions,
        expected_result_schema_ref=expected_result_schema_ref,
        continuation=continuation,
        wake_policy=wake_policy,
        provenance=provenance,
    )
    binding = AgentIncarnationBindingV2.model_validate(
        legacy.model_dump(mode="python")
        | {
            "schema_version": "aoa_agent_incarnation_binding_v2",
            "agent_obligation_ref": agent_obligation_ref,
            "actor_mandate_ref": actor_mandate_ref,
            "role_resolution_ref": role_resolution_ref,
            "model_fit_query_result_ref": model_fit_query_result_ref,
            "model_fit_projection_ref": model_fit_projection_ref,
            "binding_digest": _ZERO_DIGEST,
        }
    )
    binding = binding.model_copy(
        update={
            "binding_digest": canonical_digest(
                binding,
                exclude={"binding_digest"},
            )
        }
    )
    assert_agent_incarnation_binding_matches_plan(binding, plan)
    return binding


def assert_agent_incarnation_binding_digest(
    binding: AgentIncarnationBinding | AgentIncarnationBindingV2,
) -> None:
    expected = canonical_digest(binding, exclude={"binding_digest"})
    if binding.binding_digest != expected:
        raise IncarnationBindingError(
            f"incarnation binding digest mismatch: expected {expected}"
        )


def assert_agent_incarnation_binding_matches_plan(
    binding: AgentIncarnationBinding | AgentIncarnationBindingV2,
    plan: RunPlan,
) -> None:
    """Fail closed when a model/role/task binding drifts from its exact plan."""

    assert_plan_snapshot_digest(plan.snapshot)
    assert_run_plan_digest(plan)
    assert_agent_incarnation_binding_digest(binding)
    expected_plan_ref = ContentRef(
        object_id=plan.plan_id,
        owner_repo=plan.provenance.owner_repo,
        schema_version=plan.schema_version,
        digest=plan.plan_digest,
    )
    if binding.run_plan_ref != expected_plan_ref:
        raise IncarnationBindingError(
            "incarnation binding does not name the exact run plan"
        )
    if binding.correlation_id != plan.correlation_id:
        raise IncarnationBindingError("incarnation and run-plan correlation ids differ")
    if binding.runtime_profile_ref != plan.runtime_profile.provenance:
        raise IncarnationBindingError(
            "incarnation runtime profile differs from the run plan"
        )

    matching_agents = [
        agent
        for agent in plan.scenario_binding.agent_refs
        if agent.agent_id == binding.role_id
        and agent.provenance == binding.role_contract_ref
    ]
    if len(matching_agents) != 1:
        raise IncarnationBindingError(
            "incarnation role must match one exact aoa-agents binding in the plan"
        )

    admitted_inputs = {
        *plan.scenario_binding.input_refs,
        *(item.artifact_ref for item in plan.scenario_binding.input_artifact_bindings),
    }
    if binding.task_request_ref not in admitted_inputs:
        raise IncarnationBindingError("task request is not an exact scenario input")
    role = matching_agents[0]
    role_steps = tuple(step for step in plan.steps if role in step.agent_refs)
    if not any(binding.task_request_ref in step.input_refs for step in role_steps):
        raise IncarnationBindingError(
            "task request is not bound to an active plan step assigned to the role"
        )

    snapshot_sources = set(plan.snapshot.source_refs)
    if binding.workspace_source_ref not in snapshot_sources:
        raise IncarnationBindingError(
            "workspace source is not pinned by the plan snapshot"
        )
    if not set(binding.continuation.immutable_input_refs).issubset(snapshot_sources):
        raise IncarnationBindingError(
            "continuation immutable inputs must be pinned plan snapshot sources"
        )
    if binding.task_request_ref not in binding.continuation.immutable_input_refs:
        raise IncarnationBindingError("continuation must preserve the task request")

    role_effects = {step.effect_class for step in role_steps}
    allowed_effects = set(binding.permission_posture.allowed_effect_classes)
    if role_effects != allowed_effects:
        raise IncarnationBindingError(
            "incarnation permission classes must exactly match its role-bound plan steps"
        )
    if "external" in role_effects:
        external_steps = {
            step.step_id
            for step in plan.steps
            if role in step.agent_refs and step.effect_class == "external"
        }
        approved_steps = {
            step_id
            for requirement in plan.approval_requirements
            for step_id in requirement.applies_to_step_ids
        }
        if not external_steps.issubset(approved_steps):
            raise IncarnationBindingError(
                "external incarnation effects require explicit plan approval bindings"
            )

    if (
        binding.tool_profile.profile_ref.owner_repo
        != plan.runtime_profile.runtime_owner
    ):
        raise IncarnationBindingError(
            "tool profile must remain with the selected runtime owner"
        )
    if binding.continuation.return_owner.owner_repo == "aoa-models":
        raise IncarnationBindingError("aoa-models cannot own runtime return acceptance")


def agent_incarnation_binding_ref(
    binding: AgentIncarnationBinding | AgentIncarnationBindingV2,
) -> ContentRef:
    assert_agent_incarnation_binding_digest(binding)
    return ContentRef(
        object_id=binding.binding_id,
        owner_repo=binding.provenance.owner_repo,
        schema_version=binding.schema_version,
        digest=binding.binding_digest,
    )
