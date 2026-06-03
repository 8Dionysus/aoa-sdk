# Mechanics Roadmap Router And Package Contours

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0049
- Original date: 2026-06-02
- Surface classes: mechanics, route-law, roadmap, validation
- SDK facets: mechanics topology, roadmap, control-plane routing
- Mechanic parents: agon, antifragility, boundary-bridge, checkpoint, codex-projection, experience, questbook, recurrence, release-support, rpg, runtime-seam, titan
- Guard families: roadmap drift, mechanics topology, root-surface hygiene
- Posture: accepted

## Context

After root `ROADMAP.md` was refactored into repo-level direction, the next
unresolved pressure was mechanics future routing. `mechanics/README.md` already
owned the package atlas, and `mechanics/topology.json` already owned the active
machine map. Neither surface should become a future backlog.

Refactored sibling repositories show the same split in different shapes:

- repo root roadmaps own repo-level direction;
- root mechanics maps and cards route package entry;
- package roadmaps or direction files carry package-local future contours;
- package `PARTS.md`, `PROVENANCE.md`, and part `VALIDATION.md` keep active
  maps, source accounting, and executable checks separate.

Without a mechanics roadmap layer, future package pressure would drift back
into root `ROADMAP.md`, package `README.md`, or package `PARTS.md`.

## Options Considered

- Leave mechanics without roadmaps and rely on package `README.md` prose.
- Add only a root `mechanics/ROADMAP.md` router.
- Add a mechanics router and require package `ROADMAP.md` files for all active
  mechanics packages.

## Decision

Add `mechanics/ROADMAP.md` as the mechanics-wide future-pressure router and
add package `ROADMAP.md` files for every active mechanics package.

The mechanics router owns package future-pressure routing and mechanics-wide
stop lines. Package roadmaps own package-local current contour, next work,
condition-based future contours, and stop lines.

Update route cards, root entry surfaces, and the mechanics topology validator
so these roadmaps are required route surfaces rather than decorative files. The
package update rule belongs in route law and validators; it should not be
repeated as an identical tail inside every package roadmap.

## Rationale

`aoa-sdk` has many functioning part-local helpers. Their shipped inventories
belong in package cards, `PARTS.md`, generated companions, changelog, and
topology data. Future-facing pressure needs a different home: short enough for
agents to read before editing, but local enough not to pollute root direction.

A root-only mechanics roadmap would still centralize package future pressure.
Package roadmaps prevent that by putting future contours next to the owning
operation while keeping validation commands in `AGENTS.md` and part
`VALIDATION.md`.

## Consequences

- `mechanics/README.md` stays the atlas.
- `mechanics/ROADMAP.md` becomes the mechanics-wide future-pressure router.
- Every active mechanics package has a required `ROADMAP.md`.
- Package `README.md` files remain entry cards instead of future backlogs.
- Package `PARTS.md` files remain active part maps instead of roadmap ledgers.
- Package `PROVENANCE.md` files remain source accounting.
- Package `ROADMAP.md` files stay symmetrical with the center mechanic role:
  current contour, next work, condition-based future movement, and stop lines.
- `scripts/validate_mechanics_topology.py` and route tests now require the new
  roadmap layer.

## Source Surfaces

- `mechanics/ROADMAP.md`
- `mechanics/*/ROADMAP.md`
- `mechanics/README.md`
- `mechanics/AGENTS.md`
- `mechanics/topology.json`
- `scripts/validate_mechanics_topology.py`
- `tests/test_mechanics_topology.py`
- `README.md`
- `ROADMAP.md`
- `docs/README.md`

## Follow-Up Route

Future package changes should update only the owning package roadmap when
future pressure changes. Checked landings should continue through the owning
source surface, part route, `PARTS.md`, `PROVENANCE.md`, topology data,
changelog, and validation routes as needed.

## Verification

```bash
python scripts/generate_decision_indexes.py --check
python scripts/validate_mechanics_topology.py
python -m pytest -q tests/test_mechanics_topology.py tests/test_design_surfaces.py tests/test_docs_routes.py
```
