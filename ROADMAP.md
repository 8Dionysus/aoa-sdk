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
- root design surfaces, `DESIGN.md` and `DESIGN.AGENTS.md`, that name SDK
  system form and agent-facing guidance form for mechanics work
- canonical decision rationale lane under `docs/decisions/` with generated
  lookup indexes
- docs entry map under `docs/README.md`, with root docs kept to route,
  boundary, workspace, versioning, release-door, seed-history, and decision
  surfaces
- checked SDK source-home tree under `sdk/`, validated by
  `scripts/validate_sdk_source_home.py`
- active mechanics topology under `mechanics/`, grounded in
  `mechanics/topology.json`, package provenance, part validation routes, and
  `scripts/validate_mechanics_topology.py`
- typed compatibility checks and workspace inspection
- the compact control-plane capsule at
  `generated/workspace_control_plane.min.json`
- bounded `aoa skills enter` / `aoa skills guard` wrappers
- additive `aoa surfaces detect` and reviewed closeout handoff helpers that
  stay weaker than owner truth
- checkpoint capture, review-note, and explicit reviewed-session handoff runner surfaces
- typed Codex Projection live rollout status reads plus bounded release audit and publish
  helpers

### Current unreleased contour

The live post-`v0.2.3` direction is control-plane hardening. Its current
unreleased contour is:

- workspace topology and the compact control-plane capsule:
  `.aoa/workspace.toml`, `docs/workspace-layout.md`, and
  `generated/workspace_control_plane.min.json`
- decision rationale lane that enabled mechanics:
  `docs/decisions/README.md`,
  `docs/decisions/AOA-SDK-D-0001-decision-rationale-lane-before-mechanics.md`,
  `docs/decisions/AOA-SDK-D-0002-root-design-surfaces-before-mechanics.md`,
  `docs/decisions/indexes/`, and
  `scripts/generate_decision_indexes.py`
- root design surfaces that enabled mechanics:
  `DESIGN.md` and `DESIGN.AGENTS.md`
- SDK source-home posture:
  `sdk/README.md`, `sdk/SDK_SHAPE.md`, `sdk/source_home.manifest.json`,
  `scripts/validate_sdk_source_home.py`, and
  `docs/decisions/AOA-SDK-D-0043-sdk-source-home-tree.md`
- corrected active mechanics topology after sibling-source reread:
  `mechanics/README.md`, `mechanics/topology.json`,
  `scripts/validate_mechanics_topology.py`, and
  `docs/decisions/AOA-SDK-D-0005-mechanics-parent-boundary-correction.md`
- source-family crosswalk coverage for every `src/aoa_sdk/*` family:
  `mechanics/topology.json`,
  `docs/decisions/AOA-SDK-D-0006-mechanics-source-family-crosswalk.md`, and
  `tests/test_mechanics_topology.py`
- Codex Projection live rollout status and rollout reference boundaries:
  `mechanics/codex-projection/parts/live-rollout-status-readout/docs/live-rollout-status-readout.md`,
  `mechanics/codex-projection/parts/owner-rollout-reference-handoff/docs/deploy-operation-boundary-note.md`,
  `mechanics/codex-projection/parts/owner-rollout-reference-handoff/docs/rollout-campaign-refs.md`,
  `mechanics/codex-projection/parts/live-rollout-status-readout/schemas/live-rollout-status-snapshot.schema.json`,
  `mechanics/codex-projection/parts/live-rollout-status-readout/examples/live-rollout-status-snapshot.example.json`, and
  `src/aoa_sdk/codex/registry.py`
- reviewed closeout context carry, component-refresh followthrough,
  self-agency continuity carry, and next-kernel followthrough decision:
  `mechanics/checkpoint/parts/reviewed-closeout-context-carry/README.md`,
  `mechanics/checkpoint/parts/reviewed-closeout-context-carry/docs/owner-followthrough-map.md`,
  `mechanics/checkpoint/parts/reviewed-closeout-context-carry/docs/component-refresh-followthrough.md`,
  `mechanics/checkpoint/parts/reviewed-closeout-context-carry/docs/self-agency-continuity-carry.md`,
  `mechanics/checkpoint/parts/reviewed-closeout-context-carry/docs/next-kernel-followthrough-decision.md`,
  `mechanics/checkpoint/parts/reviewed-closeout-context-carry/schemas/closeout_owner_followthrough_map.schema.json`,
  `mechanics/checkpoint/parts/reviewed-closeout-context-carry/schemas/closeout_continuity_window.schema.json`, and
  `mechanics/checkpoint/parts/reviewed-closeout-context-carry/schemas/closeout_followthrough_decision.schema.json`
- checkpoint, surface-detection, and reviewed handoff guidance:
  `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/docs/session-growth-checkpoint-cycle.md`,
  `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/docs/reviewed-checkpoint-note-promotion.md`,
  `mechanics/checkpoint/parts/reviewed-session-handoff-runner/docs/reviewed-session-handoff-runner.md`, and
  `mechanics/boundary-bridge/parts/owner-layer-signal-handoff/docs/surface-closeout-handoff.md`
- bounded release and CI posture:
  `mechanics/release-support/parts/release-audit-publish-helper/docs/release-runbook.md`,
  `mechanics/release-support/parts/public-support-ci-posture/docs/public-support-ci-posture.md`,
  `docs/RELEASING.md`, and `docs/RELEASE_CI_POSTURE.md`

Roadmap drift is an SDK-layer risk because downstream agents use this file to
choose whether a change belongs on the control plane. It still must not turn
`aoa-sdk` into a source-owning runtime layer.

The next honest move is not to widen the SDK into a second owner layer.
It is to keep the control plane small, explicit, testable, and source-
subordinate while cross-repo growth becomes denser.

## Current cycle

### Stage 1: current-direction consolidation

Goals:

- keep `ROADMAP.md` as the root-level current-direction door
- keep `README.md` and `AGENTS.md` short and route-first
- keep `docs/README.md` as the docs entry map instead of letting `docs/`
  become a flat shelf
- keep `DESIGN.md` and `DESIGN.AGENTS.md` as the root design route for
  SDK source-home and mechanics topology
- keep `sdk/` as the checked SDK source-home tree, not an implementation or
  mechanics payload lane
- keep `docs/blueprint.md` explicit as seed history rather than current-state
  authority
- keep structural rationale in `docs/decisions/` and keep mechanics payload
  moves tied to package-local reason and validator surfaces

### Stage 2: control-plane contract hardening

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

### Stage 3: closeout and owner-followthrough discipline

Goals:

- keep checkpoint capture, review-note, and explicit reviewed session handoff bounded
- keep owner followthrough, continuity carry, and component-refresh hints
  reviewed and source-subordinate
- preserve explicit truth labels across loaded, suggested, manual-equivalent,
  and activated surfaces

Exit signals:

- reviewed closeout routes stay inspectable and weaker than owner meaning
- persistent handoff bundles remain advisory
- no closeout helper silently becomes policy, activation, or progression
  authority

### Stage 4: portability and rollout posture

Goals:

- keep sibling-workspace bootstrap and discovery overrides legible
- keep Codex Projection portability and live rollout status reads typed and bounded
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
