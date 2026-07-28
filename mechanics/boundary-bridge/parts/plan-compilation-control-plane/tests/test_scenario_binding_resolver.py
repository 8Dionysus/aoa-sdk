from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
import yaml

from aoa_sdk.contracts.control_plane import (
    AgentRef,
    CapabilityRef,
    ContentRef,
    ProvenanceRef,
    RouteCandidate,
    RouteDecision,
    ScenarioConditionBinding,
)
from aoa_sdk.contracts.skills import CapabilityGraph
from aoa_sdk.control_plane.planning import (
    ScenarioBindingError,
    bind_scenario,
    compile_run_plan,
    load_plan_compilation_snapshot,
    resolve_scenario_ref,
)
from aoa_sdk.control_plane.runner.reference import reference_runtime_profile
import aoa_sdk.control_plane.planning.bindings as scenario_bindings


ZERO_DIGEST = "sha256:" + "0" * 64
SKILLS_REF = "1" * 40
AGENTS_REF = "2" * 40
EVALS_REF = "3" * 40
MEMO_REF = "4" * 40
TARGETS = {
    "aoa-approval-gate-check": (
        "guard.operations.approval",
        "guard",
        "host-runtime",
        "route-owner-object",
        "none",
        "external",
        "healthy",
    ),
    "aoa-source-of-truth-check": (
        "mode.knowledge.authority-map",
        "mode",
        "aoa-skills",
        "merge-mode",
        "migration-alias",
        "available",
        "challenger",
    ),
    "aoa-bounded-context-map": (
        "mode.engineering-shape.contexts",
        "mode",
        "aoa-skills",
        "merge-mode",
        "migration-alias",
        "available",
        "challenger",
    ),
    "aoa-dry-run-first": (
        "guard.operations.preview",
        "guard",
        "target-runtime-owner",
        "route-owner-object",
        "none",
        "unbound",
        "unavailable",
    ),
    "aoa-change-protocol": (
        "workflow.operations.repository-change",
        "workflow",
        "host-agent",
        "route-owner-object",
        "none",
        "external",
        "healthy",
    ),
    "aoa-contract-test": (
        "mode.verification.contract",
        "mode",
        "aoa-skills",
        "merge-mode",
        "migration-alias",
        "available",
        "challenger",
    ),
    "aoa-tdd-slice": (
        "workflow.operations.tdd-slice",
        "workflow",
        "host-agent",
        "route-owner-object",
        "none",
        "external",
        "healthy",
    ),
    "aoa-adr-write": (
        "mode.decision.record",
        "mode",
        "aoa-skills",
        "merge-mode",
        "migration-alias",
        "available",
        "challenger",
    ),
    "aoa-sanitized-share": (
        "mode.knowledge.sanitized-share",
        "mode",
        "aoa-skills",
        "merge-mode",
        "migration-alias",
        "available",
        "challenger",
    ),
}


def _provenance(owner: str = "fixture-owner") -> ProvenanceRef:
    return ProvenanceRef(
        owner_repo=owner,
        artifact_ref="fixture/artifact.json",
        source_ref="fixture-source",
        artifact_digest=ZERO_DIGEST,
        schema_ref="fixture/schema.json",
        schema_version="fixture-v1",
    )


def _graph() -> CapabilityGraph:
    nodes = []
    for target_id, target_kind, target_owner, _, _, availability, health in (
        TARGETS.values()
    ):
        nodes.append(
            {
                "id": target_id,
                "kind": target_kind,
                "contract_level": "executable",
                "primary_parent": None,
                "source_family": "fixture",
                "source_path": f"capabilities/{target_id}.yaml",
                "owner": {
                    "authority": "authored",
                    "repo": target_owner,
                    "surface": f"owner/{target_id}",
                },
                "lifecycle": {
                    "state": (
                        "dormant" if health == "unavailable" else "active"
                    ),
                    "visibility": "internal",
                    "evidence_state": "fixture",
                    "health": health,
                    "version": "1",
                },
                "binding": {"availability": availability},
            }
        )
    return CapabilityGraph.model_validate(
        {
            "schema_version": "aoa-capability-graph-v1",
            "authority": False,
            "source": {
                "root": "capabilities",
                "family_files": [],
                "referenced_files": [],
                "content_hash": "fixture",
            },
            "roots": [nodes[0]["id"]],
            "nodes": nodes,
            "relations": [],
            "retrieval_documents": [],
        }
    )


def _migration_payload() -> dict:
    return {
        "schema_version": "aoa-skill-migration-v1",
        "entries": [
            {
                "legacy_name": requirement_id,
                "legacy_path": f"skills/{requirement_id}/SKILL.md",
                "action": target[3],
                "target_id": target[0],
                "target_kind": target[1],
                "target_owner": target[2],
                "compatibility": target[4],
                "evidence_state": "fixture",
                "reason": "fixture",
            }
            for requirement_id, target in TARGETS.items()
        ],
    }


class _RoutingSnapshot:
    def __init__(self) -> None:
        self.capability_graph = _graph()
        self.input_snapshot_digest = ZERO_DIGEST
        self.source_lock = SimpleNamespace(
            capability_graph=SimpleNamespace(
                source_ref=SKILLS_REF,
                relative_path="generated/capability_graph.json",
                schema_ref="schemas/capability_graph.schema.json",
                schema_version="aoa-capability-graph-v1",
            ),
            owner_source_refs={
                "aoa-agents": AGENTS_REF,
                "aoa-evals": EVALS_REF,
                "aoa-memo": MEMO_REF,
            },
        )

    def validated_for_resolution(self) -> _RoutingSnapshot:
        return self


def _owner_artifacts(migration: dict | None = None) -> dict[tuple[str, str], bytes]:
    snapshot = load_plan_compilation_snapshot()
    contour = snapshot.contour_for("bounded_change_safe")
    agents = {
        "version": 2,
        "layer": "aoa-agents",
        "artifact_identity": {"abi_epoch": "aoa_agents_role_registry_v2"},
        "agents": [
            {"name": agent_id, "status": "active"}
            for agent_id in contour.required_agent_ids
        ],
    }
    artifacts = {
        ("aoa-playbooks", contour.source_playbook_ref): (
            b"---\nid: AOA-P-0011\nscenario: bounded_change_safe\n---\n"
        ),
        ("aoa-agents", "generated/agent_registry.min.json"): (
            json.dumps(agents).encode()
        ),
        ("aoa-evals", "generated/eval_catalog.min.json"): b"{}\n",
        (
            "aoa-memo",
            "mechanics/checkpoint/parts/checkpoint-to-memory-mapping/"
            "examples/checkpoint_to_memory_contract.example.json",
        ): b"{}\n",
    }
    if migration is not None:
        artifacts[
            ("aoa-skills", "capabilities/legacy-skill-migration.yaml")
        ] = yaml.safe_dump(migration).encode()
    return artifacts


def _patch_owner_reads(
    monkeypatch: pytest.MonkeyPatch,
    artifacts: dict[tuple[str, str], bytes],
) -> None:
    def read(
        _workspace: object,
        *,
        owner_repo: str,
        source_ref: str,
        relative_path: str,
    ) -> bytes:
        assert len(source_ref) == 40
        return artifacts[(owner_repo, relative_path)]

    monkeypatch.setattr(scenario_bindings, "_read_git_artifact", read)


def _decision(scenario, routing_snapshot: _RoutingSnapshot) -> RouteDecision:
    candidate = RouteCandidate(
        candidate_id="aoa-skills:skill:entry-route",
        capability=CapabilityRef(
            capability_id="skill.entry-route",
            capability_kind="skill",
            provenance=_provenance("aoa-skills"),
        ),
        agent=AgentRef(
            agent_id="requester-not-in-contour",
            provenance=_provenance("agent-session"),
        ),
        scenario=scenario,
        rank=0,
        compatibility="compatible",
        policy_posture="eligible",
        reason_codes=("fixture-entry-route",),
        evidence_refs=(),
    )
    return RouteDecision(
        decision_id="route-decision:fixture:resolved-binding",
        correlation_id="correlation:fixture:resolved-binding",
        intent_ref=ContentRef(
            object_id="intent:fixture:resolved-binding",
            owner_repo="agent-session",
            schema_version="aoa_control_plane_v1",
            digest=ZERO_DIGEST,
        ),
        status="resolved",
        candidates=(candidate,),
        selected_candidate_id=candidate.candidate_id,
        resolver_version="fixture-route-resolver",
        reason_codes=("fixture-resolved",),
        input_snapshot_digest=routing_snapshot.input_snapshot_digest,
        provenance=_provenance("aoa-sdk"),
    )


def test_owner_resolved_scenario_binding_compiles_without_hidden_refs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_owner_reads(monkeypatch, _owner_artifacts())
    routing_snapshot = _RoutingSnapshot()
    plan_snapshot = load_plan_compilation_snapshot()
    scenario = resolve_scenario_ref(
        object(),
        "bounded_change_safe",
        plan_snapshot,
    )
    decision = _decision(scenario, routing_snapshot)
    binding = bind_scenario(
        object(),
        decision,
        "bounded_change_safe",
        routing_snapshot,
        plan_snapshot,
        binding_id="scenario-binding:fixture:resolved",
        provenance=_provenance("agent-session"),
        input_refs=(_provenance("request-owner"),),
        condition_bindings=(
            ScenarioConditionBinding(
                condition_id="preview_required",
                value=False,
                provenance=_provenance("reviewer"),
            ),
        ),
    )

    plan = compile_run_plan(
        decision,
        binding,
        reference_runtime_profile(),
        plan_snapshot,
    )

    assert [agent.agent_id for agent in binding.agent_refs] == [
        "architect",
        "coder",
        "reviewer",
        "memory-keeper",
    ]
    assert [
        item.requirement_id for item in binding.capability_bindings
    ] == [target[0] for target in TARGETS.values()]
    assert binding.capability_bindings[0].semantic_owner_repo == "host-runtime"
    preview = next(
        item
        for item in binding.capability_bindings
        if item.requirement_id == "guard.operations.preview"
    )
    assert preview.capability.capability_id == "guard.operations.preview"
    assert preview.availability == "unbound"
    assert preview.lifecycle_health == "unavailable"
    assert all(
        item.binding_action == "direct-graph-id"
        and item.compatibility == "exact-id"
        and item.migration_provenance == item.capability.provenance
        for item in binding.capability_bindings
    )
    assert decision.candidates[0].capability not in binding.capability_refs
    plan_sources = {
        (item.owner_repo, item.artifact_ref) for item in plan.snapshot.source_refs
    }
    assert {
        (
            item.migration_provenance.owner_repo,
            item.migration_provenance.artifact_ref,
        )
        for item in binding.capability_bindings
    }.issubset(plan_sources)
    assert [step.step_id for step in plan.steps] == [
        "orient",
        "mutate",
        "verify",
        "closeout",
    ]


def test_binding_rejects_route_snapshot_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_owner_reads(monkeypatch, _owner_artifacts())
    routing_snapshot = _RoutingSnapshot()
    plan_snapshot = load_plan_compilation_snapshot()
    scenario = resolve_scenario_ref(
        object(),
        "bounded_change_safe",
        plan_snapshot,
    )
    decision = _decision(scenario, routing_snapshot).model_copy(
        update={"input_snapshot_digest": "sha256:" + "f" * 64}
    )

    with pytest.raises(
        ScenarioBindingError,
        match="does not match the exact routing snapshot",
    ):
        bind_scenario(
            object(),
            decision,
            "bounded_change_safe",
            routing_snapshot,
            plan_snapshot,
            binding_id="scenario-binding:fixture:snapshot-drift",
            provenance=_provenance("agent-session"),
        )


def test_binding_requires_an_explicit_selected_scenario(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_owner_reads(monkeypatch, _owner_artifacts())
    routing_snapshot = _RoutingSnapshot()
    plan_snapshot = load_plan_compilation_snapshot()

    with pytest.raises(
        ScenarioBindingError,
        match="must select the exact admitted scenario",
    ):
        bind_scenario(
            object(),
            _decision(None, routing_snapshot),
            "bounded_change_safe",
            routing_snapshot,
            plan_snapshot,
            binding_id="scenario-binding:fixture:missing-scenario",
            provenance=_provenance("agent-session"),
        )


def test_owner_migration_target_mismatch_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    migration = _migration_payload()
    migration["entries"][0]["target_owner"] = "wrong-owner"
    _patch_owner_reads(monkeypatch, _owner_artifacts(migration))
    routing_snapshot = _RoutingSnapshot()
    plan_snapshot = load_plan_compilation_snapshot()
    legacy_contour = plan_snapshot.contour_for(
        "bounded_change_safe"
    ).model_copy(
        update={"required_capability_ids": tuple(TARGETS)}
    )

    with pytest.raises(
        ScenarioBindingError,
        match="disagrees with its owner migration",
    ):
        scenario_bindings._resolve_capabilities(
            object(),
            legacy_contour,
            routing_snapshot,
        )


def test_legacy_requirement_aliases_remain_migration_bound(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_owner_reads(monkeypatch, _owner_artifacts(_migration_payload()))
    routing_snapshot = _RoutingSnapshot()
    plan_snapshot = load_plan_compilation_snapshot()
    legacy_contour = plan_snapshot.contour_for(
        "bounded_change_safe"
    ).model_copy(
        update={"required_capability_ids": tuple(TARGETS)}
    )

    bindings = scenario_bindings._resolve_capabilities(
        object(),
        legacy_contour,
        routing_snapshot,
    )

    assert [item.requirement_id for item in bindings] == list(TARGETS)
    assert [item.capability.capability_id for item in bindings] == [
        target[0] for target in TARGETS.values()
    ]
    assert all(
        item.migration_provenance.artifact_ref.startswith(
            "capabilities/legacy-skill-migration.yaml#entries/"
        )
        for item in bindings
    )
