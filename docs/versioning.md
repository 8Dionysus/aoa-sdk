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
7. When a consumed sibling surface has moved into a part-local mechanics home,
   the active compatibility rule should name that canonical part-local path.
   Old root generated copies may remain as external history, while active
   compatibility reads use the canonical owner path.

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

For the current federation-facing route-map capsules, compatibility should also
mean:

- the public surface is schema-backed in the owner repo
- low-context route fields stay on docs, manifests, generated JSON, or schema
  contracts instead of `src/*` or `scripts/*`
- owner-local builders and validators remain visible only as validation support,
  not as the public capsule path

For the current routing and stats ABI normalization pass, compatibility also
uses a bounded dual-read posture:

- v2 `schema_version` envelopes are canonical for emitted routing federation
  surfaces and the `aoa-stats` summary surface catalog
- legacy v1 payloads remain readable during transition when they still appear
  in generated or `state/generated` overrides
- when both shapes are available, the SDK should prefer the v2 override path
  without dropping the normal `state/generated/*` precedence rules

Today that second mode is still needed for
`aoa-playbooks/generated/playbook_activation_surfaces.min.json`.

For `abyss-stack.diagnostic_surface_catalog.min`, the canonical path is the
diagnostic-spine part-local generated catalog:
`mechanics/diagnostic-spine/parts/diagnostic-surfaces/generated/diagnostic_surface_catalog.min.json`.
The old root `generated/diagnostic_surface_catalog.min.json` path is external
history, not an active compatibility input.

For `Tree-of-Sophia.root_entry_map.min`, the canonical path is the ToS
source-home derived export:
`ToS/derived-exports/root_entry_map.min.json`. The old root
`generated/root_entry_map.min.json` path is external history, not an active
compatibility input.

## Owner-Only Routing Succession

`AOA-SDK-D-0071` separates routing producer ownership from routing ABI
versioning.

During the owner-only switch:

- preserve all fourteen current public routing output paths;
- preserve `aoa_routing_thin_router_v1`;
- preserve supported schema identifiers and payload meaning;
- require candidate producer provenance to name the exact SDK source ref
  before trust/canary review and canonical provenance to name it after G5;
- do not hide a semantic or schema break inside the owner change.

An incompatible routing change needs a separate versioned decision and release
after succession. Before G5, `aoa-routing` remained canonical and SDK output
could be used only for non-publishing shadow, explicit candidate review, or
the separately profiled public release-candidate trust route. Candidate schemas
admit both known producer owners, while the selected producer posture
validator requires exactly one and preserves all ABI identifiers. Public
release trust did not start the compatibility window. The receipt-bound
`v0.8.0` G5 switch starts that window without changing the ABI or released
routing corpus. It cannot end until
consumer-zero, clean
install/upgrade/downgrade/rollback checks, two consecutive SDK validation
cycles without predecessor generation, SDK-bound runtime/trust identity, and
the absence of unresolved high-severity compatibility regressions.

The full path list and exit conditions are checked in
`mechanics/boundary-bridge/parts/consumed-surface-posture-gate/evidence/routing-succession-r1-target-operating-model.json`.

The new Agent OS control-plane family is independently versioned as
`aoa_control_plane_v1`, its lifecycle graph as `aoa_run_lifecycle_v1`, and its
adapter negotiation as `aoa_runtime_adapter_v1`. These identifiers do not
change `aoa_routing_thin_router_v1`. A semantic change to lifecycle
transitions, digest scope, approval scope, event ordering, runtime neutrality,
or owner authority requires a versioned contract decision; adapters declare
the plan and event versions they support.

C1 route selection is independently named
`aoa_control_plane_route_resolver_v1`. Its version covers candidate
intersection, score weights, negative applicability, constraint handling,
eligibility rules, ambiguity behavior, decision identity, and fallback
posture. Changing any of those semantics requires a new resolver version and
old-vs-new evaluation; it must not be hidden behind the stable
`aoa_control_plane_v1` envelope.

C2 plan compilation is independently named
`aoa_control_plane_plan_compiler_v1`. Its version covers exact scenario
binding, owner-contour interpretation, guarded pruning, plan snapshot scope,
content identity, and preservation of approvals and lifecycle requirements.
The consumed owner ABI is separately pinned as
`aoa_playbook_plan_contour_v1`; changing either semantic contract requires a
new versioned decision and fixture migration, not an in-place reinterpretation
of packaged data.

C3 lifecycle coordination is independently named
`aoa_control_plane_runner_v1`. Its version covers immutable session binding,
explicit adapter binding, runtime snapshot observation, command and approval
replay, bounded recovery, event/status/receipt reconciliation, restoration,
runtime-owned outcome correlation, and closeout admission. The SDK reference
adapter is independently named `aoa_reference_runtime_adapter_v1` and is
strictly non-executing. A production adapter may implement
`aoa_runtime_adapter_v1`, but runtime deployment and execution evidence do not
become SDK release evidence.

## Operational Expectation

- Loader functions for supported surfaces should go through the compatibility
  layer rather than reading JSON files directly.
- New read paths should add compatibility rules in the same change as the new
  loader.
- CLI commands and orchestration helpers should depend only on surfaces already
  covered by the compatibility map.
- The explicit sibling canary matrix in
  `mechanics/release-support/parts/public-support-ci-posture/config/sibling_canary_matrix.json`
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
