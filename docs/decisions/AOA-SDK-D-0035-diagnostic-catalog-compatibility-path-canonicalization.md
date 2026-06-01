# Diagnostic Catalog Compatibility Path Canonicalization

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0035
- Original date: 2026-06-01
- Surface classes: compatibility, topology, mechanics, runtime entrypoint
- SDK facets: compatibility posture, workspace MCP, active naming, sibling path routing
- Mechanic parents: boundary-bridge, codex-projection
- Guard families: compatibility, active naming, root-surface hygiene, part validation
- Posture: accepted

## Context

`aoa-sdk` consumed the `abyss-stack` diagnostic surface catalog with a
part-local preferred path and an old root `generated/diagnostic_surface_catalog.min.json`
compatibility fallback.

That kept a moved root generated path active in the SDK compatibility layer.
The workspace MCP runtime entrypoint list also still exposed the old root path.

The current `abyss-stack` source checkout has the canonical diagnostic-spine
part-local catalog at
`mechanics/diagnostic-spine/parts/diagnostic-surfaces/generated/diagnostic_surface_catalog.min.json`.

## Decision

Make the diagnostic-spine part-local path the only active compatibility path
for `abyss-stack.diagnostic_surface_catalog.min`.

Remove the old root generated path from active compatibility fallback behavior
and from the workspace MCP runtime entrypoint map.

## Rationale

The SDK compatibility layer should make owner path drift visible instead of
making stale root generated paths quietly acceptable. If a sibling has moved a
surface into a part-local mechanics home, the SDK should route to that current
owner path directly.

This keeps active names and compatibility behavior aligned: historical root
paths can remain in fixtures, decisions, or external provenance, but not as an
active fallback route.

## Consequences

- `src/aoa_sdk/compatibility/policy.py` names the diagnostic-spine part-local
  catalog as the active path.
- `src/aoa_sdk/codex/workspace_mcp.py` reports the part-local diagnostic
  catalog entrypoint.
- Workspace fixtures include the part-local catalog and retain a stale old
  root copy only as negative evidence.
- Boundary Bridge compatibility tests prove the old root copy is ignored when
  the part-local catalog is absent.
- Codex Projection workspace MCP tests prove the runtime entrypoint reports the
  canonical part-local path.

## Source Surfaces

- `src/aoa_sdk/compatibility/policy.py`
- `src/aoa_sdk/codex/workspace_mcp.py`
- `docs/versioning.md`
- `mechanics/boundary-bridge/parts/consumed-surface-posture-gate/`
- `mechanics/codex-projection/parts/workspace-mcp-server/`
- `tests/fixtures/workspace/src/abyss-stack/`

## Follow-Up Route

Apply the same rule to future consumed sibling surfaces: if the owner repo
localizes a surface into mechanics, update the SDK compatibility map to the
canonical path and add an explicit negative test for stale root fallback.

## Verification

```bash
python -m pytest -q mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_consumed_surface_compatibility_gate.py mechanics/codex-projection/parts/workspace-mcp-server/tests/test_workspace_mcp_server.py
python -m ruff check src/aoa_sdk/compatibility/policy.py src/aoa_sdk/codex/workspace_mcp.py mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_consumed_surface_compatibility_gate.py mechanics/codex-projection/parts/workspace-mcp-server/tests/test_workspace_mcp_server.py
```
