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

### Current release contour

The live direction for `v0.2.3` is control-plane hardening. Its current
release contour is:

- workspace topology and the compact control-plane capsule:
  `.aoa/workspace.toml`, `docs/workspace-layout.md`, and
  `generated/workspace_control_plane.min.json`
- Codex-plane deploy-state and rollout reference boundaries:
  `docs/CODEX_PLANE_DEPLOY_STATUS.md`,
  `docs/CODEX_DEPLOY_OPERATION_BOUNDARY_NOTE.md`,
  `docs/codex_rollout_campaign_refs.md`,
  `schemas/codex_plane_deploy_status_snapshot_v1.json`,
  `examples/codex_plane_deploy_status_snapshot.example.json`, and
  `src/aoa_sdk/codex/registry.py`
- reviewed closeout followthrough, component-refresh carry, continuity carry,
  and next-kernel hints:
  `docs/closeout-followthrough-map.md`, `docs/COMPONENT_DRIFT_HINTS.md`,
  `docs/SELF_AGENCY_CONTINUITY_CARRY.md`,
  `docs/SESSION_GROWTH_KERNEL_SIGNAL_RULES.md`,
  `schemas/closeout_owner_followthrough_map.schema.json`,
  `schemas/closeout_continuity_window.schema.json`, and
  `schemas/closeout_followthrough_decision.schema.json`
- checkpoint, surface-detection, and reviewed handoff guidance:
  `docs/session-growth-checkpoints.md`,
  `docs/checkpoint-note-promotion.md`, `docs/session-closeout.md`, and
  `docs/aoa-surface-detection-closeout-handoff.md`
- bounded release and CI posture: `docs/RELEASING.md` and
  `docs/RELEASE_CI_POSTURE.md`

Roadmap drift is an SDK-layer risk because downstream agents use this file to
choose whether a change belongs on the control plane. It still must not turn
`aoa-sdk` into a source-owning runtime layer.

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
