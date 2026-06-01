# Sibling Fallback Field Input Alias Normalization

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0040
- Original date: 2026-06-01
- Surface classes: active naming, typed model, sibling surface, compatibility input
- SDK facets: routing stats reader, playbook reader, active naming, compatibility posture
- Mechanic parents: boundary-bridge
- Guard families: active naming, compatibility alias, sibling owner boundary, part validation
- Posture: accepted

## Context

The SDK consumes sibling-owned generated surfaces from `aoa-routing` and
`aoa-playbooks`. Those external fixtures still contain `fallback_actions` and
`fallback_mode` fields.

Inside `aoa-sdk`, the same names were exposed as active model fields. That made
the SDK public readout sound like it owned fallback routes, even though the SDK
is only reading sibling surfaces and presenting their route posture to local
callers.

## Decision

Normalize the SDK-owned active model names:

- `RoutingStatsRegroundingHint.fallback_actions` becomes
  `secondary_actions`;
- `PlaybookCard.fallback_mode` becomes `recovery_mode`;
- `PlaybookActivationSurface.fallback_mode` becomes `recovery_mode`.

Keep the old sibling keys as validation aliases only, so current sibling
generated JSON remains readable without emitting stale fallback names from SDK
models.

## Rationale

The active SDK surface should name the current route role, not the historical or
neighboring vocabulary. `secondary_actions` says these are additional explicit
inspection actions after the primary regrounding action. `recovery_mode` says
how the playbook handles recovery posture.

This follows the mechanics refactor naming rule: old or weaker vocabulary may
exist as provenance, compatibility input, or legacy accounting, but active
SDK-owned fields must be route-bearing and self-describing.

## Consequences

- `src/aoa_sdk/models.py` exposes `secondary_actions` and `recovery_mode`.
- Existing sibling fixtures with `fallback_actions` or `fallback_mode` remain
  valid compatibility input through aliases.
- Boundary Bridge consumed-surface tests prove the SDK model dumps do not emit
  the old fallback keys.

## Source Surfaces

- `src/aoa_sdk/models.py`
- `src/aoa_sdk/routing/hints.py`
- `src/aoa_sdk/routing/picker.py`
- `src/aoa_sdk/playbooks/registry.py`
- `mechanics/boundary-bridge/parts/consumed-surface-posture-gate/`

## Follow-Up Route

If sibling owners later rename their generated fields, prefer updating fixtures
and compatibility policy together. Do not restore fallback vocabulary as an
active SDK output field.

## Verification

```bash
python -m pytest -q mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_routing_surface_actions.py mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_playbook_surface_reader.py
python -m ruff check src/aoa_sdk/models.py mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_routing_surface_actions.py mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_playbook_surface_reader.py
```
