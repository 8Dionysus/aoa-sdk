# Project Runtime Approvals Before Plan Compilation

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0089
- Original date: 2026-07-26
- Surface classes: public API, model contract, plan compiler, runtime boundary
- SDK facets: control-plane, plan compilation, runtime entry
- Mechanic parents: boundary-bridge, runtime-seam
- Guard families: approval integrity, owner provenance, exact binding, no execution
- Posture: accepted

## Context

Compiler v2 preserved approval requirements already present in
`RouteDecision`. That is sufficient for approval attached to route
eligibility, but it cannot express a gate owned by the selected runtime after
route resolution.

The admitted `abyss-stack` repository-change lane requires distinct
`plan_freeze` and `landing` approvals. Its compatibility descriptor already
owned those exact operations and step bindings, while the paired success test
inserted them into an example plan after compilation. A public
`RouteIntent → RouteDecision → ScenarioBinding → RunPlan` chain therefore
could not produce the exact plan the runtime admitted.

The runtime adapter cannot invent those requirements after `RunPlan`: the
Runner must know them before session preparation, and the runtime decision
does not own route selection.

## Options Considered

- Keep inserting runtime approvals into integration fixtures.
- Make routing predict approval policy for every possible runtime.
- Let the runtime emit undeclared approval requests after dispatch.
- Carry an exact scenario-scoped runtime-owner approval projection in
  `RuntimeProfile` and combine it during compilation.

## Decision

Introduce `aoa_control_plane_plan_compiler_v3`.

`RuntimeProfile` gains the backward-compatible
`runtime_approval_requirements` tuple. Every requirement must:

- retain the exact runtime-profile provenance as `approval_owner`;
- have a unique ID within the profile;
- name explicit contour step IDs when the runtime owns a scenario-specific
  gate.

Compiler v3 combines route-owned and runtime-owned requirements in stable
source order, rejects cross-family ID conflicts and inactive step bindings,
and places both unchanged in `RunPlan`. Route requirements remain a required
subset in chain validation. The compiler grants neither family.

The `abyss-stack` profile loader accepts an optional exact `scenario_id` and
projects only that compatibility entry's runtime approval requirements. A
base profile without a scenario keeps an empty projection for compatibility;
a compilation-ready production profile must select the scenario explicitly.

## Rationale

Approval necessity is known at two different boundaries. Routing can require
approval to select a capability; a runtime can require approval to perform an
effect. Preserving both owner projections in one immutable plan gives
`AoARunner` a complete lifecycle contract without asking either owner to
predict or absorb the other.

## Consequences

- Positive: the bounded golden scenario compiles through the public SDK
  directly into the two-approval plan admitted by `abyss-stack`.
- Positive: read-only A2A and degradation profiles project no artificial
  mutation approvals.
- Positive: existing serialized profiles remain valid because the new tuple
  defaults to empty.
- Tradeoff: a runtime profile intended for compilation must choose an exact
  scenario projection.
- Stop line: projecting an approval requirement is not approval, activation,
  execution, or runtime policy evaluation by the SDK.

## Source Surfaces

- `src/aoa_sdk/contracts/control_plane.py`
- `src/aoa_sdk/control_plane/planning/compiler.py`
- `src/aoa_sdk/runtime_adapters/abyss_stack.py`
- `mechanics/boundary-bridge/parts/plan-compilation-control-plane/`
- `mechanics/runtime-seam/parts/abyss-stack-runtime-adapter/`
- `repo:abyss-stack/docs/decisions/ABYSS-STACK-D-0090-project-runtime-approvals-into-run-plans.md`

## Follow-Up Route

Keep every production runtime profile projection exact and scenario-scoped.
Any future conditional approval semantics require a new runtime-profile and
compiler version rather than post-compilation plan mutation.

## Verification

Run compiler positive and conflict tests, exact profile-loader tests, all
installed-wheel golden compiles, and all three paired public
compiler-to-runtime lifecycle/closeout cycles.
