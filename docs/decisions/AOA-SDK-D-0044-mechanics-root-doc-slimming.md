# Mechanics Root Doc Slimming

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0044
- Original date: 2026-06-02
- Surface classes: topology, mechanics, validation, route-law
- SDK facets: mechanics topology, route cards, validation authority
- Mechanic parents: all
- Guard families: root-surface hygiene, mechanics topology, nested agents
- Posture: accepted

## Context

The mechanics topology had already moved from an inventory-derived skeleton to
an active part-localized map. `mechanics/topology.json`, package cards, package
`PROVENANCE.md`, and part `VALIDATION.md` now carry the active route.

The root docs still kept two migration-era surfaces:
`mechanics/TOPOLOGY_PREP.md` and `mechanics/ARTIFACT_TOPOLOGY.md`. They made
the root mechanics layer read like a prep report plus migration ledger even
though current work should enter through the atlas, machine map, package card,
part contract, and focused validator.

## Options Considered

- Keep the prep and ledger docs as active root surfaces.
- Keep the files but rewrite them into short historical notes.
- Retire the files and make the active route explicit in the atlas, route
  cards, topology map, provenance cards, and validator.

## Decision

Retire `mechanics/TOPOLOGY_PREP.md` and `mechanics/ARTIFACT_TOPOLOGY.md` from
the active mechanics root.

Root `mechanics/` now keeps the human atlas, local route law, machine topology
map, and minimal pytest glue. Former-path accounting routes through package
`PROVENANCE.md` and package-local `legacy/` indexes. Executable part proof
routes through part `VALIDATION.md`, with `mechanics/topology.json` retaining
the active validation route list.

## Rationale

The active mechanics root should answer the current operational question:
which package owns this pressure, which part is active, what source surface is
stronger, and what validator proves the route.

Prep reports and migration ledgers made future agents reread old derivation
instead of following current owner surfaces. Removing them aligns `aoa-sdk`
with the cleaner mechanics atlases in the refactored sibling repos while
preserving durable rationale in decision records and old-path lookup in
package provenance.

## Consequences

- `mechanics/README.md` becomes the root mechanics entry surface.
- `mechanics/topology.json` remains the active machine-readable map.
- `scripts/validate_mechanics_topology.py` no longer requires retired root
  report files or stale inventory text.
- Package README files point to part `VALIDATION.md` and the topology map
  instead of embedding long command blocks.
- Historical references in decisions and changelog remain historical context,
  not active route authority.

## Source Surfaces

- `mechanics/README.md`
- `mechanics/AGENTS.md`
- `mechanics/topology.json`
- `scripts/validate_mechanics_topology.py`
- `mechanics/*/README.md`
- `mechanics/*/PROVENANCE.md`
- `mechanics/*/parts/*/VALIDATION.md`

## Follow-Up Route

Future mechanics growth should update the package card, part contract,
package provenance, topology map, and validator in one slice. Do not recreate
root prep reports or migration ledgers.

## Verification

```bash
python scripts/generate_decision_indexes.py --check
python scripts/validate_mechanics_topology.py
python scripts/validate_nested_agents.py
python -m pytest -q tests/test_mechanics_topology.py tests/test_validate_nested_agents.py tests/test_docs_routes.py tests/test_design_surfaces.py
```
