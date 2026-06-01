# AGENTS.md

## Applies to

`mechanics/runtime-seam/`.

## Role

Route the shared Runtime Seam mechanic for SDK workspace roots, source checkout
versus runtime mirror boundaries, control-plane capsules, portable bootstrap,
and local automation seams.

## Read before editing

- `mechanics/AGENTS.md`
- `mechanics/runtime-seam/README.md`
- `.aoa/workspace.toml`
- `docs/workspace-layout.md`
- `generated/workspace_control_plane.min.json`
- `mechanics/runtime-seam/parts/workspace-root-resolution/README.md`
- `mechanics/runtime-seam/parts/portable-workspace-bootstrap/README.md`
- `mechanics/runtime-seam/parts/control-plane-capsule/README.md`
- `mechanics/runtime-seam/parts/runtime-mirror-boundary/README.md`
- `src/aoa_sdk/workspace/`

## Boundaries

- Stay on the control plane.
- Do not make path guessing stronger than `.aoa/workspace.toml`.
- Do not treat a deployed runtime mirror as the source checkout.
- Do not make SDK local automation a runtime implementation owner.

## Validation

```bash
python scripts/validate_mechanics_topology.py
python scripts/build_workspace_control_plane.py --check
python scripts/validate_workspace_control_plane.py
python -m pytest -q mechanics/runtime-seam/parts/workspace-root-resolution/tests/test_workspace_root_resolution.py mechanics/runtime-seam/parts/workspace-root-resolution/tests/test_workspace_root_resolution_cli.py mechanics/runtime-seam/parts/portable-workspace-bootstrap/tests/test_portable_workspace_bootstrap_cli.py mechanics/runtime-seam/parts/control-plane-capsule/tests/test_control_plane_capsule.py mechanics/runtime-seam/parts/runtime-mirror-boundary/tests/test_runtime_mirror_boundary.py
```

## Closeout

Report whether root resolution, capsule parity, bootstrap, mirror boundary, or
automation seam changed.
