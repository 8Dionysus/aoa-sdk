# Runtime Seam Provenance

## Source Surfaces

- `.aoa/workspace.toml`
- `docs/workspace-layout.md`
- `generated/workspace_control_plane.min.json`
- `scripts/build_workspace_control_plane.py`
- `scripts/validate_workspace_control_plane.py`
- `src/aoa_sdk/workspace/`
- `githooks/`
- `systemd/`
- `tests/test_workspace.py`
- `tests/test_workspace_control_plane.py`
- `tests/test_live_workspace.py`

## Stronger Owners

The host owns actual mount layout and runtime deployment. Sibling repos own
their source content. SDK Runtime Seam owns only the typed control-plane seam.

## Notes

This replaces the over-specific `workspace-topology` parent. Workspace topology
is a part of the shared Runtime Seam mechanic.
