# Public Support CI Posture

This note records the public onboarding, support, release, and CI posture for `aoa-sdk`.
It keeps the SDK on the control plane and makes its guarantees short and checkable.

## Shortest onboarding path

Use the smallest route that matches your need:

1. `README.md` for the repo contour
2. `docs/boundaries.md` for ownership discipline
3. `docs/workspace-layout.md` for local-first path rules
4. `docs/versioning.md` for compatibility posture

Use `mechanics/checkpoint/parts/child-task-reentry/docs/summon-return-checkpoint.md`
only when you need the reviewed child-task evidence-handoff path after those
first four surfaces.

## Public support posture

`aoa-sdk` publicly supports:

- typed local-first loaders over source-owned generated surfaces
- workspace discovery and sibling-repo resolution
- compatibility checks across consumed local surfaces
- passive skill inspection, surface detection, checkpoint, reviewed evidence
  handoff, and closeout helpers that preserve source ownership

`aoa-sdk` does not publicly support:

- source-authored meaning owned by sibling repositories
- hidden routing or memory policy
- runtime or service authority
- skill retrieval, composition, activation, or execution authority
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
| Tier 1 | local control-plane battery | root `AGENTS.md#verify` and `scripts/release_check.py` |
| Tier 2 | release reinforcement | `scripts/release_check.py` and `.github/workflows/repo-validation.yml` |
| Tier 3 | live sibling drift detection | the part-local sibling-canary runner and `.github/workflows/latest-sibling-canary.yml` |

Repo-scoped compatibility inspection remains owned by the SDK CLI and is
routed through root `AGENTS.md#verify`.

## Release audit surface

The SDK also owns the bounded federation release control plane. Its executable
audit and publication routes live in the release CLI and the canonical
release runbook; repository validation remains owned by
`scripts/release_check.py`.

Those helpers verify or publish release surfaces.
They do not author sibling changelog meaning.
