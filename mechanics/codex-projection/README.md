# Codex Projection Mechanic

Status: skeleton.

## Mechanic Card

### Operation

Project SDK workspace orientation into Codex-facing read surfaces: workspace
MCP, deploy-status snapshots, portability boundaries, and rollout references.

### Trigger

Use this mechanic when Codex workspace MCP behavior, deploy-status schemas,
portability docs, rollout refs, or Codex registry code changes.

### SDK owns

- local MCP server over SDK workspace orientation
- typed deploy-status snapshot reads
- portability boundary docs
- rollout reference surfaces

### Stronger owner split

Codex runtime behavior, host deployment state, rollout execution, and sibling
repo authority remain outside SDK ownership.

### Current source surfaces

- `docs/codex-workspace-mcp.md`
- `docs/CODEX_PLANE_DEPLOY_STATUS.md`
- `docs/CODEX_PLANE_PORTABILITY.md`
- `examples/codex_plane_deploy_status_snapshot.example.json`
- `schemas/codex_plane_deploy_status_snapshot_v1.json`
- `scripts/aoa_workspace_mcp_server.py`
- `src/aoa_sdk/codex/`
- Codex tests under `tests/`

### Candidate parts

- workspace-mcp
- deploy-status
- portability
- rollout-refs

### Must not claim

This mechanic must not treat a deploy-status snapshot as live deployment
authority or make the SDK a Codex runtime.

### Validation

```bash
python -m pytest -q tests/test_codex_workspace_mcp.py tests/test_codex_deploy_status.py
```

### Next route

Deployment or runtime changes route to host/Codex owners; SDK keeps typed
status reads and route documentation.
