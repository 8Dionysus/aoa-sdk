from __future__ import annotations

import json
from pathlib import Path

from aoa_sdk.codex.workspace_mcp import AoAWorkspaceMCPState


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
                'args = ["scripts/aoa_workspace_mcp_server.py"]',
                'cwd = "../aoa-sdk"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (codex_dir / "hooks.json").write_text('{"hooks":{}}' + "\n", encoding="utf-8")

    (workspace_root / "Agents-of-Abyss").mkdir(parents=True, exist_ok=True)
    (workspace_root / "Agents-of-Abyss" / "ECOSYSTEM_MAP.md").write_text(
        "# Ecosystem map\n",
        encoding="utf-8",
    )

    (workspace_root / "aoa-skills").mkdir(parents=True, exist_ok=True)
    (workspace_root / "aoa-skills" / "SKILL_INDEX.md").write_text(
        "# Skill index\n- aoa-change-protocol\n",
        encoding="utf-8",
    )
    (workspace_root / "aoa-skills" / "generated").mkdir(parents=True, exist_ok=True)
    (workspace_root / "aoa-skills" / "generated" / "runtime_discovery_index.min.json").write_text(
        "{}\n",
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

    (workspace_root / "Dionysus" / "generated").mkdir(parents=True, exist_ok=True)
    (workspace_root / "Dionysus" / "generated" / "seed_route_map.min.json").write_text(
        "{}\n",
        encoding="utf-8",
    )

    (workspace_root / "aoa-sdk" / "generated").mkdir(parents=True, exist_ok=True)
    (workspace_root / "aoa-sdk" / "generated" / "workspace_control_plane.min.json").write_text(
        "{}\n",
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
    assert health["control_plane_surface"]["exists"] is True


def test_workspace_repo_map_lists_curated_entrypoints(workspace_root: Path) -> None:
    _seed_codex_workspace(workspace_root)

    state = AoAWorkspaceMCPState.discover(workspace_root / "aoa-sdk")
    payload = state.build_repo_map()
    rows = {row["repo"]: row for row in payload["repos"]}

    assert rows["Agents-of-Abyss"]["role"] == "federation-center"
    assert rows["Agents-of-Abyss"]["preferred_entrypoints"][0]["path"] == "ECOSYSTEM_MAP.md"
    assert rows["aoa-skills"]["preferred_entrypoints"][0]["path"] == "SKILL_INDEX.md"


def test_workspace_runtime_entrypoints_report_curated_surfaces(workspace_root: Path) -> None:
    _seed_codex_workspace(workspace_root)

    state = AoAWorkspaceMCPState.discover(workspace_root / "aoa-sdk")
    payload = state.build_runtime_entrypoints()
    names = {entry["name"]: entry["exists"] for entry in payload["entrypoints"]}

    assert names["workspace_marker"] is True
    assert names["project_codex_config"] is True
    assert names["workspace_control_plane"] is True
    assert names["skill_index"] is True
    assert names["seed_route_map"] is True
    assert names["abyss_stack_diagnostic_catalog"] is True


def test_load_agent_profiles_and_skill_index_preview(workspace_root: Path) -> None:
    _seed_codex_workspace(workspace_root)

    state = AoAWorkspaceMCPState.discover(workspace_root / "aoa-sdk")

    profiles = state.load_agent_profiles()
    assert profiles["profile_count"] == 1
    assert profiles["profiles"][0]["name"] == "architect"

    skill_index = state.load_skill_index()
    assert skill_index["exists"] is True
    assert "Skill index" in skill_index["content"]
