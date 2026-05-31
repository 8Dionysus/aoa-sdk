# Runtime Seam Mechanic

Status: skeleton.

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
- `githooks/`
- `systemd/`
- workspace tests under `tests/`

### Candidate parts

- workspace-root-resolution
- control-plane-capsule
- portable-bootstrap
- runtime-mirror-boundary
- local-automation-seam

### Must not claim

This mechanic must not hide path discovery, rewrite sibling source ownership,
or make optional hooks/user units a service runtime.

### Validation

```bash
python scripts/build_workspace_control_plane.py --check
python scripts/validate_workspace_control_plane.py
python -m pytest -q tests/test_workspace.py tests/test_workspace_control_plane.py tests/test_live_workspace.py
```

### Next route

Path and mirror rules update `.aoa/workspace.toml`, `docs/workspace-layout.md`,
workspace source, capsule builders, and this mechanic together.
