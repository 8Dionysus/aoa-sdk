# Mechanics Skeleton After Inventory

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0004
- Original date: 2026-05-31
- Surface classes: topology, mechanics, route card, validation guard
- SDK facets: mechanics topology, control-plane, source inventory, agent surface
- Mechanic parents: workspace-topology, compatibility, boundary-bridge, skill-routing, surface-detection, checkpoint, closeout, recurrence, agon, titan, experience, a2a-return, rpg, codex-plane, release-support
- Guard families: source topology, mechanics topology, nested agents, release check
- Posture: accepted

## Context

The refactored AoA repositories use `mechanics/` to make repeatable operations
reviewable without making every source file live inside the mechanic package.
`aoa-sdk` needed the same topology layer, but the SDK has a different owner
shape: it is the typed control-plane consumer, not a domain source owner.

The repo already had 1000 tracked files across source, docs, schemas,
examples, generated companions, scripts, manifests, quests, route cards, and
tests. Introducing mechanics by copying sibling package names alone would have
created cosmetic topology instead of explaining the SDK's real operation
pressure.

## Options Considered

- Keep mechanics deferred and continue relying on root docs plus source
  clusters.
- Add only shared AoA mechanics copied from sibling repositories.
- Create an SDK-local `sdk/` top-level district before mechanics.
- Add a route-only `mechanics/` skeleton after full file inventory, with shared
  names where the operation is the same and SDK-local names where the SDK owns
  a distinct control-plane operation.

## Decision

Add `mechanics/` now as a route-only operation topology skeleton.

The first skeleton names 15 packages:

- `workspace-topology`
- `compatibility`
- `boundary-bridge`
- `skill-routing`
- `surface-detection`
- `checkpoint`
- `closeout`
- `recurrence`
- `agon`
- `titan`
- `experience`
- `a2a-return`
- `rpg`
- `codex-plane`
- `release-support`

Each package gets an `AGENTS.md`, `README.md`, `PARTS.md`, and
`PROVENANCE.md`. The root gets `mechanics/README.md`,
`mechanics/TOPOLOGY_PREP.md`, `mechanics/topology.json`, and a validator.

No source payload moves in this landing.

## Rationale

The SDK's real recurring operations are cross-surface routes: typed source,
docs, schemas, examples, generated companions, scripts, tests, compatibility,
checkpoint/closeout, and handoff artifacts. Mechanics make those routes
visible without making the SDK a source owner for sibling meaning.

Shared names stay shared where the recurring operation is the same AoA shape:
`boundary-bridge`, `checkpoint`, `recurrence`, `agon`, `titan`,
`experience`, `rpg`, and `release-support`.

SDK-local names are used where the operation exists because this repo is the
control-plane SDK: `workspace-topology`, `compatibility`, `skill-routing`,
`surface-detection`, `a2a-return`, and `codex-plane`.

This keeps the earlier source-home decision intact: `src/aoa_sdk/` remains the
importable Python source home, and no top-level `sdk/` district is added by
cosmetic analogy.

## Consequences

- Future agents can route changes by operation before editing scattered source
  surfaces.
- Mechanics package cards can name triggers, SDK ownership, stronger owners,
  stop-lines, and validation routes.
- Release checks now fail if the mechanics skeleton drifts from its topology
  map.
- The skeleton adds many route files, but avoids moving payload before a later
  package-local reason and validator exist.
- `mechanics/` becomes active topology, while payload still lives in the
  existing source, docs, schema, example, generated, script, manifest, quest,
  and test lanes.

## Source Surfaces

- `mechanics/README.md`
- `mechanics/TOPOLOGY_PREP.md`
- `mechanics/topology.json`
- `mechanics/*/AGENTS.md`
- `mechanics/*/README.md`
- `mechanics/*/PARTS.md`
- `mechanics/*/PROVENANCE.md`
- `scripts/validate_mechanics_topology.py`
- `scripts/validate_nested_agents.py`
- `scripts/release_check.py`
- `tests/test_mechanics_topology.py`
- `AGENTS.md`
- `DESIGN.md`
- `DESIGN.AGENTS.md`
- `README.md`
- `ROADMAP.md`
- `docs/boundaries.md`
- `CHANGELOG.md`

## Follow-Up Route

If a later change moves payload into a mechanic package, add or update the
package-local rationale, package-local validator, compatibility route, and
tests in the same landing.

## Verification

```bash
python scripts/generate_decision_indexes.py --check
python scripts/validate_mechanics_topology.py
python scripts/validate_nested_agents.py
python -m pytest -q tests/test_mechanics_topology.py tests/test_validate_nested_agents.py
```
