# Workspace MCP Server Validation

Run:

```bash
python -m pytest -q mechanics/codex-projection/parts/workspace-mcp-server/tests/test_workspace_mcp_server.py
python scripts/validate_mechanics_topology.py
```

`test_workspace_mcp_server.py` verifies:

- the runtime entrypoint for the `abyss-stack` diagnostic catalog uses the
  part-local diagnostic-spine path, not the old root generated path;
- the surface crosswalk exposes `secondary_surface` and does not emit the old
  substitute-route field;
- the `aoa-stats` repo map keeps owner entrypoints but excludes its retired
  repo-local MCP launcher, and the crosswalk names project-level `aoa_stats`.

For broader Codex Projection routing, also run:

```bash
python -m pytest -q mechanics/codex-projection/parts/live-rollout-status-readout/tests/test_live_rollout_status_readout.py tests/test_docs_routes.py mechanics/release-support/parts/public-support-ci-posture/tests/test_public_support_ci_posture.py
```
