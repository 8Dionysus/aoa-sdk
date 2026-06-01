# Boundary Bridge And Checkpoint Active Part Localization

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0013
- Original date: 2026-05-31
- Surface classes: topology, mechanics, artifact placement, public API naming
- SDK facets: mechanics topology, boundary bridge, checkpoint, A2A, surface detection
- Mechanic parents: boundary-bridge, checkpoint
- Guard families: mechanics topology, workspace control plane, part validation, docs routes, API naming
- Posture: accepted

## Context

After the Agon, Experience, Titan, Codex Projection, and Recurrence
localization slices, two active root-owned surfaces still used chronological
or landing-history names:

- surface detection docs and tests under root `docs/` and `tests/`
- A2A child-task re-entry docs, examples, tests, fixture IDs, and runtime
  closeout helper vocabulary using `wave5` or runtime-wave wording

These were not root public contracts. The mechanics topology already named
their owner parts: `boundary-bridge/owner-layer-signal-handoff` and
`checkpoint/child-task-reentry`.

## Decision

Move the owner-layer surface detection payload into
`mechanics/boundary-bridge/parts/owner-layer-signal-handoff/` and name the
docs by route role:

- `initial-surface-detection-boundary.md`
- `surface-detection-enrichment.md`
- `surface-detection-heuristics.md`
- `surface-closeout-handoff.md`

Move the A2A child-task re-entry payload into
`mechanics/checkpoint/parts/child-task-reentry/` and name the active helper
surface by its route role:

- `summon-return-checkpoint.md`
- `return-reentry.md`
- part-local A2A examples and tests
- `build_runtime_return_closeout_receipt`
- `runtime_return_closeout_receipt`
- `a2a_return_closeout_request`

Keep `src/aoa_sdk/surfaces/` and `src/aoa_sdk/a2a/` as importable SDK source
homes. Their owning mechanics are expressed through the part-local route cards,
artifact topology, and validation references.

## Rationale

Active names should tell an agent what the surface does: input, output, owner,
next route, and validation. Terms such as `first-wave`, `second-wave`, and
`wave5` described landing order, not active responsibility.

The new names preserve behavior while making the route obvious:

- owner-layer signals stay advisory until reviewed handoff
- A2A return material stays below checkpoint and owner acceptance
- runtime return closeout receipts are candidates for owner publication, not a
  hidden runtime authority

## Consequences

- Root `docs/` and `tests/` no longer carry active surface-detection or A2A
  child-task re-entry payload.
- Workspace control-plane refs now point to the boundary-bridge part-local
  owner-layer handoff docs.
- A2A fixture output and tests now use route-role names instead of `wave5`.
- Historical wave names may remain only as old path sources in git history,
  provenance, or legacy accounting.

## Source Surfaces

- `mechanics/boundary-bridge/parts/owner-layer-signal-handoff/`
- `mechanics/checkpoint/parts/child-task-reentry/`
- `src/aoa_sdk/surfaces/`
- `src/aoa_sdk/a2a/`
- `scripts/workspace_control_plane_common.py`
- `generated/workspace_control_plane.min.json`
- `mechanics/ARTIFACT_TOPOLOGY.md`
- `mechanics/topology.json`

## Follow-Up Route

Continue auditing remaining root districts for release-support, RPG,
antifragility, design-route tests, and cross-mechanic public contracts.

## Verification

```bash
python -m pytest -q mechanics/boundary-bridge/parts/owner-layer-signal-handoff/tests/test_owner_layer_signal_handoff.py mechanics/boundary-bridge/parts/owner-layer-signal-handoff/tests/test_owner_layer_signal_handoff_cli.py
python -m pytest -q mechanics/checkpoint/parts/child-task-reentry/tests/test_a2a_sdk_api.py mechanics/checkpoint/parts/child-task-reentry/tests/test_a2a_skill_contract.py mechanics/checkpoint/parts/child-task-reentry/tests/test_a2a_assessment.py mechanics/checkpoint/parts/child-task-reentry/tests/test_a2a_checkpoint_and_return.py mechanics/checkpoint/parts/child-task-reentry/tests/test_a2a_codex_and_closeout.py mechanics/checkpoint/parts/child-task-reentry/tests/test_a2a_e2e_fixture.py
python scripts/build_workspace_control_plane.py --check
python scripts/validate_workspace_control_plane.py
python scripts/validate_mechanics_topology.py
```
