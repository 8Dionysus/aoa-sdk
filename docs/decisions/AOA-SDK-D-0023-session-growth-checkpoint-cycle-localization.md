# Session Growth Checkpoint Cycle Localization

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0023
- Original date: 2026-06-01
- Surface classes: topology, mechanics, artifact placement, generated companion
- SDK facets: mechanics topology, checkpoint, workspace control plane
- Mechanic parents: checkpoint
- Guard families: mechanics topology, docs routes, generated parity, active naming
- Posture: accepted

## Context

After the reviewed-session handoff runner slice, root `docs/` still held the
session-local checkpoint cycle docs:

- `docs/session-growth-checkpoints.md`
- `docs/checkpoint-note-promotion.md`

These docs are not root-wide boundaries. They describe one Checkpoint part: how
session-local checkpoint notes are captured, reviewed, gated, promoted, and
carried into final reviewed session handoff without becoming harvest, proof,
memory, progression, quest, stats, or owner truth.

## Decision

Move the docs into:

- `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/`

Update workspace-control-plane refs to point at the part-local cycle doc and
reviewed checkpoint-note promotion doc.

## Rationale

`session-growth-checkpoint-cycle` avoids splitting one tight flow into
micro-parts. The part name shows the route: session-growth signals enter,
checkpoint evidence is captured and reviewed, then surviving material routes to
reviewed session handoff or owner surfaces.

## Consequences

- Root `docs/` no longer carries active checkpoint capture/review-note payload.
- Generated workspace-control-plane references route to the part-local docs.
- Checkpoint note review and promotion remain fail-closed and below owner truth.

## Source Surfaces

- `mechanics/checkpoint/README.md`
- `mechanics/checkpoint/PARTS.md`
- `mechanics/checkpoint/PROVENANCE.md`
- `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/`
- `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_session_growth_checkpoint_cycle_cli.py`
- `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_session_growth_checkpoint_cycle_api.py`
- `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_session_growth_checkpoint_cycle_dirty_gate.py`
- `src/aoa_sdk/checkpoints/`
- `scripts/workspace_control_plane_common.py`
- `generated/workspace_control_plane.min.json`
- `mechanics/ARTIFACT_TOPOLOGY.md`
- `mechanics/topology.json`
- `README.md`
- `ROADMAP.md`

## Follow-Up Route

Continue root technical district audit for Questbook payload and
cross-mechanic public contracts.

## Verification

```bash
python scripts/build_workspace_control_plane.py --check
python scripts/validate_workspace_control_plane.py
python -m pytest -q mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_session_growth_checkpoint_cycle_cli.py mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_session_growth_checkpoint_cycle_api.py mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_session_growth_checkpoint_cycle_dirty_gate.py tests/test_docs_routes.py mechanics/runtime-seam/parts/control-plane-capsule/tests/test_control_plane_capsule.py
python scripts/validate_mechanics_topology.py
python scripts/release_check.py
```
