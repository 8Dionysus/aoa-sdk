# AGENTS.md

## Applies to

`mechanics/workspace-topology/`.

## Role

Route the SDK-local workspace topology mechanic: root discovery, sibling lookup,
runtime mirror distinction, overrides, portable bootstrap, and the compact
control-plane capsule.

## Read before editing

- `mechanics/AGENTS.md`
- `mechanics/workspace-topology/README.md`
- `.aoa/workspace.toml`
- `docs/workspace-layout.md`
- `generated/workspace_control_plane.min.json`
- `src/aoa_sdk/workspace/`

## Boundaries

- Stay on the control plane.
- Do not make path guessing stronger than `.aoa/workspace.toml`.
- Do not treat a runtime mirror as a source checkout.
- Do not move Python source out of `src/aoa_sdk/workspace/` from this package.

## Validation

```bash
python scripts/validate_mechanics_topology.py
python scripts/build_workspace_control_plane.py --check
python scripts/validate_workspace_control_plane.py
python -m pytest -q tests/test_workspace.py tests/test_workspace_control_plane.py
```

## Closeout

Report whether the workspace root rule, generated capsule, or portable
bootstrap route changed.
