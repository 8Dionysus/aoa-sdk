# AGENTS.md

## Applies to

`mechanics/codex-projection/`.

## Role

Route the shared Codex Projection mechanic for SDK Codex workspace MCP,
deploy-status snapshots, portability boundaries, rollout references, and
Codex-facing control-plane reads.

## Read before editing

- `mechanics/AGENTS.md`
- `mechanics/codex-projection/README.md`
- `docs/codex-workspace-mcp.md`
- `docs/CODEX_PLANE_DEPLOY_STATUS.md`
- `src/aoa_sdk/codex/`
- `scripts/aoa_workspace_mcp_server.py`

## Boundaries

- Stay on the control plane.
- Do not make SDK Codex reads a Codex runtime or deploy authority.
- Keep host deployment and sibling rollout authority outside SDK.

## Validation

```bash
python scripts/validate_mechanics_topology.py
python -m pytest -q tests/test_codex_workspace_mcp.py tests/test_codex_deploy_status.py
```

## Closeout

Report whether MCP, deploy-status, portability, or rollout reference behavior
changed.
