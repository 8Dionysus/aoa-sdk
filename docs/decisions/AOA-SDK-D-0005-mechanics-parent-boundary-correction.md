# Mechanics Parent Boundary Correction

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0005
- Original date: 2026-05-31
- Surface classes: topology, mechanics, route card, validation guard
- SDK facets: mechanics topology, parent boundary, source inventory, agent surface
- Mechanic parents: agon, antifragility, boundary-bridge, checkpoint, codex-projection, experience, questbook, recurrence, release-support, rpg, runtime-seam, titan
- Guard families: source topology, mechanics topology, nested agents, release check
- Posture: accepted

## Context

The first SDK mechanics skeleton correctly avoided moving payload, but it
promoted too many SDK-local file-family lanes into parent mechanics:

- `workspace-topology`
- `compatibility`
- `skill-routing`
- `surface-detection`
- `closeout`
- `a2a-return`
- `codex-plane`

After rereading live mechanics sources in `Agents-of-Abyss`, `aoa-agents`,
`aoa-memo`, `aoa-evals`, `aoa-skills`, and `aoa-techniques`, the pattern is
clearer: parent mechanics are repeatable operations in the shared AoA
vocabulary. Narrow repo-local lanes sit under `PARTS.md` and part-local route
cards unless they have independent operation pressure, owner split, stop-line,
and validator.

## Options Considered

- Keep the 15-package skeleton and rely on package prose to explain the
  hierarchy.
- Keep SDK-local parent names but mark them as lower-level parents.
- Correct the topology now: use shared parent names and demote narrow SDK lanes
  into parts.

## Decision

Correct `aoa-sdk` mechanics to 12 top-level parent packages:

- `agon`
- `antifragility`
- `boundary-bridge`
- `checkpoint`
- `codex-projection`
- `experience`
- `questbook`
- `recurrence`
- `release-support`
- `rpg`
- `runtime-seam`
- `titan`

Demote the over-specific first-pass parents:

| Former parent candidate | Correct route |
| --- | --- |
| `workspace-topology` | `runtime-seam/workspace-root-resolution` |
| `compatibility` | `boundary-bridge/compatibility-policy` |
| `skill-routing` | `boundary-bridge/skill-runtime-bridge` |
| `surface-detection` | `boundary-bridge/surface-detection-handoff` |
| `closeout` | `checkpoint/closeout-bridge` |
| `a2a-return` | `checkpoint/return-reentry` |
| `codex-plane` | `codex-projection/deploy-status` |

## Rationale

This matches the sibling-source rule:

- top-level mechanics name repeatable operations, not topic buckets;
- file-name cluster pressure routes through `PARTS.md`;
- shared names stay shared when the operation is the same AoA shape;
- repo-local mechanics need evidence stronger than a local API or docs family.

`runtime-seam` and `codex-projection` are not new local inventions. They come
from the refactored `aoa-agents` mechanics vocabulary and fit SDK surfaces
better than `workspace-topology` and `codex-plane`.

`antifragility` and `questbook` were missing from the first SDK skeleton even
though the repository already had real antifragility docs/fixtures and a root
`quests/` source store.

## Consequences

- The SDK mechanics tree is smaller and closer to the shared AoA parent
  vocabulary.
- SDK-specific routes stay visible as parts instead of becoming parallel axes.
- Decision `AOA-SDK-D-0004` is superseded for parent package shape, but remains
  useful as the record of the first inventory-based landing.
- Validators now fail if demoted parent candidates reappear as top-level
  packages.
- No payload moves in this correction.

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
- `tests/test_mechanics_topology.py`
- `docs/decisions/AOA-SDK-D-0004-mechanics-skeleton-after-inventory.md`

## Follow-Up Route

If a future SDK-local parent mechanic is proposed, first show why it cannot be
represented as a part of `boundary-bridge`, `checkpoint`, `runtime-seam`,
`codex-projection`, `release-support`, or another shared parent.

## Verification

```bash
python scripts/generate_decision_indexes.py --check
python scripts/validate_mechanics_topology.py
python scripts/validate_nested_agents.py
python -m pytest -q tests/test_mechanics_topology.py tests/test_validate_nested_agents.py
```
