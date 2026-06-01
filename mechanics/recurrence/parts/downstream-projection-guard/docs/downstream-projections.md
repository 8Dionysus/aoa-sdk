# Recurrence Downstream Projections

The recurrence control plane can now emit narrow downstream packets for three consumer lanes.

## Lanes

### `aoa-routing`

Receives:

- owner hints;
- return hints;
- gap hints.

It does not receive full graph traversal, recurrence authority, or source meaning. Hints are marked `advisory_only: true`.

### `aoa-stats`

Receives:

- component coverage counts;
- connectivity gap counts;
- beacon pressure counts;
- review queue counts;
- review decision counts.

Its `surface_strength` is fixed to `derived_observability_only`.

### `aoa-kag`

Receives:

- donor refresh obligations;
- retrieval invalidation hints;
- source strength hints;
- regrounding modes.

It does not author source truth or widen recurrence into a hidden graph sovereign.

## Guard report

Every bundle includes `DownstreamProjectionGuardReport`. Block publication when the guard report contains `blocked` or `critical` violations.

The guard is deliberately posture-focused. It does not judge owner truth. It checks that downstream projection boundaries are not being melted into authority transfer.
