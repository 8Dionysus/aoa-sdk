# Changelog

All notable changes to `aoa-sdk` will be documented in this file.

The format is intentionally simple and human-first.
Tracking starts with the community-docs baseline for this repository.

## [Unreleased]

### Summary

- The May 31 reconciliation point covered the post-`v0.2.3` control-plane refactor span:
  22 first-parent commits and 382 changed tracked paths from `v0.2.3..main`,
  including the May 31 decision/design landing and the earlier portable
  skill, session-growth, memo-compatibility, live-workspace, and route-card
  hardening work.
- `aoa-sdk` now has the same explicit rationale/design spine expected from
  the refactored AoA repositories: decisions explain why, design surfaces
  explain system and agent-facing form, generated indexes stay derived, and
  root documents stay route-focused.
- `aoa-sdk` now has a corrected mechanics topology skeleton after full
  tracked-file inventory and sibling-source reread: package cards route 12
  shared AoA parent mechanics, while SDK-specific lanes stay as parts.
- The SDK remains a bounded typed control plane for sibling-owned surfaces. It
  can discover, validate, inspect, and hand off source-owned artifacts, but it
  still does not own routing truth, skill execution meaning, proof verdicts,
  durable memory truth, role authority, playbook law, stats state, KAG
  meaning, or runtime behavior.

### Reconciliation Basis

- Reconciled against `git log --first-parent v0.2.3..HEAD`, the current
  `CHANGELOG.md`, the landed decision records under `docs/decisions/`, root
  route cards, compatibility policy, workspace fixtures, and the current
  release gate instead of trusting PR titles alone.
- Current post-`v0.2.3` public span includes PR-backed work through #135:
  portable AoA skill foundation, session-growth and GitHub landing support,
  dry-run helper guards, refreshed shared skill exports, audit fixes, memo
  compatibility follow-ups, live workspace missing-surface handling, memory
  route trigger law, and the decision/design/canonical-surface landing.
- The largest current topology change is not a package version bump. It is the
  shift from implicit root prose and stale sibling paths toward explicit
  owner-surface routing, decision rationale, design law, and canonical sibling
  compatibility paths.

### Final Route Sweep

- Root entry now routes structural questions through `DESIGN.md`,
  agent-facing guidance questions through `DESIGN.AGENTS.md`, and rationale
  changes through `docs/decisions/README.md`.
- Decision records now live under canonical `AOA-SDK-D-####` filenames with
  generated lookup indexes by number, date, surface, SDK facet, mechanic
  parent, and guard family.
- Mechanics now live under `mechanics/` as route-only operation topology, with
  source-surface provenance, candidate parts, package-local route cards, and a
  dedicated topology validator.
- The first over-specific parent candidates are corrected: `workspace-topology`,
  `compatibility`, `skill-routing`, `surface-detection`, `closeout`,
  `a2a-return`, and `codex-plane` route as parts under shared parents.
- Compatibility policy now follows refactored sibling owner paths for
  `aoa-memo` memory, memory-object, checkpoint-to-memory, runtime-writeback,
  and `aoa-evals` runtime-candidate surfaces instead of treating old
  root-level generated paths as active routes.
- Test workspace fixtures, KAG handoff/regrounding refs, playbook federation
  refs, and sample review packet refs now point at those canonical owner
  paths so tests exercise current topology.

### Control-Plane Authority And Boundary

- `src/aoa_sdk/` stays the importable SDK source home; a future top-level
  `sdk/` district is not added merely to mirror the package name.
- `mechanics/` packages name repeatable SDK operations. The first skeleton
  does not absorb typed SDK source, generated companions, release tooling, or
  sibling source truth by theme.
- Local compatibility repairs should move the canonical path to the stronger
  owner-local path. Hidden compatibility fallback is not a substitute for
  acknowledging sibling topology drift.

### Added

- Root `DESIGN.md` as the SDK system-form surface for source homes, generated
  companions, control-plane boundaries, and the mechanics split.
- Root `DESIGN.AGENTS.md` as the agent-facing design surface for route-card
  shape, validation posture, closeout expectations, and future local guidance
  growth.
- `docs/decisions/` as the canonical rationale lane, including template,
  local `AGENTS.md`, index contract, generated read models, release-check
  wiring, and initial decisions for decisions-before-mechanics,
  design-before-mechanics, and refactored sibling surface paths.
- `mechanics/` as the SDK operation-topology skeleton with root and
  package-local `AGENTS.md`, `README.md`, `PARTS.md`, `PROVENANCE.md`,
  `TOPOLOGY_PREP.md`, `topology.json`, a validator, and regression tests.
- `AOA-SDK-D-0005` as the parent-boundary correction decision, superseding the
  first skeleton's parent package set.
- `AOA-SDK-D-0006` as the source-family crosswalk decision, making every
  `src/aoa_sdk/*` family route through a parent mechanic without promoting
  module names into parents.
- Regression coverage for decision-index freshness, design-route presence,
  canonical sibling compatibility paths, and memo source-file path selection.
- Mechanics topology validation now checks live `src/aoa_sdk/*` source-family
  coverage in addition to the parent package set and demoted parent candidates.

### Changed

- Root `AGENTS.md`, `README.md`, `ROADMAP.md`, and `docs/boundaries.md` now
  route structural, design, and decision questions to their owning surfaces
  instead of carrying the full explanation inline.
- `scripts/release_check.py` now checks generated decision indexes before the
  rest of the release gate.
- `scripts/release_check.py` now checks mechanics topology before the rest of
  the release gate.
- `scripts/validate_nested_agents.py` recognizes `DESIGN.AGENTS.md` as an
  active agent-facing guidance surface.
- `src/aoa_sdk/codex/workspace_mcp.py` and `src/aoa_sdk/routing/picker.py`
  now route memo catalog inspection to the refactored `generated/memory/`
  surface.
- `src/aoa_sdk/compatibility/policy.py` now uses canonical refactored paths
  for migrated memo and eval surfaces while preserving stable SDK surface IDs.

### Moved Or Retired

- Test fixtures for `aoa-memo` memory readers moved from root-level
  `generated/` into `generated/memory/` and `generated/memory-objects/`.
- Test fixtures for `aoa-memo` checkpoint and runtime-writeback surfaces moved
  into their mechanics part-local homes under `mechanics/checkpoint/parts/`
  and `mechanics/writeback/parts/`.
- Test fixtures for `aoa-evals` runtime-candidate readers moved into the
  audit mechanic's `candidate-readers` part-local generated lane.
- Old root-level migrated memo/eval paths are retired from active SDK
  compatibility for these surfaces; workspaces exposing only those paths now
  fail compatibility as topology drift.

### Validation

- `python scripts/generate_decision_indexes.py --check`
- `python scripts/validate_mechanics_topology.py`
- `python scripts/build_workspace_control_plane.py --check`
- `python scripts/validate_workspace_control_plane.py`
- `python -m pytest -q`
- `python -m ruff check .`
- `python -m mypy src`
- `python -m build`
- `aoa compatibility check /srv/AbyssOS/aoa-sdk`
- `python scripts/release_check.py`
- GitHub `Repo Validation` for PR #135.

### Notes

- This unreleased section is a release-ready reconciliation surface, not a new
  tag. The current public release remains `v0.2.3` until version surfaces,
  tags, and GitHub Release publication are intentionally advanced together.
- The May 31 canonical-path landing intentionally rejected hidden fallback for
  migrated `aoa-memo` and `aoa-evals` surfaces.

## [0.2.3] - 2026-04-23

### Summary

- this patch expands the SDK control plane across Agon recurrence lanes,
  helper candidates, state-packet bindings, verdict-delta and sealed-commit
  helpers, duel-kernel bindings, mechanical-trial helpers, retention-rank
  helpers, KAG/Sophian helper surfaces, and typed Experience adoption APIs
- recurrence projections, reviewed-closeout carry, stats re-grounding,
  recursor readiness, Titan runtime harnesses, Titan incarnation CLI support,
  and Experience capture/deployment/watchtower/release helper contracts are
  hardened
- `aoa-sdk` remains a bounded typed access and orchestration layer for
  sibling-owned surfaces rather than a source-owning runtime or doctrine repo

### Added

- Agon recurrence adapter registry, Wave VII/IX recurrence lanes, state-packet
  SDK bridges, verdict-delta and sealed-commit helper candidates, duel-kernel
  SDK bindings, mechanical-trial helpers, retention-rank helpers,
  KAG/Sophian helpers, and Wave XV epistemic SDK helper surfaces
- recurrence control-plane seeds, graph/manifest compatibility inserts,
  downstream projections, live-observation producers, recursor readiness
  helpers, stats re-grounding policy, and source-ref-aware routing inspection
- Titan runtime harness surfaces, Titan incarnation spine runtime support, and
  Titan CLI gate handling
- Experience capture pipeline helpers plus certification, deployment,
  federation, adoption, governance, watchtower, rollback, release, dashboard,
  and ToS dossier API contracts

### Changed

- SDK review follow-ups, recurrence projection schemas, helper imports,
  closeout follow-through capture, helper contract inputs, wave3 typed
  adoption coverage, wave4 API contract coverage, stats re-grounding behavior,
  and Titan CLI gate handling were tightened for the current control-plane
  release line

### Validation

- `python scripts/release_check.py`

### Notes

- this patch changes control-plane helper behavior and release metadata only;
  sibling repositories remain authoritative for their own objects, evidence,
  roles, runtime records, and doctrine

## [0.2.2] - 2026-04-19

### Summary

- this patch hardens checkpoint review and quarantine flow, recurrence
  control-plane surfaces, and A2A summon planning helpers across the SDK
- memo writeback intake, release workflow safety, and roadmap/repo-contract
  surfaces are tightened without widening `aoa-sdk` into a runtime owner
- `aoa-sdk` remains the bounded control plane for sibling-owned AoA surfaces

### Added

- recurrence control-plane and hook-producer surfaces plus A2A summon planning
  helpers and end-to-end fixtures
- checkpoint auto-review, review carry, and closeout follow-through fixes
  across the active session-ledger path

### Changed

- checkpoint typing, memo writeback intake, required-check plus Node24
  workflow refs, and release-facing repo posture are tightened for the current
  control-plane wave

### Validation

- `python scripts/release_check.py`

### Notes

- this patch stays on the control plane: checkpoint orchestration,
  recurrence, and summon helpers are tightened without turning `aoa-sdk` into
  a source-owning runtime layer

## [0.2.1] - 2026-04-12

### Summary

- this patch hardens Codex-plane deploy-state reads, rollout reference
  boundaries, and continuity carry in the control plane
- closeout follow-through and release publish failure handling are tightened
  without widening `aoa-sdk` into a runtime owner
- the release remains a bounded control-plane refinement over `v0.2.0`

### Added

- Codex deploy-status snapshot surfaces and deploy-operation boundary guidance
  for the control plane.
- self-agency continuity carry and closeout follow-through mapping for
  checkpoint-driven rollout sessions.
- rollout campaign reference-boundary guidance so campaign refs stay explicit
  and local-first.

### Changed

- release-audit typing and deploy-status reads are hardened across the current
  Codex-plane rollout path.

### Fixed

- `aoa release publish` now treats GitHub Release lookup timeouts as an unknown remote state and aborts before tag mutation.
- checkpoint closeout execution now writes reports and reviewed artifacts into the same runtime-session-scoped ledger as the generated closeout context.

### Validation

- `python scripts/release_check.py`

### Notes

- this patch stays on the control plane: rollout references,
  continuity carry, and deploy-state reads are tightened without turning
  `aoa-sdk` into a source-owning runtime layer.

## [0.2.0] - 2026-04-10

### Summary

- this release adds a workspace control-plane capsule, first-class checkpoint lanes, closeout bridging, and thread-aware Codex session tracing
- checkpoint typing, registry guardrails, actor references, local-time reporting, and control-plane validation are hardened across CLI and generated outputs
- `aoa-sdk` remains the typed control-plane and orchestration layer rather than a runtime owner

### Validation

- `python scripts/release_check.py`

### Notes

- detailed source, schema, generated-surface, and operator-surface coverage for this release remains enumerated below under `Added`, `Changed`, and `Included in this release`

### Added

- workspace control-plane capsule plus compatibility tracking for center/root
  entry capsules and routing/stats ABI v2
- a first-class checkpoint lane with auto-captured skill-phase and
  commit-growth checkpoints, progression carry-through, and closeout execution
  bridging
- thread-aware Codex session tracing and runtime-identity scoping for
  checkpoint closeout

### Changed

- hardened checkpoint typing, registry guardrails, actor refs, and local-time
  reporting across CLI and generated outputs
- expanded docs, tests, and dev extras around checkpoint closeout and
  control-plane validation

### Included in this release

- control-plane and typed-consumer expansion across `src/`, `schemas/`,
  `generated/`, `scripts/`, and `systemd/`, including RPG and `aoa-stats`
  consumer slices, reviewed closeout submission flows, closeout publishers and
  watchers, surface detection, and the workspace control-plane capsule
- workspace, checkpoint, and operator surfaces across `docs/`, `README.md`,
  `AGENTS.md`, `.agents/`, `.github/`, `tests/`, and `pyproject.toml`,
  including portable bootstrap and ingress wrappers, foundation skill
  detection, via negativa and antifragility doctrine, and thread-aware
  checkpoint-closeout hardening

## [0.1.0] - 2026-04-01

First public baseline release of `aoa-sdk` as the typed Python SDK for the AoA federation.

This changelog entry uses the release-prep merge date.

### Summary

- first public baseline release of `aoa-sdk` as the local-first typed consumer and orchestration spine for source-owned AoA surfaces
- the live read path now covers `aoa-routing`, `aoa-skills`, `aoa-agents`, `aoa-playbooks`, `aoa-memo`, `aoa-evals`, and bounded `aoa-kag` inspect support
- the release also ships workspace discovery, source-checkout versus runtime-mirror topology handling, compatibility checks, skill session helpers, and CLI inspection surfaces

### Added

- seeded the repository from the initial `Dionysus` `aoa-sdk` starter artifacts
- the first package scaffold, boundary docs, workspace layout docs, versioning docs, and ecosystem impact docs
- the first live local-first read path to `aoa-routing`, `aoa-skills`, and `aoa-agents`
- sibling workspace discovery, typed surface loaders, skill session helpers, and isolated fixture-based tests
- the extended local-first read path to `aoa-playbooks`, `aoa-memo`, and `aoa-evals`
- an explicit per-surface compatibility policy, including versioned and versionless surface handling
- a tracked workspace manifest, environment overrides, and CLI inspection for source-checkout versus runtime-mirror topology

### Changed

- workspace discovery now prefers the git source checkout at `~/src/abyss-stack` over the deployed runtime mirror at `/srv/AbyssOS/abyss-stack`
- package and CLI version surfaces are now aligned to `0.1.0` for the first repository release

### Validation

- `pytest -q`
- `python -m ruff check .`
- `aoa workspace inspect /srv/AbyssOS/aoa-sdk`

### Notes

- this release keeps `aoa-sdk` on the control plane: typed loading, disclosure, compatibility, activation, and handoff helpers rather than runtime ownership
