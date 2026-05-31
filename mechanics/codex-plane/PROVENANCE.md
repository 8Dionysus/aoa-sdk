# Codex Plane Provenance

## Source Surfaces

- `docs/codex-workspace-mcp.md`
- `docs/CODEX_PLANE_DEPLOY_STATUS.md`
- `docs/CODEX_PLANE_PORTABILITY.md`
- `examples/codex_plane_deploy_status_snapshot.example.json`
- `schemas/codex_plane_deploy_status_snapshot_v1.json`
- `scripts/aoa_workspace_mcp_server.py`
- `src/aoa_sdk/codex/`
- `tests/test_codex_workspace_mcp.py`
- `tests/test_codex_deploy_status.py`

## Stronger Owners

Codex runtime, host deployment state, and rollout execution are outside SDK
truth. The SDK owns typed local readouts.

## Notes

This is SDK-local because Codex-plane readouts are specific to the SDK control
plane and its workspace MCP shape.
