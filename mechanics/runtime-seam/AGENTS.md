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
python -m pytest -q tests/test_workspace.py tests/test_workspace_control_plane.py tests/test_live_workspace.py
```

## Closeout

Report whether root resolution, capsule parity, bootstrap, mirror boundary, or
automation seam changed.
