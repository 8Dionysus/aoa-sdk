# Workspace MCP Server

## Role

`workspace-mcp-server` is the Codex Projection part that runs the
workspace-level `aoa_workspace` MCP server from the SDK checkout.

## Input

- `Workspace.discover()` and `.aoa/workspace.toml`
- an optional, explicit OS-private organ registry selected by workspace config
  or `AOA_SDK_ORGAN_REGISTRY`
- project-level Codex MCP wiring from the sibling workspace root
- sibling repo paths, origins, and curated entrypoints
- part-local `abyss-stack` diagnostic-spine catalog entrypoint

## Output

- seven MCP tools for workspace resolution, health, repo map, surface
  crosswalk, runtime entrypoints, compact owner skill catalog, and agent
  profile previews; the surface crosswalk names `primary_surface` and
  `secondary_surface` rather than a substitute route
- four read-only organ tools:
  `organ_registry_status -> organ_catalog -> organ_inspect -> organ_capability`
- static status/catalog resources and URI templates for one organ or
  capability
- a transport-neutral `aoa-stats` repo map: owner catalogs remain direct
  entrypoints, while statistical MCP access routes through the project-level
  `aoa_stats` service
- MCP resources over the same readouts
- MCP prompts that route Codex toward the next owner surface
- exact skill catalog reads remain passive; semantic retrieval stays with KAG
  and runtime selection stays with the host
- all eleven tools carry read-only annotation hints, but policy and
  authorization still come from the typed registry and stronger owners

## Owner

`aoa-sdk` owns the server wrapper, typed workspace readout code under
`src/aoa_sdk/codex/workspace_mcp.py`, route documentation, and tests.
Sibling repos keep semantic truth; host/Codex layers keep runtime and deploy
authority.

## Next Route

If the server reports missing or stale project wiring, update the workspace
Codex projection owner or route semantic questions to the owning sibling repo.
If organ discovery is needed, configure one exact registry and inspect only the
selected capability. Activation-plan compilation remains in the SDK/CLI
control plane, while connection and execution remain host/runtime operations.
Do not use this part to claim runtime authority or replace owner-local truth.

## Validation

Use `VALIDATION.md`.
