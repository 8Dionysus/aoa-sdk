from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from .models import CodexLocalAgentTarget


ROLE_DEFAULTS = {
    "architect": {
        "sandbox_mode": "read-only",
        "mcp_servers": ["aoa_workspace", "aoa_stats"],
        "nickname_candidates": ["Atlas", "Lattice", "Spine"],
    },
    "coder": {
        "sandbox_mode": "workspace-write",
        "mcp_servers": ["aoa_workspace"],
        "nickname_candidates": ["Forge", "Rivet", "Patch"],
    },
    "reviewer": {
        "sandbox_mode": "read-only",
        "mcp_servers": ["aoa_workspace", "aoa_stats"],
        "nickname_candidates": ["Sentinel", "Lens", "Check"],
    },
    "evaluator": {
        "sandbox_mode": "read-only",
        "mcp_servers": ["aoa_workspace", "aoa_stats"],
        "nickname_candidates": ["Gauge", "Prism", "Delta"],
    },
    "memory-keeper": {
        "sandbox_mode": "read-only",
        "mcp_servers": ["aoa_workspace", "aoa_stats", "dionysus"],
        "nickname_candidates": ["Archive", "Ledger", "Mneme"],
    },
}


def build_codex_local_target(
    role: str,
    *,
    workspace_root: str = "/srv",
    agent_id: str | None = None,
    projection_entry: Mapping[str, Any] | None = None,
) -> CodexLocalAgentTarget:
    defaults = _resolve_role_defaults(role, projection_entry=projection_entry)
    project_codex_root = f"{workspace_root}/.codex"
    return CodexLocalAgentTarget(
        agent_id=agent_id or role,
        role=role,
        workspace_root=workspace_root,
        workspace_marker=f"{workspace_root}/AOA_WORKSPACE_ROOT",
        project_codex_root=project_codex_root,
        config_path=str((Path(project_codex_root) / defaults["config_path"]).resolve(strict=False)),
        install_surface=f"{project_codex_root}/agents",
        sandbox_mode=defaults["sandbox_mode"],
        mcp_servers=list(defaults["mcp_servers"]),
        nickname_candidates=list(defaults["nickname_candidates"]),
        projection_chain=[
            f"aoa-agents/profiles/{role}.profile.json",
            "aoa-agents/config/codex_subagent_wiring.v2.json",
            "aoa-agents/generated/codex_agents/projection_manifest.json",
            f"aoa-agents/generated/codex_agents/agents/{role}.toml",
            f"8Dionysus/.codex/agents/{role}.toml",
        ],
    )


def _resolve_role_defaults(
    role: str,
    *,
    projection_entry: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    defaults = dict(
        ROLE_DEFAULTS.get(
            role,
            {
                "sandbox_mode": "read-only",
                "mcp_servers": ["aoa_workspace"],
                "nickname_candidates": [role.title()],
            },
        )
    )
    defaults["config_path"] = f"agents/{role}.toml"
    if projection_entry is None:
        return defaults

    sandbox_mode = projection_entry.get("sandbox_mode")
    if isinstance(sandbox_mode, str) and sandbox_mode:
        defaults["sandbox_mode"] = sandbox_mode

    mcp_affinity = projection_entry.get("mcp_affinity")
    if isinstance(mcp_affinity, list) and mcp_affinity:
        defaults["mcp_servers"] = [str(item) for item in mcp_affinity]

    nickname_candidates = projection_entry.get("nickname_candidates")
    if isinstance(nickname_candidates, list) and nickname_candidates:
        defaults["nickname_candidates"] = [str(item) for item in nickname_candidates]

    config_path = projection_entry.get("config_path")
    if isinstance(config_path, str) and config_path:
        defaults["config_path"] = config_path

    return defaults
