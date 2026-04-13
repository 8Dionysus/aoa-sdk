# AoA SDK Roadmap

This roadmap is the current repo-owned direction surface for `aoa-sdk`.

Use it when the question is "what is the SDK's current control-plane phase and
what should harden next?"
Use `docs/blueprint.md` only as the original seed blueprint and historical
design context.

## Current phase

`aoa-sdk` has moved beyond seed bootstrap into control-plane contract
hardening.

The current landed surface already includes:

- workspace discovery and topology resolution grounded in
  `.aoa/workspace.toml`
- typed compatibility checks and workspace inspection
- the compact control-plane capsule at
  `generated/workspace_control_plane.min.json`
- bounded `aoa skills enter` / `aoa skills guard` wrappers
- additive `aoa surfaces detect` and reviewed closeout handoff helpers that
  stay weaker than owner truth
- checkpoint capture, review-note, and explicit closeout-bridge surfaces
- typed Codex-plane deploy-status reads plus bounded release audit and publish
  helpers

The next honest move is not to widen the SDK into a second owner layer.
It is to keep the control plane small, explicit, testable, and source-
subordinate while cross-repo growth becomes denser.

## Current cycle

### Wave 1: current-direction consolidation

Goals:

- keep `ROADMAP.md` as the root-level current-direction door
- keep `README.md` and `AGENTS.md` short and route-first
- keep `docs/blueprint.md` explicit as seed history rather than current-state
  authority

### Wave 2: control-plane contract hardening

Goals:

- harden topology, compatibility, and generated-capsule stability
- keep workspace discovery explicit and test-backed
- fail closed on silent generated-surface or route drift
- preserve the distinction between source checkouts and deployed runtime
  mirrors

Exit signals:

- the current-state verification battery stays green
- docs, tests, and the control-plane capsule stay aligned
- current repo direction no longer depends on reading the seed blueprint first

### Wave 3: closeout and owner-followthrough discipline

Goals:

- keep checkpoint capture, review-note, and explicit closeout bridge bounded
- keep owner followthrough, continuity carry, and component-refresh hints
  reviewed and source-subordinate
- preserve explicit truth labels across loaded, suggested, manual-equivalent,
  and activated surfaces

Exit signals:

- reviewed closeout routes stay inspectable and weaker than owner meaning
- persistent handoff bundles remain advisory
- no closeout helper silently becomes policy, activation, or progression
  authority

### Wave 4: portability and rollout posture

Goals:

- keep sibling-workspace bootstrap and discovery overrides legible
- keep Codex-plane portability and deploy-status reads typed and bounded
- keep release audit and publish helpers subordinate to owner-repo truth

## Standing discipline

Across all waves:

- stay on the control plane
- keep source-owned meaning in sibling repositories
- prefer manifest-driven, test-backed behavior over hidden heuristics
- keep rollout, checkpoint, and closeout helpers explicit about what they can
  read, suggest, or execute
- do not let convenience helpers impersonate routing, memory, playbook, eval,
  or role authority
