# Codex Projection Mechanic

Status: active topology with part-local payload.

## Mechanic Card

### Operation

Project SDK workspace orientation into Codex-facing read surfaces: workspace
MCP server, live rollout status snapshots, portability boundaries, and owner
rollout reference handoffs.

### Trigger

Use this mechanic when Codex workspace MCP server behavior, live rollout status
schemas, portability docs, rollout refs, or Codex registry code changes.

### SDK owns

- local workspace MCP server over SDK workspace orientation
- typed live rollout status snapshot reads
- portability boundary docs
- owner rollout reference handoff surfaces

### Stronger owner split

Codex runtime behavior, host deployment state, rollout execution, and sibling
repo authority remain outside SDK ownership.

### Current source surfaces

- `mechanics/codex-projection/parts/workspace-mcp-server/docs/workspace-mcp-server.md`
- `mechanics/codex-projection/parts/workspace-mcp-server/scripts/aoa_workspace_mcp_server.py`
- `mechanics/codex-projection/parts/workspace-mcp-server/tests/test_workspace_mcp_server.py`
- `mechanics/codex-projection/parts/live-rollout-status-readout/docs/live-rollout-status-readout.md`
- `mechanics/codex-projection/parts/live-rollout-status-readout/examples/live-rollout-status-snapshot.example.json`
- `mechanics/codex-projection/parts/live-rollout-status-readout/schemas/live-rollout-status-snapshot.schema.json`
- `mechanics/codex-projection/parts/portability-boundary/docs/portability-boundary.md`
- `mechanics/codex-projection/parts/owner-rollout-reference-handoff/docs/deploy-operation-boundary-note.md`
- `mechanics/codex-projection/parts/owner-rollout-reference-handoff/docs/rollout-campaign-refs.md`
- `src/aoa_sdk/codex/`

### Candidate parts

- workspace-mcp-server
- live-rollout-status-readout
- portability-boundary
- owner-rollout-reference-handoff

### Must not claim

This mechanic must not treat a live rollout status snapshot as live deployment
authority or make the SDK a Codex runtime.

### Validation

Use the touched part `VALIDATION.md` for executable checks. For package-wide
route changes, use `mechanics/topology.json` for the active validation list
and then run the mechanics topology gate from the root route card.

### Next route

Deployment or runtime changes route to host/Codex owners; SDK keeps typed
status reads and route documentation.
