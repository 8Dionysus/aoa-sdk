# Workspace MCP Server

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
- a surface crosswalk for AGENTS, skills, subagents, project-level MCP, and
  repo-local MCP, with primary and secondary surfaces named explicitly
- compact skill index and agent profile previews

## Install

The MCP package extra in `pyproject.toml` owns installation dependencies.
Exact operator and regression routes live in this part's `VALIDATION.md`.

## Run

The part-local server script is the executable entrypoint; its checked route is
owned by this part's `VALIDATION.md`.

For the `/srv/AbyssOS` federation workspace, the project-level Codex config should wire
the server from [`/srv/AbyssOS/.codex/config.toml`](/srv/AbyssOS/.codex/config.toml) with:

```toml
[mcp_servers.aoa_workspace]
command = "python3"
args = ["mechanics/codex-projection/parts/workspace-mcp-server/scripts/aoa_workspace_mcp_server.py"]
cwd = "../aoa-sdk"
```

## Boundaries

- `aoa-sdk` stays the control plane
- `aoa_workspace` orients; it does not claim semantic ownership
- repo-local MCP servers such as `aoa_stats` and `dionysus` remain separate layers
- `abyss-stack` path resolution must respect preferred source checkouts over runtime mirrors
