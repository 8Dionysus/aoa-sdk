# Admit the 8Dionysus Public Route Map v3 With Strict Shape

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0102
- Original date: 2026-08-21
- Surface classes: compatibility, ci, owner-boundary
- SDK facets: compatibility, release support, public support
- Mechanic parents: boundary-bridge, release-support
- Guard families: compatibility drift, source-owner boundary
- Posture: accepted

## Context

The live `Latest Sibling Canary` for `aoa-sdk` failed at the current
`8Dionysus` main because its public route map advanced from
`8dionysus_public_route_map_v2` to `8dionysus_public_route_map_v3`. The owning
`8Dionysus` change keeps the route-map-only surface and the existing route
fields, while adding the dashboard route and an explicit v3 schema.

The SDK compatibility rule still admitted only v2 and did not enforce the
declared route-map top-level shape. Merely accepting every v3 payload would
hide malformed sibling output and weaken the canary.

## Options Considered

- Keep v2 only and leave the current sibling canary failed.
- Accept v3 by version string alone.
- Admit v2 and v3 through the SDK compatibility gate, requiring the declared
  route-map top-level shape for v3 while preserving the historical v2 shape.

## Decision

Keep v2 compatibility, including the previously accepted minimal v2 payload,
and admit v3 only when the public route map contains the explicit schema,
owner, surface, authority, posture, validation, and routes fields. The SDK
records consumability; `8Dionysus` remains the owner of route-map meaning,
generation, freshness, and validation.

The SDK does not downgrade v3, rewrite sibling payloads, or infer route
semantics. A missing required field remains a canary failure.

## Rationale

The live v3 artifact and its owner schema retain the v2 route-only posture, but
the SDK cannot impose v3 fields on historical v2 payloads. The additive
dashboard route is source-owned meaning; the SDK recognizes the versioned
envelope and enforces the v3 shape only for v3. This restores an honest canary
without converting a version label into semantic approval or breaking legacy
consumers.

## Consequences

- The current v3 sibling artifact is compatible with the SDK gate.
- Historical minimal v2 route maps remain covered by a regression test.
- Malformed v3-shaped payloads fail closed on missing top-level fields.
- Future route meaning or schema changes still require an owner-first
  `8Dionysus` change followed by an SDK compatibility update.

## Source Surfaces

- `src/aoa_sdk/compatibility/policy.py`
- `mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_consumed_surface_compatibility_gate.py`
- `tests/fixtures/workspace/8Dionysus/generated/public_route_map.min.json`
- `mechanics/release-support/parts/public-support-ci-posture/scripts/run_sibling_canary.py`
- `.github/workflows/latest-sibling-canary.yml`

## Follow-Up Route

When `8Dionysus` changes the public route-map schema or route semantics again,
verify the owner schema and generated artifact first, then update this SDK
compatibility gate and its fixture/regression battery. Do not weaken the
scheduled canary to conceal an unsupported or malformed surface.

## Verification

Run the consumed-surface posture tests, the part-local sibling canary against
the live workspace, the local stats-port validator, and the root decision-index
and mechanics-topology checks.
