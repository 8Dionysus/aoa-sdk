# Root Roadmap Direction Surface

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0048
- Original date: 2026-06-02
- Surface classes: docs, route-law, roadmap, validation
- SDK facets: root docs, roadmap, control-plane routing
- Mechanic parents: release-support
- Guard families: roadmap drift, root-surface hygiene, docs routes
- Posture: accepted

## Context

Root `ROADMAP.md` still carried a long `Current unreleased contour` with
part-local file inventories. That made the roadmap act partly as changelog,
partly as release-support surface inventory, and partly as mechanics map.

The refactored sibling roadmaps with the cleanest shape separate those roles:

- `ROADMAP.md` owns repo-level direction, update rules, horizons, and future
  triggers.
- `CHANGELOG.md` owns released history and release-prep reconciliation.
- `docs/README.md`, mechanics cards, generated companions, and decision
  indexes own detailed lookup.

## Options Considered

- Keep the long current-contour inventory and update it after every docs or
  mechanics landing.
- Remove current contour entirely.
- Keep current contour as compact directional anchors, with detail routed to
  owner surfaces.

## Decision

Refactor root `ROADMAP.md` into an explicit direction surface:

- add `Authority`, `Update Rule`, and `Operating Card`;
- keep current direction and current public contour;
- move detailed shipped-surface inventory out of roadmap body expectations;
- express future movement as horizons and concrete triggers;
- keep roadmap validation focused on direction anchors, not every part-local
  file path.

## Rationale

The roadmap is useful when it tells a future agent what kind of change belongs
next and which owner surface carries detail. It becomes fragile when it tries
to mirror changelog entries, release support surfaces, generated companions,
and mechanics parts.

`aoa-sdk` has many part-local helpers. Listing all of them in root roadmap
recreates the same drift pressure recently removed from changelog and decision
README prose. Direction anchors keep discoverability without making the root
roadmap a second inventory.

## Consequences

- Root roadmap now follows the route-law shape used by the strongest
  refactored repositories.
- Local mechanics detail routes through `mechanics/`, generated companions,
  part cards, and release-support docs.
- Release-support tests assert directional anchors rather than requiring the
  roadmap to list every active part-local surface.
- Mechanics-roadmap work can start from a cleaner root contract and should
  keep package-local future pressure out of root roadmap inventory.

## Source Surfaces

- `ROADMAP.md`
- `README.md`
- `mechanics/release-support/parts/public-support-ci-posture/tests/test_public_support_ci_posture.py`
- `docs/decisions/README.md`
- `docs/decisions/indexes/`

## Follow-Up Route

The follow-up route is `mechanics/ROADMAP.md` plus package
`mechanics/<package>/ROADMAP.md` files. They should carry mechanics-wide and
package-local future pressure without forcing root `ROADMAP.md` to become a
mechanics inventory.

## Verification

The executable decision-index and owning-surface checks are routed through
`docs/decisions/AGENTS.md` and the nearest source-owner validation surface.
