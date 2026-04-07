# Release And CI Posture

This note records the public onboarding, support, release, and CI posture for `aoa-sdk`.
It keeps the SDK on the control plane and makes its guarantees short and checkable.

## Shortest onboarding path

Use the smallest route that matches your need:

1. `README.md` for the repo contour
2. `docs/boundaries.md` for ownership discipline
3. `docs/workspace-layout.md` for local-first path rules
4. `docs/versioning.md` for compatibility posture

Use `docs/session-closeout.md` only when you need the reviewed-session closeout path after those first four surfaces.

## Public support posture

`aoa-sdk` publicly supports:

- typed local-first loaders over source-owned generated surfaces
- workspace discovery and sibling-repo resolution
- compatibility checks across consumed local surfaces
- bounded activation, ingress, guard, and closeout helpers that preserve source ownership

`aoa-sdk` does not publicly support:

- source-authored meaning owned by sibling repositories
- hidden routing or memory policy
- runtime or service authority
- product-edge support guarantees for `ATM10-Agent`

## Release semantics

An SDK release may honestly claim changes only in:

- typed consumer APIs and models
- workspace topology and override behavior
- compatibility-map coverage and enforcement
- bounded control-plane helpers that remain subordinate to owner-owned publishers and validators

New upstream meaning must land in the owning repository first.
The SDK only becomes honest about it after the compatibility surface, loaders, and verification battery are updated here.

## CI tier map

Use the tiers below when you need to verify a current SDK claim:

| tier | purpose | surface |
|---|---|---|
| Tier 1 | local control-plane battery | `python -m pytest -q`, `python -m ruff check .`, `aoa workspace inspect /srv/aoa-sdk`, `aoa compatibility check /srv/aoa-sdk` |
| Tier 2 | release reinforcement | `python -m mypy src`, `python -m build`, `.github/workflows/repo-validation.yml` |
| Tier 3 | live sibling drift detection | `python scripts/run_sibling_canary.py --repo-root . --matrix scripts/sibling_canary_matrix.json`, `.github/workflows/latest-sibling-canary.yml` |

For a repo-scoped compatibility view, use `aoa compatibility check /srv/aoa-sdk --repo <repo> --json`.
