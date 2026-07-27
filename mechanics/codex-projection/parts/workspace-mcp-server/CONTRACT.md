# Workspace MCP Server Contract

## Contract

The part exposes a local MCP server for Codex workspace orientation. It reads
workspace configuration and repo-local entrypoints, then returns bounded
control-plane readouts. When an explicit organ registry is configured, it also
projects the SDK-owned progressive-discovery API through four read-only MCP
tools and four resources. It does not compile activation plans, execute sibling
workflows, deploy runtime state, or mint owner-layer truth.

## SDK-Owned Active Names

- part route: `codex-projection/workspace-mcp-server`
- runnable script: `scripts/aoa_workspace_mcp_server.py` inside this part
- source module: `src/aoa_sdk/codex/workspace_mcp.py`
- test route: `tests/test_workspace_mcp_server.py` inside this part

## MCP Surface Roles

- tools answer current workspace questions
- resources expose reusable readout payloads
- prompts provide explicit next-route recipes
- `organ_registry_status` reports configuration and validation posture;
  `organ_catalog`, `organ_inspect`, and `organ_capability` expose bounded
  progressive discovery without schema preloading or execution
- `aoa-workspace://organs/status` and
  `aoa-workspace://organs/catalog` are static resources; organ and capability
  details use URI templates
- every tool carries read-only, non-destructive, idempotent, closed-world
  annotation hints; the hints are descriptive and never authorize access
- the surface crosswalk names `primary_surface` and `secondary_surface`;
  secondary means next inspectable route, not substitute compatibility behavior

## External Compatibility Inputs

- project-level Codex config at `.codex/config.toml`
- sibling workspace marker `AOA_WORKSPACE_ROOT`
- exactly one explicit private organ-registry path from
  `.aoa/workspace.toml` or `AOA_SDK_ORGAN_REGISTRY`
- repo-local AGENTS, owner skill catalog, capability graph, profile, generated,
  and runtime entrypoint files
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
- Do not expose activation-plan compilation, registry mutation, connection,
  lifecycle, owner-tool proxying, or hidden server chaining through this MCP.
- Do not treat MCP annotations, resource visibility, endpoint presence, or a
  successful read as authorization, admission, maturity, or owner acceptance.
- Do not replace sibling repo route cards or semantic owner docs with MCP
  readouts.
- Do not expose the retired `SKILL_INDEX.md` or runtime discovery surface as a
  current skill route.
- Do not select, rank, or execute a skill through the workspace MCP server.
- Do not advertise the retired repo-local Dionysus MCP route; the current
  owner surface is its privacy-bounded interview and portrait protocol.
