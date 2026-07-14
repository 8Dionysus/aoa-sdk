# Workspace MCP Server

## Role

`workspace-mcp-server` is the Codex Projection part that runs the
workspace-level `aoa_workspace` MCP server from the SDK checkout.

## Input

- `Workspace.discover()` and `.aoa/workspace.toml`
- project-level Codex MCP wiring from the sibling workspace root
- sibling repo paths, origins, and curated entrypoints
- part-local `abyss-stack` diagnostic-spine catalog entrypoint

## Output

- MCP tools for workspace resolution, health, repo map, surface crosswalk,
  runtime entrypoints, skill index, and agent profile previews; the surface
  crosswalk names `primary_surface` and `secondary_surface` rather than a
  substitute route
- a transport-neutral `aoa-stats` repo map: owner catalogs remain direct
  entrypoints, while statistical MCP access routes through the project-level
  `aoa_stats` service
- MCP resources over the same readouts
- MCP prompts that route Codex toward the next owner surface

## Owner

`aoa-sdk` owns the server wrapper, typed workspace readout code under
`src/aoa_sdk/codex/workspace_mcp.py`, route documentation, and tests.
Sibling repos keep semantic truth; host/Codex layers keep runtime and deploy
authority.

## Next Route

If the server reports missing or stale project wiring, update the workspace
Codex projection owner or route semantic questions to the owning sibling repo.
Do not use this part to claim runtime authority or replace owner-local truth.

## Validation

Use `VALIDATION.md`.
