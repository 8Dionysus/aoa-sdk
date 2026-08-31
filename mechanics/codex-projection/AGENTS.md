# AGENTS.md

## Applies to

`mechanics/codex-projection/`.

## Role

Route the shared Codex Projection mechanic for SDK workspace MCP server,
live rollout status snapshots, portability boundaries, rollout reference
handoffs, and Codex-facing control-plane reads.

## Relevant routes

The conditional references retained from this card are: `mechanics/AGENTS.md`, `mechanics/codex-projection/README.md`, `mechanics/codex-projection/ROADMAP.md`, `mechanics/codex-projection/parts/workspace-mcp-server/README.md`, `mechanics/codex-projection/parts/live-rollout-status-readout/README.md`, `src/aoa_sdk/codex/`, `mechanics/codex-projection/parts/workspace-mcp-server/scripts/aoa_workspace_mcp_server.py`.

## Boundaries

- Stay on the control plane.
- Do not make SDK Codex reads a Codex runtime or deploy authority.
- Keep host deployment and sibling rollout authority outside SDK.

## Validation

Validation for Codex Projection paths belongs to the nearest active projection part `VALIDATION.md`; broader checks inherit root `VALIDATION.md`.

## Closeout

Report whether workspace MCP server, live rollout status, portability boundary,
or rollout reference handoff behavior changed.
