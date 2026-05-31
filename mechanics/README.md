# aoa-sdk Mechanics

Status: skeleton.

`mechanics/` names repeatable SDK operations that already span several
repository districts. It does not move payload out of `src/aoa_sdk/`, `docs/`,
`schemas/`, `examples/`, `generated/`, `scripts/`, or `tests/`.

The skeleton exists so future work can ask a narrower question: which
operation is changing, what does the SDK own, what stronger owner remains
outside, and which validator proves the crossing?

## Source Basis

This topology was derived from the tracked `aoa-sdk` file inventory:

- 1000 tracked files.
- 20 top-level districts or singleton root surfaces.
- 356 JSON files, 286 Markdown files, and 240 Python files.
- active source clusters under `src/aoa_sdk/` for recurrence, A2A, Titan,
  skills, workspace, RPG, surfaces, stats, routing, Codex, release,
  compatibility, checkpoint, closeout, and sibling facades.
- matching schema, example, generated, script, manifest, quest, and test
  families for recurrence, Agon, Titan, Experience APIs, checkpoint/closeout,
  A2A return, workspace, and release support.

The detailed inventory and derivation rules live in
[`TOPOLOGY_PREP.md`](TOPOLOGY_PREP.md). The machine-readable package map lives
in [`topology.json`](topology.json).

## Package Registry

| Mechanic | Name type | Operation |
| --- | --- | --- |
| [`workspace-topology`](workspace-topology/README.md) | SDK-local | workspace root, sibling lookup, runtime mirror, and control-plane capsule topology |
| [`compatibility`](compatibility/README.md) | SDK-local | consumed sibling-surface compatibility and canonical-path drift checks |
| [`boundary-bridge`](boundary-bridge/README.md) | shared | typed facade owner split between SDK handles and sibling meaning |
| [`skill-routing`](skill-routing/README.md) | SDK-local | portable skill discovery, disclosure, activation, and phase-aware dispatch |
| [`surface-detection`](surface-detection/README.md) | SDK-local | additive owner-layer surface detection and reviewed handoff |
| [`checkpoint`](checkpoint/README.md) | shared | session checkpoint capture, review-note gates, and closeout context bridge |
| [`closeout`](closeout/README.md) | shared | reviewed session closeout request, inbox, manifest, and owner followthrough |
| [`recurrence`](recurrence/README.md) | shared | recurrence manifests, hooks, graph, review, projections, and live observations |
| [`agon`](agon/README.md) | shared | Agon SDK helper candidates, registries, quests, and candidate-only helper packs |
| [`titan`](titan/README.md) | shared | Titan runtime harness, console, appserver, memory, session, and swarm helpers |
| [`experience`](experience/README.md) | shared | Experience API helper contracts and adoption/deployment/governance calls |
| [`a2a-return`](a2a-return/README.md) | SDK-local | A2A summon, checkpoint, reviewed closeout, and return packet bridge |
| [`rpg`](rpg/README.md) | shared | RPG typed consumer slice and surface path helper boundary |
| [`codex-plane`](codex-plane/README.md) | SDK-local | Codex workspace MCP, deploy-status reads, portability, and rollout refs |
| [`release-support`](release-support/README.md) | shared | changelog, release audit, CI posture, build, and publication gates |

## Skeleton Contract

Every package in this skeleton has:

- `AGENTS.md` for local route law.
- `README.md` for the operation card.
- `PARTS.md` for candidate sub-operations.
- `PROVENANCE.md` for current source surfaces and stronger-owner notes.

The package cards use a common shape:

- Operation
- Trigger
- SDK owns
- Stronger owner split
- Current source surfaces
- Candidate parts
- Must not claim
- Validation
- Next route

## Shared Versus SDK-Local Names

Shared names are kept when the SDK operation is the same recurring AoA
mechanic shape already visible in refactored sibling repositories:
`boundary-bridge`, `checkpoint`, `recurrence`, `agon`, `titan`,
`experience`, `rpg`, and `release-support`.

SDK-local names are used where the operation is specific to the SDK control
plane: `workspace-topology`, `compatibility`, `skill-routing`,
`surface-detection`, `a2a-return`, and `codex-plane`.

## Validation

```bash
python scripts/validate_mechanics_topology.py
python -m pytest -q tests/test_mechanics_topology.py
```

The validator checks the package registry, package files, required card
sections, root topology map, source-surface references, and nested route-card
registration.
