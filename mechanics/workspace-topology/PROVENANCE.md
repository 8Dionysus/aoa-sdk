# Workspace Topology Provenance

## Source Surfaces

- `.aoa/workspace.toml`
- `docs/workspace-layout.md`
- `generated/workspace_control_plane.min.json`
- `scripts/build_workspace_control_plane.py`
- `scripts/validate_workspace_control_plane.py`
- `src/aoa_sdk/workspace/`
- `tests/test_workspace.py`
- `tests/test_workspace_control_plane.py`

## Stronger Owners

The host owns actual mount layout and runtime mirrors. Sibling repositories own
their source content. This SDK only resolves and reports the paths it consumes.

## Notes

This is an SDK-local mechanic because refactored sibling repos do not own the
SDK workspace resolver or its generated control-plane capsule.
