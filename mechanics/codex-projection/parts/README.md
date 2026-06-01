# Codex Projection Parts

Functioning parts under `mechanics/codex-projection/parts/` own SDK-local
Codex-facing artifacts after they move out of root technical districts.

## Active Parts

| Part | Role |
| --- | --- |
| `workspace-mcp-server` | runs the workspace-level MCP server and reports Codex-facing orientation resources without claiming owner truth |
| `live-rollout-status-readout` | reads deploy-local rollout evidence and emits a bounded SDK status snapshot |
| `portability-boundary` | explains workspace-root portability without making SDK code the deploy owner |
| `owner-rollout-reference-handoff` | carries source-owned rollout campaign refs as handoff material |

Root docs, schemas, examples, and tests should not remain the active home for
these parts unless a path is explicitly kept as a public/tooling contract.
