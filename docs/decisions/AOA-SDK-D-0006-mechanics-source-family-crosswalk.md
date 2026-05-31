# Mechanics Source Family Crosswalk

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0006
- Original date: 2026-05-31
- Surface classes: topology, mechanics, validation guard, source inventory
- SDK facets: mechanics topology, source family routing, parent boundary, boundary bridge
- Mechanic parents: boundary-bridge, checkpoint, codex-projection, recurrence, release-support, rpg, runtime-seam, titan
- Guard families: source topology, mechanics topology, release check
- Posture: accepted

## Context

`AOA-SDK-D-0005` corrected the parent-mechanic set, but a follow-up audit found
that parent correctness alone is not enough. Several real `src/aoa_sdk/*`
families were named in the `boundary-bridge` package card, but were not present
in `mechanics/topology.json` source surfaces:

- `governed_runs`
- `kag`
- `loaders`
- `playbooks`
- `techniques`

Those source families do not justify new parent mechanics. They are typed
facades, loaders, or sibling-surface readers. The missing piece was a durable
crosswalk proving where every source family routes.

## Options Considered

- Leave the parent set as the only topology guard.
- Promote unmapped source families into new parent mechanics.
- Add an explicit source-family crosswalk and validate it against the live
  `src/aoa_sdk/` tree.

## Decision

Add `source_family_routes` to `mechanics/topology.json`.

Every current `src/aoa_sdk/*` family, plus root-package files, must have a
primary mechanic route. The validator now checks that:

- each live source family is present in the crosswalk;
- each crosswalk entry points to an existing parent mechanic;
- the primary mechanic lists the source family in `source_surfaces`;
- each entry includes a reason.

The crosswalk routes sibling facade families, KAG readers, governed-run readers,
technique readiness readers, playbook readers, shared loaders, root models, and
CLI command facade surfaces through `boundary-bridge` unless a stronger parent
already owns the operation.

## Rationale

The purpose is to separate two questions that were previously blurred:

- Does a source family exist?
- Does it have independent parent-mechanic pressure?

In this repo, many source families are stable typed access surfaces over
sibling-owned truth. That is `boundary-bridge` pressure, not a reason to create
`kag`, `playbooks`, `techniques`, `loaders`, or `governed-runs` as SDK parent
mechanics.

## Consequences

- The corrected 12-parent mechanics set remains unchanged.
- Future source-family additions must be routed explicitly.
- `boundary-bridge` source surfaces now list every sibling facade and loader
  family it claims.
- The mechanics validator can now catch both over-promoted parents and
  unmapped SDK source families.

## Source Surfaces

- `mechanics/topology.json`
- `mechanics/TOPOLOGY_PREP.md`
- `mechanics/README.md`
- `mechanics/boundary-bridge/README.md`
- `mechanics/boundary-bridge/PARTS.md`
- `mechanics/boundary-bridge/PROVENANCE.md`
- `scripts/validate_mechanics_topology.py`
- `tests/test_mechanics_topology.py`

## Follow-Up Route

If a new `src/aoa_sdk/*` family appears, update `source_family_routes` in the
same change. Only promote it to a parent mechanic if it has an independent
operation, owner split, stop-line, and validator that cannot honestly live as a
part of an existing shared parent.

## Verification

```bash
python scripts/generate_decision_indexes.py --check
python scripts/validate_mechanics_topology.py
python -m pytest -q tests/test_mechanics_topology.py
```
