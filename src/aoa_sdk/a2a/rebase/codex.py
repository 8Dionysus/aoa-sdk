from __future__ import annotations

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
) -> CodexLocalAgentTarget:
    defaults = ROLE_DEFAULTS.get(
        role,
        {
            "sandbox_mode": "read-only",
            "mcp_servers": ["aoa_workspace"],
            "nickname_candidates": [role.title()],
        },
    )
    project_codex_root = f"{workspace_root}/.codex"
    return CodexLocalAgentTarget(
        agent_id=agent_id or role,
        role=role,
        workspace_root=workspace_root,
        workspace_marker=f"{workspace_root}/AOA_WORKSPACE_ROOT",
        project_codex_root=project_codex_root,
        config_path=f"{project_codex_root}/agents/{role}.toml",
        install_surface=f"{project_codex_root}/agents",
        sandbox_mode=defaults["sandbox_mode"],
        mcp_servers=list(defaults["mcp_servers"]),
        nickname_candidates=list(defaults["nickname_candidates"]),
        projection_chain=[
            f"aoa-agents/profiles/{role}.profile.json",
            "aoa-agents/config/codex_subagent_wiring.v2.json",
            f"aoa-agents/generated/codex_agents/agents/{role}.toml",
            f"8Dionysus/.codex/agents/{role}.toml",
        ],
    )
