from __future__ import annotations

import hashlib
import json
from pathlib import Path

import jsonschema
import pytest
from pydantic import ValidationError

from aoa_sdk.contracts.control_plane import AgentRef, ContentRef, ProvenanceRef, RunPlan
from aoa_sdk.control_plane import (
    AgentIncarnationBinding,
    AgentIncarnationBindingV2,
    ContinuationObligation,
    IncarnationBindingError,
    IncarnationPermissionPosture,
    IncarnationStopCondition,
    IncarnationToolProfile,
    IncarnationUsageMetering,
    WakeCondition,
    WakeEscalationPolicy,
    agent_incarnation_binding_ref,
    assert_agent_incarnation_binding_digest,
    assert_agent_incarnation_binding_matches_plan,
    build_agent_incarnation_binding,
    build_agent_incarnation_binding_v2,
    build_obligation_actor_run_plan,
    load_model_realization_ref,
)
from aoa_sdk.runtime_adapters import (
    AbyssStackAdapterError,
    load_abyss_stack_external_codex_runtime_profile,
)


ROOT = Path(__file__).resolve().parents[5]
PLAN_PATH = (
    ROOT
    / "mechanics/boundary-bridge/parts/plan-compilation-control-plane/examples"
    / "a2a-eval-only.run-plan.json"
)
SCHEMA_PATH = (
    ROOT
    / "mechanics/boundary-bridge/parts/agent-incarnation-binding/schemas"
    / "agent-incarnation-binding.schema.json"
)
SCHEMA_V2_PATH = (
    ROOT
    / "mechanics/boundary-bridge/parts/agent-incarnation-binding/schemas"
    / "agent-incarnation-binding-v2.schema.json"
)
ZERO_DIGEST = "sha256:" + "0" * 64


def _ref(owner_repo: str, artifact_ref: str) -> ProvenanceRef:
    return ProvenanceRef(
        owner_repo=owner_repo,
        artifact_ref=artifact_ref,
        source_ref="fixture-source-ref",
        artifact_digest=ZERO_DIGEST,
        schema_ref="schemas/fixture.schema.json",
        schema_version="fixture-v1",
    )


def _content_ref(
    owner_repo: str,
    object_id: str,
    schema_version: str,
) -> ContentRef:
    return ContentRef(
        object_id=object_id,
        owner_repo=owner_repo,
        schema_version=schema_version,
        digest=ZERO_DIGEST,
    )


def _model_fit_projection_ref() -> ProvenanceRef:
    return ProvenanceRef(
        owner_repo="aoa-models",
        artifact_ref="generated/model-fit-projections/luna-max-readonly.json",
        source_ref="fixture-source-ref",
        artifact_digest=ZERO_DIGEST,
        schema_ref="schemas/model-fit-projection.schema.json",
        schema_version="aoa_model_fit_projection_v1",
    )


def _plan() -> RunPlan:
    return RunPlan.model_validate_json(PLAN_PATH.read_text(encoding="utf-8"))


def _task_request(plan: RunPlan) -> ProvenanceRef:
    return next(
        item.artifact_ref
        for item in plan.scenario_binding.input_artifact_bindings
        if item.artifact_kind == "summon_request"
    )


def _source(plan: RunPlan, owner_repo: str) -> ProvenanceRef:
    return next(
        item for item in plan.snapshot.source_refs if item.owner_repo == owner_repo
    )


def _binding(
    plan: RunPlan,
    *,
    task_request_ref: ProvenanceRef | None = None,
    model_realization_ref: ProvenanceRef | None = None,
    role_id: str = "architect",
    permission_posture: IncarnationPermissionPosture | None = None,
) -> AgentIncarnationBinding:
    role = next(
        item for item in plan.scenario_binding.agent_refs if item.agent_id == role_id
    )
    task_request = task_request_ref or _task_request(plan)
    workspace_source = _source(plan, "fixture-requester")
    validation_ref = _source(plan, "aoa-evals")
    stop_conditions = (
        IncarnationStopCondition(
            condition_id="authority-boundary",
            kind="authority_boundary",
            description="Stop before any effect outside the read-only fixture.",
        ),
        IncarnationStopCondition(
            condition_id="validation-failure",
            kind="validation_failure",
            description="Stop when the structured result does not validate.",
        ),
    )
    wake_policy = WakeEscalationPolicy(
        default_action="continue_without_parent",
        conditions=(
            WakeCondition(
                condition_id="bounded-result-ready",
                event_kind="result.validated",
                action="activate_review_role",
                description="Route a valid result to the independent review role.",
            ),
            WakeCondition(
                condition_id="authority-needed",
                event_kind="run.authority_required",
                action="wake_parent",
                description="Return only when the delegated authority is insufficient.",
            ),
        ),
        escalation_conditions=("authority-needed",),
    )
    continuation = ContinuationObligation(
        continuation_id="continuation:fixture:luna-landing",
        parent_objective_ref=workspace_source,
        established_decision_refs=(),
        delegated_obligation="Inspect the bounded landing packet and return evidence.",
        delegation_reason="The role is a bounded, repeatable read-only landing review.",
        exact_child_identity="incarnation:fixture:luna-max",
        owner_scope=("fixture-requester", "aoa-agents", "aoa-models", "abyss-stack"),
        immutable_input_refs=(task_request, workspace_source),
        expected_output="A schema-valid landing-readiness result with source citations.",
        validation_refs=(validation_ref,),
        deferred_parent_decisions=("Whether to accept or perform any landing effect.",),
        invariants=(
            "No mutation or external effect is authorized.",
            "Model-fit meaning remains with aoa-models and aoa-evals.",
        ),
        stop_condition_ids=tuple(item.condition_id for item in stop_conditions),
        wake_condition_ids=tuple(item.condition_id for item in wake_policy.conditions),
        return_owner=workspace_source,
        rollback_reentry_anchor=workspace_source,
    )
    return build_agent_incarnation_binding(
        plan,
        binding_id="binding:fixture:luna-max",
        incarnation_id="incarnation:fixture:luna-max",
        causation_id="causation:fixture:luna-max",
        trace_id="trace:fixture:luna-max",
        task_request_ref=task_request,
        role_id=role.agent_id,
        role_contract_ref=role.provenance,
        model_realization_ref=model_realization_ref
        or _ref("aoa-models", "source/model-realizations/gpt-5.6-luna-max.json"),
        workspace_source_ref=workspace_source,
        permission_posture=permission_posture
        or IncarnationPermissionPosture(
            sandbox_mode="read_only",
            approval_policy="never",
            allowed_effect_classes=("read_only",),
            network_access="disabled",
        ),
        tool_profile=IncarnationToolProfile(
            profile_id="abyss-stack:external_codex_agent/luna-landing-readonly-v1",
            profile_ref=plan.runtime_profile.provenance,
            required_tool_ids=("read_file", "write_structured_result"),
        ),
        usage_metering=IncarnationUsageMetering(
            metering_regime="fixture:no-billing-claim",
            dimensions=(
                "input_tokens",
                "cached_input_tokens",
                "output_tokens",
                "active_wall_seconds",
                "turn_count",
                "output_bytes",
                "executed_commands",
            ),
        ),
        stop_conditions=stop_conditions,
        expected_result_schema_ref=validation_ref,
        continuation=continuation,
        wake_policy=wake_policy,
        provenance=_ref("aoa-sdk", "bindings/fixture-luna-max.json"),
    )


def _binding_v2(plan: RunPlan) -> AgentIncarnationBindingV2:
    legacy = _binding(plan)
    return build_agent_incarnation_binding_v2(
        plan,
        binding_id=legacy.binding_id,
        incarnation_id=legacy.incarnation_id,
        causation_id=legacy.causation_id,
        trace_id=legacy.trace_id,
        task_request_ref=legacy.task_request_ref,
        role_id=legacy.role_id,
        role_contract_ref=legacy.role_contract_ref,
        model_realization_ref=legacy.model_realization_ref,
        workspace_source_ref=legacy.workspace_source_ref,
        permission_posture=legacy.permission_posture,
        tool_profile=legacy.tool_profile,
        usage_metering=legacy.usage_metering,
        stop_conditions=legacy.stop_conditions,
        expected_result_schema_ref=legacy.expected_result_schema_ref,
        continuation=legacy.continuation,
        wake_policy=legacy.wake_policy,
        agent_obligation_ref=_content_ref(
            "aoa-agents",
            "obligation:fixture:landing-review",
            "agent-obligation-v1",
        ),
        actor_mandate_ref=_content_ref(
            "aoa-agents",
            "mandate:fixture:landing-reviewer",
            "actor-mandate-v1",
        ),
        role_resolution_ref=_content_ref(
            "aoa-agents",
            "role-resolution:evaluator:release-readiness:deep",
            "aoa_role_resolution_v1",
        ),
        model_fit_query_result_ref=_content_ref(
            "aoa-models",
            "model-fit-query-result:fixture",
            "aoa_model_fit_query_result_v2",
        ),
        model_fit_projection_ref=_model_fit_projection_ref(),
        provenance=legacy.provenance,
    )


def test_obligation_actor_plan_compiler_preserves_exact_owner_inputs() -> None:
    fixture_plan = _plan()
    role = AgentRef(
        agent_id="evaluator",
        provenance=_ref("aoa-agents", "roles/evaluator/deep.json"),
    )
    task_request = _ref("aoa-sdk", "task-local/eval/summon-request.json")
    task_dag = _ref("aoa-skills", "task-local/eval/dag.json")
    obligation = _ref("aoa-agents", "task-local/eval/obligation.json")
    mandate = _ref("aoa-agents", "task-local/eval/mandate.json")
    fit = _ref("aoa-models", "task-local/eval/model-fit-result.json")
    workspace = _ref("aoa-evals", "worktree:eval-duty")
    compiler = _ref("aoa-sdk", "control-plane/obligation-actor-plan-v1")
    inputs = (
        task_request,
        task_dag,
        obligation,
        mandate,
        role.provenance,
        fit,
        workspace,
    )

    plan = build_obligation_actor_run_plan(
        plan_id="run-plan:eval-duty",
        correlation_id="correlation:eval-duty",
        decision_ref=_content_ref(
            "aoa-sdk",
            "summon-decision:eval-duty",
            "urn:aoa-sdk:a2a:summon-result:v4",
        ),
        scenario_binding_id="scenario-binding:eval-duty",
        scenario_id="task-local-dag:eval-duty",
        task_local_dag_ref=task_dag,
        role=role,
        task_request_ref=task_request,
        input_refs=inputs,
        expected_output_kinds=("eval-selection",),
        runtime_profile=fixture_plan.runtime_profile,
        snapshot_id="plan-snapshot:eval-duty",
        abi_refs=fixture_plan.snapshot.abi_refs,
        step_id="execute-eval-duty",
        effect_class="repo_mutation",
        producer_owner="aoa-evals",
        checkpoint_owner=task_dag,
        rollback_owner=workspace,
        closeout_owner=compiler,
        provenance=compiler,
    )

    assert plan.plan_digest != ZERO_DIGEST
    assert plan.steps[0].agent_refs == (role,)
    assert plan.steps[0].input_refs == inputs
    assert plan.scenario_binding.scenario.provenance == task_dag
    assert plan.scenario_binding.input_artifact_bindings[0].artifact_ref == task_request
    assert plan.evidence_requirements[0].producer_owner == "aoa-evals"
    assert "gpt-5.6-luna" not in plan.model_dump_json()
    assert "token_budget" not in plan.model_dump_json()


def test_obligation_actor_plan_compiler_rejects_selection_or_effect_smuggling() -> None:
    fixture_plan = _plan()
    role = AgentRef(
        agent_id="evaluator",
        provenance=_ref("aoa-agents", "roles/evaluator/deep.json"),
    )
    task_request = _ref("aoa-sdk", "task-local/eval/summon-request.json")
    task_dag = _ref("aoa-skills", "task-local/eval/dag.json")
    common = {
        "plan_id": "run-plan:eval-duty",
        "correlation_id": "correlation:eval-duty",
        "decision_ref": _content_ref(
            "aoa-sdk",
            "summon-decision:eval-duty",
            "urn:aoa-sdk:a2a:summon-result:v4",
        ),
        "scenario_binding_id": "scenario-binding:eval-duty",
        "scenario_id": "task-local-dag:eval-duty",
        "task_local_dag_ref": task_dag,
        "role": role,
        "task_request_ref": task_request,
        "input_refs": (task_request, task_dag, role.provenance),
        "expected_output_kinds": ("eval-selection",),
        "runtime_profile": fixture_plan.runtime_profile,
        "snapshot_id": "plan-snapshot:eval-duty",
        "abi_refs": fixture_plan.snapshot.abi_refs,
        "step_id": "execute-eval-duty",
        "producer_owner": "aoa-evals",
        "checkpoint_owner": task_dag,
        "rollback_owner": task_dag,
        "closeout_owner": task_dag,
        "provenance": _ref("aoa-sdk", "control-plane/obligation-actor-plan-v1"),
    }

    with pytest.raises(IncarnationBindingError, match="only bounded"):
        build_obligation_actor_run_plan(effect_class="external", **common)

    with pytest.raises(IncarnationBindingError, match="non-empty and unique"):
        build_obligation_actor_run_plan(
            effect_class="read_only",
            **(common | {"expected_output_kinds": ("same", "same")}),
        )


def test_binding_matches_exact_plan_and_generated_schema() -> None:
    plan = _plan()
    binding = _binding(plan)

    assert_agent_incarnation_binding_digest(binding)
    assert agent_incarnation_binding_ref(binding).digest == binding.binding_digest
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(binding.model_dump(mode="json"))
    assert binding.run_plan_ref.digest == plan.plan_digest
    assert binding.permission_posture.external_effects is False
    assert binding.usage_metering.mode == "observe_only"
    assert binding.usage_metering.execution_limit_policy == "none"
    assert binding.wake_policy.mode == "event_filtered_reentry"


def test_v2_binding_requires_complete_obligation_and_model_fit_chain() -> None:
    plan = _plan()
    binding = _binding_v2(plan)

    assert binding.schema_version == "aoa_agent_incarnation_binding_v2"
    assert binding.agent_obligation_ref.owner_repo == "aoa-agents"
    assert binding.actor_mandate_ref.owner_repo == "aoa-agents"
    assert binding.role_resolution_ref.schema_version == "aoa_role_resolution_v1"
    assert (
        binding.model_fit_query_result_ref.schema_version
        == "aoa_model_fit_query_result_v2"
    )
    assert binding.model_fit_projection_ref.owner_repo == "aoa-models"
    assert_agent_incarnation_binding_digest(binding)
    schema = json.loads(SCHEMA_V2_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(binding.model_dump(mode="json"))


@pytest.mark.parametrize(
    ("field", "replacement", "message"),
    (
        (
            "agent_obligation_ref",
            _content_ref("aoa-models", "wrong-owner", "agent-obligation-v1"),
            "agent obligation must retain exact",
        ),
        (
            "actor_mandate_ref",
            _content_ref("aoa-agents", "old-mandate", "actor-mandate-v0"),
            "actor mandate must retain exact",
        ),
        (
            "model_fit_query_result_ref",
            _content_ref(
                "aoa-models",
                "unbound-fit-result",
                "aoa_model_fit_query_result_v1",
            ),
            "model-fit query result must retain exact",
        ),
    ),
)
def test_v2_binding_rejects_owner_or_contract_drift(
    field: str,
    replacement: ContentRef,
    message: str,
) -> None:
    binding = _binding_v2(_plan())

    with pytest.raises(ValidationError, match=message):
        AgentIncarnationBindingV2.model_validate(
            binding.model_dump(mode="python") | {field: replacement}
        )


def test_v2_binding_rejects_projection_from_another_model_source() -> None:
    binding = _binding_v2(_plan())
    drifted = binding.model_fit_projection_ref.model_copy(
        update={"source_ref": "another-model-source-ref"}
    )

    with pytest.raises(ValidationError, match="must share one aoa-models source ref"):
        AgentIncarnationBindingV2.model_validate(
            binding.model_dump(mode="python") | {"model_fit_projection_ref": drifted}
        )


def test_metering_cannot_omit_a_runtime_dimension() -> None:
    with pytest.raises(ValidationError, match="at least 7 items"):
        IncarnationUsageMetering(
            metering_regime="fixture:no-billing-claim",
            dimensions=(
                "input_tokens",
                "cached_input_tokens",
                "output_tokens",
                "active_wall_seconds",
                "turn_count",
                "output_bytes",
            ),
        )


def test_task_request_must_be_an_active_pinned_plan_input() -> None:
    plan = _plan()
    with pytest.raises(IncarnationBindingError, match="exact scenario input"):
        _binding(plan, task_request_ref=_ref("requester", "requests/not-in-plan.json"))


def test_task_request_must_be_consumed_by_a_step_assigned_to_the_role() -> None:
    plan = _plan()

    with pytest.raises(
        IncarnationBindingError,
        match="active plan step assigned to the role",
    ):
        _binding(plan, role_id="evaluator")


def test_permission_classes_cannot_exceed_the_role_bound_plan_steps() -> None:
    plan = _plan()

    with pytest.raises(
        IncarnationBindingError,
        match="must exactly match",
    ):
        _binding(
            plan,
            permission_posture=IncarnationPermissionPosture(
                sandbox_mode="workspace_write",
                approval_policy="never",
                allowed_effect_classes=("read_only", "repo_mutation"),
                network_access="disabled",
            ),
        )


def test_model_realization_owner_cannot_drift() -> None:
    plan = _plan()
    with pytest.raises(ValidationError, match="model realization meaning"):
        _binding(
            plan,
            model_realization_ref=_ref("abyss-stack", "runtime/copied-model.json"),
        )


def test_digest_tampering_fails_closed() -> None:
    binding = _binding(_plan())
    tampered = binding.model_copy(update={"binding_digest": ZERO_DIGEST})

    with pytest.raises(IncarnationBindingError, match="digest mismatch"):
        assert_agent_incarnation_binding_digest(tampered)


def test_model_realization_loader_hashes_exact_bytes(tmp_path: Path) -> None:
    realization_path = tmp_path / "luna-max.json"
    payload = {
        "$schema": "https://schemas.aoa.local/models/model-realization.schema.json",
        "schema_version": "aoa_model_realization_v1",
        "kind": "ModelRealization",
        "model_realization_id": "openai:gpt-5.6-luna:codex-0.146.0:max:read-only",
        "configuration_fingerprint": "sha256:" + "1" * 64,
    }
    raw = (json.dumps(payload, sort_keys=True) + "\n").encode()
    realization_path.write_bytes(raw)

    ref = load_model_realization_ref(
        realization_path,
        artifact_ref="source/model-realizations/luna-max.json",
        source_ref="test-source-ref",
    )

    assert ref.owner_repo == "aoa-models"
    assert ref.artifact_digest == "sha256:" + hashlib.sha256(raw).hexdigest()


def test_continuation_must_name_every_wake_condition() -> None:
    binding = _binding(_plan())
    incomplete = binding.continuation.model_copy(
        update={"wake_condition_ids": ("bounded-result-ready",)}
    )

    with pytest.raises(ValidationError, match="preserve every wake condition"):
        AgentIncarnationBinding.model_validate(
            binding.model_dump(mode="python") | {"continuation": incomplete}
        )


def test_incarnation_rejects_plan_bytes_with_a_stale_digest() -> None:
    plan = _plan()
    binding = _binding(plan)
    tampered = plan.model_copy(
        update={
            "retry_policy": plan.retry_policy.model_copy(
                update={"max_attempts": plan.retry_policy.max_attempts + 1}
            )
        }
    )

    with pytest.raises(ValueError, match="run plan digest mismatch"):
        assert_agent_incarnation_binding_matches_plan(binding, tampered)


def _external_codex_descriptor() -> dict[str, object]:
    return {
        "$schema": "schemas/external-codex-runtime-profile.schema.json",
        "schema_version": "abyss_stack_external_codex_runtime_profile_v2",
        "profile_id": "runtime-profile:abyss-stack-external-codex-agent-v1",
        "runtime_owner": "abyss-stack",
        "adapter_id": "abyss_stack_external_codex_agent_v1",
        "adapter_protocol_version": "aoa_runtime_adapter_v1",
        "transport": "codex_exec_jsonl_v1",
        "source_ref": "fixture-stack-source",
        "schema_ref": "schemas/external-codex-runtime-profile.schema.json",
        "supported_plan_schema_versions": ["aoa_control_plane_v1"],
        "supported_event_schema_versions": [
            "aoa_control_plane_v1",
            "abyss_stack_external_codex_event_v1",
        ],
        "supported_effect_classes": ["read_only", "repo_mutation"],
        "process_containment": {
            "strategy": "linux_subreaper_supervisor_v1",
            "supervisor_ref": "external_codex_supervisor.py",
            "parent_death_signal": "SIGTERM",
            "term_timeout_seconds": 3.0,
            "kill_timeout_seconds": 3.0,
            "probe_executable": "/usr/bin/true",
        },
        "codex_cli": {"required_version": "codex-cli 0.146.0"},
        "model_admission": [{"model_slug": "gpt-5.6-luna"}],
        "tool_profiles": [{"profile_id": "fixture-read-only"}],
        "execution_postures": ["bounded_execution", "independent_review"],
        "owner_contracts": {
            "owner_execution_request_schema": {
                "owner_repo": "aoa-agents",
                "artifact_ref": "skills/aoa-summon/references/summon-request-v3.schema.json",
                "source_ref": "a" * 40,
                "digest": "sha256:" + "1" * 64,
                "schema_version": "summon-request-v3",
            },
            "task_local_dag_schema": {
                "owner_repo": "aoa-skills",
                "artifact_ref": "schemas/task_local_dag_v2.schema.json",
                "source_ref": "b" * 40,
                "digest": "sha256:" + "2" * 64,
                "schema_version": "aoa-task-local-dag-v2",
            },
        },
        "result_schema_ref": "schemas/external-codex-report.schema.json",
        "boundaries": {
            "launches_separate_os_process": True,
            "uses_builtin_codex_subagents": False,
            "uses_tui_transport": False,
            "model_fit_authority": False,
            "owner_acceptance_authority": False,
            "external_effects_enabled": False,
        },
    }


def test_external_codex_runtime_profile_loader_preserves_owner_provenance(
    tmp_path: Path,
) -> None:
    path = tmp_path / "runtime-profile.json"
    path.write_text(
        json.dumps(_external_codex_descriptor(), sort_keys=True) + "\n",
        encoding="utf-8",
    )

    profile = load_abyss_stack_external_codex_runtime_profile(path)

    assert profile.runtime_owner == "abyss-stack"
    assert profile.adapter_id == "abyss_stack_external_codex_agent_v1"
    assert profile.provenance.artifact_digest == (
        "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    )
    assert profile.runtime_approval_requirements == ()


def test_external_codex_runtime_profile_loader_rejects_builtin_subagents(
    tmp_path: Path,
) -> None:
    descriptor = _external_codex_descriptor()
    boundaries = dict(descriptor["boundaries"])
    boundaries["uses_builtin_codex_subagents"] = True
    descriptor["boundaries"] = boundaries
    path = tmp_path / "runtime-profile.json"
    path.write_text(json.dumps(descriptor) + "\n", encoding="utf-8")

    with pytest.raises(AbyssStackAdapterError, match="identity is invalid"):
        load_abyss_stack_external_codex_runtime_profile(path)


def test_external_codex_runtime_profile_loader_rejects_weaker_containment(
    tmp_path: Path,
) -> None:
    descriptor = _external_codex_descriptor()
    process_containment = dict(descriptor["process_containment"])
    process_containment["strategy"] = "process_group_only"
    descriptor["process_containment"] = process_containment
    path = tmp_path / "runtime-profile.json"
    path.write_text(json.dumps(descriptor) + "\n", encoding="utf-8")

    with pytest.raises(AbyssStackAdapterError, match="identity is invalid"):
        load_abyss_stack_external_codex_runtime_profile(path)


def test_external_codex_runtime_profile_loader_rejects_domain_specific_posture(
    tmp_path: Path,
) -> None:
    descriptor = _external_codex_descriptor()
    descriptor["execution_postures"] = ["landing_readiness"]
    path = tmp_path / "runtime-profile.json"
    path.write_text(json.dumps(descriptor) + "\n", encoding="utf-8")

    with pytest.raises(AbyssStackAdapterError, match="unsupported execution postures"):
        load_abyss_stack_external_codex_runtime_profile(path)
