"""Owner-qualified scenario binding for the C1-to-C2 control-plane handoff."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

from ...contracts.control_plane import (
    AgentRef,
    CapabilityRef,
    ContentRef,
    ProvenanceRef,
    RouteDecision,
    ScenarioArtifactBinding,
    ScenarioBinding,
    ScenarioCapabilityBinding,
    ScenarioConditionBinding,
    ScenarioRef,
    canonical_digest,
)
from ...errors import AoASDKError, RepoNotFound
from ...workspace.discovery import Workspace
from ..routing.snapshot import RoutingResolutionSnapshot
from .snapshot import PlanCompilationSnapshot, PlanContour


_OID_RE = re.compile(r"^[0-9a-f]{40}$")
_AGENT_REGISTRY_PATH = "generated/agent_registry.min.json"
_CAPABILITY_MIGRATION_PATH = "capabilities/legacy-skill-migration.yaml"
_PLAYBOOK_SOURCE_SCHEMA = (
    "mechanics/activation/parts/activation-surface/"
    "docs/playbook-bundle-contract.md"
)


class ScenarioBindingError(AoASDKError, ValueError):
    """Exact owner inputs cannot form the requested scenario binding."""


def resolve_scenario_ref(
    workspace: Workspace,
    scenario_id: str,
    snapshot: PlanCompilationSnapshot,
) -> ScenarioRef:
    """Build an exact source-owned scenario ref without parsing playbook prose."""

    contour = snapshot.contour_for(scenario_id)
    raw = _read_git_artifact(
        workspace,
        owner_repo="aoa-playbooks",
        source_ref=snapshot.source_lock.owner_source_ref,
        relative_path=contour.source_playbook_ref,
    )
    return ScenarioRef(
        scenario_id=contour.scenario,
        provenance=ProvenanceRef(
            owner_repo="aoa-playbooks",
            artifact_ref=contour.source_playbook_ref,
            source_ref=snapshot.source_lock.owner_source_ref,
            artifact_digest=_sha256(raw),
            schema_ref=_PLAYBOOK_SOURCE_SCHEMA,
            schema_version="aoa_playbook_authored_bundle_v1",
        ),
    )


def bind_scenario(
    workspace: Workspace,
    decision: RouteDecision,
    scenario_id: str,
    routing_snapshot: RoutingResolutionSnapshot,
    plan_snapshot: PlanCompilationSnapshot,
    *,
    binding_id: str,
    provenance: ProvenanceRef,
    input_refs: tuple[ProvenanceRef, ...] = (),
    input_artifact_bindings: tuple[ScenarioArtifactBinding, ...] = (),
    condition_bindings: tuple[ScenarioConditionBinding, ...] = (),
) -> ScenarioBinding:
    """Resolve owner refs for one admitted contour and exact route decision."""

    routing_snapshot = routing_snapshot.validated_for_resolution()
    if decision.input_snapshot_digest != routing_snapshot.input_snapshot_digest:
        raise ScenarioBindingError(
            "route decision does not match the exact routing snapshot used for binding"
        )
    if decision.status == "blocked" or decision.selected_candidate_id is None:
        raise ScenarioBindingError("a blocked route decision cannot bind a scenario")

    contour = plan_snapshot.contour_for(scenario_id)
    scenario = resolve_scenario_ref(workspace, scenario_id, plan_snapshot)
    selected = next(
        candidate
        for candidate in decision.candidates
        if candidate.candidate_id == decision.selected_candidate_id
    )
    if selected.scenario != scenario:
        raise ScenarioBindingError(
            "route decision must select the exact admitted scenario before binding"
        )

    agents = _resolve_agents(
        workspace,
        contour,
        routing_snapshot,
    )
    capability_bindings = _resolve_capabilities(
        workspace,
        contour,
        routing_snapshot,
    )
    requirement_refs = _resolve_requirement_refs(
        workspace,
        contour,
        routing_snapshot,
    )
    decision_ref = ContentRef(
        object_id=decision.decision_id,
        owner_repo=decision.provenance.owner_repo,
        schema_version=decision.schema_version,
        digest=canonical_digest(decision),
    )
    return ScenarioBinding(
        binding_id=binding_id,
        correlation_id=decision.correlation_id,
        scenario=scenario,
        decision_ref=decision_ref,
        agent_refs=agents,
        capability_refs=tuple(
            binding.capability for binding in capability_bindings
        ),
        capability_bindings=capability_bindings,
        input_refs=input_refs,
        input_artifact_bindings=input_artifact_bindings,
        condition_bindings=condition_bindings,
        requirement_refs=requirement_refs,
        expected_artifact_kinds=contour.expected_artifact_kinds,
        provenance=provenance,
    )


def _resolve_agents(
    workspace: Workspace,
    contour: PlanContour,
    routing_snapshot: RoutingResolutionSnapshot,
) -> tuple[AgentRef, ...]:
    source_ref = _owner_source_ref(routing_snapshot, "aoa-agents")
    raw = _read_git_artifact(
        workspace,
        owner_repo="aoa-agents",
        source_ref=source_ref,
        relative_path=_AGENT_REGISTRY_PATH,
    )
    payload = _decode_json(raw, "aoa-agents agent registry")
    if payload.get("version") != 2 or payload.get("layer") != "aoa-agents":
        raise ScenarioBindingError("pinned aoa-agents registry identity is invalid")
    records = payload.get("agents")
    if not isinstance(records, list) or not all(
        isinstance(record, dict) for record in records
    ):
        raise ScenarioBindingError("pinned aoa-agents registry has invalid records")
    by_name = {
        record.get("name"): record
        for record in records
        if isinstance(record.get("name"), str)
    }
    if len(by_name) != len(records):
        raise ScenarioBindingError(
            "pinned aoa-agents registry names must be present and unique"
        )
    missing = [
        agent_id
        for agent_id in contour.required_agent_ids
        if agent_id not in by_name
    ]
    if missing:
        raise ScenarioBindingError(
            "owner contour agents are absent from the pinned aoa-agents registry: "
            + ",".join(missing)
        )
    inactive = [
        agent_id
        for agent_id in contour.required_agent_ids
        if by_name[agent_id].get("status") != "active"
    ]
    if inactive:
        raise ScenarioBindingError(
            "owner contour agents are not active in the pinned registry: "
            + ",".join(inactive)
        )
    artifact_identity = payload.get("artifact_identity")
    abi_epoch = (
        artifact_identity.get("abi_epoch")
        if isinstance(artifact_identity, dict)
        else None
    )
    schema_version = (
        abi_epoch
        if isinstance(abi_epoch, str)
        else "aoa_agents_role_registry_v2"
    )
    digest = _sha256(raw)
    return tuple(
        AgentRef(
            agent_id=agent_id,
            provenance=ProvenanceRef(
                owner_repo="aoa-agents",
                artifact_ref=f"{_AGENT_REGISTRY_PATH}#agents/{agent_id}",
                source_ref=source_ref,
                artifact_digest=digest,
                schema_ref="schemas/agent-registry.schema.json",
                schema_version=schema_version,
            ),
        )
        for agent_id in contour.required_agent_ids
    )


def _resolve_capabilities(
    workspace: Workspace,
    contour: PlanContour,
    routing_snapshot: RoutingResolutionSnapshot,
) -> tuple[ScenarioCapabilityBinding, ...]:
    source_ref = routing_snapshot.source_lock.capability_graph.source_ref
    nodes = {node.id: node for node in routing_snapshot.capability_graph.nodes}
    legacy_requirement_ids = tuple(
        requirement_id
        for requirement_id in contour.required_capability_ids
        if requirement_id not in nodes
    )
    by_name: dict[str, dict[str, object]] = {}
    if legacy_requirement_ids:
        raw = _read_git_artifact(
            workspace,
            owner_repo="aoa-skills",
            source_ref=source_ref,
            relative_path=_CAPABILITY_MIGRATION_PATH,
        )
        try:
            payload = yaml.safe_load(raw)
        except yaml.YAMLError as exc:
            raise ScenarioBindingError(
                f"pinned aoa-skills capability migration is invalid YAML: {exc}"
            ) from exc
        if not isinstance(payload, dict) or payload.get("schema_version") != (
            "aoa-skill-migration-v1"
        ):
            raise ScenarioBindingError(
                "pinned aoa-skills capability migration identity is invalid"
            )
        records = payload.get("entries")
        if not isinstance(records, list) or not all(
            isinstance(record, dict) for record in records
        ):
            raise ScenarioBindingError(
                "pinned aoa-skills capability migration has invalid entries"
            )
        by_name = {
            record.get("legacy_name"): record
            for record in records
            if isinstance(record.get("legacy_name"), str)
        }
        if len(by_name) != len(records):
            raise ScenarioBindingError(
                "pinned aoa-skills migration names must be present and unique"
            )

    bindings: list[ScenarioCapabilityBinding] = []
    graph_lock = routing_snapshot.source_lock.capability_graph
    for requirement_id in contour.required_capability_ids:
        node = nodes.get(requirement_id)
        migration: dict[str, object] | None = None
        if node is None:
            migration = by_name.get(requirement_id)
            if migration is None:
                raise ScenarioBindingError(
                    f"owner contour capability {requirement_id!r} is absent from "
                    "the graph and has no pinned migration"
                )
            target_id = _required_string(migration, "target_id", requirement_id)
            target_kind = _required_string(
                migration,
                "target_kind",
                requirement_id,
            )
            target_owner = _required_string(
                migration,
                "target_owner",
                requirement_id,
            )
            node = nodes.get(target_id)
            if node is None:
                raise ScenarioBindingError(
                    f"pinned capability target {target_id!r} is absent from the graph"
                )
            if node.kind != target_kind or node.owner.repo != target_owner:
                raise ScenarioBindingError(
                    f"pinned capability target {target_id!r} disagrees with its "
                    "owner migration"
                )

        availability = node.binding.get("availability")
        health = node.lifecycle.health
        if not isinstance(availability, str) or not availability:
            raise ScenarioBindingError(
                f"pinned capability target {node.id!r} has no availability"
            )
        if not isinstance(health, str) or not health:
            raise ScenarioBindingError(
                f"pinned capability target {node.id!r} has no health"
            )
        node_provenance = ProvenanceRef(
            owner_repo="aoa-skills",
            artifact_ref=f"{graph_lock.relative_path}#nodes/{node.id}",
            source_ref=source_ref,
            artifact_digest=canonical_digest(node),
            schema_ref=graph_lock.schema_ref,
            schema_version=graph_lock.schema_version,
        )
        if migration is None:
            binding_action = "direct-graph-id"
            compatibility = "exact-id"
            resolution_provenance = node_provenance
        else:
            binding_action = _required_string(
                migration,
                "action",
                requirement_id,
            )
            compatibility = _required_string(
                migration,
                "compatibility",
                requirement_id,
            )
            resolution_provenance = ProvenanceRef(
                owner_repo="aoa-skills",
                artifact_ref=(
                    f"{_CAPABILITY_MIGRATION_PATH}"
                    f"#entries/{requirement_id}"
                ),
                source_ref=source_ref,
                artifact_digest=_mapping_digest(migration),
                schema_ref=_CAPABILITY_MIGRATION_PATH,
                schema_version="aoa-skill-migration-v1",
            )
        bindings.append(
            ScenarioCapabilityBinding(
                requirement_id=requirement_id,
                capability=CapabilityRef(
                    capability_id=node.id,
                    capability_kind=node.kind,
                    provenance=node_provenance,
                ),
                semantic_owner_repo=node.owner.repo,
                binding_action=binding_action,
                compatibility=compatibility,
                availability=availability,
                lifecycle_state=node.lifecycle.state,
                lifecycle_health=health,
                migration_provenance=resolution_provenance,
            )
        )
    return tuple(bindings)


def _resolve_requirement_refs(
    workspace: Workspace,
    contour: PlanContour,
    routing_snapshot: RoutingResolutionSnapshot,
) -> tuple[ProvenanceRef, ...]:
    refs: dict[tuple[str, str], ProvenanceRef] = {}
    requirement_inputs = [
        (requirement.input_ref.owner_repo, requirement.input_ref.artifact_ref)
        for requirement in contour.eval_requirements
    ]
    requirement_inputs.extend(
        (requirement.input_ref.owner_repo, requirement.input_ref.artifact_ref)
        for requirement in contour.retention_requirements
    )
    rollback_input = contour.rollback_policy.rollback_artifact_input_ref
    if rollback_input is not None:
        requirement_inputs.append(
            (rollback_input.owner_repo, rollback_input.artifact_ref)
        )
    for owner_repo, artifact_ref in requirement_inputs:
        key = (owner_repo, artifact_ref)
        if key in refs:
            continue
        source_ref = _owner_source_ref(routing_snapshot, owner_repo)
        raw = _read_git_artifact(
            workspace,
            owner_repo=owner_repo,
            source_ref=source_ref,
            relative_path=artifact_ref,
        )
        refs[key] = ProvenanceRef(
            owner_repo=owner_repo,
            artifact_ref=artifact_ref,
            source_ref=source_ref,
            artifact_digest=_sha256(raw),
            schema_ref=artifact_ref,
            schema_version="pinned_git_artifact_v1",
        )
    return tuple(refs.values())


def _owner_source_ref(
    routing_snapshot: RoutingResolutionSnapshot,
    owner_repo: str,
) -> str:
    source_ref = routing_snapshot.source_lock.owner_source_refs.get(owner_repo)
    if not isinstance(source_ref, str) or not _OID_RE.fullmatch(source_ref):
        raise ScenarioBindingError(
            f"routing snapshot has no exact source ref for owner {owner_repo!r}"
        )
    return source_ref


def _read_git_artifact(
    workspace: Workspace,
    *,
    owner_repo: str,
    source_ref: str,
    relative_path: str,
) -> bytes:
    if not _OID_RE.fullmatch(source_ref):
        raise ScenarioBindingError(
            f"source ref for owner {owner_repo!r} is not an exact Git OID"
        )
    path = Path(relative_path)
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise ScenarioBindingError(
            f"owner artifact path is not bounded: {relative_path!r}"
        )
    try:
        repo_root = workspace.repo_path(owner_repo)
    except RepoNotFound as exc:
        raise ScenarioBindingError(
            f"required owner repository is unavailable: {owner_repo}"
        ) from exc
    result = subprocess.run(
        [
            "git",
            "-C",
            str(repo_root),
            "show",
            f"{source_ref}:{path.as_posix()}",
        ],
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise ScenarioBindingError(
            f"cannot read pinned {owner_repo}:{path.as_posix()}@{source_ref}: "
            f"{detail or 'git show failed'}"
        )
    return result.stdout


def _required_string(
    record: Mapping[str, Any],
    field: str,
    requirement_id: str,
) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value:
        raise ScenarioBindingError(
            f"capability migration {requirement_id!r} has invalid field {field!r}"
        )
    return value


def _decode_json(raw: bytes, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ScenarioBindingError(f"{label} is invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ScenarioBindingError(f"{label} must contain an object")
    return payload


def _sha256(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _mapping_digest(value: Mapping[str, Any]) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return _sha256(raw)
