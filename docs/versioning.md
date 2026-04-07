# Surface Versioning Policy

`aoa-sdk` reads source-owned generated surfaces from sibling AoA repositories.
Before CLI breadth or orchestration depth increases, the SDK needs an explicit
compatibility policy for every surface it consumes.

## Rules

1. Every surface read by the SDK must be registered in the compatibility map.
2. Versioned surfaces must declare the exact JSON field that carries the
   surface version.
3. The SDK only accepts explicitly listed versions for a versioned surface.
4. A version mismatch is a hard compatibility failure, not a soft warning.
5. Versionless surfaces are allowed only when the rule marks them explicitly as
   `unversioned` and the SDK treats them as strict-shape local-first
   dependencies.
6. Route-directed public surfaces must resolve through the compatibility map;
   routed reads must not fall back to raw path loads.

## Why This Exists

The federation already has strong contract surfaces, but version fields are not
uniform across repositories. Some use `version`, some use `schema_version`,
some use `catalog_version`, and some use specialized keys such as
`comparison_spine_version`. A few useful surfaces are still versionless list
exports.

Without an explicit policy, a future SDK CLI or orchestration seam could start
depending on incompatible surface changes without noticing.

## Current Policy Shape

The compatibility layer distinguishes two modes:

- `versioned`: require a known version field and an allowed version value
- `unversioned`: accept the surface only as a strict-shape local-first
  dependency and report that no version negotiation is available

Today that second mode is still needed for
`aoa-playbooks/generated/playbook_activation_surfaces.min.json`.

## Operational Expectation

- Loader functions for supported surfaces should go through the compatibility
  layer rather than reading JSON files directly.
- New read paths should add compatibility rules in the same change as the new
  loader.
- CLI commands and orchestration helpers should depend only on surfaces already
  covered by the compatibility map.
- The explicit sibling canary matrix in `scripts/sibling_canary_matrix.json`
  and the scheduled lane in `.github/workflows/latest-sibling-canary.yml`
  should stay aligned with the current compatibility surface set.

## Next Honest Move

The next CLI and orchestration slices should build on:

- compatibility-checked routing and skills surfaces
- compatibility-checked agents, playbooks, memo, and eval surfaces
- explicit handling of the remaining versionless upstream surfaces rather than
  silently assuming they are stable
- scheduled sibling canaries that keep the control plane honest against live
  sibling repos
