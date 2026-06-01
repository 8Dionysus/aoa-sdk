# Codex Projection Parts

## Candidate Parts

| Part | Current surfaces | Future payload condition |
| --- | --- | --- |
| workspace-mcp-server | `parts/workspace-mcp-server/` | owns the runnable MCP server route, docs, and tests; importable source remains in `src/aoa_sdk/codex/` |
| live-rollout-status-readout | `parts/live-rollout-status-readout/` | reads external rollout evidence and emits a bounded SDK status snapshot |
| portability-boundary | `parts/portability-boundary/docs/portability-boundary.md` | explains workspace-root portability without making SDK code the deploy owner |
| owner-rollout-reference-handoff | `parts/owner-rollout-reference-handoff/docs/` | carries source-owned rollout refs without making them SDK truth |

## Provenance Bridge

Former parent-name candidates for this package live only in
`legacy/INDEX.md`. Active Codex Projection routes name the operation:
workspace MCP server, live rollout status readout, portability boundary, and
owner rollout reference handoff.
