# Mechanic Artifact Localization

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0007
- Original date: 2026-05-31
- Surface classes: topology, mechanics, artifact placement, validation guard
- SDK facets: mechanics topology, artifact localization, part-local validation, root technical districts
- Mechanic parents: agon
- Guard families: mechanics topology, nested agents, generated parity, part validation
- Posture: accepted

## Context

`AOA-SDK-D-0004` created a route-only mechanics skeleton. `AOA-SDK-D-0005`
corrected the parent boundary. `AOA-SDK-D-0006` made source-family routing
explicit.

That still left mechanic-owned payload in root technical districts. For Agon
recurrence adapter work, the active config, docs, schemas, generated
companions, scripts, tests, and quest records were single-mechanic and
single-part owned. Keeping them in root made the active route less legible and
kept old root paths stronger than the mechanic topology.

## Options Considered

- Keep root technical districts as the active home and treat mechanics as
  route cards only.
- Move all Agon files in one broad sweep before part contracts exist.
- Start controlled localization with one functioning part that has a local
  contract, validation route, and migration ledger.

## Decision

Start part-local mechanic artifact localization with
`mechanics/agon/parts/recurrence-adapter/`.

The Agon recurrence adapter and prebinding review-lane payload moves from
root technical districts into the functioning part home:

- `config/` -> `mechanics/agon/parts/recurrence-adapter/config/`
- `docs/` -> `mechanics/agon/parts/recurrence-adapter/docs/`
- `schemas/` -> `mechanics/agon/parts/recurrence-adapter/schemas/`
- `generated/` -> `mechanics/agon/parts/recurrence-adapter/generated/`
- `scripts/` -> `mechanics/agon/parts/recurrence-adapter/scripts/`
- `tests/` -> `mechanics/agon/parts/recurrence-adapter/tests/`
- `quests/` source-record placement is superseded by `AOA-SDK-D-0042`;
  helper contracts stay part-local while durable quest source records live in
  root `quests/<lane>/<state>/`.

Root technical districts remain valid only for public, repo-wide, shared,
cross-mechanic, or tooling-facing contracts. Old root paths are migration
evidence, not active fallback routes.

## Rationale

The recurrence adapter has a complete local operation boundary:

- role: candidate-only Agon recurrence adapter and prebinding review lanes;
- input: local seed configs and public-safe recurrence review examples;
- output: deterministic compact generated registries;
- owner: `aoa-sdk` for the adapter shape, stronger Agon owners for meaning;
- next route: Agon owner review for stronger claims;
- validation: part-local builders, validators, tests, and mechanics topology.

That makes it a better first localization slice than a broad name-based move.
It proves the pattern without moving importable `src/aoa_sdk/` source or
turning mechanics into a second Python package home.

## Consequences

- `mechanics/` is no longer only a skeleton surface.
- The first functioning part now has `README.md`, `CONTRACT.md`, and
  `VALIDATION.md`.
- `mechanics/ARTIFACT_TOPOLOGY.md` becomes the placement law and migration
  ledger for future root-to-part moves.
- Validators now check functioning part directories when they exist.
- Remaining root Agon helper files are not accepted as final; they require
  follow-up localization or a documented root ownership reason.

## Source Surfaces

- `mechanics/ARTIFACT_TOPOLOGY.md`
- `mechanics/topology.json`
- `mechanics/README.md`
- `mechanics/AGENTS.md`
- `mechanics/agon/PARTS.md`
- `mechanics/agon/parts/AGENTS.md`
- `mechanics/agon/parts/recurrence-adapter/README.md`
- `mechanics/agon/parts/recurrence-adapter/CONTRACT.md`
- `mechanics/agon/parts/recurrence-adapter/VALIDATION.md`
- `scripts/validate_mechanics_topology.py`
- `scripts/validate_nested_agents.py`

## Follow-Up Route

Continue localizing remaining single-mechanic-owned root artifacts through
`mechanics/ARTIFACT_TOPOLOGY.md`.

`AOA-SDK-D-0009` resolves the next Agon helper candidates as functioning
part-local routes. Recurrence manifests and shared recurrence examples still
need owner review before moving, because their nearest active owner may be
`recurrence` rather than `agon`.

## Verification

```bash
python scripts/generate_decision_indexes.py --check
python scripts/validate_mechanics_topology.py
python mechanics/agon/parts/recurrence-adapter/scripts/build_agon_recurrence_adapter_registry.py --check
python mechanics/agon/parts/recurrence-adapter/scripts/validate_agon_recurrence_adapter.py
python mechanics/agon/parts/recurrence-adapter/scripts/build_agon_recurrence_prebinding_review_lanes.py --check
python mechanics/agon/parts/recurrence-adapter/scripts/validate_agon_recurrence_prebinding_review_lanes.py
python -m pytest -q mechanics/agon/parts/recurrence-adapter/tests/test_agon_recurrence_adapter.py mechanics/agon/parts/recurrence-adapter/tests/test_agon_recurrence_prebinding_review_lanes.py tests/test_mechanics_topology.py tests/test_validate_nested_agents.py
```
