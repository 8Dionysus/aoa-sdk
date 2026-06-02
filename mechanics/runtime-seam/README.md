# Runtime Seam Mechanic

Status: active topology with part-local payload.

## Mechanic Card

### Operation

Keep SDK workspace and local automation seams explicit: source checkout versus
runtime mirror, workspace root lookup, compact control-plane capsule, portable
bootstrap, and optional local units/hooks.

### Trigger

Use this mechanic when workspace discovery, source/runtime mirror distinction,
workspace bootstrap, generated control-plane capsule, hook posture, or bounded
local automation changes.

### SDK owns

- local workspace config loading and root resolution
- source checkout versus runtime mirror reporting
- generated control-plane capsule parity
- portable bootstrap helper behavior
- bounded local seam docs for hooks and user units

### Stronger owner split

Host layout, runtime deployment, sibling source content, and service runtime
ownership remain outside SDK truth.

### Current source surfaces

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
- workspace tests under `mechanics/runtime-seam/parts/*/tests/`

### Candidate parts

- workspace-root-resolution
- portable-workspace-bootstrap
- control-plane-capsule
- runtime-mirror-boundary

### Must not claim

This mechanic must not hide path discovery or rewrite sibling source ownership.

### Validation

Use the touched part `VALIDATION.md` for executable checks. For package-wide
route changes, use `mechanics/topology.json` for the active validation list
and then run the mechanics topology gate from the root route card.

### Next route

Path and mirror rules update `.aoa/workspace.toml`, `docs/workspace-layout.md`,
workspace source, capsule builders, and this mechanic together.
