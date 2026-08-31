# AGENTS.md

## Applies to

`mechanics/runtime-seam/`.

## Role

Route the shared Runtime Seam mechanic for SDK workspace roots, source checkout
versus runtime mirror boundaries, control-plane capsules, portable bootstrap,
and local automation seams.

## Relevant routes

The conditional references retained from this card are: `mechanics/AGENTS.md`, `mechanics/runtime-seam/README.md`, `mechanics/runtime-seam/ROADMAP.md`, `.aoa/workspace.toml`, `docs/workspace-layout.md`, `generated/workspace_control_plane.min.json`, `mechanics/runtime-seam/parts/workspace-root-resolution/README.md`, `mechanics/runtime-seam/parts/portable-workspace-bootstrap/README.md`, `mechanics/runtime-seam/parts/control-plane-capsule/README.md`, `mechanics/runtime-seam/parts/runtime-mirror-boundary/README.md`, `src/aoa_sdk/workspace/`.

## Boundaries

- Stay on the control plane.
- Do not make path guessing stronger than `.aoa/workspace.toml`.
- Do not treat a deployed runtime mirror as the source checkout.
- Do not make SDK local automation a runtime implementation owner.

## Validation

Validation for Runtime Seam paths belongs to the nearest active runtime-seam part `VALIDATION.md`; broader checks inherit root `VALIDATION.md`.

## Closeout

Report whether root resolution, capsule parity, bootstrap, mirror boundary, or
automation seam changed.
