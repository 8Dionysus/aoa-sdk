# Runtime Seam Provenance

## Source Surfaces

- `.aoa/workspace.toml`
- `docs/workspace-layout.md`
- `generated/workspace_control_plane.min.json`
- `scripts/build_workspace_control_plane.py`
- `scripts/validate_workspace_control_plane.py`
- `src/aoa_sdk/workspace/`
- `mechanics/runtime-seam/parts/workspace-root-resolution/`
- `mechanics/runtime-seam/parts/portable-workspace-bootstrap/`
- `mechanics/runtime-seam/parts/control-plane-capsule/`
- `mechanics/runtime-seam/parts/runtime-mirror-boundary/`
- `mechanics/runtime-seam/parts/workspace-root-resolution/tests/test_workspace_root_resolution.py`
- `mechanics/runtime-seam/parts/workspace-root-resolution/tests/test_workspace_root_resolution_cli.py`
- `mechanics/runtime-seam/parts/portable-workspace-bootstrap/tests/test_portable_workspace_bootstrap_cli.py`
- `mechanics/runtime-seam/parts/control-plane-capsule/tests/test_control_plane_capsule.py`
- `mechanics/runtime-seam/parts/runtime-mirror-boundary/tests/test_runtime_mirror_boundary.py`

## Stronger Owners

The host owns actual mount layout and runtime deployment. Sibling repos own
their source content. SDK Runtime Seam owns only the typed control-plane seam.

## Notes

Former parent-name candidates for this package live only in
`legacy/INDEX.md`. Active Runtime Seam routes name the operation: workspace
root resolution, source/runtime boundary, control-plane capsule, bootstrap,
and local automation seam.

Former root workspace tests moved into `mechanics/runtime-seam/parts/`. Old
root names such as `tests/test_workspace.py`, `tests/test_workspace_control_plane.py`,
and `tests/test_live_workspace.py` are provenance only, not active routes.

Former root workspace CLI cases from `tests/test_cli.py` moved into
`workspace-root-resolution` and `portable-workspace-bootstrap`. The old root
CLI file name is provenance only, not an active validation route.

Former root local automation districts moved to their owning Checkpoint parts:
managed Git hook templates to `session-growth-checkpoint-cycle/git-boundary-hook-templates/` and
closeout user units to `reviewed-session-handoff-runner/closeout-inbox-user-units/`.
