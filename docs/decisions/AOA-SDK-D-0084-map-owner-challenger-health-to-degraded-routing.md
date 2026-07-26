# Map Owner Challenger Health to Degraded Routing

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0084
- Original date: 2026-07-26
- Surface classes: route law, owner projection, compatibility, agent trial
- SDK facets: control-plane, public interface, facade boundary
- Mechanic parents: boundary-bridge
- Guard families: owner provenance, lifecycle health, fail closed, versioned behavior
- Posture: accepted

## Context

The first T1 installed-wheel smoke used the receipt-bound SDK-canonical
runtime mirror and the exact pinned live `aoa-skills` capability graph. The
snapshot validated, nine candidates were explained, and fallback remained
false, but resolver v1 blocked every route.

The leading `aoa-decision` candidate carried the owner-authored lifecycle:

```text
state: candidate
visibility: advertised
evidence_state: pilot-verified
health: challenger
```

The `aoa-skills` lifecycle schema requires `challenger` as one of five health
values. Its admitted lifecycle review deliberately keeps `aoa-decision` as
the only advertised challenger without promoting it to `active/healthy`.
Resolver v1 recognized only `healthy` and `degraded`, so it mislabeled the
valid owner value as `owner_health_missing_or_unrecognized` and made the live
control plane unusable.

## Decision

Introduce `aoa_control_plane_route_resolver_v2`.

- `healthy` remains compatible.
- `challenger` becomes degraded with reason
  `owner_health_challenger`.
- `degraded` remains degraded with reason `owner_health_degraded`.
- missing, unknown, unavailable, or retired health remains incompatible.
- lifecycle, visibility, binding, effect, approval, negative-applicability,
  and explicit-capability gates remain unchanged.

A v2 decision selected from challenger health must itself be `degraded`.
Neither the SDK nor an agent may report the owner capability as healthy,
active, verified, or beneficial from this mapping.

## Rejected Alternatives

- Mark the owner capability healthy in an SDK projection.
- Treat every non-empty health string as compatible.
- Keep v1 and require a fake `healthy` fixture for Agent OS trials.
- Change behavior without a resolver version because C1 is still unreleased.

The first two absorb owner authority or weaken fail-closed behavior. The third
hides a real live incompatibility. The fourth would make old-versus-new trial
evidence and later replay ambiguous.

## Consequences

- Positive: the exact advertised owner challenger is usable through an
  explicit degraded result.
- Positive: unknown or unavailable health still cannot become a route.
- Positive: old-versus-new live behavior is attributable to separate resolver
  versions.
- Tradeoff: consumers that require strictly compatible decisions must still
  reject the challenger until its owner promotes it.
- Tradeoff: selection is navigation evidence only; T1 still must prove
  fresh-context usability and task outcomes separately.

## Source Surfaces

- `src/aoa_sdk/control_plane/routing/resolver.py`
- `mechanics/boundary-bridge/parts/route-resolution-control-plane/`
- `repo:aoa-skills/schemas/capability_family.schema.json`
- `repo:aoa-skills/docs/reviews/2026-07-15-capability-family-lifecycle.md`

## Verification

Run the C1 focused suite with healthy, challenger, degraded, missing, unknown,
and unavailable owner health. Rebuild an installed wheel and repeat the exact
live smoke against the SDK-canonical runtime mirror. Record both v1 and v2
typed results before any fresh-context agent trial.
