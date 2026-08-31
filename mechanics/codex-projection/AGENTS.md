# AGENTS.md

## Applies to

`mechanics/codex-projection/`.

## Role

Route the shared Codex Projection mechanic for SDK workspace MCP server,
live rollout status snapshots, portability boundaries, rollout reference
handoffs, and Codex-facing control-plane reads.

## Relevant routes

Start with root `AGENTS.md`, then this nearest card. Open only the owner source, README, DESIGN, CONTRACT, VALIDATION, release, generated, or sibling-owner surface required by the touched path, semantic question, or requested operation. This is a conditional route, not an unconditional reading inventory. The conditional references retained from this card are: `mechanics/AGENTS.md`, `mechanics/codex-projection/README.md`, `mechanics/codex-projection/ROADMAP.md`, `mechanics/codex-projection/parts/workspace-mcp-server/README.md`, `mechanics/codex-projection/parts/live-rollout-status-readout/README.md`, `src/aoa_sdk/codex/`, `mechanics/codex-projection/parts/workspace-mcp-server/scripts/aoa_workspace_mcp_server.py`.

## Boundaries

- Stay on the control plane.
- Do not make SDK Codex reads a Codex runtime or deploy authority.
- Keep host deployment and sibling rollout authority outside SDK.

## Validation route

Use the nearest applicable `VALIDATION.md` when the touched path, semantic question, or requested operation requires executable checks. For repository-wide, release-facing, generated, or cross-owner work, follow root `VALIDATION.md`. The machine gate remains `scripts/release_check.py`; the owner claim/evidence manifest, accepted validation graph, and serial completeness oracle remain authoritative.

## Closeout

Report whether workspace MCP server, live rollout status, portability boundary,
or rollout reference handoff behavior changed.
