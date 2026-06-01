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
promoted too many SDK-local file-family lanes into parent mechanics. Those
former names now live in package-local legacy indexes instead of active route
maps.

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

Demote the over-specific first-pass parents into topological part routes:

| Active parent | Active route |
| --- | --- |
| `runtime-seam` | `runtime-seam/workspace-root-resolution` |
| `runtime-seam` | `runtime-seam/portable-workspace-bootstrap` |
| `runtime-seam` | `runtime-seam/control-plane-capsule` |
| `runtime-seam` | `runtime-seam/runtime-mirror-boundary` |
| `boundary-bridge` | `boundary-bridge/consumed-surface-posture-gate` |
| `boundary-bridge` | `boundary-bridge/skill-runtime-bridge` |
| `boundary-bridge` | `boundary-bridge/owner-layer-signal-handoff` |
| `checkpoint` | `checkpoint/session-growth-checkpoint-cycle` |
| `checkpoint` | `checkpoint/reviewed-session-handoff-runner` |
| `checkpoint` | `checkpoint/child-task-reentry` |
| `checkpoint` | `checkpoint/reviewed-closeout-context-carry` |
| `codex-projection` | `codex-projection/workspace-mcp-server` |
| `codex-projection` | `codex-projection/live-rollout-status-readout` |

## Rationale

This matches the sibling-source rule:

- top-level mechanics name repeatable operations, not topic buckets;
- file-name cluster pressure routes through `PARTS.md`;
- shared names stay shared when the operation is the same AoA shape;
- repo-local mechanics need evidence stronger than a local API or docs family.

`runtime-seam` and `codex-projection` are not new local inventions. They come
from the refactored `aoa-agents` mechanics vocabulary and fit SDK surfaces
better than file-family parent buckets.

`antifragility` and `questbook` were missing from the first SDK skeleton even
though the repository already had real antifragility docs/fixtures and a root
`quests/` source store.

## Consequences

- The SDK mechanics tree is smaller and closer to the shared AoA parent
  vocabulary.
- SDK-specific routes stay visible as parts instead of becoming parallel axes.
- Decision `AOA-SDK-D-0004` is superseded for parent package shape, but remains
  useful as the record of the first inventory-based landing.
- Validators now fail if former parent names reappear as top-level packages or
  active topology maps.
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
