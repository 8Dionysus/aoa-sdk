# SDK Source Home Tree

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0043
- Original date: 2026-06-01
- Surface classes: topology, source home, agent route cards, validation
- SDK facets: sdk source home, public interface, facade boundary, runtime entry, distribution
- Mechanic parents: boundary-bridge, checkpoint, codex-projection, release-support, runtime-seam
- Guard families: source topology, nested agents, manifest validation, root route law
- Posture: accepted

## Context

The earlier design rule rejected a top-level `sdk/` folder because it could
become cosmetic symmetry with sibling source homes such as `agents/`, `memo/`,
`evals/`, `skills/`, and `techniques/`.

After the mechanics refactor, that rule became too flat. `aoa-sdk` now has
strong operation topology under `mechanics/`, but it still needs a visible
home for SDK-owned posture that is not the Python implementation tree and not
the mechanics layer.

Sibling source homes are tree-shaped and route-card driven. They do not merely
collect files; they expose role, owner, branches, source families, validation,
and stop-lines.

## Options Considered

- Keep SDK posture only in root docs and `src/aoa_sdk/`.
- Add a flat `sdk/` folder with a few route files.
- Add `sdk/` as a tree-shaped, manifest-checked source home.

## Decision

Add `sdk/` as the source-authored SDK home.

The initial branches are:

- `sdk/public-interface/`;
- `sdk/facade-boundary/`;
- `sdk/runtime-entry/`;
- `sdk/distribution/`.

Each branch has a local `AGENTS.md` and `README.md`. The home has
`sdk/AGENTS.md`, `sdk/README.md`, `sdk/SDK_SHAPE.md`, and
`sdk/source_home.manifest.json`.

Add `scripts/validate_sdk_source_home.py` and run it from
`scripts/release_check.py`.

Do not add `PARTS.md` to `sdk/`. In this repository, `parts` is mechanics
vocabulary and belongs under `mechanics/<parent>/parts/<part>/`.

## Rationale

The SDK needs an obvious organ for its own posture:

- public API, CLI, and typed model promises;
- sibling facade and truth-label boundaries;
- runtime entry posture for workspace, Codex, and reviewed closeout;
- package, release, and public support promises.

Putting that in `src/aoa_sdk/` would confuse implementation with source-home
route law. Putting it in `mechanics/` would confuse operation topology with SDK
identity. A checked `sdk/` tree gives agents a direct route without moving
behavior out of its owning surface.

## Consequences

- `DESIGN.md` now treats `sdk/` as the SDK source home and `src/aoa_sdk/` as
  the importable Python implementation lane.
- `DESIGN.AGENTS.md` includes `sdk/` branch cards in the protected local card
  mesh.
- `scripts/validate_nested_agents.py` requires the new SDK route cards.
- `scripts/validate_sdk_source_home.py` verifies the manifest, branches,
  families, README routes, owner surfaces, and route targets.
- Future SDK source-home additions need branch/family manifest coverage and
  validation, not cosmetic folders.

## Source Surfaces

- `sdk/AGENTS.md`
- `sdk/README.md`
- `sdk/SDK_SHAPE.md`
- `sdk/source_home.manifest.json`
- `scripts/validate_sdk_source_home.py`
- `DESIGN.md`
- `DESIGN.AGENTS.md`
- `scripts/validate_nested_agents.py`
- `scripts/release_check.py`

## Follow-Up Route

Future source-home branches route through `sdk/source_home.manifest.json`,
nearest `sdk/**/AGENTS.md`, and `scripts/validate_sdk_source_home.py` before
they touch implementation or mechanics.

## Verification

The executable decision-index and owning-surface checks are routed through
`docs/decisions/AGENTS.md` and the nearest source-owner validation surface.
