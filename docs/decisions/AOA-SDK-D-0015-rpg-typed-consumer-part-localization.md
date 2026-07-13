# RPG Typed Consumer Part Localization

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0015
- Original date: 2026-06-01
- Surface classes: topology, mechanics, artifact placement, validation guard
- SDK facets: mechanics topology, RPG, typed consumer API, surface path transport
- Mechanic parents: rpg
- Guard families: mechanics topology, part validation, docs routes, active naming
- Posture: accepted

## Context

After the Antifragility localization slice, RPG still carried
single-mechanic payload in root districts:

- `docs/RPG_SDK_ADDENDUM.md`
- `docs/RPG_SURFACE_PATHS.md`
- `tests/test_rpg_api.py`

These files are not repo-wide contracts. They describe SDK-local RPG consumer
behavior: typed Python reads over owner surfaces and expected upstream
generated transport paths.

The importable SDK source remains `src/aoa_sdk/rpg/`. Moving docs and tests
must not imply that gameplay, frontend, runtime, quest, progression, proof, or
RPG doctrine moved into `aoa-sdk`.

## Decision

Localize RPG root docs and API tests into two functioning part homes:

- `mechanics/rpg/parts/typed-consumer-api/`
- `mechanics/rpg/parts/surface-path-transport/`

Keep `src/aoa_sdk/rpg/` as the importable SDK implementation package and route
it through the RPG mechanic in `mechanics/topology.json`.

## Rationale

Active names should show the operation map. `RPG_SDK_ADDENDUM.md` and
`RPG_SURFACE_PATHS.md` were topic titles and root locations. The new part
names say what the SDK actually owns:

- `typed-consumer-api` loads owner RPG surfaces into stable Python objects
- `surface-path-transport` records expected generated paths, collection
  wrappers, and fragment refs

This keeps RPG as a shared parent mechanic without creating a local parent or
moving importable source out of `src/aoa_sdk`.

## Consequences

- Root `docs/` and `tests/` no longer own active RPG payload.
- Old RPG root paths live in `mechanics/rpg/PROVENANCE.md` and
  `mechanics/ARTIFACT_TOPOLOGY.md`, not as active fallbacks.
- RPG part-local tests keep API behavior and path routing visible.
- Runtime/gameplay/frontend/progression/quest semantics remain with stronger
  owners.

## Source Surfaces

- `src/aoa_sdk/rpg/`
- `mechanics/rpg/README.md`
- `mechanics/rpg/PARTS.md`
- `mechanics/rpg/PROVENANCE.md`
- `mechanics/rpg/parts/`
- `mechanics/ARTIFACT_TOPOLOGY.md`
- `mechanics/topology.json`
- `README.md`

## Follow-Up Route

Continue root technical district audit for closeout/checkpoint carry,
questbook, release-support, and cross-mechanic public contracts.

## Verification

The executable decision-index and owning-surface checks are routed through
`docs/decisions/AGENTS.md` and the nearest source-owner validation surface.
