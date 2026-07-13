# Runtime Seam Test Surface Localization

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0026
- Original date: 2026-06-01
- Surface classes: topology, mechanics, test placement, generated companion
- SDK facets: mechanics topology, workspace, runtime seam
- Mechanic parents: runtime-seam
- Guard families: mechanics topology, generated parity, root-surface hygiene
- Posture: accepted

## Context

Runtime Seam topology listed workspace tests as active source surfaces while
they still lived in root `tests/`:

- `tests/test_workspace.py`
- `tests/test_workspace_control_plane.py`
- `tests/test_live_workspace.py`

Those tests validate explicit workspace root resolution, control-plane capsule
parity, and source-checkout versus runtime-mirror boundaries. They belong to
Runtime Seam parts, not anonymous root test buckets.

## Decision

Activate three existing Runtime Seam part names:

- `workspace-root-resolution`
- `control-plane-capsule`
- `runtime-mirror-boundary`

Move their tests under:

- `mechanics/runtime-seam/parts/workspace-root-resolution/tests/`
- `mechanics/runtime-seam/parts/control-plane-capsule/tests/`
- `mechanics/runtime-seam/parts/runtime-mirror-boundary/tests/`

Update the generated workspace control-plane validation refs to point at the
part-local control-plane capsule test.

## Rationale

Each part name gives an agent a usable route: input, owner, output, and the
next validation surface. Root test names like `tests/test_workspace.py` hide
whether the test protects path resolution, generated capsule parity, or live
runtime mirror behavior.

## Consequences

- Root `tests/` no longer carries Runtime Seam active test homes.
- The control-plane capsule generated surface now validates against a
  part-local test path.
- Runtime mirror checks remain read-only and must report missing future
  surfaces honestly.

## Source Surfaces

- `mechanics/runtime-seam/README.md`
- `mechanics/runtime-seam/PARTS.md`
- `mechanics/runtime-seam/PROVENANCE.md`
- `mechanics/runtime-seam/parts/workspace-root-resolution/`
- `mechanics/runtime-seam/parts/control-plane-capsule/`
- `mechanics/runtime-seam/parts/runtime-mirror-boundary/`
- `scripts/workspace_control_plane_common.py`
- `generated/workspace_control_plane.min.json`
- `mechanics/ARTIFACT_TOPOLOGY.md`
- `mechanics/topology.json`

## Follow-Up Route

Continue root test audit for release-support, public CLI, decision/design/docs,
and validator surfaces.

## Verification

The executable decision-index and owning-surface checks are routed through
`docs/decisions/AGENTS.md` and the nearest source-owner validation surface.
