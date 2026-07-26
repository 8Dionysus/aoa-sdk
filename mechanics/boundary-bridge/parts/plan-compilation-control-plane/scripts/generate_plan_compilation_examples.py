#!/usr/bin/env python3
"""Generate three deterministic C2 RunPlan branch fixtures."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[5]
SOURCE_ROOT = REPO_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from aoa_sdk.contracts.control_plane import (  # noqa: E402
    AgentRef,
    ApprovalRequirement,
    CapabilityRef,
    ContentRef,
    ProvenanceRef,
    RouteCandidate,
    RouteDecision,
    RuntimeProfile,
    ScenarioArtifactBinding,
    ScenarioBinding,
    ScenarioConditionBinding,
    ScenarioRef,
    canonical_digest,
)
from aoa_sdk.control_plane.planning import (  # noqa: E402
    compile_run_plan,
    load_plan_compilation_snapshot,
)


EXAMPLE_ROOT = (
    REPO_ROOT
    / "mechanics"
    / "boundary-bridge"
    / "parts"
    / "plan-compilation-control-plane"
    / "examples"
)
ZERO_DIGEST = "sha256:" + "0" * 64
CASES = {
    "bounded-preview-pruned": (
        "bounded_change_safe",
        {"preview_required": False},
    ),
    "a2a-eval-only": (
        "a2a_summon_return_checkpoint",
        {
            "a2a_eval_packet_earned": True,
            "memo_writeback_earned": False,
        },
    ),
    "runtime-proof-without-reground": (
        "runtime_chaos_recovery",
        {
            "derived_surface_recovery_required": False,
            "proof_handoff_earned": True,
        },
    ),
}
WHEEL_SMOKE_PATH = EXAMPLE_ROOT / "installed-wheel-smoke.inputs.json"


def _provenance(
    owner: str,
    artifact_ref: str,
    *,
    source_ref: str = "fixture-source-ref",
) -> ProvenanceRef:
    return ProvenanceRef(
        owner_repo=owner,
        artifact_ref=artifact_ref,
        source_ref=source_ref,
        artifact_digest=ZERO_DIGEST,
        schema_ref="schemas/fixture.schema.json",
        schema_version="fixture-v1",
    )


def _compiler_provenance() -> ProvenanceRef:
    return _provenance(
        "aoa-sdk",
        "src/aoa_sdk/control_plane/planning/compiler.py",
    )


def _fixture_inputs(
    scenario_id: str,
    conditions: dict[str, bool],
) -> tuple[RouteDecision, ScenarioBinding, RuntimeProfile]:
    snapshot = load_plan_compilation_snapshot()
    contour = snapshot.contour_for(scenario_id)
    scenario_ref = ScenarioRef(
        scenario_id=scenario_id,
        provenance=_provenance(
            "aoa-playbooks",
            contour.source_playbook_ref,
            source_ref=snapshot.source_lock.owner_source_ref,
        ),
    )
    agents = tuple(
        AgentRef(
            agent_id=agent_id,
            provenance=_provenance(
                "aoa-agents",
                f"generated/agent_catalog.min.json#agents/{agent_id}",
            ),
        )
        for agent_id in contour.required_agent_ids
    )
    capabilities = tuple(
        CapabilityRef(
            capability_id=capability_id,
            capability_kind="skill",
            provenance=_provenance(
                "aoa-skills",
                f"generated/capability_graph.json#nodes/{capability_id}",
            ),
        )
        for capability_id in contour.required_capability_ids
    )
    runtime_provenance = _provenance(
        "abyss-stack",
        "runtime/agent-os/profile.json",
    )
    approval = ApprovalRequirement(
        requirement_id="approval:fixture:reviewed-effect",
        approval_owner=runtime_provenance,
        operation="reviewed-effect-boundary",
        risk_class="fixture",
    )
    decision = RouteDecision(
        decision_id=f"route-decision:fixture:{scenario_id}",
        correlation_id=f"correlation:fixture:{scenario_id}",
        intent_ref=ContentRef(
            object_id=f"route-intent:fixture:{scenario_id}",
            owner_repo="fixture-requester",
            schema_version="aoa_control_plane_v1",
            digest=ZERO_DIGEST,
        ),
        status="resolved",
        candidates=(
            RouteCandidate(
                candidate_id=f"route-candidate:fixture:{scenario_id}",
                capability=capabilities[0],
                agent=agents[0],
                scenario=scenario_ref,
                rank=0,
                compatibility="compatible",
                policy_posture="approval_required",
                reason_codes=("fixture_exact_owner_projection",),
                evidence_refs=(),
            ),
        ),
        selected_candidate_id=f"route-candidate:fixture:{scenario_id}",
        approval_requirements=(approval,),
        resolver_version="fixture-route-resolver-v1",
        reason_codes=("fixture_resolved",),
        input_snapshot_digest=ZERO_DIGEST,
        provenance=_provenance(
            "aoa-sdk",
            "src/aoa_sdk/control_plane/routing/resolver.py",
        ),
    )
    decision_ref = ContentRef(
        object_id=decision.decision_id,
        owner_repo=decision.provenance.owner_repo,
        schema_version=decision.schema_version,
        digest=canonical_digest(decision),
    )
    requirement_refs: dict[tuple[str, str], ProvenanceRef] = {}
    for requirement in (
        *contour.eval_requirements,
        *contour.retention_requirements,
    ):
        key = (
            requirement.input_ref.owner_repo,
            requirement.input_ref.artifact_ref,
        )
        requirement_refs[key] = _provenance(*key)
    binding = ScenarioBinding(
        binding_id=f"scenario-binding:fixture:{scenario_id}",
        correlation_id=decision.correlation_id,
        scenario=scenario_ref,
        decision_ref=decision_ref,
        agent_refs=agents,
        capability_refs=capabilities,
        input_refs=(
            (
                _provenance(
                    "fixture-requester",
                    f"requests/{scenario_id}.json",
                ),
            )
            if not contour.input_artifact_kinds
            else ()
        ),
        input_artifact_bindings=tuple(
            ScenarioArtifactBinding(
                artifact_kind=artifact_kind,
                artifact_ref=_provenance(
                    "fixture-scenario-inputs",
                    f"artifacts/{artifact_kind}.json",
                ),
            )
            for artifact_kind in contour.input_artifact_kinds
        ),
        condition_bindings=tuple(
            ScenarioConditionBinding(
                condition_id=condition.condition_id,
                value=conditions[condition.condition_id],
                provenance=_provenance(
                    "fixture-reviewer",
                    f"reviews/{scenario_id}/{condition.condition_id}.json",
                ),
            )
            for condition in contour.scenario_conditions
        ),
        requirement_refs=tuple(
            requirement_refs[key] for key in sorted(requirement_refs)
        ),
        expected_artifact_kinds=contour.expected_artifact_kinds,
        provenance=_provenance(
            "fixture-requester",
            f"bindings/{scenario_id}.json",
        ),
    )
    runtime = RuntimeProfile(
        profile_id="runtime-profile:fixture",
        runtime_owner="abyss-stack",
        adapter_id="fixture-non-executing-adapter",
        supported_plan_schema_versions=("aoa_control_plane_v1",),
        supported_event_schema_versions=("aoa_control_plane_v1",),
        supported_effect_classes=(
            "read_only",
            "repo_mutation",
            "runtime_mutation",
            "external",
        ),
        provenance=runtime_provenance,
    )
    return decision, binding, runtime


def build_examples() -> dict[Path, bytes]:
    snapshot = load_plan_compilation_snapshot()
    compiler_provenance = _compiler_provenance()
    outputs: dict[Path, bytes] = {}
    for slug, (scenario_id, conditions) in CASES.items():
        decision, binding, runtime = _fixture_inputs(
            scenario_id,
            conditions,
        )
        plan = compile_run_plan(
            decision,
            binding,
            runtime,
            snapshot,
            compiler_provenance=compiler_provenance,
        )
        outputs[EXAMPLE_ROOT / f"{slug}.run-plan.json"] = (
            json.dumps(
                plan.model_dump(mode="json"),
                ensure_ascii=True,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8")
    return outputs


def build_wheel_smoke_fixture() -> bytes:
    scenario_id, conditions = CASES["bounded-preview-pruned"]
    decision, binding, runtime = _fixture_inputs(scenario_id, conditions)
    payload = {
        "schema_version": "aoa_control_plane_plan_wheel_smoke_v1",
        "decision": decision.model_dump(mode="json"),
        "scenario_binding": binding.model_dump(mode="json"),
        "runtime_profile": runtime.model_dump(mode="json"),
        "compiler_provenance": _compiler_provenance().model_dump(mode="json"),
        "expected_plan": "bounded-preview-pruned.run-plan.json",
    }
    return (
        json.dumps(
            payload,
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = {
        **build_examples(),
        WHEEL_SMOKE_PATH: build_wheel_smoke_fixture(),
    }
    stale = [
        path
        for path, expected in outputs.items()
        if not path.is_file() or path.read_bytes() != expected
    ]
    if args.check:
        if stale:
            raise SystemExit(
                "stale plan compilation examples: "
                + ", ".join(path.relative_to(REPO_ROOT).as_posix() for path in stale)
            )
        print("[ok] deterministic C2 RunPlan examples are current")
        return 0
    for path, payload in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    print("[ok] generated deterministic C2 RunPlan examples")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
