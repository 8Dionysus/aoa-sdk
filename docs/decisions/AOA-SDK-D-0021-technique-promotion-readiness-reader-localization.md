# Technique Promotion Readiness Reader Localization

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0021
- Original date: 2026-06-01
- Surface classes: topology, mechanics, artifact placement, validation guard
- SDK facets: mechanics topology, Boundary Bridge, techniques facade
- Mechanic parents: boundary-bridge
- Guard families: mechanics topology, part validation, active naming, owner boundary
- Posture: accepted

## Context

After the technique publication observation-boundary slice, root `tests/` still
held `tests/test_techniques.py`. The test is not a repo-wide regression: it
checks one SDK facade over the `aoa-techniques` promotion-readiness generated
surface.

The importable source stays in `src/aoa_sdk/techniques/`. The test payload
belongs in a Boundary Bridge part because the SDK reads owner-authored technique
status without owning technique meaning.

## Decision

Move the root test into:

- `mechanics/boundary-bridge/parts/technique-promotion-readiness-reader/`

Keep `src/aoa_sdk/techniques/` as the importable SDK source family and route
source changes through Boundary Bridge.

## Rationale

The active part name is intentionally specific. It says the input
(`aoa-techniques` promotion readiness), the operation (reader), and the owner
boundary (Boundary Bridge). It does not imply technique promotion, review, or
distillation authority inside `aoa-sdk`.

## Consequences

- Root `tests/` no longer carries the single-facade technique readiness
  regression.
- Boundary Bridge part docs now make the `aoa-techniques` stop-line explicit.
- Technique status, blockers, canonicalization, and promotion remain owned by
  `aoa-techniques`.

## Source Surfaces

- `mechanics/boundary-bridge/README.md`
- `mechanics/boundary-bridge/PARTS.md`
- `mechanics/boundary-bridge/PROVENANCE.md`
- `mechanics/boundary-bridge/parts/technique-promotion-readiness-reader/`
- `src/aoa_sdk/techniques/`
- `mechanics/ARTIFACT_TOPOLOGY.md`
- `mechanics/topology.json`

## Follow-Up Route

Continue root technical district audit for Checkpoint test placement, Questbook
payload, and cross-mechanic public contracts.

## Verification

```bash
python -m pytest -q mechanics/boundary-bridge/parts/technique-promotion-readiness-reader/tests/test_technique_promotion_readiness_reader.py tests/test_mechanics_topology.py
python scripts/validate_mechanics_topology.py
python scripts/release_check.py
```
