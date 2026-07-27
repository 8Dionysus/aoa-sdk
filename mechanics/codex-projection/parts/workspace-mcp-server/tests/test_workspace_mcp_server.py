from __future__ import annotations

import asyncio
import json
from pathlib import Path

from aoa_sdk.codex.workspace_mcp import AoAWorkspaceMCPState, build_server


def _seed_codex_workspace(workspace_root: Path) -> None:
    (workspace_root / "AOA_WORKSPACE_ROOT").write_text("", encoding="utf-8")

    codex_dir = workspace_root / ".codex"
    codex_dir.mkdir(parents=True, exist_ok=True)
    (codex_dir / "config.toml").write_text(
        "\n".join(
            [
                'project_root_markers = ["AOA_WORKSPACE_ROOT", ".git"]',
                "",
                "[features]",
                "codex_hooks = true",
                "",
                "[mcp_servers.aoa_workspace]",
                'command = "python3"',
                'args = ["mechanics/codex-projection/parts/workspace-mcp-server/scripts/aoa_workspace_mcp_server.py"]',
                'cwd = "../aoa-sdk"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (codex_dir / "hooks.json").write_text('{"hooks":{}}' + "\n", encoding="utf-8")
    (
        workspace_root
        / "aoa-sdk"
        / "mechanics"
        / "codex-projection"
        / "parts"
        / "workspace-mcp-server"
        / "scripts"
    ).mkdir(parents=True, exist_ok=True)
    (
        workspace_root
        / "aoa-sdk"
        / "mechanics"
        / "codex-projection"
        / "parts"
        / "workspace-mcp-server"
        / "scripts"
        / "aoa_workspace_mcp_server.py"
    ).write_text("# server\n", encoding="utf-8")

    (workspace_root / "Agents-of-Abyss").mkdir(parents=True, exist_ok=True)
    (workspace_root / "Agents-of-Abyss" / "ECOSYSTEM_MAP.md").write_text(
        "# Ecosystem map\n",
        encoding="utf-8",
    )

    (workspace_root / "aoa-skills").mkdir(parents=True, exist_ok=True)
    (workspace_root / "aoa-skills" / "README.md").write_text(
        "# aoa-skills\n",
        encoding="utf-8",
    )
    (workspace_root / "aoa-skills" / "generated").mkdir(parents=True, exist_ok=True)
    (
        workspace_root
        / "aoa-skills"
        / "generated"
        / "agent_skill_catalog.min.json"
    ).write_text(
        json.dumps(
            {
                "catalog_version": 2,
                "profile": "codex-facing-v2",
                "skills": [{"name": "aoa-decision", "candidate_only": False}],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    profiles_dir = workspace_root / "aoa-agents" / "profiles"
    profiles_dir.mkdir(parents=True, exist_ok=True)
    (profiles_dir / "architect.profile.json").write_text(
        json.dumps(
            {
                "name": "architect",
                "description": "System architect",
                "model": "gpt-5.4",
                "role": "architect",
            }
        ),
        encoding="utf-8",
    )

    (workspace_root / "Dionysus" / "interviews").mkdir(parents=True, exist_ok=True)
    (workspace_root / "Dionysus" / "README.md").write_text(
        "# Dionysus\n",
        encoding="utf-8",
    )
    (workspace_root / "Dionysus" / "interviews" / "catalog.toml").write_text(
        'schema_version = "dionysus_interview_catalog_v1"\n',
        encoding="utf-8",
    )

    (workspace_root / "aoa-sdk" / "generated").mkdir(parents=True, exist_ok=True)
    (workspace_root / "aoa-sdk" / "generated" / "workspace_control_plane.min.json").write_text(
        "{}\n",
        encoding="utf-8",
    )

    (workspace_root / "aoa-stats" / "generated").mkdir(parents=True, exist_ok=True)
    (workspace_root / "aoa-stats" / "generated" / "summary_surface_catalog.min.json").write_text(
        "{}\n",
        encoding="utf-8",
    )
    (workspace_root / "aoa-stats" / "README.md").write_text(
        "# aoa-stats\n",
        encoding="utf-8",
    )
    (workspace_root / "aoa-stats" / "scripts").mkdir(parents=True, exist_ok=True)
    (workspace_root / "aoa-stats" / "scripts" / "aoa_stats_mcp_server.py").write_text(
        "# retired repo-local launcher\n",
        encoding="utf-8",
    )


def test_workspace_resolution_prefers_manifest_abyss_stack_source_checkout(workspace_root: Path) -> None:
    state = AoAWorkspaceMCPState.discover(workspace_root / "aoa-sdk")
    payload = state.build_workspace_resolution()

    assert payload["federation_root"] == str(workspace_root.resolve())
    assert payload["repos"]["abyss-stack"]["path"] == str((workspace_root / "src" / "abyss-stack").resolve())
    assert payload["repos"]["abyss-stack"]["origin"] == "manifest:repos.abyss-stack.preferred"


def test_workspace_health_reports_project_layer_and_control_plane_surface(workspace_root: Path) -> None:
    _seed_codex_workspace(workspace_root)

    state = AoAWorkspaceMCPState.discover(workspace_root / "aoa-sdk")
    health = state.build_health()

    assert health["workspace_marker"]["present"] is True
    assert health["project_codex"]["config_exists"] is True
    assert health["project_codex"]["hooks_exists"] is True
    assert health["project_codex"]["aoa_workspace_server"]["configured"] is True
    assert health["project_codex"]["aoa_workspace_server"]["uses_part_local_script"] is True
    assert health["project_codex"]["aoa_workspace_server"]["script_exists"] is True
    assert health["control_plane_surface"]["exists"] is True


def test_workspace_repo_map_lists_curated_entrypoints(workspace_root: Path) -> None:
    _seed_codex_workspace(workspace_root)

    state = AoAWorkspaceMCPState.discover(workspace_root / "aoa-sdk")
    payload = state.build_repo_map()
    rows = {row["repo"]: row for row in payload["repos"]}

    assert rows["Agents-of-Abyss"]["role"] == "federation-center"
    assert rows["Agents-of-Abyss"]["preferred_entrypoints"][0]["path"] == "ECOSYSTEM_MAP.md"
    assert rows["aoa-skills"]["preferred_entrypoints"][0]["path"] == (
        "generated/agent_skill_catalog.min.json"
    )
    assert rows["Dionysus"]["role"] == "portrait-protocol-owner"
    assert "scripts/dionysus_mcp_server.py" not in {
        entry["path"] for entry in rows["Dionysus"]["preferred_entrypoints"]
    }


def test_workspace_repo_map_keeps_aoa_stats_entrypoints_transport_neutral(workspace_root: Path) -> None:
    _seed_codex_workspace(workspace_root)

    state = AoAWorkspaceMCPState.discover(workspace_root / "aoa-sdk")
    rows = {row["repo"]: row for row in state.build_repo_map()["repos"]}

    assert [entry["path"] for entry in rows["aoa-stats"]["preferred_entrypoints"]] == [
        "generated/summary_surface_catalog.min.json",
        "README.md",
    ]


def test_surface_crosswalk_uses_secondary_surface_not_fallback_route(workspace_root: Path) -> None:
    _seed_codex_workspace(workspace_root)

    state = AoAWorkspaceMCPState.discover(workspace_root / "aoa-sdk")
    payload = state.build_surface_crosswalk()

    assert payload["crosswalk"]
    assert all("primary_surface" in row for row in payload["crosswalk"])
    assert all("secondary_surface" in row for row in payload["crosswalk"])
    assert all("fallback" not in row for row in payload["crosswalk"])
    stats_row = next(row for row in payload["crosswalk"] if row["need"].startswith("derived metrics"))
    assert stats_row["primary_surface"] == "project-level MCP: aoa_stats"


def test_workspace_runtime_entrypoints_report_curated_surfaces(workspace_root: Path) -> None:
    _seed_codex_workspace(workspace_root)

    state = AoAWorkspaceMCPState.discover(workspace_root / "aoa-sdk")
    payload = state.build_runtime_entrypoints()
    entries = {entry["name"]: entry for entry in payload["entrypoints"]}

    assert entries["workspace_marker"]["exists"] is True
    assert entries["project_codex_config"]["exists"] is True
    assert entries["workspace_control_plane"]["exists"] is True
    assert entries["agent_skill_catalog"]["exists"] is True
    assert entries["capability_graph"]["exists"] is True
    assert entries["dionysus_interview_catalog"]["exists"] is True
    assert entries["abyss_stack_diagnostic_catalog"]["exists"] is True
    assert entries["abyss_stack_diagnostic_catalog"]["path"] == (
        "mechanics/diagnostic-spine/parts/diagnostic-surfaces/generated/"
        "diagnostic_surface_catalog.min.json"
    )


def test_load_agent_profiles_and_passive_skill_catalog(workspace_root: Path) -> None:
    _seed_codex_workspace(workspace_root)

    state = AoAWorkspaceMCPState.discover(workspace_root / "aoa-sdk")

    profiles = state.load_agent_profiles()
    assert profiles["profile_count"] == 1
    assert profiles["profiles"][0]["name"] == "architect"

    skill_catalog = state.load_agent_skill_catalog()
    assert skill_catalog["exists"] is True
    assert skill_catalog["parse_error"] is None
    assert skill_catalog["payload"]["catalog_version"] == 2
    assert skill_catalog["payload"]["skills"] == [
        {"name": "aoa-decision", "candidate_only": False}
    ]


def test_organ_discovery_is_explicit_bounded_and_non_executing(
    workspace_root: Path,
    monkeypatch,
) -> None:
    _seed_codex_workspace(workspace_root)
    registry = (
        Path(__file__).resolve().parents[4]
        / "boundary-bridge"
        / "parts"
        / "organ-access-control-plane"
        / "examples"
        / "organ_registry.wave1-shadow.example.json"
    )
    monkeypatch.setenv("AOA_SDK_ORGAN_REGISTRY", str(registry))

    state = AoAWorkspaceMCPState.discover(workspace_root / "aoa-sdk")
    status = state.build_organ_registry_status()
    assert status["configured"] is True
    assert status["valid"] is True
    assert status["record_count"] == 3
    assert status["execution_authorized"] is False

    catalog = state.build_organ_catalog(
        query="knowledge",
        allow_organs=["aoa-kag"],
        byte_budget=8_192,
    )
    assert [entry["organ_id"] for entry in catalog["entries"]] == ["aoa-kag"]
    assert catalog["schema_bytes_loaded"] == 0

    organ = state.build_organ_inspection("aoa-kag")
    capability = state.build_organ_capability(
        "aoa-kag",
        "knowledge-retrieval",
    )
    assert organ["registry_state"] == "shadow"
    assert organ["endpoint"] is None
    assert capability["policy_family"] == "read"


def test_workspace_mcp_catalog_is_read_only_and_has_no_activation_tool(
    workspace_root: Path,
) -> None:
    _seed_codex_workspace(workspace_root)
    server = build_server(workspace_root / "aoa-sdk")
    tools = asyncio.run(server.list_tools())
    names = {tool.name for tool in tools}

    assert names == {
        "workspace_resolution",
        "workspace_health",
        "workspace_repo_map",
        "workspace_surface_crosswalk",
        "workspace_runtime_entrypoints",
        "workspace_agent_skill_catalog",
        "workspace_agent_profiles",
        "organ_registry_status",
        "organ_catalog",
        "organ_inspect",
        "organ_capability",
    }
    assert "organ_activation" not in names
    for tool in tools:
        assert tool.annotations is not None
        assert tool.annotations.readOnlyHint is True
        assert tool.annotations.destructiveHint is False
        assert tool.annotations.idempotentHint is True
        assert tool.annotations.openWorldHint is False

    resources = asyncio.run(server.list_resources())
    assert {
        str(resource.uri)
        for resource in resources
        if str(resource.uri).startswith("aoa-workspace://organs/")
    } == {
        "aoa-workspace://organs/catalog",
        "aoa-workspace://organs/status",
    }
    templates = asyncio.run(server.list_resource_templates())
    assert {template.uriTemplate for template in templates} == {
        "aoa-workspace://organs/{organ_id}",
        "aoa-workspace://organs/{organ_id}/capabilities/{capability_id}",
    }
