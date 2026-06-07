# AoA SDK Roadmap

This roadmap tracks repo-level direction for `aoa-sdk` as the typed control
plane for the AoA federation.

Use it when the question is "what direction should shape the next SDK-layer
change?", not "which shipped surface should I open?"

Use `docs/blueprint.md` only as the original seed blueprint and historical
design context.

## Authority

Root `ROADMAP.md` owns:

- repo-level SDK direction;
- current control-plane contract hardening posture;
- source-home, mechanics, compatibility, workspace, release-support, and
  generated-capsule pressure when that pressure changes the whole repo contour;
- concrete future triggers that belong to `aoa-sdk`.

It does not own release history, mechanic-local roadmaps, checked mechanic
landings, decision rationale, generated truth, sibling meaning, quest state,
proof verdicts, memory objects, routing policy, role policy, playbook law, or
runtime implementation.

Use the stronger surface when the change is narrower:

- public entry and route choice: [README](README.md);
- route law and executable checks: [AGENTS](AGENTS.md), then the nearest
  nested `AGENTS.md`;
- system form: [DESIGN](DESIGN.md);
- agent-facing guidance form: [DESIGN.AGENTS](DESIGN.AGENTS.md);
- docs entry and placement: [docs README](docs/README.md);
- boundaries: [docs/boundaries](docs/boundaries.md);
- workspace topology: [docs/workspace-layout](docs/workspace-layout.md) and
  [.aoa/workspace](.aoa/workspace.toml);
- compatibility posture: [docs/versioning](docs/versioning.md);
- SDK source-home posture: [sdk](sdk/README.md) and
  `sdk/source_home.manifest.json`;
- operation topology: [mechanics](mechanics/README.md), [mechanics roadmap](mechanics/ROADMAP.md),
  parent route cards, parent `ROADMAP.md`, parent `PARTS.md`, parent
  `PROVENANCE.md`, and part `VALIDATION.md`;
- release history: [CHANGELOG](CHANGELOG.md);
- durable rationale: [docs/decisions](docs/decisions/README.md) and generated
  `docs/decisions/indexes/`;
- durable obligations: [QUESTBOOK](QUESTBOOK.md) and [quests](quests/README.md).

## Update Rule

Update this roadmap only when a change moves repo-level SDK direction,
control-plane posture, source-home topology, mechanics-to-source interface,
workspace or compatibility posture, release-support direction, generated
capsule posture, or a concrete future trigger.

Do not update it for local mechanic landings, generated refreshes, release
notes, decision records, quest lifecycle moves, package-local artifact
relocation, or validator maintenance unless that local change alters
repo-level direction.

Before closeout, ask: did this change move the SDK's direction, or did it only
land a local surface?

## Operating Card

| Field | Route |
| --- | --- |
| input | SDK-layer pressure, direction changes, horizon order, or public-contour changes |
| output | direction, horizon posture, future trigger, or owner-route pressure |
| owner | root roadmap for direction; source, mechanics, decisions, generated companions, and release docs for detail |
| next route | [sdk](sdk/README.md), [mechanics](mechanics/README.md), [mechanics roadmap](mechanics/ROADMAP.md), [docs](docs/README.md), [generated capsule](generated/workspace_control_plane.min.json), then nearest local route card |
| validation | [AGENTS.md#verify](AGENTS.md#verify), plus route-specific tests when roadmap contracts move |

## Current Direction

`aoa-sdk` is past seed bootstrap. The current post-`v0.4.0` direction is
control-plane contract hardening.

The repo should now:

- keep root entry surfaces compact enough to trust;
- keep `README.md` as the public front door and `ROADMAP.md` as direction, not
  shipped-surface inventory;
- keep `docs/README.md` as the docs entry map and `docs/blueprint.md` as seed
  history;
- keep source-authored SDK posture in `sdk/` while `src/aoa_sdk/` remains the
  importable implementation;
- keep repeatable SDK operations in `mechanics/`;
- keep generated companions subordinate to source docs, builders, validators,
  and local route cards;
- keep workspace discovery explicit through `.aoa/workspace.toml`,
  `docs/workspace-layout.md`, and `generated/workspace_control_plane.min.json`;
- keep compatibility checks explicit and source-subordinate;
- keep `aoa skills enter` / `aoa skills guard`, `aoa surfaces detect`,
  checkpoint capture, review-note, and explicit reviewed-session handoff runner
  surfaces bounded and weaker than owner truth;
- keep typed Codex Projection reads and release audit and publish helpers below
  rollout, release, and sibling-owner authority.

The main near-term risk is roadmap drift: shipped workspace, compatibility,
Codex, checkpoint, closeout, release, and mechanics surfaces must stay
discoverable, but their full inventories belong in `docs/README.md`,
`CHANGELOG.md`, `mechanics/`, generated companions, part route cards, and
decision indexes rather than in this roadmap.

Roadmap drift is an SDK-layer risk because downstream agents use this file to
choose whether a change belongs on the control plane. It still must not turn
`aoa-sdk` into a source-owning runtime layer.

The next honest move is not to widen the SDK into a second owner layer.
It is to keep the control plane small, explicit, testable, and source-
subordinate while cross-repo growth becomes denser.

## Current Public Contour

Current release marker: `v0.4.0`.

Current unreleased contour: control-plane contract hardening after `v0.4.0`.
This is a directional contour, not a changelog replacement.

Current anchors:

| Anchor | Surface | Directional use |
| --- | --- | --- |
| Root entry and route law | `README.md`, `AGENTS.md`, `docs/README.md` | Keep entry, commands, and docs wayfinding separate. |
| System and agent-facing form | `DESIGN.md`, `DESIGN.AGENTS.md` | Keep SDK shape, source-home posture, and guidance mesh explicit. |
| Decision rationale | `docs/decisions/README.md`, `docs/decisions/indexes/` | Keep route-law and topology rationale findable without manual rosters. |
| Workspace control plane | `.aoa/workspace.toml`, `docs/workspace-layout.md`, `generated/workspace_control_plane.min.json` | Keep source checkouts, runtime mirrors, and generated capsule posture aligned. |
| Compatibility posture | `docs/versioning.md` and compatibility checks | Keep consumed sibling surfaces explicit, versioned where possible, and fail-closed on drift. |
| SDK source home | `sdk/README.md`, `sdk/source_home.manifest.json`, `src/aoa_sdk/` | Keep public SDK posture separate from importable implementation. |
| Mechanics atlas | `mechanics/README.md`, `mechanics/ROADMAP.md`, `mechanics/topology.json`, parent cards, parent roadmaps, part `VALIDATION.md` | Keep operation detail and package future pressure local while root watches repo-wide direction. |
| Bounded helpers | skill guards, surface detection, checkpoint and closeout route cards | Keep loaded, suggested, manual-equivalent, and activated states visibly separate. |
| Release support | `docs/RELEASING.md`, `docs/RELEASE_CI_POSTURE.md`, release-support parts | Keep release preflight, CI posture, sibling canaries, audit, and publish helpers subordinate to owner truth. |

## Horizons

### Horizon: Root Clarity

| Field | Direction |
| --- | --- |
| Current posture | `README.md`, `AGENTS.md`, `DESIGN.md`, `DESIGN.AGENTS.md`, `ROADMAP.md`, `docs/README.md`, and `docs/boundaries.md` now have separate jobs. |
| Next honest move | Keep root surfaces as entry, route law, shape, agent-facing shape, direction, docs map, and boundaries. Move inventories to changelog, docs maps, generated readers, mechanics, or decisions. |
| Guardrail | Root docs must not become archives of every part, validator, release note, or session. |

### Horizon: Source Home And Implementation

| Field | Direction |
| --- | --- |
| Current posture | `sdk/` is the checked source-authored SDK posture tree; `src/aoa_sdk/` is the importable Python implementation. |
| Next honest move | Keep public-interface, facade-boundary, runtime-entry, and distribution posture tied to `sdk/source_home.manifest.json`, source tests, and decision rationale. |
| Guardrail | `sdk/` must not become a second implementation tree, and `src/aoa_sdk/` must not absorb sibling meaning. |

### Horizon: Mechanics Atlas

| Field | Direction |
| --- | --- |
| Current posture | `mechanics/` owns repeatable SDK operations across compatibility, runtime seams, checkpoint, release support, Codex projection, RPG, questbook, recurrence, antifragility, Agon, Experience, and Titan helper boundaries. |
| Next honest move | Let `mechanics/ROADMAP.md`, package route cards, package `ROADMAP.md`, `PARTS.md`, `PROVENANCE.md`, part READMEs, and part `VALIDATION.md` files carry local detail and package future pressure while root watches only repo-wide direction. |
| Guardrail | Mechanics route operation pressure; they do not become source-owned sibling truth, proof verdicts, memory objects, playbooks, or runtime workers. |

### Horizon: Workspace And Compatibility

| Field | Direction |
| --- | --- |
| Current posture | Workspace discovery, runtime mirror separation, canonical sibling paths, and compatibility posture are explicit and test-backed. |
| Next honest move | Keep canonical owner paths current, remove hidden fallback behavior, and make any new consumed surface enter through the compatibility map. |
| Guardrail | Local convenience must not turn stale sibling paths or runtime mirrors into source truth. |

### Horizon: Bounded Handoff Helpers

| Field | Direction |
| --- | --- |
| Current posture | Skill guards, surface detection, checkpoint notes, reviewed closeout carry, owner followthrough hints, and reviewed-session handoff runner surfaces are available as bounded helper routes. |
| Next honest move | Preserve truth labels and owner-subordination while making handoff evidence easier to inspect and validate. |
| Guardrail | No helper silently becomes activation, progression, proof, durable memory, routing, or runtime authority. |

### Horizon: Release And Support

| Field | Direction |
| --- | --- |
| Current posture | Root release docs are thin route doors; detailed runbook, public support posture, sibling canaries, release audit, and publish helpers live in release-support parts. |
| Next honest move | Keep public claims aligned across README, changelog, release docs, release-support parts, generated companions, and GitHub validation. |
| Guardrail | No roadmap history as changelog truth, no support claim without release-support route, and no publish claim before actual publication. |

## When The Time Comes

These are repo-level triggers that should wait for real evidence:

- Add a new consumed sibling surface only after the owner path, compatibility
  mode, validator, and typed read posture are clear.
- Widen CLI or orchestration breadth only after existing workspace,
  compatibility, and truth-label helpers stay green under sibling drift.
- Promote a helper closer to activation only after the source owner has named
  the meaning and rollback/approval posture.
- Add a new mechanic parent only when an existing parent would become less
  clear by owning the pressure.
- Add broader remote adapter or MCP/A2A behavior only after local-first
  contracts remain stable.

An item belongs here only when its trigger is concrete and repo-wide. If the
future pressure is mechanic-local, use the owning mechanic package. If it is a
durable obligation, use `QUESTBOOK.md` and `quests/`.

## Standing Direction

Across all horizons:

- stay on the control plane;
- keep source-owned meaning in sibling repositories;
- keep root documents compact and route-bound;
- keep source, generated, runtime, and compatibility surfaces distinct;
- prefer manifest-driven, test-backed behavior over hidden heuristics;
- keep rollout, checkpoint, and closeout helpers explicit about what they can
  read, suggest, or execute;
- do not let convenience helpers impersonate routing, memory, playbook, eval,
  role, stats, KAG, or runtime authority.
