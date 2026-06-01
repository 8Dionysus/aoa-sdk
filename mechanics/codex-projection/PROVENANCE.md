# Codex Projection Provenance

## Source Surfaces

- `mechanics/codex-projection/parts/workspace-mcp-server/docs/workspace-mcp-server.md`
- `mechanics/codex-projection/parts/workspace-mcp-server/scripts/aoa_workspace_mcp_server.py`
- `mechanics/codex-projection/parts/workspace-mcp-server/tests/test_workspace_mcp_server.py`
- `mechanics/codex-projection/parts/live-rollout-status-readout/docs/live-rollout-status-readout.md`
- `mechanics/codex-projection/parts/live-rollout-status-readout/examples/live-rollout-status-snapshot.example.json`
- `mechanics/codex-projection/parts/live-rollout-status-readout/schemas/live-rollout-status-snapshot.schema.json`
- `mechanics/codex-projection/parts/live-rollout-status-readout/tests/test_live_rollout_status_readout.py`
- `mechanics/codex-projection/parts/portability-boundary/docs/portability-boundary.md`
- `mechanics/codex-projection/parts/owner-rollout-reference-handoff/docs/deploy-operation-boundary-note.md`
- `mechanics/codex-projection/parts/owner-rollout-reference-handoff/docs/rollout-campaign-refs.md`
- `src/aoa_sdk/codex/`

## Stronger Owners

Codex runtime, host deployment state, and rollout execution are outside SDK
truth. The SDK owns typed local readouts.

## Notes

Former parent-name candidates for this package live only in
`legacy/INDEX.md`. The active shared parent is `codex-projection`; SDK
workspace MCP server and live rollout status readouts live as parts under it.
