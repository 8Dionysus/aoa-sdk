# Control Plane Capsule

## Role

`control-plane-capsule` builds and validates the compact
`generated/workspace_control_plane.min.json` routing surface.

## Input

- `scripts/workspace_control_plane_common.py`
- `scripts/build_workspace_control_plane.py`
- `scripts/validate_workspace_control_plane.py`
- `schemas/workspace-control-plane.schema.json`
- `mechanics/runtime-seam/parts/control-plane-capsule/CONTRACT.md`
- route docs and part-local verification refs

## Output

- deterministic generated control-plane JSON
- `artifact_identity` that tells consumers the capsule's ABI epoch, producer,
  privacy boundary, trust layer, and required verification
- validation failures for stale refs, low-context implementation refs, or schema
  drift

## Owner

`aoa-sdk` owns this compact routing capsule. Referenced mechanics and root docs
own their own deeper meaning.

## Validation

Use `VALIDATION.md`.
