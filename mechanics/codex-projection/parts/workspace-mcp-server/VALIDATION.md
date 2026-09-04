# Workspace MCP Server Validation

Run:

```bash
python -m pytest -q mechanics/codex-projection/parts/workspace-mcp-server/tests/test_workspace_mcp_server.py
```

`test_workspace_mcp_server.py` verifies:

- the runtime entrypoint for the `abyss-stack` diagnostic catalog uses the
  part-local diagnostic-spine path, not the old root generated path;
- the surface crosswalk exposes `secondary_surface` and does not emit the old
  substitute-route field;
- the `aoa-stats` repo map keeps owner entrypoints but excludes its retired
  repo-local MCP launcher, and the crosswalk names project-level `aoa_stats`.
- the skill readout uses the compact owner catalog and capability graph, not
  retired index or runtime-discovery files.
- explicit private-registry configuration exposes bounded catalog, organ, and
  capability inspection without schema preloading or execution;
- the server exposes exactly eleven tools, all with read-only annotation
  hints, and no activation tool;
- two static organ resources and two organ URI templates are registered;
- the current Dionysus interview catalog replaces its retired repo-local MCP
  launcher in curated workspace entrypoints.

For the underlying organ contracts, also run:

```bash
python -m pytest -q mechanics/boundary-bridge/parts/organ-access-control-plane/tests
```

For broader Codex Projection routing, also run:

```bash
python -m pytest -q mechanics/codex-projection/parts/live-rollout-status-readout/tests/test_live_rollout_status_readout.py tests/test_docs_routes.py mechanics/release-support/parts/public-support-ci-posture/tests/test_public_support_ci_posture.py
```

The repository-wide topology gate is owned by [root `VALIDATION.md`](../../../../VALIDATION.md#focused-repository-checks).

Organ-access schema and example generation are owned by [the organ-access validation surface](../../../boundary-bridge/parts/organ-access-control-plane/VALIDATION.md).
