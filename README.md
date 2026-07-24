# aoa-sdk

Typed Python SDK and control-plane helper layer for the AoA federation.

`aoa-sdk` consumes source-owned sibling surfaces and exposes local-first Python
and CLI handles for discovery, compatibility, routing, skill inspection,
checkpoint, closeout, release, and bounded handoff. It keeps federation state
legible without becoming the source of truth for sibling-layer meaning.

This README is the public front door. When work becomes operational,
source-authored, generated, mechanic-local, release-facing, or agent-facing,
follow the linked owner surface instead of expanding this page.

> Current release: `v0.5.1`. See [CHANGELOG](CHANGELOG.md) for release notes.

## What This Repository Does

| Function | Owner Surface |
| --- | --- |
| Repository boundary and stronger-owner stop lines | [docs/boundaries](docs/boundaries.md) |
| System form | [DESIGN](DESIGN.md) |
| Agent-facing guidance form | [DESIGN.AGENTS](DESIGN.AGENTS.md) |
| Local route law and executable checks | [AGENTS](AGENTS.md) and nearest nested `AGENTS.md` |
| Documentation map | [docs](docs/README.md) |
| Checked SDK source-home posture | [sdk](sdk/README.md), [source home manifest](sdk/source_home.manifest.json) |
| SDK-owned statistical questions | [stats](stats/README.md), [local stats port](stats/port.manifest.json) |
| Callable Titan helper procedures | [skills](skills/README.md), [owner skill port](skills/port.manifest.json) |
| Importable implementation | [src/aoa_sdk](src/aoa_sdk/AGENTS.md) |
| Repeatable SDK mechanics | [mechanics](mechanics/README.md), [mechanics roadmap](mechanics/ROADMAP.md), [mechanics topology](mechanics/topology.json) |
| Workspace discovery, source topology, and control-plane capsule | [workspace layout](docs/workspace-layout.md), [.aoa workspace](.aoa/workspace.toml), [generated source topology](generated/source_topology.min.json), [generated capsule](generated/workspace_control_plane.min.json) |
| Compatibility, release, and public support posture | [versioning](docs/versioning.md), [releasing](docs/RELEASING.md), [release and CI posture](docs/RELEASE_CI_POSTURE.md), [release support mechanic](mechanics/release-support/README.md) |
| Durable rationale | [decision records](docs/decisions/README.md) |
| Current direction and durable obligations | [ROADMAP](ROADMAP.md), [QUESTBOOK](QUESTBOOK.md), [quests](quests/README.md) |
| Seed history | [blueprint](docs/blueprint.md), the original seed blueprint and historical design context |

## Start Here

| Need | Route |
| --- | --- |
| Get the shortest repo overview | Stay on this README, then choose an owner surface from the tables. |
| Decide whether a change belongs in this repo | Read [docs/boundaries](docs/boundaries.md), [DESIGN](DESIGN.md), and the relevant source-home or mechanic card. |
| Work on SDK-facing source posture | Start at [sdk](sdk/README.md) and the nearest branch `AGENTS.md`. |
| Change an SDK-owned measurement question or reference packet | Start at [stats](stats/README.md) and [stats/AGENTS](stats/AGENTS.md); shared grammar remains in `aoa-stats`. |
| Change an SDK-owned Titan helper skill | Start at [skills](skills/README.md) and [skills/AGENTS](skills/AGENTS.md); runtime, operator, memory, proof, and playbook meaning remain with stronger owners. |
| Change importable Python behavior | Start at [src/aoa_sdk/AGENTS.md](src/aoa_sdk/AGENTS.md), then route to the owning tests or mechanic. |
| Change repeatable operations, helpers, schemas, examples, or part tests | Start at [mechanics](mechanics/README.md), then package `AGENTS.md`, package `README.md`, package `ROADMAP.md`, package `PARTS.md`, package `PROVENANCE.md`, and the active part `VALIDATION.md`. |
| Change workspace, compatibility, checkpoint, Codex projection, release, or closeout behavior | Follow the matching mechanic package route before changing root docs. |
| Change public support, release posture, or CI posture | Start at [docs/RELEASE_CI_POSTURE](docs/RELEASE_CI_POSTURE.md) and [mechanics/release-support](mechanics/release-support/README.md). |
| Change direction, obligation, or rationale | Use [ROADMAP](ROADMAP.md), [QUESTBOOK](QUESTBOOK.md), [quests](quests/README.md), and [decision records](docs/decisions/README.md). |
| Work as an agent | Read [AGENTS](AGENTS.md), then the nearest nested route card. |

## Common Mechanic Routes

| Pressure | Route |
| --- | --- |
| Stress dispatch, reviewed stress carry, and via negativa pruning | [mechanics/antifragility](mechanics/antifragility/README.md) |
| Sibling facades, compatibility, skill bridges, technique readers, surface hints, and owner-layer handoff | [mechanics/boundary-bridge](mechanics/boundary-bridge/README.md) |
| Checkpoint capture, review gates, closeout handoff, child-task re-entry, and reviewed carry | [mechanics/checkpoint](mechanics/checkpoint/README.md) |
| Codex workspace MCP, live rollout status, portability boundary, and rollout refs | [mechanics/codex-projection](mechanics/codex-projection/README.md) |
| Release audit, publication helpers, CI posture, and sibling canaries | [mechanics/release-support](mechanics/release-support/README.md) |
| RPG typed consumer reads and surface-path transport | [mechanics/rpg](mechanics/rpg/README.md) |
| Workspace roots, mirrors, bootstrap, and generated control-plane capsule | [mechanics/runtime-seam](mechanics/runtime-seam/README.md) |
| Durable obligation source records and quest reader posture | [mechanics/questbook](mechanics/questbook/README.md) |

## Control-Plane Check

| Question | Route |
| --- | --- |
| Who owns the meaning? | Usually the sibling repo or a stronger owner named in [docs/boundaries](docs/boundaries.md). |
| What does `aoa-sdk` own? | Typed handles, route cards, local checks, generated read models, and bounded helper behavior. |
| What proves the change? | The nearest part `VALIDATION.md`, root [AGENTS](AGENTS.md), and the touched test route. |
| Is this activation, durable memory, proof, progression, gameplay, or runtime deployment? | Route away from SDK helper authority unless the source owner has already made the meaning explicit. |

## Current Contour

The current landed surface includes:

- workspace discovery grounded in [.aoa/workspace.toml](.aoa/workspace.toml);
- root design surfaces, [DESIGN](DESIGN.md) and [DESIGN.AGENTS](DESIGN.AGENTS.md);
- canonical decision rationale under [docs/decisions](docs/decisions/README.md);
- the checked SDK source-home tree under [sdk](sdk/README.md);
- the SDK-owned compatibility posture measurement under [stats](stats/README.md);
- the admitted Titan helper procedure home under [skills](skills/README.md);
- the accepted, not-yet-active staged routing producer succession in
  [AOA-SDK-D-0071](docs/decisions/AOA-SDK-D-0071-staged-routing-producer-succession.md)
  and its
  [target operating model](mechanics/boundary-bridge/parts/consumed-surface-posture-gate/docs/routing-succession-r1-target-operating-model.md);
- active mechanics topology under [mechanics](mechanics/README.md) with
  future-pressure routing in [mechanics roadmap](mechanics/ROADMAP.md);
- typed compatibility and workspace inspection helpers;
- the compact control-plane capsule at
  [generated/workspace_control_plane.min.json](generated/workspace_control_plane.min.json);
- the generated implementation tree index at
  [generated/source_topology.min.json](generated/source_topology.min.json);
- bounded skill inspection, surface-detection, checkpoint, closeout, Codex projection,
  release, and public support helpers.

Detailed shipped-surface maps live in [mechanics](mechanics/README.md),
[sdk](sdk/README.md), generated companions, decision indexes, and release
history. Package-local future pressure lives in mechanics package roadmaps.
[ROADMAP](ROADMAP.md) keeps direction at the repo level. The root README should not become that inventory.

## Core Districts

| District | Use For |
| --- | --- |
| [.aoa](.aoa/) | Workspace metadata consumed by SDK discovery. |
| [docs](docs/README.md) | Documentation map, boundaries, release route, versioning, seed history, and decision records. |
| [evals](evals/) | SDK-local eval pressure intake, suites, and reports before adoption by `aoa-evals`. |
| [generated](generated/) | Derived read models and compact control-plane companions. |
| [mechanics](mechanics/) | Repeatable SDK operations with package and part ownership. |
| [sdk](sdk/) | Source-authored SDK posture and manifest-checked route map. |
| [stats](stats/) | SDK-owned measurement questions and evidence-linked reference packets using the shared `aoa-stats` grammar. |
| [skills](skills/) | Admitted callable procedures over SDK-owned Titan helper contracts; globally exposed only through the OS user profile. |
| [src/aoa_sdk](src/aoa_sdk/) | Importable Python package and public API implementation. |
| [schemas](schemas/) | Shared contract schemas used across SDK surfaces. |
| [quests](quests/) | Source records for durable SDK obligations. |
| [tests](tests/) | Repo-wide regression and route-contract tests. |

## Validation

Executable validation routes live in [AGENTS](AGENTS.md#verify), nearest nested
`AGENTS.md`, and part `VALIDATION.md` files. Release gates live in
[docs/RELEASING](docs/RELEASING.md) and
[mechanics/release-support](mechanics/release-support/README.md).

Use this README to choose the route, not to run the route.

## Downstream Consumers

The SDK is useful to agents and humans that need a typed, local-first view over
AoA workspace state. It must remain subordinate to sibling repositories for
source truth:

- sibling generated readers stay source-owned;
- SDK compatibility checks are posture checks, not source verdicts;
- checkpoint and closeout helpers carry reviewed context without becoming
  durable memory or proof authority;
- release helpers describe or dry-run SDK release posture until GitHub,
  package, and owner surfaces actually publish.

## License

Licensed under the [Apache License 2.0](LICENSE).
