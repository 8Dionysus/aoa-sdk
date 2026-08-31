# AGENTS.md

Local guidance for `src/aoa_sdk/` in `aoa-sdk`. Read the root `AGENTS.md` first.
This directory owns typed control-plane facades for consumed AoA surfaces.

## Scope

Code here loads, validates, inspects, and hands off owner-owned surfaces.
Stay on the control plane: the explicitly accepted
`control_plane/routing/` family owns deterministic routing producer and route
candidate contracts, but no typed helper may become a runtime service, hidden
policy engine, or source of sibling-repo meaning.

## Local contract

- Preserve owner boundaries, truth labels, source refs, review state, and
  explicit no-execution claims in every helper.
- Keep source presence, installed projection, capability candidate, reviewed
  evidence, owner acceptance, and actual execution distinct.
- Prefer explicit manifests and config over magic discovery.
- Keep imports cheap and testable; do not require sibling repos, live services, or private workspace state for basic imports.
- When topology, CLI behavior, compatibility, or reviewed closeout behavior changes, update docs and tests together.
