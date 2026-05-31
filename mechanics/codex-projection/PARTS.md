# Codex Projection Parts

## Candidate Parts

| Part | Current surfaces | Future payload condition |
| --- | --- | --- |
| workspace-mcp | `docs/codex-workspace-mcp.md`, `scripts/aoa_workspace_mcp_server.py` | only if MCP resources need package-local schemas |
| deploy-status | deploy-status schema, example, registry | only if snapshots become a generated read lane |
| portability | `docs/CODEX_PLANE_PORTABILITY.md` | only if portability contracts need examples |
| rollout-refs | rollout campaign refs and deploy operation note | only if rollout references become package-local manifests |

## Provenance Bridge

This parent replaces the over-specific `codex-plane` parent. The SDK-specific
plane wording is a part-local concern inside the shared Codex Projection
mechanic.
