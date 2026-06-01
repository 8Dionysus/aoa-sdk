# Workspace MCP Surface Crosswalk Secondary Route Naming

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0037
- Original date: 2026-06-01
- Surface classes: MCP readout, active naming, Codex projection
- SDK facets: workspace MCP, active naming, route selection, agent guidance
- Mechanic parents: codex-projection
- Guard families: active naming, fallback removal, route clarity, part validation
- Posture: accepted

## Context

The workspace MCP `surface-crosswalk` readout used a `fallback` field to name
the next surface after `primary_surface`.

That field was not a compatibility fallback, failure fallback, or legacy path.
It meant a second inspectable route for orientation. Keeping the word active
made the readout sound like the SDK was endorsing fallback behavior, while the
mechanics refactor is explicitly removing hidden fallbacks from active routes.

## Decision

Rename the active crosswalk field from `fallback` to `secondary_surface`.

Update the workspace MCP prompts to ask for a primary choice and a secondary
surface rather than a fallback.

## Rationale

The surface crosswalk should be an operational map: role, primary route,
secondary route, owner boundary, and validation posture. `secondary_surface`
describes that map directly. `fallback` is overloaded with legacy and
compatibility behavior and can train agents to treat weaker routes as acceptable
substitutes for owner truth.

## Consequences

- `src/aoa_sdk/codex/workspace_mcp.py` emits `secondary_surface` in each
  crosswalk row.
- Workspace MCP prompts ask for one primary choice and one secondary surface.
- Part-local workspace MCP tests reject an active `fallback` crosswalk field.
- The change intentionally favors clearer active topology over preserving a
  stale readout field name.

## Source Surfaces

- `src/aoa_sdk/codex/workspace_mcp.py`
- `mechanics/codex-projection/parts/workspace-mcp-server/`

## Follow-Up Route

Keep future MCP readout fields action-bearing. If a route is genuinely a
compatibility fallback, name and validate it as compatibility. If it is a next
surface for orientation, use route vocabulary such as primary, secondary,
owner, validation, or boundary.

## Verification

```bash
python -m pytest -q mechanics/codex-projection/parts/workspace-mcp-server/tests/test_workspace_mcp_server.py
python -m ruff check src/aoa_sdk/codex/workspace_mcp.py mechanics/codex-projection/parts/workspace-mcp-server/tests/test_workspace_mcp_server.py
```
