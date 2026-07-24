from __future__ import annotations

import copy
import json
import os
import shutil
from pathlib import Path

import pytest

from aoa_sdk.control_plane.routing import core as router_core
from aoa_sdk.control_plane.routing import producer as build_router


PART_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_ROOT = Path(os.environ["AOA_ROUTING_PRODUCER_FIXTURE_ROOT"])
CANONICAL_GENERATED_ROOT = Path(
    os.environ["AOA_ROUTING_CANONICAL_GENERATED_ROOT"]
)
FIXTURE_REPO_NAMES = (
    "aoa-techniques",
    "aoa-skills",
    "aoa-evals",
    "aoa-memo",
    "aoa-stats",
    "aoa-sdk",
    "aoa-agents",
    "Agents-of-Abyss",
    "aoa-playbooks",
    "aoa-kag",
    "Tree-of-Sophia",
    "Dionysus",
    "8Dionysus",
    "abyss-stack",
)


def test_shadow_producer_refuses_canonical_looking_generated_directory(
    tmp_path: Path,
) -> None:
    with pytest.raises(router_core.RouterError, match="must not be named 'generated'"):
        build_router.ensure_non_publishing_output_dir(tmp_path / "generated")


def test_default_dependency_root_climbs_out_of_codex_worktree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OS_ABYSS_ROOT", raising=False)
    monkeypatch.delenv("AOA_WORKSPACE_ROOT", raising=False)
    workspace = tmp_path / "workspace"
    routing_root = workspace / ".codex" / "worktrees" / "aoa-routing-fix"
    sibling_root = workspace / "aoa-skills"
    routing_root.mkdir(parents=True)
    sibling_root.mkdir(parents=True)

    assert router_core.default_dependency_root("aoa-skills", routing_root) == sibling_root


def test_default_dependency_root_prefers_abyss_stack_source_checkout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for env_name in (
        "ABYSS_STACK_ROOT",
        "AOA_SOURCE_ROOT",
        "OS_ABYSS_ROOT",
        "AOA_WORKSPACE_ROOT",
    ):
        monkeypatch.delenv(env_name, raising=False)
    workspace = tmp_path / "workspace"
    routing_root = workspace / ".codex" / "worktrees" / "aoa-routing-fix"
    configs_root = workspace / "abyss-stack" / "Configs"
    source_root = workspace / "abyss-stack"
    routing_root.mkdir(parents=True)
    configs_root.mkdir(parents=True)

    expected_root = Path.home() / "src" / "abyss-stack"
    if not expected_root.exists():
        expected_root = configs_root

    assert router_core.default_dependency_root("abyss-stack", routing_root) == expected_root
    assert source_root.exists()


def test_default_dependency_root_honors_cross_host_workspace_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    routing_root = tmp_path / "isolated" / "aoa-routing"
    sibling_root = workspace / "aoa-skills"
    routing_root.mkdir(parents=True)
    sibling_root.mkdir(parents=True)
    monkeypatch.setenv("OS_ABYSS_ROOT", str(workspace))

    assert router_core.default_dependency_root("aoa-skills", routing_root) == sibling_root


def test_cross_host_workspace_prefers_abyss_stack_source_checkout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    routing_root = tmp_path / "isolated" / "aoa-routing"
    configs_root = workspace / "abyss-stack" / "Configs"
    routing_root.mkdir(parents=True)
    configs_root.mkdir(parents=True)
    monkeypatch.setenv("HOME", str(tmp_path / "empty-home"))
    monkeypatch.setenv("OS_ABYSS_ROOT", str(workspace))
    monkeypatch.delenv("ABYSS_STACK_ROOT", raising=False)
    monkeypatch.delenv("AOA_SOURCE_ROOT", raising=False)

    assert router_core.default_dependency_root("abyss-stack", routing_root) == configs_root


def test_default_dependency_root_honors_explicit_abyss_stack_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    routing_root = tmp_path / "isolated" / "aoa-routing"
    source_root = tmp_path / "source" / "abyss-stack"
    routing_root.mkdir(parents=True)
    source_root.mkdir(parents=True)
    monkeypatch.setenv("ABYSS_STACK_ROOT", str(source_root))

    assert router_core.default_dependency_root("abyss-stack", routing_root) == source_root
KAG_SOURCE_LIFT_TECHNIQUE_IDS = [
    "AOA-T-0018",
    "AOA-T-0019",
    "AOA-T-0020",
    "AOA-T-0021",
    "AOA-T-0022",
]


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, separators=(",", ":")) + "\n", encoding="utf-8")


def write_output(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == ".jsonl":
        rows = payload if isinstance(payload, list) else [payload]
        path.write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
            encoding="utf-8",
        )
        return
    write_json(path, payload)


def build_fixture_outputs(
    *,
    techniques_root: Path = FIXTURES_ROOT / "aoa-techniques",
    skills_root: Path = FIXTURES_ROOT / "aoa-skills",
    evals_root: Path = FIXTURES_ROOT / "aoa-evals",
    memo_root: Path = FIXTURES_ROOT / "aoa-memo",
    stats_root: Path = FIXTURES_ROOT / "aoa-stats",
    sdk_root: Path = FIXTURES_ROOT / "aoa-sdk",
    agents_root: Path = FIXTURES_ROOT / "aoa-agents",
    aoa_root: Path = FIXTURES_ROOT / "Agents-of-Abyss",
    playbooks_root: Path = FIXTURES_ROOT / "aoa-playbooks",
    kag_root: Path = FIXTURES_ROOT / "aoa-kag",
    tos_root: Path = FIXTURES_ROOT / "Tree-of-Sophia",
    source_route_root: Path = FIXTURES_ROOT / "Dionysus",
    profile_root: Path = FIXTURES_ROOT / "8Dionysus",
    abyss_stack_root: Path = FIXTURES_ROOT / "abyss-stack",
    routing_root: Path = FIXTURES_ROOT / "aoa-routing",
) -> dict[str, dict[str, object]]:
    return build_router.build_outputs(
        techniques_root,
        skills_root,
        evals_root,
        memo_root,
        stats_root,
        agents_root,
        aoa_root,
        playbooks_root,
        kag_root,
        tos_root,
        sdk_root,
        source_route_root,
        profile_root,
        abyss_stack_root,
        routing_root,
    )


def build_kag_source_lift_technique_entries() -> list[dict[str, object]]:
    return [
        {
            "id": "AOA-T-0018",
            "name": "markdown-technique-section-lift",
            "domain": "docs",
            "status": "promoted",
            "summary": "Lift stable technique markdown sections into derived section-level units while keeping the bundle markdown authoritative.",
            "maturity_score": 3,
            "rigor_level": "bounded",
            "reversibility": "easy",
            "review_required": True,
            "validation_strength": "source_backed",
            "export_ready": True,
            "technique_path": "techniques/docs/markdown-technique-section-lift/TECHNIQUE.md",
            "relations": [{"type": "complements", "target": "AOA-T-0019"}],
        },
        {
            "id": "AOA-T-0019",
            "name": "frontmatter-metadata-spine",
            "domain": "docs",
            "status": "canonical",
            "summary": "Treat bounded frontmatter and derived catalog outputs as a metadata spine for bundle routing without replacing markdown meaning.",
            "maturity_score": 5,
            "rigor_level": "bounded",
            "reversibility": "easy",
            "review_required": True,
            "validation_strength": "cross_context",
            "export_ready": True,
            "technique_path": "techniques/docs/frontmatter-metadata-spine/TECHNIQUE.md",
            "relations": [
                {"type": "complements", "target": "AOA-T-0018"},
                {"type": "used_together_for", "target": "AOA-T-0020"},
                {"type": "used_together_for", "target": "AOA-T-0021"},
            ],
        },
        {
            "id": "AOA-T-0020",
            "name": "evidence-note-provenance-lift",
            "domain": "docs",
            "status": "promoted",
            "summary": "Use typed evidence note kinds and note paths as bounded provenance handles in derived manifests without flattening them into a note graph.",
            "maturity_score": 3,
            "rigor_level": "bounded",
            "reversibility": "easy",
            "review_required": True,
            "validation_strength": "source_backed",
            "export_ready": True,
            "technique_path": "techniques/docs/evidence-note-provenance-lift/TECHNIQUE.md",
            "relations": [{"type": "requires", "target": "AOA-T-0019"}],
        },
        {
            "id": "AOA-T-0021",
            "name": "bounded-relation-lift-for-kag",
            "domain": "docs",
            "status": "promoted",
            "summary": "Lift small typed direct relations into bounded edge hints for derived consumers without turning them into graph semantics.",
            "maturity_score": 3,
            "rigor_level": "bounded",
            "reversibility": "easy",
            "review_required": True,
            "validation_strength": "source_backed",
            "export_ready": True,
            "technique_path": "techniques/docs/bounded-relation-lift-for-kag/TECHNIQUE.md",
            "relations": [{"type": "requires", "target": "AOA-T-0019"}],
        },
        {
            "id": "AOA-T-0022",
            "name": "risk-and-negative-effect-lift",
            "domain": "docs",
            "status": "promoted",
            "summary": "Lift richer `Risks` language into bounded caution-oriented lookup and reuse without turning caution into metadata or scoring.",
            "maturity_score": 3,
            "rigor_level": "bounded",
            "reversibility": "easy",
            "review_required": True,
            "validation_strength": "source_backed",
            "export_ready": True,
            "technique_path": "techniques/docs/risk-and-negative-effect-lift/TECHNIQUE.md",
            "relations": [{"type": "complements", "target": "AOA-T-0018"}],
        },
    ]


def test_collect_technique_entries_reads_generated_catalog() -> None:
    entries = build_router.collect_technique_entries(FIXTURES_ROOT / "aoa-techniques")

    assert [entry["id"] for entry in entries] == ["AOA-T-0001", "AOA-T-0002"]
    assert entries[0]["kind"] == "technique"
    assert entries[0]["repo"] == "aoa-techniques"
    assert entries[0]["source_type"] == "generated-catalog"
    assert entries[0]["attributes"]["domain"] == "agent-workflows"


def test_collect_skill_entries_reads_generated_catalog() -> None:
    entries = build_router.collect_skill_entries(FIXTURES_ROOT / "aoa-skills")

    assert [entry["id"] for entry in entries] == ["aoa-decision", "aoa-verification"]
    assert entries[0]["path"] == "skills/core/engineering/aoa-decision/SKILL.md"
    assert entries[0]["source_type"] == "generated-catalog"
    assert entries[0]["attributes"] == {
        "scope": "stewardship.decisions",
        "invocation_mode": "invoke",
        "technique_dependencies": [],
        "allow_implicit_invocation": True,
        "candidate_only": False,
        "trust_posture": "portable-core",
        "projection_path": ".agents/skills/aoa-decision/SKILL.md",
        "capability_id": "skill.aoa-decision",
        "capability_graph_ref": "generated/capability_graph.json",
        "capability_source_path": "capabilities/families/decisions.yaml",
        "lifecycle": {
            "evidence_state": "pilot-verified",
            "health": "challenger",
            "state": "candidate",
            "version": "0.1.0",
            "visibility": "advertised",
        },
        "target_owner": "aoa-skills",
        "requires_human_approval": False,
    }


def test_collect_eval_entries_reads_generated_catalog() -> None:
    entries = build_router.collect_eval_entries(FIXTURES_ROOT / "aoa-evals")

    assert [entry["id"] for entry in entries] == [
        "aoa-bounded-change-quality",
        "aoa-context-scan-quality",
    ]
    assert entries[0]["path"] == "bundles/aoa-bounded-change-quality/EVAL.md"
    assert entries[0]["source_type"] == "generated-catalog"
    assert entries[0]["attributes"]["skill_dependencies"] == []
    assert entries[0]["attributes"]["capability_dependencies"] == [
        "workflow.operations.repository-change"
    ]


def test_collect_memo_entries_reads_generated_catalog() -> None:
    entries = build_router.collect_memo_entries(FIXTURES_ROOT / "aoa-memo")

    assert [entry["id"] for entry in entries] == ["AOA-M-0001", "AOA-M-0002"]
    assert entries[0]["kind"] == "memo"
    assert entries[0]["repo"] == "aoa-memo"
    assert entries[0]["path"] == "CHARTER.md"
    assert entries[0]["source_type"] == "generated-catalog"
    assert entries[0]["attributes"]["recall_modes"] == ["semantic", "source_route"]
    assert entries[0]["attributes"]["inspect_surface"] == "generated/memory/memory_catalog.min.json"


def test_collect_skill_entries_raises_on_missing_generated_catalog(tmp_path: Path) -> None:
    skills_root = tmp_path / "aoa-skills"
    shutil.copytree(FIXTURES_ROOT / "aoa-skills", skills_root)
    (skills_root / "generated" / "agent_skill_catalog.min.json").unlink()

    with pytest.raises(build_router.RouterError, match="agent_skill_catalog.min.json"):
        build_router.collect_skill_entries(skills_root)


def test_build_outputs_rejects_missing_live_quest_catalog_surface(tmp_path: Path) -> None:
    roots = {}
    for repo_name in FIXTURE_REPO_NAMES:
        target = tmp_path / repo_name
        shutil.copytree(FIXTURES_ROOT / repo_name, target)
        roots[repo_name] = target
    (roots["aoa-techniques"] / "generated" / "quest_catalog.min.json").unlink()

    with pytest.raises(build_router.RouterError, match="quest_catalog.min.json"):
        build_router.build_outputs(
            roots["aoa-techniques"],
            roots["aoa-skills"],
            roots["aoa-evals"],
            roots["aoa-memo"],
            roots["aoa-stats"],
            roots["aoa-agents"],
            roots["Agents-of-Abyss"],
            roots["aoa-playbooks"],
            roots["aoa-kag"],
            roots["Tree-of-Sophia"],
            roots["aoa-sdk"],
            roots["Dionysus"],
            roots["8Dionysus"],
            roots["abyss-stack"],
        )


def test_build_outputs_rejects_missing_live_quest_dispatch_surface(tmp_path: Path) -> None:
    roots = {}
    for repo_name in FIXTURE_REPO_NAMES:
        target = tmp_path / repo_name
        shutil.copytree(FIXTURES_ROOT / repo_name, target)
        roots[repo_name] = target
    (roots["aoa-skills"] / "generated" / "quest_dispatch.min.json").unlink()

    with pytest.raises(build_router.RouterError, match="quest_dispatch.min.json"):
        build_router.build_outputs(
            roots["aoa-techniques"],
            roots["aoa-skills"],
            roots["aoa-evals"],
            roots["aoa-memo"],
            roots["aoa-stats"],
            roots["aoa-agents"],
            roots["Agents-of-Abyss"],
            roots["aoa-playbooks"],
            roots["aoa-kag"],
            roots["Tree-of-Sophia"],
            roots["aoa-sdk"],
            roots["Dionysus"],
            roots["8Dionysus"],
            roots["abyss-stack"],
        )


def test_collect_eval_entries_raises_on_missing_required_field(tmp_path: Path) -> None:
    evals_root = tmp_path / "aoa-evals"
    shutil.copytree(FIXTURES_ROOT / "aoa-evals", evals_root)
    catalog_path = evals_root / "generated" / "eval_catalog.min.json"
    payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    del payload["evals"][0]["verdict_shape"]
    write_json(catalog_path, payload)

    with pytest.raises(build_router.RouterError, match="verdict_shape"):
        build_router.collect_eval_entries(evals_root)


def test_collect_skill_entries_rejects_parent_directory_skill_path(tmp_path: Path) -> None:
    skills_root = tmp_path / "aoa-skills"
    shutil.copytree(FIXTURES_ROOT / "aoa-skills", skills_root)
    catalog_path = skills_root / "generated" / "agent_skill_catalog.min.json"
    payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    payload["skills"][0]["path"] = "../secret.md"
    write_json(catalog_path, payload)

    with pytest.raises(build_router.RouterError, match="must not traverse outside the repository root"):
        build_router.collect_skill_entries(skills_root)


def test_collect_skill_entries_rejects_foreign_capability_owner(tmp_path: Path) -> None:
    skills_root = tmp_path / "aoa-skills"
    shutil.copytree(FIXTURES_ROOT / "aoa-skills", skills_root)
    graph_path = skills_root / "generated" / "capability_graph.json"
    payload = json.loads(graph_path.read_text(encoding="utf-8"))
    skill_node = next(node for node in payload["nodes"] if node["kind"] == "skill")
    skill_node["owner"]["repo"] = "aoa-routing"
    write_json(graph_path, payload)

    with pytest.raises(build_router.RouterError, match="owner.repo must equal 'aoa-skills'"):
        build_router.collect_skill_entries(skills_root)


def test_collect_skill_entries_accepts_external_owner_graph_reference(tmp_path: Path) -> None:
    skills_root = tmp_path / "aoa-skills"
    shutil.copytree(FIXTURES_ROOT / "aoa-skills", skills_root)
    graph_path = skills_root / "generated" / "capability_graph.json"
    payload = json.loads(graph_path.read_text(encoding="utf-8"))
    external_node = copy.deepcopy(
        next(node for node in payload["nodes"] if node["kind"] == "skill")
    )
    external_node["id"] = "skill.aoa-summon"
    external_node["owner"] = {
        "authority": "external-authority",
        "repo": "aoa-agents",
        "surface": "skills/aoa-summon/SKILL.md",
    }
    payload["nodes"].append(external_node)
    write_json(graph_path, payload)

    entries = build_router.collect_skill_entries(skills_root)

    assert [entry["id"] for entry in entries] == ["aoa-decision", "aoa-verification"]


def test_collect_skill_entries_rejects_unpublished_local_graph_skill(tmp_path: Path) -> None:
    skills_root = tmp_path / "aoa-skills"
    shutil.copytree(FIXTURES_ROOT / "aoa-skills", skills_root)
    graph_path = skills_root / "generated" / "capability_graph.json"
    payload = json.loads(graph_path.read_text(encoding="utf-8"))
    local_node = copy.deepcopy(
        next(node for node in payload["nodes"] if node["kind"] == "skill")
    )
    local_node["id"] = "skill.unpublished-local"
    payload["nodes"].append(local_node)
    write_json(graph_path, payload)

    with pytest.raises(
        build_router.RouterError,
        match="contains non-catalog skill nodes without external owner authority",
    ):
        build_router.collect_skill_entries(skills_root)


def test_collect_eval_entries_rejects_parent_directory_eval_path(tmp_path: Path) -> None:
    evals_root = tmp_path / "aoa-evals"
    shutil.copytree(FIXTURES_ROOT / "aoa-evals", evals_root)
    catalog_path = evals_root / "generated" / "eval_catalog.min.json"
    payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    payload["evals"][0]["eval_path"] = "../secret.md"
    write_json(catalog_path, payload)

    with pytest.raises(build_router.RouterError, match="must not traverse outside the repository root"):
        build_router.collect_eval_entries(evals_root)


def test_collect_eval_entries_rejects_capability_ref_order_drift(tmp_path: Path) -> None:
    evals_root = tmp_path / "aoa-evals"
    shutil.copytree(FIXTURES_ROOT / "aoa-evals", evals_root)
    catalog_path = evals_root / "generated" / "eval_catalog.min.json"
    payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    payload["evals"][0]["capability_refs"][0]["id"] = "guard.operations.approval"
    write_json(catalog_path, payload)

    with pytest.raises(
        build_router.RouterError,
        match="capability_refs must preserve the ordered capability_dependencies IDs",
    ):
        build_router.collect_eval_entries(evals_root)


@pytest.mark.parametrize(
    ("drift", "expected_message"),
    [
        ("missing-node", "is missing from"),
        ("kind", "does not match owner graph kind"),
        ("registry-path", "does not match owner graph source_path"),
        ("target-owner", "does not match owner graph owner.repo"),
    ],
)
def test_build_rejects_eval_capability_ref_drift_from_owner_graph(
    tmp_path: Path,
    drift: str,
    expected_message: str,
) -> None:
    skills_root = tmp_path / "aoa-skills"
    shutil.copytree(FIXTURES_ROOT / "aoa-skills", skills_root)
    graph_path = skills_root / "generated" / "capability_graph.json"
    payload = json.loads(graph_path.read_text(encoding="utf-8"))
    node = next(
        item
        for item in payload["nodes"]
        if item["id"] == "workflow.operations.repository-change"
    )
    if drift == "missing-node":
        payload["nodes"].remove(node)
    elif drift == "kind":
        node["kind"] = "mode"
    elif drift == "registry-path":
        node["source_path"] = "capabilities/families/stale-operations.yaml"
    elif drift == "target-owner":
        node["owner"]["repo"] = "stale-owner"
    else:  # pragma: no cover - the parametrization is closed above.
        raise AssertionError(f"unsupported drift case: {drift}")
    write_json(graph_path, payload)

    with pytest.raises(build_router.RouterError, match=expected_message):
        build_fixture_outputs(skills_root=skills_root)


def test_build_outputs_from_fixtures() -> None:
    outputs = build_fixture_outputs()

    registry = outputs["cross_repo_registry.min.json"]
    router = outputs["aoa_router.min.json"]
    hints = outputs["task_to_surface_hints.json"]
    tier_hints = outputs["task_to_tier_hints.json"]
    federation = outputs["federation_entrypoints.min.json"]
    return_navigation = outputs["return_navigation_hints.min.json"]
    recommended = outputs["recommended_paths.min.json"]
    relation_hints = outputs["kag_source_lift_relation_hints.min.json"]
    composite = outputs["composite_stress_route_hints.min.json"]
    shortlist = outputs["owner_layer_shortlist.min.json"]
    pairing = outputs["pairing_hints.min.json"]
    quest_dispatch_hints = outputs["quest_dispatch_hints.min.json"]
    tiny_model = outputs["tiny_model_entrypoints.json"]

    assert [entry["kind"] for entry in registry["entries"]] == [
        "technique",
        "technique",
        "skill",
        "skill",
        "eval",
        "eval",
        "memo",
        "memo",
    ]
    assert [entry["kind"] for entry in router["entries"]] == [
        "technique",
        "technique",
        "skill",
        "skill",
        "eval",
        "eval",
        "memo",
        "memo",
    ]
    assert router["artifact_identity"] == router_core.ROUTING_READMODEL_ARTIFACT_IDENTITY
    assert {entry["source_type"] for entry in registry["entries"]} == {"generated-catalog"}
    assert relation_hints == {
        "version": 1,
        "scope": "kag_source_lift_family",
        "source_repo": "aoa-techniques",
        "source_catalog": "generated/technique_catalog.min.json",
        "family_ids": KAG_SOURCE_LIFT_TECHNIQUE_IDS,
        "entries": [],
    }
    assert composite["schema_version"] == "aoa_routing_composite_stress_route_hints_v1"
    assert [item["repo"] for item in composite["source_inputs"]] == [
        "aoa-stats",
        "aoa-playbooks",
        "aoa-playbooks",
        "aoa-kag",
        "aoa-kag",
        "aoa-memo",
    ]
    assert composite["hints"][0]["preferred_posture"] == "source_first_until_pass"
    assert composite["hints"][0]["memo_context"] == []
    assert [step["kind"] for step in composite["hints"][0]["next_hops"]] == [
        "source_receipt",
        "playbook_lane",
        "reentry_gate",
        "projection_health",
        "regrounding_ticket",
    ]
    assert quest_dispatch_hints["version"] == 1
    assert quest_dispatch_hints["contour_scope"] == "source-only"
    assert quest_dispatch_hints["actions_enabled"] == ["inspect", "expand", "handoff"]
    assert shortlist["schema_version"] == "aoa_routing_owner_layer_shortlist_v2"
    assert (
        shortlist["schema_ref"]
        == "mechanics/boundary-bridge/parts/owner-layer-shortlist/schemas/owner-layer-shortlist.schema.json"
    )
    assert shortlist["owner_repo"] == "aoa-routing"
    assert shortlist["surface_kind"] == "owner_layer_shortlist"
    assert {
        (entry["signal"], entry["owner_repo"], entry["ambiguity"])
        for entry in shortlist["hints"]
        if entry["signal"] in {"proof-need", "scenario-recurring", "repeated-pattern"}
    } >= {
        ("proof-need", "aoa-evals", "clear"),
        ("scenario-recurring", "aoa-playbooks", "clear"),
        ("scenario-recurring", "aoa-techniques", "ambiguous"),
        ("repeated-pattern", "aoa-techniques", "clear"),
    }
    assert quest_dispatch_hints["source_inputs"] == [
        {"repo": "aoa-techniques", "surface_kind": "quest_catalog", "ref": "generated/quest_catalog.min.json"},
        {"repo": "aoa-techniques", "surface_kind": "quest_dispatch", "ref": "generated/quest_dispatch.min.json"},
        {"repo": "aoa-skills", "surface_kind": "quest_catalog", "ref": "generated/quest_catalog.min.json"},
        {"repo": "aoa-skills", "surface_kind": "quest_dispatch", "ref": "generated/quest_dispatch.min.json"},
        {"repo": "aoa-evals", "surface_kind": "quest_catalog", "ref": "generated/quest_catalog.min.json"},
        {"repo": "aoa-evals", "surface_kind": "quest_dispatch", "ref": "generated/quest_dispatch.min.json"},
    ]
    assert [(hint["repo"], hint["id"]) for hint in quest_dispatch_hints["hints"]] == [
        ("aoa-techniques", "AOA-TECH-Q-0003"),
        ("aoa-techniques", "AOA-TECH-Q-0004"),
        ("aoa-skills", "AOA-SK-Q-0003"),
        ("aoa-skills", "AOA-SK-Q-0004"),
        ("aoa-evals", "AOA-EV-Q-0003"),
        ("aoa-evals", "AOA-EV-Q-0004"),
    ]
    assert quest_dispatch_hints["hints"][0] == {
        "schema_version": "quest_dispatch_hint_v2",
        "id": "AOA-TECH-Q-0003",
        "repo": "aoa-techniques",
        "state": "captured",
        "band": "near",
        "difficulty": "d3_seam",
        "risk": "r2_contract",
        "delegate_tier": "planner",
        "source_path": "quests/AOA-TECH-Q-0003.yaml",
        "public_safe": True,
        "next_actions": [
            {
                "verb": "inspect",
                "target_repo": "aoa-techniques",
                "target_surface": "generated/quest_dispatch.min.json",
                "match_key": "id",
                "target_value": "AOA-TECH-Q-0003",
            },
            {
                "verb": "expand",
                "target_repo": "aoa-techniques",
                "target_surface": "mechanics/growth-cycle/parts/questbook-integration/README.md",
                "match_key": "path",
                "target_value": "mechanics/growth-cycle/parts/questbook-integration/README.md",
            },
            {
                "verb": "handoff",
                "target_repo": "aoa-routing",
                "target_surface": "generated/federation_entrypoints.min.json",
                "match_key": "id",
                "target_value": "planner",
            },
        ],
        "fallback": {
            "verb": "inspect",
            "target_repo": "aoa-techniques",
            "target_surface": "generated/quest_catalog.min.json",
            "match_key": "id",
            "target_value": "AOA-TECH-Q-0003",
        },
    }

    technique_hint = next(hint for hint in hints["hints"] if hint["kind"] == "technique")
    assert technique_hint["actions"]["inspect"] == {
        "enabled": True,
        "surface_file": "generated/technique_capsules.json",
        "match_field": "id",
    }
    assert technique_hint["actions"]["expand"] == {
        "enabled": True,
        "surface_file": "generated/technique_sections.full.json",
        "match_field": "id",
        "section_key_field": "key",
        "default_sections": [
            "intent",
            "when_to_use",
            "inputs",
            "outputs",
            "core_procedure",
            "contracts",
            "risks",
            "validation",
        ],
        "supported_sections": [
            "intent",
            "when_to_use",
            "when_not_to_use",
            "inputs",
            "outputs",
            "core_procedure",
            "contracts",
            "risks",
            "validation",
            "adaptation_notes",
            "public_sanitization_notes",
            "example",
            "checks",
            "promotion_history",
            "future_evolution",
        ],
    }
    assert technique_hint["actions"]["pair"] == {
        "enabled": True,
        "surface_repo": "aoa-routing",
        "surface_file": "generated/pairing_hints.min.json",
        "match_field": "id",
    }
    assert technique_hint["actions"]["second_cut"] == {
        "enabled": True,
        "surface_repo": "aoa-techniques",
        "surface_file": "generated/technique_kind_manifest.min.json",
        "collection_key": "kinds",
        "match_field": "kind",
        "selection_axis": "kind",
        "prerequisite_axes": ["domain"],
    }
    memo_hint = next(hint for hint in hints["hints"] if hint["kind"] == "memo")
    assert memo_hint == {
        "kind": "memo",
        "enabled": True,
        "source_repo": "aoa-memo",
        "use_when": "need bounded recall or memory-layer doctrine surfaces without copying memo truth into routing",
        "actions": {
            "pick": {"enabled": True},
            "inspect": {
                "enabled": True,
                "surface_file": "generated/memory/memory_catalog.min.json",
                "match_field": "id",
            },
            "expand": {
                "enabled": True,
                "surface_file": "generated/memory/memory_sections.full.json",
                "match_field": "id",
                "section_key_field": "section_id",
                "default_sections": [],
                "supported_sections": [],
            },
            "pair": {"enabled": False},
            "recall": {
                "enabled": True,
                "contract_file": "examples/recall/recall_contract.router.semantic.json",
                "default_mode": "semantic",
                "supported_modes": ["semantic", "source_route", "lineage"],
                "contracts_by_mode": {
                    "semantic": "examples/recall/recall_contract.router.semantic.json",
                    "source_route": "examples/recall/recall_contract.router.source_route.json",
                    "lineage": "examples/recall/recall_contract.router.lineage.json",
                },
                "capsule_surfaces_by_mode": {
                    "semantic": "generated/memory/memory_capsules.json",
                    "lineage": "generated/memory/memory_capsules.json",
                },
                "parallel_families": {
                    "memory_objects": {
                        "inspect_surface": "generated/memory-objects/memory_object_catalog.min.json",
                        "expand_surface": "generated/memory-objects/memory_object_sections.full.json",
                        "default_mode": "working",
                        "supported_modes": ["working", "semantic", "lineage"],
                        "contracts_by_mode": {
                            "working": "examples/recall/recall_contract.object.working.json",
                            "semantic": "examples/recall/recall_contract.object.semantic.json",
                            "lineage": "examples/recall/recall_contract.object.lineage.json",
                        },
                        "capsule_surfaces_by_mode": {
                            "semantic": "generated/memory-objects/memory_object_capsules.json",
                            "lineage": "generated/memory-objects/memory_object_capsules.json",
                        },
                    }
                },
            },
        },
    }
    assert tier_hints["source_of_truth"] == {
        "tier_registry_repo": "aoa-agents",
        "tier_registry_path": "generated/model_tier_registry.json",
    }
    assert tier_hints["hints"][0] == {
        "task_family": "task-triage",
        "preferred_tier": "router",
        "fallback_tier": "planner",
        "use_when": "need the fastest classification of task shape, risk, and smallest next step",
        "output_artifact": "route_decision",
    }

    by_key = {(entry["kind"], entry["id"]): entry for entry in recommended["entries"]}
    decision_skill = by_key[("skill", "aoa-decision")]
    assert decision_skill == {
        "kind": "skill",
        "id": "aoa-decision",
        "upstream": [],
        "downstream": [],
    }
    context_eval = by_key[("eval", "aoa-context-scan-quality")]
    assert context_eval["upstream"] == [
        {"kind": "technique", "id": "AOA-T-0002", "relation": "requires"},
        {"kind": "skill", "id": "aoa-verification", "relation": "requires"},
    ]
    assert by_key[("memo", "AOA-M-0001")] == {
        "kind": "memo",
        "id": "AOA-M-0001",
        "upstream": [],
        "downstream": [],
    }

    pairing_by_key = {(entry["kind"], entry["id"]): entry for entry in pairing["entries"]}
    assert pairing_by_key[("technique", "AOA-T-0001")] == {
        "kind": "technique",
        "id": "AOA-T-0001",
        "pairs": [
            {"kind": "eval", "id": "aoa-bounded-change-quality", "relation": "required_by"},
        ],
    }
    assert pairing_by_key[("skill", "aoa-verification")] == {
        "kind": "skill",
        "id": "aoa-verification",
        "pairs": [
            {"kind": "eval", "id": "aoa-context-scan-quality", "relation": "required_by"},
        ],
    }
    assert federation["schema_version"] == "aoa_routing_federation_entrypoints_v2"
    assert (
        federation["schema_ref"]
        == "mechanics/boundary-bridge/parts/federation-entry/schemas/federation-entrypoints.schema.json"
    )
    assert federation["owner_repo"] == "aoa-routing"
    assert federation["surface_kind"] == "federation_entrypoints"
    assert federation["artifact_identity"] == {
        "artifact_class": "generated_readmodel",
        "surface_state": "public_generated_navigation_surface",
        "owner_repo": "aoa-routing",
        "authority_ref": "mechanics/boundary-bridge/parts/federation-entry/docs/federation-entry-abi.md",
        "producer": "scripts/build_router.py from sibling owner-generated source inputs",
        "consumer_expectation": "consumers verify schema_version, schema_ref, source_inputs, owner authority refs, and validate_router/build_router --check before treating entry cards as usable orientation",
        "privacy_boundary": "public route references only; no copied owner payloads, private state, source corpora, or runtime secrets",
        "content_identity": "generated/federation_entrypoints.min.json rebuilt from declared source_inputs and compared by build_router --check",
        "abi_epoch": "aoa_routing_federation_entrypoints_v2",
        "contract_version": "federation-entrypoints.schema.json@aoa_routing_federation_entrypoints_v2#artifact_identity",
        "trust_layer": ["abi_contract_signature"],
        "verification": ["python scripts/validate_router.py", "python scripts/build_router.py --check"],
        "action": "ADD_CONSUMER_EXPECTATION",
    }
    assert federation["active_entry_kinds"] == [
        "agent",
        "tier",
        "playbook",
        "kag_view",
        "source_route",
        "runtime_surface",
        "orientation_surface",
    ]
    assert federation["declared_entry_kinds"] == ["tos_node"]
    assert return_navigation["schema_version"] == "aoa_routing_return_navigation_hints_v2"
    assert (
        return_navigation["schema_ref"]
        == "mechanics/recurrence/parts/return-navigation/schemas/return-navigation-hints.schema.json"
    )
    assert return_navigation["owner_repo"] == "aoa-routing"
    assert return_navigation["surface_kind"] == "return_navigation_hints"
    memo_return = next(
        record for record in return_navigation["thin_router_returns"] if record["context_kind"] == "memo"
    )
    assert memo_return == {
        "context_kind": "memo",
        "source_repo": "aoa-memo",
        "supported_return_reasons": [
            "checkpoint_continuity_needed",
            "artifact_contract_lost",
            "source_boundary_lost",
        ],
        "primary_action": {
            "verb": "recall",
            "target_repo": "aoa-memo",
            "target_surface": "examples/recall/recall_contract.object.working.return.json",
        },
        "secondary_action": {
            "verb": "inspect",
            "target_repo": "aoa-memo",
            "target_surface": "generated/memory-objects/memory_object_catalog.min.json",
            "match_field": "id",
        },
        "ownership_note": "Checkpoint continuity and recall meaning stay in aoa-memo; routing only points back to the public return-ready contract and object surface.",
    }
    aoa_root_return = next(
        record for record in return_navigation["federation_root_returns"] if record["root_id"] == "aoa-root"
    )
    assert aoa_root_return["primary_action"] == {
        "verb": "inspect",
        "target_repo": "Agents-of-Abyss",
        "target_surface": "CHARTER.md",
    }
    tos_root_return = next(
        record for record in return_navigation["federation_root_returns"] if record["root_id"] == "tos-root"
    )
    assert tos_root_return["secondary_action"] == {
        "verb": "inspect",
        "target_repo": "Tree-of-Sophia",
        "target_surface": "ToS/public-compatibility/tos_tiny_entry_route.example.json",
        "match_field": "route_id",
        "target_value": "tos-tiny-entry.zarathustra-prologue",
    }
    playbook_return = next(
        record
        for record in return_navigation["federation_kind_returns"]
        if record["entry_kind"] == "playbook"
    )
    assert playbook_return["primary_action"] == {
        "verb": "inspect",
        "target_repo": "aoa-playbooks",
        "target_surface": "generated/playbook_registry.min.json",
    }
    assert playbook_return["fallback_action"] == {
        "verb": "inspect",
        "target_repo": "aoa-routing",
        "target_surface": "generated/federation_entrypoints.min.json",
        "match_field": "kind",
        "target_value": "playbook",
    }
    source_route_return = next(
        record
        for record in return_navigation["federation_kind_returns"]
        if record["entry_kind"] == "source_route"
    )
    assert source_route_return["primary_action"] == {
        "verb": "inspect",
        "target_repo": "Dionysus",
        "target_surface": "docs/decisions/DION-D-0001-conversational-self-portrait.md",
    }
    runtime_return = next(
        record
        for record in return_navigation["federation_kind_returns"]
        if record["entry_kind"] == "runtime_surface"
    )
    assert runtime_return["primary_action"] == {
        "verb": "inspect",
        "target_repo": "aoa-sdk",
        "target_surface": "generated/workspace_control_plane.min.json",
    }
    orientation_return = next(
        record
        for record in return_navigation["federation_kind_returns"]
        if record["entry_kind"] == "orientation_surface"
    )
    assert orientation_return["primary_action"] == {
        "verb": "inspect",
        "target_repo": "8Dionysus",
        "target_surface": "generated/public_route_map.min.json",
    }
    entry_returns = return_navigation["federation_entry_returns"]
    assert entry_returns["AOA-P-0031"]["supported_return_reasons"] == [
        "authority_unclear",
        "artifact_contract_lost",
        "checkpoint_continuity_needed",
        "split_route_needed",
        "human_gate_required",
        "reroute_required",
    ]
    assert entry_returns["AOA-P-0031"]["primary_action"] == {
        "verb": "inspect",
        "target_repo": "aoa-playbooks",
        "target_surface": "generated/playbook_registry.min.json",
        "match_field": "id",
        "target_value": "AOA-P-0031",
    }
    assert "summon child-return checkpoint route" in entry_returns["AOA-P-0031"]["ownership_note"]
    assert "SDK E2E fixture re-entry" in entry_returns["AOA-P-0031"]["ownership_note"]
    assert entry_returns["aoa-sdk-control-plane"]["primary_action"] == {
        "verb": "inspect",
        "target_repo": "aoa-sdk",
        "target_surface": "generated/workspace_control_plane.min.json",
    }
    assert entry_returns["aoa-sdk-control-plane"]["fallback_action"] == {
        "verb": "inspect",
        "target_repo": "aoa-routing",
        "target_surface": "generated/federation_entrypoints.min.json",
        "match_field": "id",
        "target_value": "aoa-sdk-control-plane",
    }
    assert entry_returns["aoa-stats-summary-catalog"]["primary_action"] == {
        "verb": "inspect",
        "target_repo": "aoa-stats",
        "target_surface": "generated/summary_surface_catalog.min.json",
    }
    assert entry_returns["abyss-stack-diagnostic-spine"]["primary_action"] == {
        "verb": "inspect",
        "target_repo": "abyss-stack",
        "target_surface": router_core.ABYSS_STACK_DIAGNOSTIC_SURFACE_CATALOG_PATH,
    }
    assert entry_returns["dionysus-source-route"]["primary_action"] == {
        "verb": "inspect",
        "target_repo": "Dionysus",
        "target_surface": "docs/decisions/DION-D-0001-conversational-self-portrait.md",
    }
    assert entry_returns["8dionysus-public-route-map"]["primary_action"] == {
        "verb": "inspect",
        "target_repo": "8Dionysus",
        "target_surface": "generated/public_route_map.min.json",
    }
    assert federation["source_inputs"][0:4] == [
        {
            "name": "aoa_root_readme",
            "repo": "Agents-of-Abyss",
            "role": "public_root",
            "ref": "README.md",
        },
        {
            "name": "aoa_center_entry_map",
            "repo": "Agents-of-Abyss",
            "role": "root_capsule",
            "ref": "generated/center_entry_map.min.json",
        },
        {
            "name": "tos_root_readme",
            "repo": "Tree-of-Sophia",
            "role": "public_root",
            "ref": "README.md",
        },
        {
            "name": "tos_root_entry_map",
            "repo": "Tree-of-Sophia",
            "role": "root_capsule",
            "ref": "ToS/derived-exports/root_entry_map.min.json",
        },
    ]
    assert federation["source_inputs"][4] == {
        "name": "tos_tiny_entry_route",
        "repo": "Tree-of-Sophia",
        "role": "tiny_entry_handoff",
        "ref": "ToS/public-compatibility/tos_tiny_entry_route.example.json",
    }
    assert federation["source_inputs"][5] == {
        "name": "agent_registry",
        "repo": "aoa-agents",
        "role": "agent_entries",
        "ref": "generated/agent_registry.min.json",
    }
    assert federation["source_inputs"][6:8] == [
        {
            "name": "model_tier_registry",
            "repo": "aoa-agents",
            "role": "tier_entries",
            "ref": "generated/model_tier_registry.json",
        },
        {
            "name": "runtime_seam_bindings",
            "repo": "aoa-agents",
            "role": "tier_role_bindings",
            "ref": "generated/runtime_seam_bindings.json",
        },
    ]
    assert {
        (entry["name"], entry["ref"])
        for entry in federation["source_inputs"]
        if entry["repo"] in {"aoa-sdk", "Dionysus", "abyss-stack"}
    } >= {
        ("aoa_sdk_workspace_control_plane", "generated/workspace_control_plane.min.json"),
        (
            "dionysus_source_route_retirement_anchor",
            "docs/decisions/DION-D-0001-conversational-self-portrait.md",
        ),
        (
            "abyss_stack_diagnostic_surface_catalog",
            router_core.ABYSS_STACK_DIAGNOSTIC_SURFACE_CATALOG_PATH,
        ),
    }
    assert tiny_model["queries"][0] == {
        "verb": "pick",
        "source_repo": "aoa-routing",
        "target_surface": "generated/aoa_router.min.json",
        "match_key": "kind",
        "allowed_kinds": ["technique", "skill", "eval", "memo"],
    }
    assert tiny_model["schema_version"] == "aoa_routing_tiny_model_entrypoints_v2"
    assert tiny_model["schema_ref"] == "routing/core/schemas/tiny-model-entrypoints.schema.json"
    assert tiny_model["owner_repo"] == "aoa-routing"
    assert tiny_model["surface_kind"] == "tiny_model_entrypoints"
    assert tiny_model["queries"][-2:] == [
        {
            "verb": "recall",
            "source_repo": "aoa-routing",
            "target_surface": "generated/task_to_surface_hints.json",
            "match_key": "kind",
            "allowed_kinds": ["memo"],
        },
        {
            "verb": "recall",
            "source_repo": "aoa-routing",
            "target_surface": "generated/task_to_surface_hints.json",
            "match_key": "kind",
            "allowed_kinds": ["memo"],
            "recall_family": "memory_objects",
        },
    ]

    assert tiny_model["starters"] == [
        {
            "name": "router-root",
            "verb": "pick",
            "source_repo": "aoa-routing",
            "target_surface": "generated/aoa_router.min.json",
            "match_key": "kind",
            "allowed_kinds": ["technique", "skill", "eval", "memo"],
        },
        {
            "name": "technique-root",
            "verb": "pick",
            "source_repo": "aoa-routing",
            "target_surface": "generated/aoa_router.min.json",
            "match_key": "kind",
            "allowed_kinds": ["technique"],
            "target_kind": "technique",
            "target_value": "technique",
        },
        {
            "name": "skill-root",
            "verb": "pick",
            "source_repo": "aoa-routing",
            "target_surface": "generated/aoa_router.min.json",
            "match_key": "kind",
            "allowed_kinds": ["skill"],
            "target_kind": "skill",
            "target_value": "skill",
        },
        {
            "name": "eval-root",
            "verb": "pick",
            "source_repo": "aoa-routing",
            "target_surface": "generated/aoa_router.min.json",
            "match_key": "kind",
            "allowed_kinds": ["eval"],
            "target_kind": "eval",
            "target_value": "eval",
        },
        {
            "name": "memo-root",
            "verb": "pick",
            "source_repo": "aoa-routing",
            "target_surface": "generated/aoa_router.min.json",
            "match_key": "kind",
            "allowed_kinds": ["memo"],
            "target_kind": "memo",
            "target_value": "memo",
        },
        {
            "name": "memo-recall-semantic",
            "verb": "recall",
            "source_repo": "aoa-routing",
            "target_surface": "generated/task_to_surface_hints.json",
            "match_key": "kind",
            "allowed_kinds": ["memo"],
            "target_kind": "memo",
            "target_value": "memo",
            "recall_mode": "semantic",
        },
        {
            "name": "memo-recall-source-route",
            "verb": "recall",
            "source_repo": "aoa-routing",
            "target_surface": "generated/task_to_surface_hints.json",
            "match_key": "kind",
            "allowed_kinds": ["memo"],
            "target_kind": "memo",
            "target_value": "memo",
            "recall_mode": "source_route",
        },
        {
            "name": "memo-recall-lineage",
            "verb": "recall",
            "source_repo": "aoa-routing",
            "target_surface": "generated/task_to_surface_hints.json",
            "match_key": "kind",
            "allowed_kinds": ["memo"],
            "target_kind": "memo",
            "target_value": "memo",
            "recall_mode": "lineage",
        },
        {
            "name": "memo-object-recall-working",
            "verb": "recall",
            "source_repo": "aoa-routing",
            "target_surface": "generated/task_to_surface_hints.json",
            "match_key": "kind",
            "allowed_kinds": ["memo"],
            "target_kind": "memo",
            "target_value": "memo",
            "recall_family": "memory_objects",
            "recall_mode": "working",
        },
        {
            "name": "memo-object-recall-semantic",
            "verb": "recall",
            "source_repo": "aoa-routing",
            "target_surface": "generated/task_to_surface_hints.json",
            "match_key": "kind",
            "allowed_kinds": ["memo"],
            "target_kind": "memo",
            "target_value": "memo",
            "recall_family": "memory_objects",
            "recall_mode": "semantic",
        },
        {
            "name": "memo-object-recall-lineage",
            "verb": "recall",
            "source_repo": "aoa-routing",
            "target_surface": "generated/task_to_surface_hints.json",
            "match_key": "kind",
            "allowed_kinds": ["memo"],
            "target_kind": "memo",
            "target_value": "memo",
            "recall_family": "memory_objects",
            "recall_mode": "lineage",
        },
    ]
    assert tiny_model["federation_queries"] == [
        {
            "name": "federation-kind-pick",
            "verb": "pick",
            "source_repo": "aoa-routing",
            "target_surface": "generated/federation_entrypoints.min.json",
            "match_key": "kind",
            "allowed_entry_kinds": [
                "agent",
                "tier",
                "playbook",
                "kag_view",
                "source_route",
                "runtime_surface",
                "orientation_surface",
            ],
        },
        {
            "name": "federation-entry-inspect",
            "verb": "inspect",
            "source_repo": "aoa-routing",
            "target_surface": "generated/federation_entrypoints.min.json",
            "match_key": "id",
            "allowed_entry_kinds": [
                "agent",
                "tier",
                "playbook",
                "kag_view",
                "source_route",
                "runtime_surface",
                "orientation_surface",
            ],
        },
        {
            "name": "federation-root-inspect",
            "verb": "inspect",
            "source_repo": "aoa-routing",
            "target_surface": "generated/federation_entrypoints.min.json",
            "match_key": "id",
            "allowed_root_ids": ["aoa-root", "tos-root"],
        },
    ]
    assert tiny_model["federation_starters"] == [
        {
            "name": "federation-root",
            "verb": "pick",
            "source_repo": "aoa-routing",
            "target_surface": "generated/federation_entrypoints.min.json",
        },
        {
            "name": "aoa-root",
            "verb": "inspect",
            "source_repo": "aoa-routing",
            "target_surface": "generated/federation_entrypoints.min.json",
            "match_key": "id",
            "target_value": "aoa-root",
        },
        {
            "name": "tos-root",
            "verb": "inspect",
            "source_repo": "aoa-routing",
            "target_surface": "generated/federation_entrypoints.min.json",
            "match_key": "id",
            "target_value": "tos-root",
        },
        {
            "name": "agent-root",
            "verb": "inspect",
            "source_repo": "aoa-routing",
            "target_surface": "generated/federation_entrypoints.min.json",
            "match_key": "id",
            "target_value": "AOA-A-0001",
            "entry_kind": "agent",
        },
        {
            "name": "tier-root",
            "verb": "inspect",
            "source_repo": "aoa-routing",
            "target_surface": "generated/federation_entrypoints.min.json",
            "match_key": "id",
            "target_value": "router",
            "entry_kind": "tier",
        },
        {
            "name": "playbook-root",
            "verb": "inspect",
            "source_repo": "aoa-routing",
            "target_surface": "generated/federation_entrypoints.min.json",
            "match_key": "id",
            "target_value": "AOA-P-0008",
            "entry_kind": "playbook",
        },
        {
            "name": "kag-view-root",
            "verb": "inspect",
            "source_repo": "aoa-routing",
            "target_surface": "generated/federation_entrypoints.min.json",
            "match_key": "id",
            "target_value": "aoa-techniques",
            "entry_kind": "kag_view",
        },
        {
            "name": "source-route-root",
            "verb": "inspect",
            "source_repo": "aoa-routing",
            "target_surface": "generated/federation_entrypoints.min.json",
            "match_key": "id",
            "target_value": "dionysus-source-route",
            "entry_kind": "source_route",
        },
        {
            "name": "runtime-surface-root",
            "verb": "inspect",
            "source_repo": "aoa-routing",
            "target_surface": "generated/federation_entrypoints.min.json",
            "match_key": "id",
            "target_value": "aoa-sdk-control-plane",
            "entry_kind": "runtime_surface",
        },
        {
            "name": "checkpoint-root",
            "verb": "inspect",
            "source_repo": "aoa-routing",
            "target_surface": "generated/federation_entrypoints.min.json",
            "match_key": "id",
            "target_value": "aoa-sdk-control-plane",
            "entry_kind": "runtime_surface",
        },
        {
            "name": "orientation-surface-root",
            "verb": "inspect",
            "source_repo": "aoa-routing",
            "target_surface": "generated/federation_entrypoints.min.json",
            "match_key": "id",
            "target_value": "8dionysus-public-route-map",
            "entry_kind": "orientation_surface",
        },
    ]


def test_validate_generated_dir_matches_outputs_accepts_fixture_build(tmp_path: Path) -> None:
    outputs = build_fixture_outputs()
    generated_dir = tmp_path / "generated"
    for filename, payload in outputs.items():
        write_output(generated_dir / filename, payload)

    mismatches = build_router.validate_generated_dir_matches_outputs(outputs, generated_dir=generated_dir)
    assert mismatches == []


def test_validate_generated_dir_matches_outputs_rejects_stale_output(tmp_path: Path) -> None:
    outputs = build_fixture_outputs()
    generated_dir = tmp_path / "generated"
    for filename, payload in outputs.items():
        write_output(generated_dir / filename, payload)

    stale_path = generated_dir / "aoa_router.min.json"
    stale_payload = json.loads(stale_path.read_text(encoding="utf-8"))
    stale_payload["entries"][0]["summary"] = "stale router output"
    write_output(stale_path, stale_payload)

    mismatches = build_router.validate_generated_dir_matches_outputs(outputs, generated_dir=generated_dir)
    assert mismatches == [f"stale generated output: {stale_path.as_posix()}"]


def test_build_outputs_publish_federation_entry_abi_from_fixtures() -> None:
    outputs = build_fixture_outputs()
    federation = outputs["federation_entrypoints.min.json"]

    root_by_id = {entry["id"]: entry for entry in federation["root_entries"]}
    entry_by_key = {
        (entry["kind"], entry["id"]): entry for entry in federation["entrypoints"]
    }

    aoa_root = root_by_id["aoa-root"]
    assert aoa_root["capsule_surface"] == "Agents-of-Abyss:generated/center_entry_map.min.json"
    assert aoa_root["authority_surface"] == "Agents-of-Abyss:CHARTER.md"
    assert aoa_root["next_actions"] == [
        {
            "verb": "inspect",
            "target_repo": "Agents-of-Abyss",
            "target_surface": "generated/center_entry_map.min.json",
            "match_key": "route_id",
            "target_value": "center-overview",
        },
        {
            "verb": "inspect",
            "target_repo": "Agents-of-Abyss",
            "target_surface": "generated/center_entry_map.min.json",
            "match_key": "route_id",
            "target_value": "public-contour",
        },
        {
            "verb": "inspect",
            "target_repo": "Agents-of-Abyss",
            "target_surface": "generated/center_entry_map.min.json",
            "match_key": "route_id",
            "target_value": "source-of-truth-rules",
        },
    ]
    assert aoa_root["fallback"] == {
        "verb": "pick",
        "target_repo": "aoa-routing",
        "target_surface": "generated/aoa_router.min.json",
        "match_key": "kind",
        "target_value": "technique",
    }
    assert aoa_root["next_hops"] == [
        {"kind": "tier", "id": "router"},
        {"kind": "playbook", "id": "AOA-P-0008"},
        {"kind": "kag_view", "id": "aoa-techniques"},
    ]

    tos_root = root_by_id["tos-root"]
    assert tos_root["capsule_surface"] == "Tree-of-Sophia:ToS/derived-exports/root_entry_map.min.json"
    assert tos_root["authority_surface"] == "Tree-of-Sophia:CHARTER.md"
    assert tos_root["next_actions"] == [
        {
            "verb": "inspect",
            "target_repo": "Tree-of-Sophia",
            "target_surface": "ToS/derived-exports/root_entry_map.min.json",
            "match_key": "route_id",
            "target_value": "current-tiny-entry",
        },
        {
            "verb": "inspect",
            "target_repo": "Tree-of-Sophia",
            "target_surface": "ToS/derived-exports/root_entry_map.min.json",
            "match_key": "route_id",
            "target_value": "tree-first-model",
        },
        {
            "verb": "inspect",
            "target_repo": "Tree-of-Sophia",
            "target_surface": "ToS/derived-exports/root_entry_map.min.json",
            "match_key": "route_id",
            "target_value": "bounded-export",
        },
    ]
    assert tos_root["fallback"] == {
        "verb": "inspect",
        "target_repo": "aoa-routing",
        "target_surface": "generated/federation_entrypoints.min.json",
        "match_key": "id",
        "target_value": "aoa-root",
    }
    assert tos_root["next_hops"] == [
        {"kind": "kag_view", "id": "Tree-of-Sophia"},
        {"kind": "playbook", "id": "AOA-P-0009"},
    ]
    assert "source-owned tiny-entry route" in tos_root["risk"]

    router_tier = entry_by_key[("tier", "router")]
    assert router_tier["capsule_surface"] == "aoa-agents:generated/model_tier_registry.json"
    assert (
        router_tier["authority_surface"]
        == "aoa-agents:agents/operating-model/tiers/router.tier.json"
    )
    assert router_tier["fallback"] == {
        "verb": "inspect",
        "target_repo": "aoa-routing",
        "target_surface": "generated/federation_entrypoints.min.json",
        "match_key": "id",
        "target_value": "AOA-A-0001",
    }
    assert router_tier["next_hops"] == [{"kind": "agent", "id": "AOA-A-0001"}]

    kag_view = entry_by_key[("kag_view", "aoa-techniques")]
    assert kag_view["capsule_surface"] == f"aoa-kag:{router_core.FEDERATION_SPINE_PATH}"
    assert kag_view["authority_surface"] == f"aoa-kag:{router_core.FEDERATION_SPINE_AUTHORITY_PATH}"
    assert kag_view["next_actions"] == [
        {
            "verb": "inspect",
            "target_repo": "aoa-techniques",
            "target_surface": "generated/repo_doc_surface_manifest.min.json",
            "match_key": "doc_id",
            "target_value": "readme",
        },
        {
            "verb": "inspect",
            "target_repo": "aoa-techniques",
            "target_surface": "generated/technique_catalog.min.json",
            "match_key": "id",
            "target_value": "AOA-T-0001",
        },
    ]
    assert kag_view["next_hops"] == [
        {"kind": "tier", "id": "router"},
        {"kind": "playbook", "id": "AOA-P-0008"},
    ]

    tos_kag_view = entry_by_key[("kag_view", "Tree-of-Sophia")]
    assert tos_kag_view["capsule_surface"] == f"aoa-kag:{router_core.FEDERATION_SPINE_PATH}"
    assert tos_kag_view["authority_surface"] == f"aoa-kag:{router_core.FEDERATION_SPINE_AUTHORITY_PATH}"
    assert tos_kag_view["next_actions"] == [
        {
            "verb": "inspect",
            "target_repo": "Tree-of-Sophia",
            "target_surface": "ToS/zarathustra/public-entry/TINY_ENTRY_ROUTE.md",
            "match_key": "path",
            "target_value": "ToS/zarathustra/public-entry/TINY_ENTRY_ROUTE.md",
        },
        {
            "verb": "inspect",
            "target_repo": "Tree-of-Sophia",
            "target_surface": "ToS/public-compatibility/tos_tiny_entry_route.example.json",
            "match_key": "route_id",
            "target_value": "tos-tiny-entry.zarathustra-prologue",
        },
        {
            "verb": "inspect",
            "target_repo": "aoa-kag",
            "target_surface": router_core.TOS_ROUTE_RETRIEVAL_SURFACE_REF,
            "match_key": "retrieval_id",
            "target_value": "AOA-K-0011::thus-spoke-zarathustra/prologue-1",
        },
    ]
    assert tos_kag_view["next_hops"] == [
        {"kind": "tier", "id": "router"},
        {"kind": "playbook", "id": "AOA-P-0009"},
    ]
    assert "Tree-of-Sophia remains authoritative" in tos_kag_view["risk"]

    source_route_entry = entry_by_key[("source_route", "dionysus-source-route")]
    assert (
        source_route_entry["capsule_surface"]
        == "Dionysus:docs/decisions/DION-D-0001-conversational-self-portrait.md"
    )
    assert (
        source_route_entry["authority_surface"]
        == "Dionysus:docs/decisions/DION-D-0001-conversational-self-portrait.md"
    )
    assert source_route_entry["next_hops"] == [
        {"kind": "orientation_surface", "id": "8dionysus-public-route-map"},
        {"kind": "runtime_surface", "id": "aoa-sdk-control-plane"},
    ]

    sdk_runtime_entry = entry_by_key[("runtime_surface", "aoa-sdk-control-plane")]
    assert (
        sdk_runtime_entry["capsule_surface"]
        == "aoa-sdk:generated/workspace_control_plane.min.json"
    )
    assert sdk_runtime_entry["authority_surface"] == "aoa-sdk:docs/boundaries.md"

    stats_runtime_entry = entry_by_key[("runtime_surface", "aoa-stats-summary-catalog")]
    assert (
        stats_runtime_entry["capsule_surface"]
        == "aoa-stats:generated/summary_surface_catalog.min.json"
    )

    abyss_runtime_entry = entry_by_key[("runtime_surface", "abyss-stack-diagnostic-spine")]
    assert (
        abyss_runtime_entry["capsule_surface"]
        == f"abyss-stack:{router_core.ABYSS_STACK_DIAGNOSTIC_SURFACE_CATALOG_PATH}"
    )

    profile_entry = entry_by_key[("orientation_surface", "8dionysus-public-route-map")]
    assert profile_entry["capsule_surface"] == "8Dionysus:generated/public_route_map.min.json"


def test_build_outputs_reject_tos_kag_view_spine_drift(tmp_path: Path) -> None:
    kag_root = tmp_path / "aoa-kag"
    shutil.copytree(FIXTURES_ROOT / "aoa-kag", kag_root)
    spine_path = kag_root / router_core.FEDERATION_SPINE_PATH
    payload = json.loads(spine_path.read_text(encoding="utf-8"))
    payload["repos"][1]["entry_surface_ref"] = "Tree-of-Sophia/README.md"
    write_json(spine_path, payload)

    with pytest.raises(build_router.RouterError, match="entry_surface_ref must stay"):
        build_fixture_outputs(kag_root=kag_root)


def test_build_outputs_reject_kag_view_export_object_drift(tmp_path: Path) -> None:
    kag_root = tmp_path / "aoa-kag"
    shutil.copytree(FIXTURES_ROOT / "aoa-kag", kag_root)
    spine_path = kag_root / router_core.FEDERATION_SPINE_PATH
    payload = json.loads(spine_path.read_text(encoding="utf-8"))
    payload["repos"][0]["object_id"] = "AOA-T-DRIFTED"
    write_json(spine_path, payload)

    with pytest.raises(build_router.RouterError, match="object_id must stay"):
        build_fixture_outputs(kag_root=kag_root)


def test_tos_tiny_entry_hop_surface_canonicalizes_equivalent_relative_refs(tmp_path: Path) -> None:
    tos_root = tmp_path / "Tree-of-Sophia"
    target = tos_root / "ToS" / "public-compatibility" / "concept_node.example.json"
    target.parent.mkdir(parents=True)
    target.write_text("{}\n", encoding="utf-8")

    hop = router_core.load_tos_tiny_entry_hop_surface(
        {
            "bounded_hop": "ToS/public-compatibility/./concept_node.example.json",
            "lineage_or_context_hop": "ToS/public-compatibility/concept_node.example.json",
        },
        "fixture",
        tos_root=tos_root,
    )

    assert hop == "ToS/public-compatibility/concept_node.example.json"


def test_build_outputs_accept_compact_kag_spine_entries(tmp_path: Path) -> None:
    kag_root = tmp_path / "aoa-kag"
    shutil.copytree(FIXTURES_ROOT / "aoa-kag", kag_root)
    spine_path = kag_root / router_core.FEDERATION_SPINE_PATH
    payload = json.loads(spine_path.read_text(encoding="utf-8"))
    payload["repos"] = [
        {
            "repo": "aoa-techniques",
            "pilot_posture": "source_owned_export_tiny",
            "export_ref": "aoa-techniques/generated/kag_export.min.json",
            "kind": "technique",
            "object_id": "AOA-T-0043",
            "entry_surface_ref": "aoa-techniques/generated/technique_capsules.json",
            "adjunct_surfaces": [],
            "summary_50": payload["repos"][0]["provenance_note"],
            "provenance_note": payload["repos"][0]["provenance_note"],
            "non_identity_boundary": payload["repos"][0]["non_identity_boundary"],
        },
        {
            "repo": "Tree-of-Sophia",
            "pilot_posture": "source_owned_export_tiny",
            "export_ref": "Tree-of-Sophia/ToS/derived-exports/kag_export.min.json",
            "kind": "source_node",
            "object_id": "tos.source.thus-spoke-zarathustra.prologue",
            "entry_surface_ref": "Tree-of-Sophia/ToS/public-compatibility/source_node.example.json",
            "adjunct_surfaces": [
                {
                    "surface_id": "AOA-K-0011",
                    "surface_name": "tos-zarathustra-route-retrieval-surface",
                    "surface_ref": router_core.TOS_ROUTE_RETRIEVAL_SURFACE_REF,
                    "match_key": "retrieval_id",
                    "target_value": "AOA-K-0011::thus-spoke-zarathustra/prologue-1",
                    "route_id": "thus-spoke-zarathustra/prologue-1",
                }
            ],
            "summary_50": payload["repos"][1]["provenance_note"],
            "provenance_note": payload["repos"][1]["provenance_note"],
            "non_identity_boundary": payload["repos"][1]["non_identity_boundary"],
        },
    ]
    write_json(spine_path, payload)

    outputs = build_fixture_outputs(kag_root=kag_root)

    entry_by_key = {
        (entry["kind"], entry["id"]): entry
        for entry in outputs["federation_entrypoints.min.json"]["entrypoints"]
    }
    assert entry_by_key[("kag_view", "aoa-techniques")]["next_actions"] == [
        {
            "verb": "inspect",
            "target_repo": "aoa-techniques",
            "target_surface": "generated/repo_doc_surface_manifest.min.json",
            "match_key": "doc_id",
            "target_value": "readme",
        },
        {
            "verb": "inspect",
            "target_repo": "aoa-techniques",
            "target_surface": "generated/technique_catalog.min.json",
            "match_key": "id",
            "target_value": "AOA-T-0001",
        },
    ]
    assert entry_by_key[("kag_view", "Tree-of-Sophia")]["next_actions"] == [
        {
            "verb": "inspect",
            "target_repo": "Tree-of-Sophia",
            "target_surface": "ToS/zarathustra/public-entry/TINY_ENTRY_ROUTE.md",
            "match_key": "path",
            "target_value": "ToS/zarathustra/public-entry/TINY_ENTRY_ROUTE.md",
        },
        {
            "verb": "inspect",
            "target_repo": "Tree-of-Sophia",
            "target_surface": "ToS/public-compatibility/tos_tiny_entry_route.example.json",
            "match_key": "route_id",
            "target_value": "tos-tiny-entry.zarathustra-prologue",
        },
        {
            "verb": "inspect",
            "target_repo": "aoa-kag",
            "target_surface": router_core.TOS_ROUTE_RETRIEVAL_SURFACE_REF,
            "match_key": "retrieval_id",
            "target_value": "AOA-K-0011::thus-spoke-zarathustra/prologue-1",
        },
    ]


def test_build_outputs_lifts_kag_source_family_relations(tmp_path: Path) -> None:
    techniques_root = tmp_path / "aoa-techniques"
    shutil.copytree(FIXTURES_ROOT / "aoa-techniques", techniques_root)
    catalog_path = techniques_root / "generated" / "technique_catalog.min.json"
    payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    payload["techniques"].extend(build_kag_source_lift_technique_entries())
    write_json(catalog_path, payload)

    outputs = build_fixture_outputs(techniques_root=techniques_root)

    relation_hints = outputs["kag_source_lift_relation_hints.min.json"]
    pairing = outputs["pairing_hints.min.json"]
    tiny_model = outputs["tiny_model_entrypoints.json"]
    assert relation_hints["family_ids"] == KAG_SOURCE_LIFT_TECHNIQUE_IDS
    by_id = {entry["id"]: entry for entry in relation_hints["entries"]}
    assert by_id["AOA-T-0018"]["relations"] == [
        {"type": "complements", "target": "AOA-T-0019"}
    ]
    assert by_id["AOA-T-0019"]["relations"] == [
        {"type": "complements", "target": "AOA-T-0018"},
        {"type": "used_together_for", "target": "AOA-T-0020"},
        {"type": "used_together_for", "target": "AOA-T-0021"},
    ]
    assert by_id["AOA-T-0021"]["relations"] == [
        {"type": "requires", "target": "AOA-T-0019"}
    ]
    pairing_by_id = {entry["id"]: entry for entry in pairing["entries"] if entry["kind"] == "technique"}
    assert pairing_by_id["AOA-T-0019"]["pairs"] == [
        {"kind": "technique", "id": "AOA-T-0018", "relation": "complements"},
        {"kind": "technique", "id": "AOA-T-0020", "relation": "used_together_for"},
        {"kind": "technique", "id": "AOA-T-0021", "relation": "used_together_for"},
    ]
    assert tiny_model["starters"][-2:] == [
        {
            "name": "kag-source-lift-default",
            "verb": "inspect",
            "source_repo": "aoa-techniques",
            "target_surface": "generated/technique_capsules.json",
            "match_key": "id",
            "allowed_kinds": ["technique"],
            "target_kind": "technique",
            "target_value": "AOA-T-0019",
        },
        {
            "name": "kag-source-lift-companions",
            "verb": "pair",
            "source_repo": "aoa-routing",
            "target_surface": "generated/pairing_hints.min.json",
            "match_key": "id",
            "allowed_kinds": ["technique"],
            "target_kind": "technique",
            "target_value": "AOA-T-0019",
        },
    ]


def test_build_outputs_do_not_recreate_a_routing_owned_skill_router() -> None:
    outputs = build_fixture_outputs()

    assert not any("two_stage" in output_name for output_name in outputs)
    skill_hint = next(
        hint for hint in outputs["task_to_surface_hints.json"]["hints"]
        if hint["kind"] == "skill"
    )
    assert skill_hint["actions"]["inspect"]["surface_file"] == (
        "generated/agent_skill_catalog.min.json"
    )
    assert skill_hint["actions"]["expand"]["surface_file"] == (
        "generated/capability_graph.json"
    )
    assert skill_hint["actions"]["pair"] == {"enabled": False}


def test_build_outputs_limits_tiny_model_recall_modes_to_router_ready_contracts(tmp_path: Path) -> None:
    memo_root = tmp_path / "aoa-memo"
    shutil.copytree(FIXTURES_ROOT / "aoa-memo", memo_root)
    (memo_root / "examples" / "recall" / "recall_contract.router.source_route.json").unlink()
    (memo_root / "examples" / "recall" / "recall_contract.router.lineage.json").unlink()

    outputs = build_fixture_outputs(memo_root=memo_root)

    memo_hint = next(
        hint for hint in outputs["task_to_surface_hints.json"]["hints"] if hint["kind"] == "memo"
    )
    assert memo_hint["actions"]["recall"] == {
        "enabled": True,
        "contract_file": "examples/recall/recall_contract.router.semantic.json",
        "default_mode": "semantic",
        "supported_modes": ["semantic"],
        "contracts_by_mode": {
            "semantic": "examples/recall/recall_contract.router.semantic.json",
        },
        "capsule_surfaces_by_mode": {
            "semantic": "generated/memory/memory_capsules.json",
        },
        "parallel_families": {
            "memory_objects": {
                "inspect_surface": "generated/memory-objects/memory_object_catalog.min.json",
                "expand_surface": "generated/memory-objects/memory_object_sections.full.json",
                "default_mode": "working",
                "supported_modes": ["working", "semantic", "lineage"],
                "contracts_by_mode": {
                    "working": "examples/recall/recall_contract.object.working.json",
                    "semantic": "examples/recall/recall_contract.object.semantic.json",
                    "lineage": "examples/recall/recall_contract.object.lineage.json",
                },
                "capsule_surfaces_by_mode": {
                    "semantic": "generated/memory-objects/memory_object_capsules.json",
                    "lineage": "generated/memory-objects/memory_object_capsules.json",
                },
            }
        },
    }
    recall_starters = [
        starter
        for starter in outputs["tiny_model_entrypoints.json"]["starters"]
        if starter["verb"] == "recall"
    ]
    assert recall_starters == [
        {
            "name": "memo-recall-semantic",
            "verb": "recall",
            "source_repo": "aoa-routing",
            "target_surface": "generated/task_to_surface_hints.json",
            "match_key": "kind",
            "allowed_kinds": ["memo"],
            "target_kind": "memo",
            "target_value": "memo",
            "recall_mode": "semantic",
        },
        {
            "name": "memo-object-recall-working",
            "verb": "recall",
            "source_repo": "aoa-routing",
            "target_surface": "generated/task_to_surface_hints.json",
            "match_key": "kind",
            "allowed_kinds": ["memo"],
            "target_kind": "memo",
            "target_value": "memo",
            "recall_family": "memory_objects",
            "recall_mode": "working",
        },
        {
            "name": "memo-object-recall-semantic",
            "verb": "recall",
            "source_repo": "aoa-routing",
            "target_surface": "generated/task_to_surface_hints.json",
            "match_key": "kind",
            "allowed_kinds": ["memo"],
            "target_kind": "memo",
            "target_value": "memo",
            "recall_family": "memory_objects",
            "recall_mode": "semantic",
        },
        {
            "name": "memo-object-recall-lineage",
            "verb": "recall",
            "source_repo": "aoa-routing",
            "target_surface": "generated/task_to_surface_hints.json",
            "match_key": "kind",
            "allowed_kinds": ["memo"],
            "target_kind": "memo",
            "target_value": "memo",
            "recall_family": "memory_objects",
            "recall_mode": "lineage",
        },
    ]


def test_build_outputs_omits_parallel_object_family_when_object_contract_is_missing(tmp_path: Path) -> None:
    memo_root = tmp_path / "aoa-memo"
    shutil.copytree(FIXTURES_ROOT / "aoa-memo", memo_root)
    (memo_root / "examples" / "recall" / "recall_contract.object.lineage.json").unlink()

    outputs = build_fixture_outputs(memo_root=memo_root)

    memo_hint = next(
        hint for hint in outputs["task_to_surface_hints.json"]["hints"] if hint["kind"] == "memo"
    )
    assert "parallel_families" not in memo_hint["actions"]["recall"]
    assert all(
        starter.get("recall_family") != "memory_objects"
        for starter in outputs["tiny_model_entrypoints.json"]["starters"]
        if starter["verb"] == "recall"
    )
    assert all(
        query.get("recall_family") != "memory_objects"
        for query in outputs["tiny_model_entrypoints.json"]["queries"]
        if query["verb"] == "recall"
    )


def test_build_outputs_omits_parallel_object_family_when_object_surface_is_missing(tmp_path: Path) -> None:
    memo_root = tmp_path / "aoa-memo"
    shutil.copytree(FIXTURES_ROOT / "aoa-memo", memo_root)
    (
        memo_root
        / "generated"
        / "memory-objects"
        / "memory_object_sections.full.json"
    ).unlink()

    outputs = build_fixture_outputs(memo_root=memo_root)

    memo_hint = next(
        hint for hint in outputs["task_to_surface_hints.json"]["hints"] if hint["kind"] == "memo"
    )
    assert "parallel_families" not in memo_hint["actions"]["recall"]
    assert all(
        starter.get("recall_family") != "memory_objects"
        for starter in outputs["tiny_model_entrypoints.json"]["starters"]
        if starter["verb"] == "recall"
    )
    assert all(
        query.get("recall_family") != "memory_objects"
        for query in outputs["tiny_model_entrypoints.json"]["queries"]
        if query["verb"] == "recall"
    )


def test_build_uses_catalog_only_ingestion_for_skills_and_evals(tmp_path: Path) -> None:
    skills_root = tmp_path / "aoa-skills"
    evals_root = tmp_path / "aoa-evals"
    shutil.copytree(FIXTURES_ROOT / "aoa-skills", skills_root)
    shutil.copytree(FIXTURES_ROOT / "aoa-evals", evals_root)
    shutil.rmtree(skills_root / "skills")
    shutil.rmtree(evals_root / "bundles")

    outputs = build_fixture_outputs(skills_root=skills_root, evals_root=evals_root)

    assert len(outputs["cross_repo_registry.min.json"]["entries"]) == 8


def test_build_preserves_typed_eval_capability_dependencies() -> None:
    outputs = build_fixture_outputs()
    registry_entries = outputs["cross_repo_registry.min.json"]["entries"]
    eval_entry = next(
        entry for entry in registry_entries
        if entry["kind"] == "eval" and entry["id"] == "aoa-bounded-change-quality"
    )
    assert eval_entry["attributes"]["capability_dependencies"] == [
        "workflow.operations.repository-change"
    ]
    assert eval_entry["attributes"]["capability_refs"] == [
        {
            "id": "workflow.operations.repository-change",
            "kind": "workflow",
            "registry_repo": "aoa-skills",
            "registry_path": "capabilities/families/operations.yaml",
            "target_owner": "host-agent",
        }
    ]


def test_build_outputs_composite_stress_hints_include_memo_recovery_context(
    tmp_path: Path,
) -> None:
    roots = {}
    for repo_name in FIXTURE_REPO_NAMES:
        target = tmp_path / repo_name
        shutil.copytree(FIXTURES_ROOT / repo_name, target)
        roots[repo_name] = target

    catalog_path = (
        roots["aoa-memo"]
        / "generated"
        / "memory-objects"
        / "memory_object_catalog.min.json"
    )
    catalog_payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    catalog_payload["memory_objects"].append(
        {
            "id": "memo.pattern.2026-04-07.antifragility-stress-recovery-window",
            "kind": "pattern",
            "title": "Stress recovery stays bounded only when replay follows source receipt, gate, and regrounding order",
            "summary": "Reviewed recovery pattern for the composite stress window.",
            "scope_classes": ["repo", "project"],
            "temperature": "cool",
            "review_state": "confirmed",
            "current_recall_status": "preferred",
            "authority_kind": "human_reviewed",
            "primary_recall_modes": ["procedural", "semantic"],
            "source_path": "examples/pattern.antifragility-stress-recovery-window.example.json",
            "inspect_key": "memo.pattern.2026-04-07.antifragility-stress-recovery-window",
            "expand_key": "memo.pattern.2026-04-07.antifragility-stress-recovery-window",
        }
    )
    write_json(catalog_path, catalog_payload)

    outputs = build_router.build_outputs(
        roots["aoa-techniques"],
        roots["aoa-skills"],
        roots["aoa-evals"],
        roots["aoa-memo"],
        roots["aoa-stats"],
        roots["aoa-agents"],
        roots["Agents-of-Abyss"],
        roots["aoa-playbooks"],
        roots["aoa-kag"],
        roots["Tree-of-Sophia"],
        roots["aoa-sdk"],
        roots["Dionysus"],
        roots["8Dionysus"],
        roots["abyss-stack"],
    )

    hint = outputs["composite_stress_route_hints.min.json"]["hints"][0]
    assert hint["input_refs"]["memo_pattern_refs"] == [
        "aoa-memo:examples/pattern.antifragility-stress-recovery-window.example.json"
    ]
    assert hint["memo_context"] == [
        {
            "memory_id": "memo.pattern.2026-04-07.antifragility-stress-recovery-window",
            "title": "Stress recovery stays bounded only when replay follows source receipt, gate, and regrounding order",
            "source_path": "examples/pattern.antifragility-stress-recovery-window.example.json",
            "review_state": "confirmed",
            "current_recall_status": "preferred",
        }
    ]
    assert hint["next_hops"][-1] == {
        "kind": "memo_pattern",
        "target_repo": "aoa-memo",
        "target_surface": "examples/pattern.antifragility-stress-recovery-window.example.json",
        "reason": "Reviewed recovery-pattern context may be recalled after source receipts and re-entry gates are named.",
        "bounded": True,
    }


def test_build_outputs_adds_stats_regrounding_advisory_hints() -> None:
    outputs = build_fixture_outputs()
    payload = outputs["stats_regrounding_hints.min.json"]

    assert payload["schema_version"] == "aoa_routing_stats_regrounding_hints_v1"
    assert (
        payload["schema_ref"]
        == "mechanics/boundary-bridge/parts/stats-regrounding/schemas/stats-regrounding-hints.schema.json"
    )
    assert payload["coverage_thin_signal_flags"] == [
        "missing_owner_repos",
        "owner_share_dominant",
    ]
    hint = next(
        item for item in payload["hints"] if item["surface_name"] == "surface_detection_summary"
    )
    assert hint["recommended_action"] == "reground_before_using_stats"
    assert hint["advisory_only"] is True
    assert hint["primary_action"] == {
        "verb": "inspect",
        "target_repo": "aoa-skills",
        "target_ref": "aoa-skills core skill application receipts",
    }
    assert "high_consumer_risk" in hint["reason_codes"]
    assert "coverage_owner_share_dominant" in hint["reason_codes"]


def test_stats_regrounding_routes_progression_snapshot_to_current_owner_truth(
    tmp_path: Path,
) -> None:
    stats_root = tmp_path / "aoa-stats"
    shutil.copytree(FIXTURES_ROOT / "aoa-stats", stats_root)
    catalog_path = stats_root / "generated" / "summary_surface_catalog.min.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    owner_truth_inputs = [
        "aoa-skills/skills/core/session-growth/aoa-session-progression-lift/references/progression-delta-receipt-schema.yaml",
        "aoa-skills/mechanics/growth-cycle/examples/session-growth-artifacts/progression_delta_receipt.kernel-maturity.json",
        "Agents-of-Abyss RPG center progression vocabulary and stop-lines",
        "aoa-agents agent-layer seven-axis progression-model contract",
        "aoa-sdk typed progression and checkpoint-carry contracts",
    ]
    authority_note = (
        "Weaker than current aoa-skills semantic receipts, the RPG center vocabulary, "
        "aoa-agents progression meaning, aoa-sdk contracts, and owner-local route "
        "decisions; this legacy numeric snapshot is not live progression truth."
    )
    catalog["surfaces"].append(
        {
            "name": "route_progression_summary",
            "surface_ref": "generated/route_progression_summary.min.json",
            "input_posture": "committed_legacy_numeric_receipt_snapshot",
            "owner_truth_inputs": owner_truth_inputs,
            "authority_ceiling": authority_note,
            "consumer_risk": "high",
            "live_state_capable": False,
        }
    )
    write_json(catalog_path, catalog)

    payload = build_router.build_stats_regrounding_hints_payload(stats_root)
    derived_hint = next(
        item
        for item in payload["hints"]
        if item["surface_name"] == "route_progression_summary"
    )
    committed_payload = json.loads(
        (
            CANONICAL_GENERATED_ROOT
            / "stats_regrounding_hints.min.json"
        ).read_text(encoding="utf-8")
    )
    committed_hint = next(
        item
        for item in committed_payload["hints"]
        if item["surface_name"] == "route_progression_summary"
    )

    assert derived_hint["owner_truth_inputs"] == owner_truth_inputs
    assert derived_hint["primary_action"] == {
        "verb": "inspect",
        "target_repo": "aoa-skills",
        "target_ref": owner_truth_inputs[0],
    }
    assert derived_hint["authority_note"] == authority_note
    for field in ("owner_truth_inputs", "primary_action", "authority_note"):
        assert committed_hint[field] == derived_hint[field]


def test_stats_regrounding_omits_retired_runtime_closeout_and_keeps_receipt_routes(
    tmp_path: Path,
) -> None:
    stats_root = tmp_path / "aoa-stats"
    shutil.copytree(FIXTURES_ROOT / "aoa-stats", stats_root)
    catalog_path = stats_root / "generated" / "summary_surface_catalog.min.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    generic_receipt_routes = {
        "object_summary": {
            "surface_ref": "generated/object_summary.min.json",
            "owner_truth_inputs": ["owner-local receipts across the active registry"],
            "authority_note": "Weaker than the owner repos named in object_ref and weaker than any linked evidence surface.",
        },
        "repeated_window_summary": {
            "surface_ref": "generated/repeated_window_summary.min.json",
            "owner_truth_inputs": ["owner-local receipts across the active registry"],
            "authority_note": "Weaker than the underlying receipt feed and any owner-local chronology or closeout record.",
        },
    }
    for surface_name, contract in generic_receipt_routes.items():
        catalog["surfaces"].append(
            {
                "name": surface_name,
                "surface_ref": contract["surface_ref"],
                "input_posture": "receipt_backed_live",
                "owner_truth_inputs": contract["owner_truth_inputs"],
                "authority_ceiling": contract["authority_note"],
                "consumer_risk": "medium",
                "live_state_capable": True,
            }
        )
    write_json(catalog_path, catalog)

    payload = build_router.build_stats_regrounding_hints_payload(stats_root)
    derived_hints = {item["surface_name"]: item for item in payload["hints"]}
    committed_payload = json.loads(
        (
            CANONICAL_GENERATED_ROOT
            / "stats_regrounding_hints.min.json"
        ).read_text(encoding="utf-8")
    )
    committed_hints = {
        item["surface_name"]: item for item in committed_payload["hints"]
    }

    assert "runtime_closeout_summary" not in derived_hints
    assert "runtime_closeout_summary" not in committed_hints
    assert "generated/runtime_closeout_summary.min.json" not in json.dumps(
        committed_payload, sort_keys=True
    )

    for surface_name, contract in generic_receipt_routes.items():
        derived_hint = derived_hints[surface_name]
        assert derived_hint["owner_truth_inputs"] == contract["owner_truth_inputs"]
        assert derived_hint["authority_note"] == contract["authority_note"]
        for field in ("owner_truth_inputs", "primary_action", "authority_note"):
            assert committed_hints[surface_name][field] == derived_hint[field]

    assert "source_coverage_summary" in derived_hints
    assert "source_coverage_summary" in committed_hints


def test_stats_regrounding_routes_active_titan_and_omits_retired_summon(
    tmp_path: Path,
) -> None:
    stats_root = tmp_path / "aoa-stats"
    shutil.copytree(FIXTURES_ROOT / "aoa-stats", stats_root)
    catalog_path = stats_root / "generated" / "summary_surface_catalog.min.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    incarnation_contract = {
        "surface_ref": "generated/titan_incarnation_summary.min.json",
        "owner_truth_inputs": [
            "aoa-agents/mechanics/titan/parts/incarnation-spine/examples/operator-console-roster.v0.json",
            "aoa-agents/mechanics/titan/parts/runtime-roster/examples/runtime-roster.v0.json",
            "aoa-sdk/mechanics/titan/parts/incarnation-identity-runtime-helper-contracts/examples/titan_session_receipt.v2.example.json",
        ],
        "primary_action": {
            "verb": "inspect",
            "target_repo": "aoa-agents",
            "target_ref": "aoa-agents/mechanics/titan/parts/incarnation-spine/examples/operator-console-roster.v0.json",
        },
        "authority_note": "Weaker than current aoa-agents Titan identity and gate state, aoa-sdk runtime state, any owner-local session receipt, and operator review evidence.",
    }
    catalog["surfaces"].append(
        {
            "name": "titan_incarnation_summary",
            "surface_ref": incarnation_contract["surface_ref"],
            "input_posture": "reference_only",
            "owner_truth_inputs": incarnation_contract["owner_truth_inputs"],
            "authority_ceiling": incarnation_contract["authority_note"],
            "consumer_risk": "high",
            "live_state_capable": False,
        }
    )
    write_json(catalog_path, catalog)

    payload = build_router.build_stats_regrounding_hints_payload(stats_root)
    derived_hints = {item["surface_name"]: item for item in payload["hints"]}
    committed_payload = json.loads(
        (
            CANONICAL_GENERATED_ROOT
            / "stats_regrounding_hints.min.json"
        ).read_text(encoding="utf-8")
    )
    committed_hints = {
        item["surface_name"]: item for item in committed_payload["hints"]
    }

    derived_hint = derived_hints["titan_incarnation_summary"]
    assert derived_hint["owner_truth_inputs"] == incarnation_contract[
        "owner_truth_inputs"
    ]
    assert derived_hint["primary_action"] == incarnation_contract["primary_action"]
    assert derived_hint["authority_note"] == incarnation_contract["authority_note"]
    for field in ("owner_truth_inputs", "primary_action", "authority_note"):
        assert committed_hints["titan_incarnation_summary"][field] == derived_hint[
            field
        ]

    assert "titan_summon_summary" not in derived_hints
    assert "titan_summon_summary" not in committed_hints
    assert "generated/titan_summon_summary.min.json" not in json.dumps(
        committed_payload, sort_keys=True
    )


def test_stats_regrounding_omits_retired_owner_landing_and_keeps_turnover_routes(
    tmp_path: Path,
) -> None:
    stats_root = tmp_path / "aoa-stats"
    shutil.copytree(FIXTURES_ROOT / "aoa-stats", stats_root)
    catalog_path = stats_root / "generated" / "summary_surface_catalog.min.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    owner_truth_inputs = [
        "aoa-skills reviewed harvest receipts",
        "aoa-skills reviewed owner landing receipts",
        "Dionysus source-route owner landing traces",
    ]
    authority_note = (
        "Weaker than reviewed turnover records and any owner-local acceptance or "
        "rejection rationale."
    )
    catalog["surfaces"].append(
        {
            "name": "supersession_drop_summary",
            "surface_ref": "generated/supersession_drop_summary.min.json",
            "input_posture": "receipt_backed_live",
            "owner_truth_inputs": owner_truth_inputs,
            "authority_ceiling": authority_note,
            "consumer_risk": "high",
            "live_state_capable": True,
        }
    )
    write_json(catalog_path, catalog)

    payload = build_router.build_stats_regrounding_hints_payload(stats_root)
    derived_hints = {item["surface_name"]: item for item in payload["hints"]}
    committed_payload = json.loads(
        (
            CANONICAL_GENERATED_ROOT
            / "stats_regrounding_hints.min.json"
        ).read_text(encoding="utf-8")
    )
    committed_hints = {
        item["surface_name"]: item for item in committed_payload["hints"]
    }

    assert "owner_landing_summary" not in derived_hints
    assert "owner_landing_summary" not in committed_hints
    assert "generated/owner_landing_summary.min.json" not in json.dumps(
        committed_payload, sort_keys=True
    )

    derived_hint = derived_hints["supersession_drop_summary"]
    assert derived_hint["owner_truth_inputs"] == owner_truth_inputs
    assert derived_hint["primary_action"] == {
        "verb": "inspect",
        "target_repo": "aoa-skills",
        "target_ref": owner_truth_inputs[0],
    }
    assert derived_hint["authority_note"] == authority_note
    for field in ("owner_truth_inputs", "primary_action", "authority_note"):
        assert committed_hints["supersession_drop_summary"][field] == derived_hint[
            field
        ]


def test_stats_regrounding_hints_require_summary_surfaces_key(tmp_path: Path) -> None:
    stats_root = tmp_path / "aoa-stats"
    shutil.copytree(FIXTURES_ROOT / "aoa-stats", stats_root)
    catalog_path = stats_root / "generated" / "summary_surface_catalog.min.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    catalog.pop("surfaces")
    write_json(catalog_path, catalog)

    with pytest.raises(build_router.RouterError, match="summary_surface_catalog.surfaces"):
        build_router.build_stats_regrounding_hints_payload(stats_root)


def test_stats_regrounding_hints_read_legacy_surface_path(tmp_path: Path) -> None:
    stats_root = tmp_path / "aoa-stats"
    shutil.copytree(FIXTURES_ROOT / "aoa-stats", stats_root)
    catalog_path = stats_root / "generated" / "summary_surface_catalog.min.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    surface = next(item for item in catalog["surfaces"] if item["name"] == "surface_detection_summary")
    legacy_ref = surface.pop("surface_ref")
    surface["surface_path"] = legacy_ref
    write_json(catalog_path, catalog)

    payload = build_router.build_stats_regrounding_hints_payload(stats_root)
    hint = next(
        item for item in payload["hints"] if item["surface_name"] == "surface_detection_summary"
    )

    assert hint["surface_ref"] == legacy_ref


def test_build_outputs_composite_stress_hints_skip_unreviewed_or_unrecallable_patterns(
    tmp_path: Path,
) -> None:
    roots = {}
    for repo_name in FIXTURE_REPO_NAMES:
        target = tmp_path / repo_name
        shutil.copytree(FIXTURES_ROOT / repo_name, target)
        roots[repo_name] = target

    catalog_path = (
        roots["aoa-memo"]
        / "generated"
        / "memory-objects"
        / "memory_object_catalog.min.json"
    )
    catalog_payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    catalog_payload["memory_objects"].extend(
        [
            {
                "id": "memo.pattern.2026-04-07.antifragility-stress-recovery-window-draft",
                "kind": "pattern",
                "title": "Draft recovery pattern should stay out of routing",
                "summary": "Unreviewed recovery pattern.",
                "scope_classes": ["repo"],
                "temperature": "warm",
                "review_state": "captured",
                "current_recall_status": "preferred",
                "authority_kind": "human_reviewed",
                "primary_recall_modes": ["procedural"],
                "source_path": "examples/pattern.antifragility-stress-recovery-window-draft.example.json",
                "inspect_key": "memo.pattern.2026-04-07.antifragility-stress-recovery-window-draft",
                "expand_key": "memo.pattern.2026-04-07.antifragility-stress-recovery-window-draft",
            },
            {
                "id": "memo.pattern.2026-04-07.antifragility-stress-recovery-window-muted",
                "kind": "pattern",
                "title": "Muted recovery pattern should stay out of routing",
                "summary": "Non-recallable recovery pattern.",
                "scope_classes": ["repo"],
                "temperature": "warm",
                "review_state": "confirmed",
                "current_recall_status": "blocked",
                "authority_kind": "human_reviewed",
                "primary_recall_modes": ["procedural"],
                "source_path": "examples/pattern.antifragility-stress-recovery-window-muted.example.json",
                "inspect_key": "memo.pattern.2026-04-07.antifragility-stress-recovery-window-muted",
                "expand_key": "memo.pattern.2026-04-07.antifragility-stress-recovery-window-muted",
            },
        ]
    )
    write_json(catalog_path, catalog_payload)

    outputs = build_router.build_outputs(
        roots["aoa-techniques"],
        roots["aoa-skills"],
        roots["aoa-evals"],
        roots["aoa-memo"],
        roots["aoa-stats"],
        roots["aoa-agents"],
        roots["Agents-of-Abyss"],
        roots["aoa-playbooks"],
        roots["aoa-kag"],
        roots["Tree-of-Sophia"],
        roots["aoa-sdk"],
        roots["Dionysus"],
        roots["8Dionysus"],
        roots["abyss-stack"],
    )

    hint = outputs["composite_stress_route_hints.min.json"]["hints"][0]
    assert hint["input_refs"]["memo_pattern_refs"] == []
    assert hint["memo_context"] == []


def test_build_is_deterministic_on_repeated_runs(tmp_path: Path) -> None:
    generated_dir = tmp_path / "generated"
    outputs_a = build_fixture_outputs()
    for filename, payload in outputs_a.items():
        write_output(generated_dir / filename, payload)
    snapshot_a = {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted(generated_dir.iterdir())
    }

    outputs_b = build_fixture_outputs()
    for filename, payload in outputs_b.items():
        write_output(generated_dir / filename, payload)
    snapshot_b = {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted(generated_dir.iterdir())
    }

    assert snapshot_a == snapshot_b


def test_owner_layer_shortlist_includes_explicit_and_ambiguous_family_hints() -> None:
    outputs = build_fixture_outputs()

    shortlist = outputs["owner_layer_shortlist.min.json"]
    explicit_skill = next(
        entry
        for entry in shortlist["hints"]
        if entry["signal"] == "explicit-request" and entry["owner_repo"] == "aoa-skills"
    )
    recurring_entries = [
        entry
        for entry in shortlist["hints"]
        if entry["signal"] == "scenario-recurring"
    ]
    explicit_source_route = next(
        entry
        for entry in shortlist["hints"]
        if entry["signal"] == "explicit-request" and entry["owner_repo"] == "Dionysus"
    )
    explicit_runtime = next(
        entry
        for entry in shortlist["hints"]
        if entry["signal"] == "explicit-request" and entry["owner_repo"] == "abyss-stack"
    )
    explicit_profile = next(
        entry
        for entry in shortlist["hints"]
        if entry["signal"] == "explicit-request" and entry["owner_repo"] == "8Dionysus"
    )

    assert explicit_skill["target_surface"] == "aoa-skills.agent_skill_catalog.min"
    assert explicit_source_route["target_surface"] == "Dionysus.source_route_anchor"
    assert explicit_runtime["target_surface"] == "abyss-stack.diagnostic_surface_catalog.min"
    assert explicit_profile["target_surface"] == "8Dionysus.public_route_map.min"
    assert explicit_skill["confidence"] == "high"
    assert {entry["owner_repo"] for entry in recurring_entries} == {
        "aoa-playbooks",
        "aoa-techniques",
    }
    assert {entry["ambiguity"] for entry in recurring_entries} == {"clear", "ambiguous"}


def test_owner_layer_shortlist_routes_memory_readiness_pressure_to_memo_registry() -> None:
    outputs = build_fixture_outputs()

    shortlist = outputs["owner_layer_shortlist.min.json"]
    memory_readiness = next(
        entry
        for entry in shortlist["hints"]
        if entry["shortlist_id"] == "recall-need.memory-readiness-boundary.primary"
    )

    assert memory_readiness["signal"] == "recall-need"
    assert memory_readiness["owner_repo"] == "aoa-memo"
    assert memory_readiness["object_kind"] == "memo"
    assert memory_readiness["target_surface"] == "aoa-memo.memo_registry.min"
    assert memory_readiness["inspect_surface"] == "aoa-memo.memo_registry.min"
    assert "docs/MEMORY_READINESS_BOUNDARY.md" in memory_readiness["hint_reason"]
    assert "not proof" in memory_readiness["hint_reason"]
    assert "KAG policy" in memory_readiness["hint_reason"]
    assert "routing authority" in memory_readiness["hint_reason"]


def test_build_task_to_tier_hints_reads_agents_registry_artifacts(tmp_path: Path) -> None:
    agents_root = tmp_path / "aoa-agents"
    shutil.copytree(FIXTURES_ROOT / "aoa-agents", agents_root)
    registry_path = agents_root / "generated" / "model_tier_registry.json"
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    payload["model_tiers"][0]["artifact_requirement"] = "triage_packet"
    write_json(registry_path, payload)

    outputs = build_fixture_outputs(agents_root=agents_root)

    assert outputs["task_to_tier_hints.json"]["hints"][0]["output_artifact"] == "triage_packet"
