# AGENTS.md

## Applies to

`mechanics/runtime-seam/`.

## Role

Route the shared Runtime Seam mechanic for SDK workspace roots, source checkout
versus runtime mirror boundaries, control-plane capsules, portable bootstrap,
and local automation seams.

## Relevant routes

Start with root `AGENTS.md`, then this nearest card. Open only the owner source, README, DESIGN, CONTRACT, VALIDATION, release, generated, or sibling-owner surface required by the touched path, semantic question, or requested operation. This is a conditional route, not an unconditional reading inventory. The conditional references retained from this card are: `mechanics/AGENTS.md`, `mechanics/runtime-seam/README.md`, `mechanics/runtime-seam/ROADMAP.md`, `.aoa/workspace.toml`, `docs/workspace-layout.md`, `generated/workspace_control_plane.min.json`, `mechanics/runtime-seam/parts/workspace-root-resolution/README.md`, `mechanics/runtime-seam/parts/portable-workspace-bootstrap/README.md`, `mechanics/runtime-seam/parts/control-plane-capsule/README.md`, `mechanics/runtime-seam/parts/runtime-mirror-boundary/README.md`, `src/aoa_sdk/workspace/`.

## Boundaries

- Stay on the control plane.
- Do not make path guessing stronger than `.aoa/workspace.toml`.
- Do not treat a deployed runtime mirror as the source checkout.
- Do not make SDK local automation a runtime implementation owner.

## Validation route

Use the nearest applicable `VALIDATION.md` when the touched path, semantic question, or requested operation requires executable checks. For repository-wide, release-facing, generated, or cross-owner work, follow root `VALIDATION.md`. The machine gate remains `scripts/release_check.py`; the owner claim/evidence manifest, accepted validation graph, and serial completeness oracle remain authoritative.

## Closeout

Report whether root resolution, capsule parity, bootstrap, mirror boundary, or
automation seam changed.
