# Checkpoint Path Topology Tree

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0050
- Original date: 2026-06-03
- Surface classes: source-topology, mechanics, checkpoint, validation
- SDK facets: importable implementation, checkpoint control-plane, path topology
- Mechanic parents: checkpoint
- Guard families: source topology, checkpoint path routing, session-growth state
- Posture: accepted

## Context

`src/aoa_sdk/checkpoints/registry.py` had become the largest implementation
module in the SDK. It still owned the public `CheckpointsAPI`, but it also
mixed unrelated internal layers: checkpoint path topology, runtime-session
scope naming, legacy migration, closeout context, markdown rendering,
post-commit status reports, hook lookup, and promotion/handoff writing.

The first safe cut is the layer that can be named without changing behavior:
filesystem path topology for checkpoint session-growth state.

## Options Considered

- Leave all checkpoint internals in `registry.py`.
- Rename `registry.py` or split the public API first.
- Move checkpoint filesystem topology into a named tree under
  `src/aoa_sdk/checkpoints/topology/`.

## Decision

Create `src/aoa_sdk/checkpoints/topology/paths.py` as the checkpoint path
topology module and keep `src/aoa_sdk/checkpoints/registry.py` as the
behavioral API facade.

The topology module owns `CheckpointPaths`, checkpoint current-root routing,
runtime-session scope-key naming, repo-label path construction, and
post-commit status path construction. It does not own note migration,
checkpoint capture, closeout rendering, hook lookup, or owner handoff.

## Rationale

Path topology is a stable naming boundary. It is used by several checkpoint
flows, but it does not need to know how checkpoint notes are built or closed.
Moving it first makes the tree readable without creating a broad behavioral
split or changing public imports.

This also gives future cuts a clean direction: behavior can keep moving out of
`registry.py` by route role, while the public `CheckpointsAPI` remains the
entrypoint.

## Consequences

- `src/aoa_sdk/checkpoints/topology/paths.py` becomes the local owner for
  checkpoint path naming.
- `src/aoa_sdk/checkpoints/registry.py` no longer carries raw filesystem
  path topology definitions.
- Runtime-scoped checkpoint paths stay under
  `.aoa/session-growth/current/<runtime-scope>/<repo-label>/`.
- Post-commit status paths stay under
  `.aoa/session-growth/post-commit-status/<repo-label>.latest.json`.
- Future checkpoint cuts should name the next owner branch by route role, not
  by incidental implementation size.

## Source Surfaces

- `src/aoa_sdk/checkpoints/topology/__init__.py`
- `src/aoa_sdk/checkpoints/topology/paths.py`
- `src/aoa_sdk/checkpoints/registry.py`
- `generated/source_topology.min.json`
- `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_checkpoint_path_topology.py`

## Follow-Up Route

The next checkpoint split should separate one behavioral route at a time, for
example runtime-session lookup, closeout context assembly, hook templates, or
promotion/handoff writing. Keep `CheckpointsAPI` stable while those branches
move.

## Verification

```bash
python -m pytest -q mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_checkpoint_path_topology.py mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_session_growth_checkpoint_cycle_api.py mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_session_growth_checkpoint_cycle_cli.py
python scripts/generate_decision_indexes.py --check
```
