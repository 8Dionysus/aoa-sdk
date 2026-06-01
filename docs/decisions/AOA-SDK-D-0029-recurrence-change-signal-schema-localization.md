# Recurrence Change Signal Schema Localization

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0029
- Original date: 2026-06-01
- Surface classes: topology, mechanics, artifact placement, schema
- SDK facets: mechanics topology, recurrence, component manifest gate
- Mechanic parents: recurrence
- Guard families: mechanics topology, schema placement, active naming
- Posture: accepted

## Context

After recurrence payload localization, `schemas/change_signal.schema.json`
remained in the root schema district. The schema is not a repo-wide public
contract like the workspace control-plane capsule. It describes the recurrence
change signal produced by manifest-registry matching and consumed downstream by
observations, beacon pressure, review surfaces, and wiring handoffs.

## Decision

Move the schema into:

- `mechanics/recurrence/parts/component-manifest-gate/schemas/change_signal.schema.json`

Keep `schemas/workspace-control-plane.schema.json` at root because it is the
root-published schema for `generated/workspace_control_plane.min.json`.

## Rationale

`component-manifest-gate` owns the first boundary where changed paths are
matched to recurrence components. Downstream recurrence parts consume the
result, but they do not own the matching contract. The part-local path makes
the schema owner, input route, and validation home explicit.

## Consequences

- Root `schemas/` now carries root-published schemas only.
- The change signal schema has a part-local `$id`.
- Old root schema path remains provenance only in the artifact ledger and
  recurrence provenance.

## Source Surfaces

- `mechanics/recurrence/parts/component-manifest-gate/schemas/change_signal.schema.json`
- `mechanics/recurrence/parts/component-manifest-gate/README.md`
- `mechanics/recurrence/PROVENANCE.md`
- `mechanics/ARTIFACT_TOPOLOGY.md`
- `mechanics/topology.json`
- `schemas/AGENTS.md`

## Follow-Up Route

Keep any future recurrence-only schemas in part-local homes. Root `schemas/`
is reserved for root-published cross-mechanic or generated control-plane
contracts.

## Verification

```bash
python scripts/validate_mechanics_topology.py
python scripts/generate_decision_indexes.py --check
python -m ruff check scripts/validate_mechanics_topology.py
```
