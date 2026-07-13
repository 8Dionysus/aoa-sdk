# Surface Registry Route-Role Branches

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0054
- Original date: 2026-06-03
- Surface classes: source-topology, boundary-bridge, implementation, validation
- SDK facets: importable implementation, surface detection, owner-layer handoff
- Mechanic parents: boundary-bridge, checkpoint
- Guard families: source topology, owner-layer signal handoff, checkpoint session-growth
- Posture: accepted

## Context

`src/aoa_sdk/surfaces/registry.py` had the right public entrypoint, but it was
not only the `SurfacesAPI` facade. It also owned skill-to-item derivation,
heuristic owner-layer item construction, enrichment from shortlist, stats, and
skill receipts, checkpoint candidate clusters, progression-axis hints,
reviewed closeout handoff targets, and checkpoint note lookup.

That mixture made the owner-layer signal handoff route hard to enter safely.
The risk was not just file size: advisory surface hints could turn into hidden
policy if future behavior landed in the registry without a named owner branch.

## Options Considered

- Leave `registry.py` as the single surface detection implementation module.
- Split only the largest helper functions.
- Move `SurfacesAPI` into a new public module.
- Keep `SurfacesAPI` stable and split internals by route role.

## Decision

Keep `src/aoa_sdk/surfaces/registry.py` as the public `SurfacesAPI` facade and
route-role orchestrator.

Move surface implementation helpers into named branches:

- `surfaces/items.py` owns surface opportunity item derivation and merging.
- `surfaces/context.py` owns session, routing shortlist, stats regrounding, and
  skill receipt context loading and enrichment.
- `surfaces/checkpoint_candidates.py` owns checkpoint candidate clusters,
  lineage hints, promotion posture, explicit mutation growth, and checkpoint
  note refs.
- `surfaces/progression.py` owns progression-axis signals and movement
  adjustment.
- `surfaces/closeout_handoff.py` owns reviewed closeout handoff assembly,
  followups, owner-layer notes, surviving checkpoint clusters, and handoff
  targets.
- `surfaces/common.py` owns only small shared type aliases and pure helpers.
- `surfaces/heuristics.py` remains the deterministic heuristic rule owner.

## Rationale

The split follows the Boundary Bridge part boundary:
`owner-layer-signal-handoff` exposes advisory detection reports and reviewed
handoff packets, while sibling repos keep skill, eval, memo, playbook, agent,
technique, stats, and routing meaning.

Checkpoint-facing candidates remain provisional session-growth material. They
do not become memory truth, proof verdicts, progression movement, quest
acceptance, owner approval, or hidden closeout execution.

Branch names tell an agent where behavior belongs before they open the public
facade. The generated source topology remains a read model and does not
replace source files, tests, route cards, or this rationale.

## Consequences

- Public imports stay stable: `aoa_sdk.surfaces.SurfacesAPI` remains the
  entrypoint.
- `registry.py` no longer owns broad helper families.
- New surface detection behavior should land in the branch that owns its route
  role.
- Receipt enrichment tests now target `surfaces/context.py` instead of a
  private helper inside the facade.
- Future changes must preserve the advisory boundary before strengthening any
  candidate, progression, or handoff behavior.

## Source Surfaces

- `src/aoa_sdk/surfaces/registry.py`
- `src/aoa_sdk/surfaces/items.py`
- `src/aoa_sdk/surfaces/context.py`
- `src/aoa_sdk/surfaces/checkpoint_candidates.py`
- `src/aoa_sdk/surfaces/progression.py`
- `src/aoa_sdk/surfaces/closeout_handoff.py`
- `src/aoa_sdk/surfaces/common.py`
- `src/aoa_sdk/surfaces/heuristics.py`
- `mechanics/boundary-bridge/parts/owner-layer-signal-handoff/`
- `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/`
- `generated/source_topology.min.json`
- `tests/test_source_topology_index.py`

## Follow-Up Route

Keep `registry.py` thin. Add new behavior to the named surface branch that
owns the route role, and route stronger claims back to the owning sibling or
checkpoint closeout path.

## Verification

The executable decision-index and owning-surface checks are routed through
`docs/decisions/AGENTS.md` and the nearest source-owner validation surface.
