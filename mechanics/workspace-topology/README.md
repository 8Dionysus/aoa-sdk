# Workspace Topology Mechanic

Status: skeleton.

## Mechanic Card

### Operation

Resolve workspace roots, sibling lookup, runtime mirrors, override rules, and
the compact control-plane capsule.

### Trigger

Use this mechanic when a change touches workspace discovery, source checkout
versus runtime mirror posture, bootstrap behavior, or the generated workspace
capsule.

### SDK owns

- local workspace config loading and root resolution
- typed workspace inspection helpers
- generated control-plane capsule parity
- portable bootstrap helper behavior

### Stronger owner split

Host layout, sibling repository content, and deployed runtime mirrors remain
outside SDK truth.

### Current source surfaces

- `.aoa/workspace.toml`
- `docs/workspace-layout.md`
- `generated/workspace_control_plane.min.json`
- `scripts/build_workspace_control_plane.py`
- `scripts/validate_workspace_control_plane.py`
- `src/aoa_sdk/workspace/`
- `tests/test_workspace.py`
- `tests/test_workspace_control_plane.py`

### Candidate parts

- workspace-root-resolution
- control-plane-capsule
- portable-bootstrap

### Must not claim

This mechanic must not introduce hidden path discovery, rewrite sibling source
ownership, or make `/srv/AbyssOS/abyss-stack` equivalent to the source checkout.

### Validation

```bash
python scripts/build_workspace_control_plane.py --check
python scripts/validate_workspace_control_plane.py
python -m pytest -q tests/test_workspace.py tests/test_workspace_control_plane.py
```

### Next route

If a path rule changes, update `docs/workspace-layout.md`,
`.aoa/workspace.toml`, the capsule builder, and this mechanic together.
