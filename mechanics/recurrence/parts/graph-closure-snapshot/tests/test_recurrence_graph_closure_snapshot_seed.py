from __future__ import annotations

import json
from pathlib import Path

from aoa_sdk.recurrence.api import RecurrenceAPI
from aoa_sdk.recurrence.detector import detect_change_signal
from aoa_sdk.recurrence.graph import (
    build_graph_closure_report,
    build_graph_snapshot,
    diff_graph_snapshots,
    expand_component_graph,
)
from aoa_sdk.recurrence.planner import build_propagation_plan
from aoa_sdk.recurrence.registry import load_registry
from aoa_sdk.workspace.discovery import Workspace


def _write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )


def _component(
    ref: str,
    owner: str,
    *,
    source: str,
    edges: list[dict] | None = None,
    action: str = "revalidate",
) -> dict:
    return {
        "manifest_kind": "recurrence_component",
        "schema_version": "aoa_recurrence_component_v2",
        "component_ref": ref,
        "owner_repo": owner,
        "source_inputs": [source],
        "proof_surfaces": [f"python scripts/validate_{owner}.py"],
        "refresh_routes": [
            {"action": action, "commands": [f"python scripts/{ref.split(':')[-1]}.py"]}
        ],
        "consumer_edges": edges or [],
    }


def _workspace(tmp_path: Path) -> Workspace:
    root = tmp_path / "federation"
    sdk = root / "aoa-sdk"
    skills = root / "aoa-skills"
    evals = root / "aoa-evals"
    routing = root / "aoa-routing"
    for repo in (sdk, skills, evals, routing):
        repo.mkdir(parents=True, exist_ok=True)
    _write_json(
        skills / "manifests/recurrence/component.skills.activation.json",
        _component(
            "component:skills:activation-boundary",
            "aoa-skills",
            source="docs/TRIGGER_EVALS.md",
            edges=[
                {
                    "kind": "evaluated_by",
                    "target": "component:evals:trigger-evals",
                    "target_repo": "aoa-evals",
                    "required": True,
                    "suggested_action": "revalidate",
                },
                {
                    "kind": "routes_via",
                    "target": "generated/owner_layer_shortlist.min.json",
                    "target_repo": "aoa-routing",
                    "required": False,
                    "suggested_action": "reroute",
                },
            ],
        ),
    )
    _write_json(
        evals / "manifests/recurrence/component.evals.trigger.json",
        _component(
            "component:evals:trigger-evals",
            "aoa-evals",
            source="docs/TRIGGER_EVALS.md",
            edges=[
                {
                    "kind": "documents",
                    "target": "component:skills:activation-boundary",
                    "target_repo": "aoa-skills",
                    "required": False,
                    "suggested_action": "repair",
                },
                {
                    "kind": "requires_regrounding",
                    "target": "return_regrounding_pack",
                    "target_repo": "aoa-kag",
                    "required": True,
                    "suggested_action": "reground",
                },
            ],
        ),
    )
    (skills / "docs").mkdir(parents=True, exist_ok=True)
    (skills / "docs/TRIGGER_EVALS.md").write_text(
        "trigger boundary changed\n", encoding="utf-8"
    )
    return Workspace(
        root=root,
        federation_root=root,
        federation_root_source="test",
        manifest_path=None,
        repo_roots={
            "aoa-sdk": sdk,
            "aoa-skills": skills,
            "aoa-evals": evals,
            "aoa-routing": routing,
        },
        repo_origins={
            "aoa-sdk": "test",
            "aoa-skills": "test",
            "aoa-evals": "test",
            "aoa-routing": "test",
        },
    )


def test_graph_closure_detects_transitive_edges_cycles_and_external_impacts(
    tmp_path: Path,
) -> None:
    workspace = _workspace(tmp_path)
    registry = load_registry(workspace)
    expansion = expand_component_graph(
        direct_component_refs=["component:skills:activation-boundary"],
        registry=registry,
        depth_limit=6,
    )
    assert [node.component_ref for node in expansion.component_nodes] == [
        "component:skills:activation-boundary",
        "component:evals:trigger-evals",
    ]
    assert expansion.component_nodes[1].depth == 1
    assert expansion.cycles, (
        "the optional documents edge should be recorded as a cycle, not traversed forever"
    )
    assert {impact.edge.target_repo for impact in expansion.external_impacts} == {
        "aoa-routing",
        "aoa-kag",
    }
    required_only = expand_component_graph(
        direct_component_refs=["component:skills:activation-boundary"],
        registry=registry,
        depth_limit=6,
        include_optional=False,
    )
    assert not required_only.cycles
    assert {impact.edge.target_repo for impact in required_only.external_impacts} == {
        "aoa-kag"
    }

    report = build_graph_closure_report(
        workspace,
        direct_component_refs=["component:skills:activation-boundary"],
        registry=registry,
    )
    assert report.propagation_batches[0].component_refs == [
        "component:skills:activation-boundary"
    ]
    assert any(item.target_repo == "aoa-kag" for item in report.external_impacts)


def test_snapshot_and_delta_report_edge_changes(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    registry = load_registry(workspace)
    before = build_graph_snapshot(workspace, registry=registry)
    assert before.node_count == 2
    assert before.edge_count == 4

    # Add a new external edge and compare snapshots.
    skills_manifest = (
        workspace.repo_roots["aoa-skills"]
        / "manifests/recurrence/component.skills.activation.json"
    )
    payload = json.loads(skills_manifest.read_text(encoding="utf-8"))
    payload["consumer_edges"].append(
        {
            "kind": "summarized_by",
            "target": "generated/recurrence_summary.min.json",
            "target_repo": "aoa-stats",
            "required": False,
            "suggested_action": "restat",
        }
    )
    _write_json(skills_manifest, payload)

    after = build_graph_snapshot(workspace, registry=load_registry(workspace))
    delta = diff_graph_snapshots(before, after)
    assert len(delta.added_edges) == 1
    assert "aoa-stats" in delta.added_edges[0].key
    assert "+1 edge" in delta.summary


def test_planner_gets_batches_depths_and_edge_strengths(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    registry = load_registry(workspace)
    signal = detect_change_signal(
        workspace,
        repo_root=str(workspace.repo_roots["aoa-skills"]),
        paths=["docs/TRIGGER_EVALS.md"],
        registry=registry,
    )
    plan = build_propagation_plan(workspace, signal=signal, registry=registry)
    assert plan.propagation_batches
    assert plan.ordered_steps[0].batch_order == 0
    assert any(step.graph_depth == 1 for step in plan.ordered_steps)
    assert any(step.edge_strength == "recommended" for step in plan.ordered_steps)
    assert any("cycle detected" in question for question in plan.open_questions)

    api_snapshot = RecurrenceAPI(workspace).graph_snapshot()
    assert api_snapshot.node_count == 2
