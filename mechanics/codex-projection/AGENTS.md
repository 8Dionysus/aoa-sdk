# AGENTS.md

## Applies to

`mechanics/codex-projection/`.

## Role

Route the shared Codex Projection mechanic for SDK workspace MCP server,
live rollout status snapshots, portability boundaries, rollout reference
handoffs, and Codex-facing control-plane reads.

## Read before editing

- `mechanics/AGENTS.md`
- `mechanics/codex-projection/README.md`
- `mechanics/codex-projection/parts/workspace-mcp-server/README.md`
- `mechanics/codex-projection/parts/live-rollout-status-readout/README.md`
- `src/aoa_sdk/codex/`
- `mechanics/codex-projection/parts/workspace-mcp-server/scripts/aoa_workspace_mcp_server.py`

## Boundaries

- Stay on the control plane.
- Do not make SDK Codex reads a Codex runtime or deploy authority.
- Keep host deployment and sibling rollout authority outside SDK.

## Validation

```bash
python scripts/validate_mechanics_topology.py
python -m pytest -q mechanics/codex-projection/parts/workspace-mcp-server/tests/test_workspace_mcp_server.py mechanics/codex-projection/parts/live-rollout-status-readout/tests/test_live_rollout_status_readout.py
```

## Closeout

Report whether workspace MCP server, live rollout status, portability boundary,
or rollout reference handoff behavior changed.
