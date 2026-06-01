# Control Plane Capsule

## Role

`control-plane-capsule` builds and validates the compact
`generated/workspace_control_plane.min.json` routing surface.

## Input

- `scripts/workspace_control_plane_common.py`
- `scripts/build_workspace_control_plane.py`
- `scripts/validate_workspace_control_plane.py`
- `schemas/workspace-control-plane.schema.json`
- route docs and part-local verification refs

## Output

- deterministic generated control-plane JSON
- validation failures for stale refs, low-context implementation refs, or schema
  drift

## Owner

`aoa-sdk` owns this compact routing capsule. Referenced mechanics and root docs
own their own deeper meaning.

## Validation

Use `VALIDATION.md`.
