from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest
from typer.testing import CliRunner

from aoa_sdk import AoASDK
from aoa_sdk.cli.main import app
from aoa_sdk.contracts.control_plane import (
    AgentRef,
    ProvenanceRef,
    RouteConstraint,
    RouteIntent,
    assert_decision_matches_intent,
    assert_explanation_matches_decision,
)
from aoa_sdk.control_plane import ControlPlaneAPI
from aoa_sdk.control_plane.routing.snapshot import RoutingSnapshotError
from aoa_sdk.workspace.discovery import Workspace


REPO_ROOT = Path(__file__).resolve().parents[5]
ROUTING_SCHEMAS = REPO_ROOT / "src" / "aoa_sdk" / "control_plane" / "routing" / "schemas"
ZERO_DIGEST = "sha256:" + "0" * 64
SDK_PRODUCER_REF = "a" * 40
RUNTIME_CONSUMER_REF = "b" * 40
ROUTING_SUBJECT_DIGEST = "sha256:" + "c" * 64


def _sha256(raw: bytes) -> str:
    return f"sha256:{hashlib.sha256(raw).hexdigest()}"


def _canonical_digest(payload: object) -> str:
    return _sha256(
        json.dumps(
            payload,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    )


def _write_json(path: Path, payload: dict) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    ).encode()
    path.write_bytes(raw)
    return raw


def _git_capability_graph(
    workspace_root: Path,
    *,
    ambiguous: bool = False,
    deferred: bool = False,
    negative_phrase: str | None = None,
    owner_mismatch: bool = False,
    owner_health: str | None = "healthy",
) -> tuple[str, bytes]:
    repo = workspace_root / "aoa-skills"
    graph_path = repo / "generated" / "capability_graph.json"
    capability_specs = [
        {
            "id": "skill.aoa-decision",
            "title": "AoA Decision",
            "description": "Find and record durable repository decisions.",
            "positive_tokens": ["decision", "durable", "rationale"],
            "routing_tokens": ["decision"],
            "tokens": ["decision", "durable", "repository", "rationale"],
            "negative_tokens": ["ordinary"],
            "negative_phrases": [negative_phrase] if negative_phrase else [],
            "visibility": "deferred" if deferred else "advertised",
        },
        {
            "id": "skill.aoa-eval",
            "title": "AoA Eval",
            "description": "Select a bounded evaluation surface.",
            "positive_tokens": (
                ["decision", "durable", "rationale"]
                if ambiguous
                else ["eval", "evaluation", "proof"]
            ),
            "routing_tokens": ["decision"] if ambiguous else ["eval"],
            "tokens": (
                ["decision", "durable", "repository", "rationale"]
                if ambiguous
                else ["eval", "evaluation", "proof"]
            ),
            "negative_tokens": [],
            "negative_phrases": [],
            "visibility": "advertised",
        },
    ]
    nodes = []
    documents = []
    for spec in capability_specs:
        nodes.append(
            {
                "id": spec["id"],
                "kind": "skill",
                "contract_level": "executable",
                "primary_parent": "aoa",
                "source_family": "fixture",
                "source_path": "capabilities/families/fixture.yaml",
                "owner": {
                    "authority": "authored",
                    "repo": (
                        "aoa-evals"
                        if owner_mismatch and spec["id"] == "skill.aoa-decision"
                        else "aoa-skills"
                    ),
                    "surface": f"skills/{spec['id'].removeprefix('skill.')}/SKILL.md",
                },
                "lifecycle": {
                    "state": "candidate",
                    "visibility": spec["visibility"],
                    "health": owner_health,
                    "version": "1.0.0",
                },
                "title": spec["title"],
                "description": spec["description"],
                "binding": {
                    "availability": "available",
                    "kind": "skill",
                    "operation": "route-one-mode",
                    "ref": (
                        "skills/"
                        f"{spec['id'].removeprefix('skill.')}/SKILL.md"
                    ),
                },
                "trust": {
                    "posture": "authored-procedure",
                    "public_safe": True,
                    "requires_human_approval": False,
                },
                "execution": {"effects": ["none"]},
            }
        )
        documents.append(
            {
                "id": spec["id"],
                "kind": "skill",
                "visibility": spec["visibility"],
                "title": spec["title"],
                "description": spec["description"],
                "search_text": spec["description"],
                "positive_text": spec["description"],
                "negative_text": " ".join(spec["negative_phrases"]),
                "negative_phrases": spec["negative_phrases"],
                "routing_tokens": spec["routing_tokens"],
                "positive_tokens": spec["positive_tokens"],
                "negative_tokens": spec["negative_tokens"],
                "tokens": spec["tokens"],
            }
        )
    graph = {
        "schema_version": "aoa-capability-graph-v1",
        "authority": False,
        "source": {
            "root": "capabilities/families",
            "family_files": [],
            "referenced_files": [],
            "content_hash": "fixture-route-resolution",
        },
        "roots": ["aoa"],
        "nodes": nodes,
        "relations": [],
        "retrieval_documents": documents,
    }
    graph_raw = _write_json(graph_path, graph)
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "AoA Test"], cwd=repo, check=True)
    subprocess.run(
        ["git", "config", "user.email", "aoa-test@example.invalid"],
        cwd=repo,
        check=True,
    )
    subprocess.run(
        ["git", "add", "generated/capability_graph.json"],
        cwd=repo,
        check=True,
    )
    subprocess.run(
        ["git", "commit", "-q", "-m", "fixture capability graph"],
        cwd=repo,
        check=True,
    )
    source_ref = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return source_ref, graph_raw


def _routing_inputs(
    workspace_root: Path,
    *,
    ambiguous: bool = False,
    deferred: bool = False,
    negative_phrase: str | None = None,
    owner_mismatch: bool = False,
    owner_health: str | None = "healthy",
    malformed_registry_attribute: tuple[str, object] | None = None,
) -> tuple[Path, Path]:
    shutil.rmtree(workspace_root / "aoa-routing")
    bundle_root = (
        workspace_root
        / "abyss-stack"
        / "Knowledge"
        / "federation"
        / "aoa-routing"
    )
    source_ref, graph_raw = _git_capability_graph(
        workspace_root,
        ambiguous=ambiguous,
        deferred=deferred,
        negative_phrase=negative_phrase,
        owner_mismatch=owner_mismatch,
        owner_health=owner_health,
    )
    router_raw = _write_json(
        bundle_root / "generated" / "aoa_router.min.json",
        {
            "schema_version": "fixture-router-v1",
            "owner_repo": "aoa-sdk",
        },
    )
    entries = []
    for name in ("aoa-decision", "aoa-eval"):
        attributes = {
            "scope": "fixture",
            "invocation_mode": (
                "suggest" if deferred and name == "aoa-decision" else "invoke"
            ),
            "allow_implicit_invocation": not (
                deferred and name == "aoa-decision"
            ),
            "candidate_only": deferred and name == "aoa-decision",
            "capability_id": f"skill.{name}",
            "capability_graph_ref": "generated/capability_graph.json",
            "capability_source_path": "capabilities/families/fixture.yaml",
            "target_owner": "aoa-skills",
            "requires_human_approval": False,
        }
        if malformed_registry_attribute is not None and name == "aoa-decision":
            field, value = malformed_registry_attribute
            attributes[field] = value
        entries.append(
            {
                "kind": "skill",
                "id": name,
                "name": name,
                "repo": "aoa-skills",
                "path": f"skills/{name}/SKILL.md",
                "status": "candidate",
                "summary": f"{name} fixture route",
                "source_type": "generated-catalog",
                "attributes": attributes,
            }
        )
    registry_raw = _write_json(
        bundle_root / "generated" / "cross_repo_registry.min.json",
        {
            "registry_version": 1,
            "reserved_kinds": [],
            "entries": entries,
        },
    )
    hints_raw = _write_json(
        bundle_root / "generated" / "task_to_surface_hints.json",
        {
            "version": 1,
            "hints": [
                {
                    "kind": "skill",
                    "enabled": True,
                    "source_repo": "aoa-skills",
                    "use_when": "a typed callable capability is requested",
                    "actions": {
                        "pick": {"enabled": True},
                        "inspect": {
                            "enabled": True,
                            "surface_file": "generated/agent_skill_catalog.min.json",
                            "match_field": "name",
                        },
                        "expand": {
                            "enabled": True,
                            "surface_file": "generated/capability_graph.json",
                            "match_field": "id",
                            "section_key_field": "id",
                            "default_sections": [],
                            "supported_sections": [],
                        },
                        "pair": {"enabled": False},
                        "recall": {"enabled": False},
                    },
                }
            ],
        },
    )
    schema_artifacts: dict[str, bytes] = {}
    for name in (
        "cross-repo-registry.schema.json",
        "router-entry.schema.json",
        "task-to-surface-hints.schema.json",
    ):
        target = bundle_root / "schemas" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROUTING_SCHEMAS / name, target)
        schema_artifacts[name] = target.read_bytes()

    authority = {
        "archive_authorized": False,
        "canonical_producer_switch_authorized": True,
        "compatibility_window_started": True,
        "live_runtime_mutation_authorized": True,
        "predecessor_maintenance_only": True,
        "sdk_canonical": True,
    }
    owner_switch_receipt = {
        "schema": "aoa_sdk_routing_g5_owner_switch_receipt_v1",
        "status": "g5_switch_authorized",
        "g5_authority": authority,
        "sdk": {"source_ref": SDK_PRODUCER_REF},
        "runtime_consumer": {
            "owner_repo": "abyss-stack",
            "source_ref": RUNTIME_CONSUMER_REF,
        },
    }
    owner_switch_receipt_digest = _canonical_digest(owner_switch_receipt)
    source_lock = {
        "schema_version": "aoa_control_plane_routing_source_lock_v1",
        "routing_abi": {
            "abi_id": "aoa_routing_thin_router_v1",
            "abi_version": "aoa_routing_thin_router_v1",
            "owner_repo": "aoa-sdk",
            "schema_ref": "schemas/aoa-router.schema.json",
            "source_ref": SDK_PRODUCER_REF,
            "artifact_digest": _sha256(router_raw),
        },
        "routing_bundle_subject_digest": ROUTING_SUBJECT_DIGEST,
        "owner_switch_receipt_digest": owner_switch_receipt_digest,
        "runtime_consumer_source_ref": RUNTIME_CONSUMER_REF,
        "runtime_manifest_schema_ref": (
            "abyss-stack:schemas/federation-mirror-manifest.schema.json"
        ),
        "cross_repo_registry": {
            "owner_repo": "aoa-sdk",
            "relative_path": "generated/cross_repo_registry.min.json",
            "source_ref": SDK_PRODUCER_REF,
            "artifact_digest": _sha256(registry_raw),
            "schema_ref": "schemas/cross-repo-registry.schema.json",
            "schema_version": "1",
        },
        "cross_repo_registry_schema": {
            "owner_repo": "aoa-sdk",
            "relative_path": "schemas/cross-repo-registry.schema.json",
            "source_ref": SDK_PRODUCER_REF,
            "artifact_digest": _sha256(
                schema_artifacts["cross-repo-registry.schema.json"]
            ),
            "schema_ref": "schemas/cross-repo-registry.schema.json",
            "schema_version": "1",
        },
        "router_entry_schema": {
            "owner_repo": "aoa-sdk",
            "relative_path": "schemas/router-entry.schema.json",
            "source_ref": SDK_PRODUCER_REF,
            "artifact_digest": _sha256(
                schema_artifacts["router-entry.schema.json"]
            ),
            "schema_ref": "schemas/router-entry.schema.json",
            "schema_version": "1",
        },
        "task_to_surface_hints": {
            "owner_repo": "aoa-sdk",
            "relative_path": "generated/task_to_surface_hints.json",
            "source_ref": SDK_PRODUCER_REF,
            "artifact_digest": _sha256(hints_raw),
            "schema_ref": "schemas/task-to-surface-hints.schema.json",
            "schema_version": "1",
        },
        "task_to_surface_hints_schema": {
            "owner_repo": "aoa-sdk",
            "relative_path": "schemas/task-to-surface-hints.schema.json",
            "source_ref": SDK_PRODUCER_REF,
            "artifact_digest": _sha256(
                schema_artifacts["task-to-surface-hints.schema.json"]
            ),
            "schema_ref": "schemas/task-to-surface-hints.schema.json",
            "schema_version": "1",
        },
        "capability_graph": {
            "owner_repo": "aoa-skills",
            "relative_path": "generated/capability_graph.json",
            "source_ref": source_ref,
            "artifact_digest": _sha256(graph_raw),
            "schema_ref": "schemas/capability_graph.schema.json",
            "schema_version": "aoa-capability-graph-v1",
        },
        "owner_source_refs": {
            "aoa-sdk": SDK_PRODUCER_REF,
            "aoa-skills": source_ref,
        },
    }
    source_lock_path = workspace_root / "routing-source-lock.json"
    _write_json(source_lock_path, source_lock)
    _write_json(
        bundle_root / "manifest" / "federation_mirror_manifest.json",
        {
            "schema": "abyss_stack_federation_mirror_manifest_v1",
            "layer": "aoa-routing",
            "source_git_commit": SDK_PRODUCER_REF,
            "routing_producer_posture": "sdk_canonical",
            "cutover_activation_mode": "authorized_live_cutover",
            "mirror_is_authority": False,
            "artifact_subject_digest": ROUTING_SUBJECT_DIGEST,
            "owner_switch_receipt_digest": owner_switch_receipt_digest,
            "g5_authority": authority,
            "canonical_producer": {
                "owner_repo": "aoa-sdk",
                "source_ref": SDK_PRODUCER_REF,
            },
            "owner_switch_receipt": owner_switch_receipt,
            "trust_verdict": {
                "ok": True,
                "verdict": "allow",
                "subject_digest": ROUTING_SUBJECT_DIGEST,
                "decision": {"allow": True},
                "record": {
                    "producer_admission": {
                        "profile_id": "aoa-sdk-g5-canonical",
                        "owner_repo": "aoa-sdk",
                        "canonical_owner_repo": "aoa-sdk",
                        "source_ref": SDK_PRODUCER_REF,
                        "status": "canonical_producer",
                        "g5_authority": authority,
                        "owner_switch_receipt": {
                            "digest": owner_switch_receipt_digest,
                        },
                    }
                },
            },
            "file_sha256": {
                "generated/aoa_router.min.json": _sha256(router_raw).removeprefix(
                    "sha256:"
                ),
                "generated/cross_repo_registry.min.json": _sha256(
                    registry_raw
                ).removeprefix("sha256:"),
                "generated/task_to_surface_hints.json": _sha256(
                    hints_raw
                ).removeprefix("sha256:"),
                "schemas/cross-repo-registry.schema.json": _sha256(
                    schema_artifacts["cross-repo-registry.schema.json"]
                ).removeprefix("sha256:"),
                "schemas/router-entry.schema.json": _sha256(
                    schema_artifacts["router-entry.schema.json"]
                ).removeprefix("sha256:"),
                "schemas/task-to-surface-hints.schema.json": _sha256(
                    schema_artifacts["task-to-surface-hints.schema.json"]
                ).removeprefix("sha256:"),
            },
        },
    )
    return bundle_root, source_lock_path


def _provenance() -> ProvenanceRef:
    return ProvenanceRef(
        owner_repo="aoa-agents",
        artifact_ref="agents/c1-test-agent.json",
        source_ref="fixture-agent",
        artifact_digest=ZERO_DIGEST,
        schema_ref="schemas/agent.schema.json",
        schema_version="fixture",
    )


def _intent(
    *,
    objective: str = "find a durable repository decision and rationale",
    constraints: tuple[RouteConstraint, ...] = (),
) -> RouteIntent:
    provenance = _provenance()
    return RouteIntent(
        intent_id="intent:c1-test",
        correlation_id="correlation:c1-test",
        objective=objective,
        requested_by=AgentRef(agent_id="c1-test-agent", provenance=provenance),
        requested_capability_kinds=("skill",),
        constraints=constraints,
        authored_at=datetime(2026, 7, 26, tzinfo=timezone.utc),
        provenance=provenance,
    )


def _api(
    workspace_root: Path,
    bundle_root: Path,
    source_lock_path: Path,
) -> ControlPlaneAPI:
    return ControlPlaneAPI(
        Workspace.discover(workspace_root / "aoa-sdk"),
        routing_bundle_root=bundle_root,
        routing_source_lock=source_lock_path,
    )


def test_resolve_is_deterministic_explainable_and_needs_no_predecessor_checkout(
    workspace_root: Path,
) -> None:
    bundle_root, lock_path = _routing_inputs(workspace_root)
    api = _api(workspace_root, bundle_root, lock_path)
    intent = _intent()

    first = api.resolve(intent)
    second = api.resolve(intent)
    explanation = api.explain(first)

    assert first == second
    assert first.status == "resolved"
    assert first.selected_candidate_id == "aoa-skills:skill:aoa-decision"
    assert first.resolver_version == "aoa_control_plane_route_resolver_v1"
    assert len(first.candidates) == 2
    assert explanation.fallback_used is False
    assert len(explanation.candidate_explanations) == len(first.candidates)
    dispositions = {
        candidate.candidate_id: candidate.disposition
        for candidate in explanation.candidate_explanations
    }
    assert dispositions["aoa-skills:skill:aoa-decision"] == "selected"
    assert dispositions["aoa-skills:skill:aoa-eval"] == "rejected"
    assert not (workspace_root / "aoa-routing").exists()
    assert_decision_matches_intent(intent, first)
    assert_explanation_matches_decision(first, explanation)


def test_nonpositive_scores_are_rejected_in_blocked_explanation(
    workspace_root: Path,
) -> None:
    bundle_root, lock_path = _routing_inputs(workspace_root)
    api = _api(workspace_root, bundle_root, lock_path)

    decision = api.resolve(
        _intent(objective="weather forecast tomorrow")
    )
    explanation = api.explain(decision)

    assert decision.status == "blocked"
    assert "no_eligible_capability" in decision.reason_codes
    assert all(
        candidate.disposition == "rejected"
        for candidate in explanation.candidate_explanations
    )


def test_equal_top_scores_block_without_lexical_fallback(
    workspace_root: Path,
) -> None:
    bundle_root, lock_path = _routing_inputs(workspace_root, ambiguous=True)
    decision = _api(workspace_root, bundle_root, lock_path).resolve(_intent())

    assert decision.status == "blocked"
    assert decision.selected_candidate_id is None
    assert any(
        reason.startswith("ambiguous_top_rank:")
        for reason in decision.reason_codes
    )
    assert [candidate.rank for candidate in decision.candidates[:2]] == [0, 0]


def test_deferred_capability_requires_explicit_owner_scoped_constraint(
    workspace_root: Path,
) -> None:
    bundle_root, lock_path = _routing_inputs(workspace_root, deferred=True)
    api = _api(workspace_root, bundle_root, lock_path)

    implicit = api.resolve(_intent())
    explicit = api.resolve(
        _intent(
            constraints=(
                RouteConstraint(
                    constraint_id="require-decision",
                    kind="required_capability",
                    value="skill.aoa-decision",
                    source=_provenance(),
                ),
            )
        )
    )

    decision_candidate = next(
        candidate
        for candidate in implicit.candidates
        if candidate.capability.capability_id == "skill.aoa-decision"
    )
    assert decision_candidate.policy_posture == "forbidden"
    assert implicit.selected_candidate_id != decision_candidate.candidate_id
    assert explicit.status == "resolved"
    assert explicit.selected_candidate_id == decision_candidate.candidate_id


def test_required_capability_is_a_hard_constraint(
    workspace_root: Path,
) -> None:
    bundle_root, lock_path = _routing_inputs(workspace_root)
    decision = _api(workspace_root, bundle_root, lock_path).resolve(
        _intent(
            constraints=(
                RouteConstraint(
                    constraint_id="require-missing",
                    kind="required_capability",
                    value="skill.missing",
                    source=_provenance(),
                ),
            )
        )
    )

    assert decision.status == "blocked"
    assert decision.selected_candidate_id is None
    assert all(
        candidate.policy_posture == "forbidden"
        and "required_capability_constraint_mismatch"
        in candidate.reason_codes
        for candidate in decision.candidates
    )


def test_exact_owner_negative_phrase_blocks_candidate(
    workspace_root: Path,
) -> None:
    phrase = "ordinary documentation edit"
    bundle_root, lock_path = _routing_inputs(
        workspace_root,
        negative_phrase=phrase,
    )
    decision = _api(workspace_root, bundle_root, lock_path).resolve(
        _intent(objective=f"{phrase} with no durable decision")
    )

    decision_candidate = next(
        candidate
        for candidate in decision.candidates
        if candidate.capability.capability_id == "skill.aoa-decision"
    )
    assert decision_candidate.policy_posture == "forbidden"
    assert "owner_negative_applicability_match" in decision_candidate.reason_codes


def test_unsupported_policy_constraint_returns_typed_blocked_decision(
    workspace_root: Path,
) -> None:
    bundle_root, lock_path = _routing_inputs(workspace_root)
    decision = _api(workspace_root, bundle_root, lock_path).resolve(
        _intent(
            constraints=(
                RouteConstraint(
                    constraint_id="unknown-risk-order",
                    kind="risk_ceiling",
                    value="medium",
                    source=_provenance(),
                ),
            )
        )
    )

    assert decision.status == "blocked"
    assert decision.selected_candidate_id is None
    assert (
        "constraint_not_resolvable_in_c1:unknown-risk-order"
        in decision.reason_codes
    )


def test_snapshot_tampering_fails_closed(
    workspace_root: Path,
) -> None:
    bundle_root, lock_path = _routing_inputs(workspace_root)
    api = _api(workspace_root, bundle_root, lock_path)
    api.resolve(_intent())
    registry = bundle_root / "generated" / "cross_repo_registry.min.json"
    registry.write_bytes(registry.read_bytes() + b" ")

    with pytest.raises(RoutingSnapshotError, match="digest mismatch"):
        api.resolve(_intent())


def test_deployed_router_tampering_fails_closed(
    workspace_root: Path,
) -> None:
    bundle_root, lock_path = _routing_inputs(workspace_root)
    router = bundle_root / "generated" / "aoa_router.min.json"
    router.write_bytes(router.read_bytes() + b" ")

    with pytest.raises(
        RoutingSnapshotError,
        match="digest mismatch.*aoa_router",
    ):
        _api(workspace_root, bundle_root, lock_path).resolve(_intent())


def test_embedded_owner_switch_receipt_tampering_fails_closed(
    workspace_root: Path,
) -> None:
    bundle_root, lock_path = _routing_inputs(workspace_root)
    manifest_path = (
        bundle_root / "manifest" / "federation_mirror_manifest.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["owner_switch_receipt"]["authorized_at"] = "tampered"
    _write_json(manifest_path, manifest)

    with pytest.raises(RoutingSnapshotError, match="locked digest"):
        _api(workspace_root, bundle_root, lock_path).resolve(_intent())


@pytest.mark.parametrize(
    ("field_path", "match"),
    (
        (("trust_verdict",), "trust verdict must be a JSON object"),
        (
            ("trust_verdict", "decision"),
            "trust decision must be a JSON object",
        ),
        (
            ("trust_verdict", "record"),
            "trust record must be a JSON object",
        ),
        (
            ("trust_verdict", "record", "producer_admission"),
            "producer admission must be a JSON object",
        ),
        (
            (
                "trust_verdict",
                "record",
                "producer_admission",
                "owner_switch_receipt",
            ),
            "producer receipt summary must be a JSON object",
        ),
        (("file_sha256",), "manifest file hashes must be a JSON object"),
    ),
)
def test_malformed_runtime_manifest_objects_fail_closed(
    workspace_root: Path,
    field_path: tuple[str, ...],
    match: str,
) -> None:
    bundle_root, lock_path = _routing_inputs(workspace_root)
    manifest_path = (
        bundle_root / "manifest" / "federation_mirror_manifest.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    parent = manifest
    for field in field_path[:-1]:
        parent = parent[field]
    parent[field_path[-1]] = []
    _write_json(manifest_path, manifest)

    with pytest.raises(RoutingSnapshotError, match=match):
        _api(workspace_root, bundle_root, lock_path).resolve(_intent())


def test_source_lock_owner_binding_fails_closed(
    workspace_root: Path,
) -> None:
    bundle_root, lock_path = _routing_inputs(workspace_root)
    source_lock = json.loads(lock_path.read_text(encoding="utf-8"))
    source_lock["owner_source_refs"]["aoa-sdk"] = "e" * 40
    _write_json(lock_path, source_lock)

    with pytest.raises(RoutingSnapshotError, match="bind aoa-sdk"):
        _api(workspace_root, bundle_root, lock_path).resolve(_intent())


def test_inconsistent_registry_and_owner_projection_blocks(
    workspace_root: Path,
) -> None:
    bundle_root, lock_path = _routing_inputs(
        workspace_root,
        owner_mismatch=True,
    )
    decision = _api(workspace_root, bundle_root, lock_path).resolve(_intent())

    assert decision.status == "blocked"
    assert decision.selected_candidate_id is None
    assert (
        "routing_candidates_inconsistent_owner_projection:aoa-decision"
        in decision.reason_codes
    )


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("candidate_only", "true"),
        ("allow_implicit_invocation", "false"),
        ("requires_human_approval", "false"),
        ("requires_human_approval", True),
        ("invocation_mode", ["invoke"]),
        ("capability_id", "skill.aoa-eval"),
    ),
)
def test_invalid_registry_invocation_posture_blocks(
    workspace_root: Path,
    field: str,
    value: object,
) -> None:
    bundle_root, lock_path = _routing_inputs(
        workspace_root,
        malformed_registry_attribute=(field, value),
    )

    decision = _api(workspace_root, bundle_root, lock_path).resolve(_intent())

    assert decision.status == "blocked"
    assert decision.selected_candidate_id is None
    assert (
        "routing_candidates_inconsistent_owner_projection:aoa-decision"
        in decision.reason_codes
    )


@pytest.mark.parametrize("owner_health", (None, "unhealthy", "blocked"))
def test_missing_or_unrecognized_owner_health_is_incompatible(
    workspace_root: Path,
    owner_health: str | None,
) -> None:
    bundle_root, lock_path = _routing_inputs(
        workspace_root,
        owner_health=owner_health,
    )

    decision = _api(workspace_root, bundle_root, lock_path).resolve(_intent())

    assert decision.status == "blocked"
    assert decision.selected_candidate_id is None
    assert all(
        candidate.compatibility == "incompatible"
        and "owner_health_missing_or_unrecognized" in candidate.reason_codes
        for candidate in decision.candidates
    )


def test_degraded_owner_health_remains_an_explicit_degraded_posture(
    workspace_root: Path,
) -> None:
    bundle_root, lock_path = _routing_inputs(
        workspace_root,
        owner_health="degraded",
    )

    decision = _api(workspace_root, bundle_root, lock_path).resolve(_intent())

    assert decision.status == "degraded"
    assert decision.selected_candidate_id is not None
    selected = next(
        candidate
        for candidate in decision.candidates
        if candidate.candidate_id == decision.selected_candidate_id
    )
    assert selected.compatibility == "degraded"
    assert "owner_health_degraded" in selected.reason_codes


def test_conflicting_effect_ceilings_block_deterministically(
    workspace_root: Path,
) -> None:
    bundle_root, lock_path = _routing_inputs(workspace_root)
    intent = _intent(
        constraints=(
            RouteConstraint(
                constraint_id="read-only",
                kind="effect_ceiling",
                value="read_only",
                source=_provenance(),
            ),
            RouteConstraint(
                constraint_id="runtime",
                kind="effect_ceiling",
                value="runtime_mutation",
                source=_provenance(),
            ),
        )
    )
    api = _api(workspace_root, bundle_root, lock_path)

    first = api.resolve(intent)
    second = api.resolve(intent)

    assert first == second
    assert first.status == "blocked"
    assert first.selected_candidate_id is None
    assert (
        "conflicting_effect_ceiling_constraints:read_only,runtime_mutation"
        in first.reason_codes
    )


def test_route_cli_resolve_explain_and_validate(
    workspace_root: Path,
) -> None:
    bundle_root, lock_path = _routing_inputs(workspace_root)
    intent_path = workspace_root / "intent.json"
    _write_json(intent_path, _intent().model_dump(mode="json"))
    runner = CliRunner()

    resolved = runner.invoke(
        app,
        [
            "route",
            "resolve",
            str(intent_path),
            "--root",
            str(workspace_root / "aoa-sdk"),
            "--routing-bundle",
            str(bundle_root),
            "--source-lock",
            str(lock_path),
        ],
    )
    assert resolved.exit_code == 0, resolved.output
    decision_payload = json.loads(resolved.output)
    assert decision_payload["selected_candidate_id"] == (
        "aoa-skills:skill:aoa-decision"
    )

    decision_path = workspace_root / "decision.json"
    _write_json(decision_path, decision_payload)
    explained = runner.invoke(
        app,
        [
            "route",
            "explain",
            str(decision_path),
        ],
    )
    assert explained.exit_code == 0, explained.output
    explanation_payload = json.loads(explained.output)
    assert explanation_payload["fallback_used"] is False

    explanation_path = workspace_root / "explanation.json"
    _write_json(explanation_path, explanation_payload)
    validated = runner.invoke(
        app,
        [
            "route",
            "validate",
            str(explanation_path),
            "--against",
            str(decision_path),
        ],
    )
    assert validated.exit_code == 0, validated.output
    assert json.loads(validated.output)["execution_authorized"] is False


def test_aoasdk_constructs_control_plane_without_reading_snapshot(
    workspace_root: Path,
) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    assert isinstance(sdk.control_plane, ControlPlaneAPI)
    with pytest.raises(
        RoutingSnapshotError,
        match="explicit routing bundle root does not exist",
    ):
        sdk.control_plane.resolve(_intent())
