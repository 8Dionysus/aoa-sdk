# Workspace Root Resolution

## Role

`workspace-root-resolution` resolves AoA workspace roots, repo paths, source
checkouts, and environment overrides without hidden path guessing.

## Input

- `.aoa/workspace.toml`
- `docs/workspace-layout.md`
- workspace CLI inspect calls
- `mechanics/runtime-seam/parts/workspace-root-resolution/tests/test_workspace_root_resolution_cli.py`
- `src/aoa_sdk/workspace/` discovery and root helpers

## Output

- explicit workspace root and federation root selection
- repo path origins and source-checkout preference labels
- failures for missing required repos or ambiguous roots

## Owner

`aoa-sdk` owns local workspace resolution. Host layout, sibling repo contents,
and runtime mirror provisioning remain outside SDK truth.

## Validation

Use `VALIDATION.md`.
