#!/usr/bin/env python3
"""Verify the installed public C1-to-C2 chain for all admitted scenarios."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from typing import Any

import aoa_sdk
from aoa_sdk import AoASDK
from aoa_sdk.models import (
    AgentRef,
    ProvenanceRef,
    RouteIntent,
    RuntimeProfile,
    ScenarioArtifactBinding,
    ScenarioConditionBinding,
)


PART_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PART_ROOT.parents[3]
NOW = datetime(2026, 7, 26, tzinfo=timezone.utc)
SCENARIOS = {
    "bounded_change_safe": {
        "objective": (
            "resolve authority among authored generated runtime and installed "
            "sources before a bounded repository change"
        ),
        "selected": "aoa-skills:skill:aoa-knowledge-stewardship",
        "input_artifact_kinds": (),
        "conditions": {"preview_required": False},
        "steps": ("orient", "mutate", "verify", "closeout"),
    },
    "a2a_summon_return_checkpoint": {
        "objective": (
            "extract and classify a literal closed reviewed session packet "
            "before a bounded child return checkpoint"
        ),
        "selected": "aoa-skills:skill:aoa-session-harvest",
        "input_artifact_kinds": (
            "summon_request",
            "summon_decision",
            "child_task_result",
        ),
        "conditions": {
            "a2a_eval_packet_earned": True,
            "memo_writeback_earned": False,
        },
        "steps": (
            "inspect-parent-anchor",
            "inspect-child-target",
            "review-return",
            "checkpoint-return",
            "evaluate-return",
            "closeout-dry-run",
        ),
    },
    "runtime_chaos_recovery": {
        "objective": (
            "decide whether live-session closeout evidence yields one guarded "
            "memo candidate after runtime recovery"
        ),
        "selected": "aoa-skills:skill:aoa-memo-writeback",
        "input_artifact_kinds": ("owner_runtime_receipt",),
        "conditions": {
            "derived_surface_recovery_required": False,
            "proof_handoff_earned": True,
        },
        "steps": (
            "inspect-runtime-receipt",
            "validate-degraded-lane",
            "evaluate-reentry",
            "closeout-recovery",
        ),
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workspace",
        type=Path,
        required=True,
        help="Workspace root whose pinned owner repositories are available.",
    )
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args()


def _digest(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _provenance(
    owner_repo: str,
    artifact_ref: str,
    marker: str,
) -> ProvenanceRef:
    return ProvenanceRef(
        owner_repo=owner_repo,
        artifact_ref=artifact_ref,
        source_ref="g8-installed-wheel-golden-chain",
        artifact_digest=_digest(f"{owner_repo}:{artifact_ref}:{marker}"),
        schema_ref="aoa_control_plane_v1",
        schema_version="aoa_control_plane_v1",
    )


def _runtime_profile() -> RuntimeProfile:
    provenance = _provenance(
        "abyss-stack",
        "runtime/agent-os/g8-verification-profile.json",
        "runtime-profile",
    )
    return RuntimeProfile(
        profile_id="runtime-profile:g8-installed-wheel",
        runtime_owner="abyss-stack",
        adapter_id="g8-verification-adapter",
        supported_plan_schema_versions=("aoa_control_plane_v1",),
        supported_event_schema_versions=("aoa_control_plane_v1",),
        supported_effect_classes=(
            "read_only",
            "repo_mutation",
            "runtime_mutation",
            "external",
        ),
        provenance=provenance,
    )


def _scenario_inputs(
    scenario_id: str,
    input_artifact_kinds: tuple[str, ...],
) -> tuple[tuple[ProvenanceRef, ...], tuple[ScenarioArtifactBinding, ...]]:
    if not input_artifact_kinds:
        return (
            (
                _provenance(
                    "agent-session",
                    f"requests/{scenario_id}.json",
                    scenario_id,
                ),
            ),
            (),
        )
    return (
        (),
        tuple(
            ScenarioArtifactBinding(
                artifact_kind=artifact_kind,
                artifact_ref=_provenance(
                    (
                        "abyss-stack"
                        if artifact_kind == "owner_runtime_receipt"
                        else "aoa-summon"
                    ),
                    f"artifacts/{scenario_id}/{artifact_kind}.json",
                    scenario_id,
                ),
            )
            for artifact_kind in input_artifact_kinds
        ),
    )


def _verify_scenario(
    sdk: AoASDK,
    scenario_id: str,
    case: dict[str, Any],
) -> dict[str, Any]:
    scenario = sdk.control_plane.scenario_ref(scenario_id)
    caller = _provenance(
        "agent-session",
        f"intents/{scenario_id}.json",
        case["objective"],
    )
    intent = RouteIntent(
        intent_id=f"intent:g8:{scenario_id}",
        correlation_id=f"correlation:g8:{scenario_id}",
        objective=case["objective"],
        requested_by=AgentRef(
            agent_id="g8-installed-wheel-caller",
            provenance=caller,
        ),
        scenario=scenario,
        requested_capability_kinds=("skill",),
        authored_at=NOW,
        provenance=caller,
    )
    decision = sdk.control_plane.resolve(intent)
    repeated_decision = sdk.control_plane.resolve(intent)
    if decision != repeated_decision:
        raise SystemExit(f"{scenario_id}: route resolution is not repeatable")
    if decision.status not in {"resolved", "degraded"}:
        raise SystemExit(
            f"{scenario_id}: route decision is unexpectedly {decision.status}"
        )
    if decision.selected_candidate_id != case["selected"]:
        raise SystemExit(
            f"{scenario_id}: selected {decision.selected_candidate_id!r}, "
            f"expected {case['selected']!r}"
        )
    selected = next(
        candidate
        for candidate in decision.candidates
        if candidate.candidate_id == decision.selected_candidate_id
    )
    if selected.scenario != scenario:
        raise SystemExit(f"{scenario_id}: route did not retain the exact scenario")
    if selected.agent is not None:
        raise SystemExit(
            f"{scenario_id}: route caller was projected as a provider agent"
        )

    input_refs, artifact_bindings = _scenario_inputs(
        scenario_id,
        case["input_artifact_kinds"],
    )
    conditions = tuple(
        ScenarioConditionBinding(
            condition_id=condition_id,
            value=value,
            provenance=_provenance(
                "agent-session",
                f"reviews/{scenario_id}/{condition_id}.json",
                str(value),
            ),
        )
        for condition_id, value in case["conditions"].items()
    )
    binding_provenance = _provenance(
        "agent-session",
        f"bindings/{scenario_id}.json",
        decision.decision_id,
    )
    binding = sdk.control_plane.bind_scenario(
        decision,
        scenario_id,
        binding_id=f"scenario-binding:g8:{scenario_id}",
        provenance=binding_provenance,
        input_refs=input_refs,
        input_artifact_bindings=artifact_bindings,
        condition_bindings=conditions,
    )
    repeated_binding = sdk.control_plane.bind_scenario(
        decision,
        scenario_id,
        binding_id=f"scenario-binding:g8:{scenario_id}",
        provenance=binding_provenance,
        input_refs=input_refs,
        input_artifact_bindings=artifact_bindings,
        condition_bindings=conditions,
    )
    if binding != repeated_binding:
        raise SystemExit(f"{scenario_id}: scenario binding is not repeatable")
    if selected.capability in binding.capability_refs:
        raise SystemExit(
            f"{scenario_id}: entry capability leaked into the scenario contour"
        )
    if not binding.capability_bindings:
        raise SystemExit(f"{scenario_id}: capability aliases were not resolved")
    for item in binding.capability_bindings:
        if item.capability.provenance.owner_repo != "aoa-skills":
            raise SystemExit(
                f"{scenario_id}: capability projection escaped aoa-skills"
            )
        if item.migration_provenance.source_ref != (
            item.capability.provenance.source_ref
        ):
            raise SystemExit(
                f"{scenario_id}: capability and migration pins disagree"
            )
        if (
            item.availability == "unbound"
            and item.lifecycle_health != "unavailable"
        ):
            raise SystemExit(
                f"{scenario_id}: an unbound capability was silently promoted"
            )

    runtime_profile = _runtime_profile()
    plan = sdk.control_plane.compile(decision, binding, runtime_profile)
    repeated_plan = sdk.control_plane.compile(
        decision,
        binding,
        runtime_profile,
    )
    if plan != repeated_plan:
        raise SystemExit(f"{scenario_id}: plan compilation is not repeatable")
    actual_steps = tuple(step.step_id for step in plan.steps)
    if actual_steps != case["steps"]:
        raise SystemExit(
            f"{scenario_id}: compiled steps {actual_steps!r} "
            f"do not match {case['steps']!r}"
        )
    if not plan.provenance.source_ref.startswith(
        "aoa_control_plane_plan_compiler_v2@"
    ):
        raise SystemExit(f"{scenario_id}: plan was not compiled by compiler v2")

    return {
        "agent_refs": [
            {
                "agent_id": item.agent_id,
                "source_ref": item.provenance.source_ref,
            }
            for item in binding.agent_refs
        ],
        "capability_bindings": [
            {
                "availability": item.availability,
                "capability_id": item.capability.capability_id,
                "compatibility": item.compatibility,
                "lifecycle_health": item.lifecycle_health,
                "requirement_id": item.requirement_id,
                "semantic_owner_repo": item.semantic_owner_repo,
            }
            for item in binding.capability_bindings
        ],
        "decision_id": decision.decision_id,
        "decision_status": decision.status,
        "input_snapshot_digest": decision.input_snapshot_digest,
        "plan_digest": plan.plan_digest,
        "plan_id": plan.plan_id,
        "scenario_source_ref": scenario.provenance.source_ref,
        "selected_agent": selected.agent,
        "selected_candidate_id": decision.selected_candidate_id,
        "steps": list(actual_steps),
    }


def main() -> int:
    args = parse_args()
    module_path = Path(aoa_sdk.__file__).resolve()
    if REPO_ROOT.resolve() in module_path.parents:
        raise SystemExit(f"aoa_sdk was imported from the checkout: {module_path}")

    sdk = AoASDK.from_workspace(args.workspace)
    report = {
        "package": {
            "module_path": str(module_path),
            "version": version("aoa-sdk"),
        },
        "schema_version": "aoa_sdk_g8_golden_scenario_chain_v1",
        "scenarios": {
            scenario_id: _verify_scenario(sdk, scenario_id, case)
            for scenario_id, case in SCENARIOS.items()
        },
        "verdict": "pass",
    }
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
