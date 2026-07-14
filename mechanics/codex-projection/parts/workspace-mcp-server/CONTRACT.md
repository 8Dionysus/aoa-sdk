# Workspace MCP Server Contract

## Contract

The part exposes a local MCP server for Codex workspace orientation. It reads
workspace configuration and repo-local entrypoints, then returns bounded
control-plane readouts. It does not execute sibling workflows, deploy runtime
state, or mint owner-layer truth.

## SDK-Owned Active Names

- part route: `codex-projection/workspace-mcp-server`
- runnable script: `scripts/aoa_workspace_mcp_server.py` inside this part
- source module: `src/aoa_sdk/codex/workspace_mcp.py`
- test route: `tests/test_workspace_mcp_server.py` inside this part

## MCP Surface Roles

- tools answer current workspace questions
- resources expose reusable readout payloads
- prompts provide explicit next-route recipes
- the surface crosswalk names `primary_surface` and `secondary_surface`;
  secondary means next inspectable route, not substitute compatibility behavior

## External Compatibility Inputs

- project-level Codex config at `.codex/config.toml`
- sibling workspace marker `AOA_WORKSPACE_ROOT`
- repo-local AGENTS, skill, profile, generated, and runtime entrypoint files
- project-level `aoa_stats` as the statistical read transport; its runtime
  implementation and registration remain outside SDK ownership
- `abyss-stack` diagnostic catalog at
  `mechanics/diagnostic-spine/parts/diagnostic-surfaces/generated/diagnostic_surface_catalog.min.json`
  rather than the old root generated path

## Stop-Lines

- Do not keep the runnable MCP server script in the root `scripts/` district.
- Do not surface old root diagnostic catalog paths as current runtime
  entrypoints.
- Expose `secondary_surface` for the next inspectable route.
- Do not advertise a launcher inside `aoa-stats`; the repo map exposes its
  owner surfaces and the crosswalk routes transport through `aoa_stats`.
- Do not make the server a deployment authority or Codex runtime owner.
- Do not replace sibling repo route cards or semantic owner docs with MCP
  readouts.
