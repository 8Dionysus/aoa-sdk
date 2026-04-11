# Codex Workspace MCP

`aoa-sdk` can host the workspace-level `aoa_workspace` MCP server for the AoA
federation.

This surface stays on the control plane:

- it reuses `Workspace.discover()` and `.aoa/workspace.toml`
- it reports repo paths and origins without inventing a second topology model
- it orients Codex toward the right repo or surface
- it does not replace owner-layer truth in sibling repositories

## What it exposes

- resolved workspace paths and repo origins
- project-level Codex wiring health at the sibling workspace root
- advisory repo-role map and curated entrypoints
- a surface crosswalk for AGENTS, skills, subagents, project-level MCP, and repo-local MCP
- compact skill index and agent profile previews

## Install

From the `aoa-sdk` checkout:

```bash
python -m pip install -e '.[mcp]'
```

## Run

```bash
python scripts/aoa_workspace_mcp_server.py
```

For the `/srv` federation workspace, the project-level Codex config should wire
the server from [`/srv/.codex/config.toml`](/srv/.codex/config.toml) with:

```toml
[mcp_servers.aoa_workspace]
command = "python3"
args = ["scripts/aoa_workspace_mcp_server.py"]
cwd = "../aoa-sdk"
```

## Boundaries

- `aoa-sdk` stays the control plane
- `aoa_workspace` orients; it does not claim semantic ownership
- repo-local MCP servers such as `aoa_stats` and `dionysus` remain separate layers
- `abyss-stack` path resolution must respect preferred source checkouts over runtime mirrors
