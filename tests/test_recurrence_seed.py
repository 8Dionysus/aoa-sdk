from __future__ import annotations

import json
from pathlib import Path

from aoa_sdk.recurrence.api import RecurrenceAPI
from aoa_sdk.workspace.discovery import Workspace


CODEX_PLANE_MANIFEST = {
    "schema_version": "aoa_recurrence_component_v1",
    "component_ref": "component:codex-plane:shared-root",
    "owner_repo": "8Dionysus",
    "description": "Shared-root Codex plane render and drift carry.",
    "source_inputs": [
        "config/codex_plane/runtime_manifest.v1.json",
        "config/codex_plane/profiles/*.json"
    ],
    "generated_surfaces": [
        ".codex/config.toml",
        ".codex/hooks.json"
    ],
    "contract_surfaces": [
        "docs/CODEX_PLANE_REGENERATION.md",
        "docs/COMPONENT_REFRESH_ROUTE.md"
    ],
    "proof_surfaces": [
        "python scripts/render_codex_plane.py",
        "python scripts/validate_codex_plane.py",
        "python .codex/bin/aoa-codex-doctor"
    ],
    "refresh_routes": [
        {
            "action": "regenerate",
            "commands": [
                "python scripts/render_codex_plane.py",
                "python scripts/validate_codex_plane.py",
                "python .codex/bin/aoa-codex-doctor"
            ],
            "notes": "rerender checked-in deployment surfaces from source manifest and profiles"
        },
        {
            "action": "repair",
            "commands": [
                "python scripts/render_codex_plane.py",
                "python scripts/validate_codex_plane.py"
            ],
            "notes": "repair path-bound drift through normal rerender and validation"
        }
    ],
    "consumer_edges": [
        {
            "kind": "routes_via",
            "target": "generated/return_navigation_hints.min.json",
            "target_repo": "aoa-routing",
            "required": True,
            "suggested_action": "reroute",
            "suggested_commands": [
                "python scripts/build_router.py",
                "python scripts/validate_router.py"
            ],
            "notes": "refresh bounded return hints after shared-root Codex plane change"
        },
        {
            "kind": "summarized_by",
            "target": "generated/component_refresh_summary.min.json",
            "target_repo": "aoa-stats",
            "required": True,
            "suggested_action": "restat",
            "suggested_commands": [
                "python scripts/build_views.py",
                "python scripts/validate_repo.py"
            ],
            "notes": "publish descriptive closure after owner refresh work"
        },
        {
            "kind": "requires_regrounding",
            "target": "generated/return_regrounding_pack.min.json",
            "target_repo": "aoa-kag",
            "required": True,
            "suggested_action": "reground",
            "suggested_commands": [],
            "notes": "fill from aoa-kag owner route when the manifest lands"
        },
        {
            "kind": "handoff_home",
            "target": "AOA-P-0030",
            "target_repo": "aoa-playbooks",
            "required": True,
            "suggested_action": "handoff",
            "suggested_commands": [],
            "notes": "component refresh opener when one named component has real owner-law drift"
        }
    ],
    "drift_signals": [
        {
            "signal": "public_workspace_root_changed_without_rerender",
            "recommended_action": "regenerate",
            "severity": "high"
        }
    ],
    "freshness": {
        "stale_after_days": 7,
        "repeat_trigger_threshold": 2,
        "open_window_days": 5
    },
    "rollback_anchors": [
        "docs/CODEX_PLANE_ROLLOUT.md",
        ".codex/config.toml",
        ".codex/hooks.json"
    ],
    "tags": ["workspace", "codex", "shared-root"]
}

SUBAGENT_MANIFEST = {
    "schema_version": "aoa_recurrence_component_v1",
    "component_ref": "component:codex-subagents:projection",
    "owner_repo": "aoa-agents",
    "description": "Codex custom-agent projection from source profiles and wiring.",
    "source_inputs": [
        "profiles/*.profile.json",
        "config/codex_subagent_wiring.v2.json"
    ],
    "generated_surfaces": [
        "generated/codex_agents/agents/*.toml",
        "generated/codex_agents/config.subagents.generated.toml",
        "generated/codex_agents/projection_manifest.json"
    ],
    "projected_surfaces": [
        ".codex/agents/"
    ],
    "contract_surfaces": [
        "docs/CODEX_SUBAGENT_PROJECTION.md",
        "docs/CODEX_SUBAGENT_REFRESH_LAW.md"
    ],
    "proof_surfaces": [
        "python scripts/build_published_surfaces.py",
        "python scripts/build_codex_subagents_v2.py",
        "python scripts/validate_codex_subagents.py --profiles-root profiles --wiring config/codex_subagent_wiring.v2.json --agents-dir generated/codex_agents/agents --config-snippet generated/codex_agents/config.subagents.generated.toml --manifest generated/codex_agents/projection_manifest.json"
    ],
    "refresh_routes": [
        {
            "action": "regenerate",
            "commands": [
                "python scripts/build_published_surfaces.py",
                "python scripts/build_codex_subagents_v2.py",
                "python scripts/validate_codex_subagents.py --profiles-root profiles --wiring config/codex_subagent_wiring.v2.json --agents-dir generated/codex_agents/agents --config-snippet generated/codex_agents/config.subagents.generated.toml --manifest generated/codex_agents/projection_manifest.json"
            ],
            "notes": "regenerate repo-owned custom-agent projection surfaces"
        },
        {
            "action": "reproject",
            "commands": [
                "python scripts/build_published_surfaces.py",
                "python scripts/build_codex_subagents_v2.py",
                "python scripts/validate_codex_subagents.py --profiles-root profiles --wiring config/codex_subagent_wiring.v2.json --agents-dir generated/codex_agents/agents --config-snippet generated/codex_agents/config.subagents.generated.toml --manifest generated/codex_agents/projection_manifest.json"
            ],
            "notes": "refresh repo-owned projection and then explicitly install into workspace .codex/agents/"
        }
    ],
    "consumer_edges": [
        {
            "kind": "projects_to",
            "target": ".codex/agents/",
            "target_repo": "8Dionysus",
            "required": True,
            "suggested_action": "reproject",
            "suggested_commands": [],
            "notes": "explicit workspace install step remains outside hidden automation"
        },
        {
            "kind": "summarized_by",
            "target": "generated/component_refresh_summary.min.json",
            "target_repo": "aoa-stats",
            "required": True,
            "suggested_action": "restat",
            "suggested_commands": [
                "python scripts/build_views.py",
                "python scripts/validate_repo.py"
            ],
            "notes": "publish descriptive closure after projection refresh"
        },
        {
            "kind": "handoff_home",
            "target": "AOA-P-0030",
            "target_repo": "aoa-playbooks",
            "required": True,
            "suggested_action": "handoff",
            "suggested_commands": [],
            "notes": "component refresh opener when projection drift becomes a real owner route"
        }
    ],
    "drift_signals": [
        {
            "signal": "profile_changed_without_projection_refresh",
            "recommended_action": "regenerate",
            "severity": "medium"
        },
        {
            "signal": "workspace_install_projection_stale",
            "recommended_action": "reproject",
            "severity": "medium"
        }
    ],
    "freshness": {
        "stale_after_days": 7,
        "repeat_trigger_threshold": 2,
        "open_window_days": 5
    },
    "rollback_anchors": [
        "docs/CODEX_SUBAGENT_PROJECTION.md",
        "generated/codex_agents/projection_manifest.json",
        "generated/codex_agents/config.subagents.generated.toml"
    ],
    "tags": ["agents", "codex", "projection"]
}


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _make_workspace(tmp_path: Path) -> Workspace:
    federation_root = tmp_path / "federation"
    sdk_root = federation_root / "aoa-sdk"
    root_root = federation_root / "8Dionysus"
    agents_root = federation_root / "aoa-agents"
    for item in (sdk_root, root_root, agents_root):
        item.mkdir(parents=True, exist_ok=True)

    _write_json(root_root / "manifests/recurrence/component.codex-plane.shared-root.json", CODEX_PLANE_MANIFEST)
    _write_json(agents_root / "manifests/recurrence/component.codex-subagents.projection.json", SUBAGENT_MANIFEST)

    (root_root / "config/codex_plane/profiles").mkdir(parents=True, exist_ok=True)
    (root_root / "config/codex_plane/runtime_manifest.v1.json").write_text("{}", encoding="utf-8")
    (root_root / "docs").mkdir(parents=True, exist_ok=True)
    (root_root / "docs/CODEX_PLANE_REGENERATION.md").write_text("# regen\n", encoding="utf-8")

    (agents_root / "profiles").mkdir(parents=True, exist_ok=True)
    (agents_root / "profiles/architect.profile.json").write_text("{}", encoding="utf-8")
    (agents_root / "config").mkdir(parents=True, exist_ok=True)
    (agents_root / "config/codex_subagent_wiring.v2.json").write_text("{}", encoding="utf-8")
    (agents_root / "docs").mkdir(parents=True, exist_ok=True)
    (agents_root / "docs/CODEX_SUBAGENT_PROJECTION.md").write_text("# projection\n", encoding="utf-8")

    return Workspace(
        root=federation_root,
        federation_root=federation_root,
        federation_root_source="test",
        manifest_path=None,
        repo_roots={
            "aoa-sdk": sdk_root,
            "8Dionysus": root_root,
            "aoa-agents": agents_root,
        },
        repo_origins={
            "aoa-sdk": "test",
            "8Dionysus": "test",
            "aoa-agents": "test",
        },
    )


def test_detect_matches_codex_plane_component(tmp_path: Path) -> None:
    workspace = _make_workspace(tmp_path)
    api = RecurrenceAPI(workspace)
    signal = api.detect(
        repo_root=str(workspace.repo_roots["8Dionysus"]),
        paths=["config/codex_plane/runtime_manifest.v1.json"],
    )
    assert signal.direct_components
    assert signal.direct_components[0].component_ref == "component:codex-plane:shared-root"
    assert signal.direct_components[0].match_class == "source"


def test_plan_creates_local_and_downstream_steps(tmp_path: Path) -> None:
    workspace = _make_workspace(tmp_path)
    api = RecurrenceAPI(workspace)
    signal = api.detect(
        repo_root=str(workspace.repo_roots["8Dionysus"]),
        paths=["config/codex_plane/runtime_manifest.v1.json"],
    )
    plan = api.plan(signal)
    component_refs = [step.component_ref for step in plan.ordered_steps]
    assert "component:codex-plane:shared-root" in component_refs
    assert "aoa-routing:generated/return_navigation_hints.min.json" in component_refs
    assert "aoa-stats:generated/component_refresh_summary.min.json" in component_refs
    assert plan.unresolved_edges == []


def test_doctor_exposes_open_owner_boundaries(tmp_path: Path) -> None:
    workspace = _make_workspace(tmp_path)
    api = RecurrenceAPI(workspace)
    signal = api.detect(
        repo_root=str(workspace.repo_roots["8Dionysus"]),
        paths=["config/codex_plane/runtime_manifest.v1.json", "unknown/unmapped.file"],
    )
    report = api.doctor(signal)
    gap_kinds = {gap.gap_kind for gap in report.gaps}
    assert "weak_owner_handoff" in gap_kinds
    assert "missing_target_route" in gap_kinds
    assert "unmapped_changed_path" in gap_kinds


def test_return_handoff_preserves_owner_targets(tmp_path: Path) -> None:
    workspace = _make_workspace(tmp_path)
    api = RecurrenceAPI(workspace)
    signal = api.detect(
        repo_root=str(workspace.repo_roots["aoa-agents"]),
        paths=["profiles/architect.profile.json"],
    )
    plan = api.plan(signal)
    handoff = api.build_return_handoff(plan, reviewed=True)
    targets = {(target.owner_repo, target.target) for target in handoff.targets}
    assert ("aoa-agents", "docs/CODEX_SUBAGENT_PROJECTION.md") in targets
    assert any(target.owner_repo == "aoa-playbooks" for target in handoff.targets)
