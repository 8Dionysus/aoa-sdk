# Codex Workspace MCP Server Localization

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0019
- Original date: 2026-06-01
- Surface classes: topology, mechanics, artifact placement, validation guard
- SDK facets: mechanics topology, Codex Projection, workspace MCP server
- Mechanic parents: codex-projection
- Guard families: mechanics topology, part validation, docs routes, active naming, MCP wiring
- Posture: accepted

## Context

After the Release Support slice, Codex Projection still had one clear
single-mechanic root payload cluster:

- workspace MCP documentation under `docs/codex-workspace-mcp.md`
- runnable MCP server wrapper under `scripts/aoa_workspace_mcp_server.py`
- workspace MCP regression tests under `tests/test_codex_workspace_mcp.py`

The importable SDK source remains `src/aoa_sdk/codex/workspace_mcp.py`; moving
that module would blur SDK source-home rules. The root docs/script/test files,
however, were part payload and made Codex Projection look like an exception to
the active mechanics topology.

## Decision

Localize the runnable workspace MCP server route into:

- `mechanics/codex-projection/parts/workspace-mcp-server/`

Keep `src/aoa_sdk/codex/workspace_mcp.py` as importable SDK source. Update the
project-level config guidance and health readout around the part-local script
path instead of leaving the root script as an active fallback.

## Rationale

`workspace-mcp-server` is more topological than `workspace-mcp`: it names the
part as the server route that turns workspace discovery and Codex config into
MCP tools, resources, and prompts. The name also leaves room for other MCP or
Codex Projection parts without making this part the whole projection parent.

The source module stays in `src/aoa_sdk/codex/` because it is the reusable SDK
implementation. The part owns the runnable script, local docs, tests, and route
contract.

## Consequences

- Root `docs/`, `scripts/`, and `tests/` no longer carry the active workspace
  MCP server payload.
- Project-level `aoa_workspace` config should point at the part-local script.
- The MCP health readout now reports whether config uses the expected
  part-local script and whether that script exists.
- Codex runtime behavior, host deployment, and sibling semantic truth remain
  outside SDK ownership.

## Source Surfaces

- `mechanics/codex-projection/README.md`
- `mechanics/codex-projection/PARTS.md`
- `mechanics/codex-projection/PROVENANCE.md`
- `mechanics/codex-projection/parts/workspace-mcp-server/`
- `src/aoa_sdk/codex/workspace_mcp.py`
- `mechanics/ARTIFACT_TOPOLOGY.md`
- `mechanics/topology.json`
- `README.md`

## Follow-Up Route

Continue root technical district audit for Questbook payload, Checkpoint
test placement, and cross-mechanic public contracts.

## Verification

The executable decision-index and owning-surface checks are routed through
`docs/decisions/AGENTS.md` and the nearest source-owner validation surface.
