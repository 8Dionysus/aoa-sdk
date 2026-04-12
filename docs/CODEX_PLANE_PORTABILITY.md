# Codex Plane Portability

This note clarifies how `aoa-sdk` should relate to the shared-root AoA Codex
plane when the live workspace root changes.

## Boundary

`aoa-sdk` owns:

- workspace discovery
- workspace inspection
- bootstrap and control-plane helpers
- MCP implementation for the workspace surface

It does not own:

- the source-authored shared-root Codex install subset
- the manifest/profile pair used to regenerate `8Dionysus/.codex/config.toml`
  and `8Dionysus/.codex/hooks.json`
- the role meaning projected into Codex agents
- the seed/stats MCP implementation owned elsewhere

## Practical rule

If the live AoA workspace root changes:

- use SDK discovery overrides only when you need the SDK to inspect or resolve
  a non-default layout
- regenerate the checked-in `8Dionysus/.codex/config.toml` and
  `8Dionysus/.codex/hooks.json` from the `8Dionysus` Codex-plane
  manifest/profile pair
- then project the refreshed shared-root surfaces into the live workspace root

Do not patch SDK code or MCP server names just to chase deployment-path drift
that belongs in the shared-root renderer.

## Why this matters

The SDK should stay a typed consumer and control-plane helper, not become the
hidden owner of Codex-plane deployment state.
