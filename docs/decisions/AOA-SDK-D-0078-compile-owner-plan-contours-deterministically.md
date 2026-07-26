# Compile Admitted Owner Plan Contours Deterministically

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0078
- Original date: 2026-07-26
- Surface classes: public API, CLI, plan ABI, owner projection, package data
- SDK facets: control-plane, public interface, facade boundary, distribution
- Mechanic parents: boundary-bridge
- Guard families: deterministic compilation, snapshot trust, owner binding, no execution
- Posture: accepted

## Context

C1 resolves an intent into a receipt-bound `RouteDecision`, while R2 already
defines a runtime-neutral `RunPlan`. The SDK still lacked the stable boundary
between them. Reconstructing workflow order from playbook prose, reading a
mutable sibling checkout during compilation, or hard-coding scenario meaning
inside the SDK would make compilation non-replayable or absorb
`aoa-playbooks` authority.

The owner now publishes a schema-validated plan-contour projection, but a
generated projection is not source truth merely because it exists. The SDK
needs an exact admitted input and reviewed bindings before it can compile a
plan without becoming a workflow or runtime owner.

## Options Considered

- Parse authored playbook prose at compile time.
- Hard-code each supported scenario DAG in `aoa-sdk`.
- Load the current `aoa-playbooks` checkout or latest projection on every
  compile.
- Package an exact trust-admitted owner projection and schema, then compile
  reviewed bindings against that immutable snapshot.

## Decision

Implement C2 as `aoa_control_plane_plan_compiler_v1`.

The SDK packages the exact `aoa_playbook_plan_contour_v1` projection and
schema selected from a clean, exact `aoa-playbooks` revision after the
artifact trust gate returns the latest `allow` record with subject-store and
required-control evidence. The source lock records the owner revision,
artifact digests, ABI identity, trust record, and subject-store aggregate.
Loading revalidates the lock, both packaged resources, JSON Schema, typed
shape, ABI identity, and admission invariants.

`AoASDK.control_plane.compile()` accepts an exact non-blocked
`RouteDecision`, reviewed `ScenarioBinding`, and `RuntimeProfile`. It must:

- bind the exact decision digest and correlation;
- require owner contour agents, capabilities, artifacts, conditions, and
  owner requirement references exactly;
- prune only explicitly false reviewed guards while preserving remaining
  order and dependencies;
- preserve artifact binding roles, eval anchors, approval references,
  checkpoint, retry, rollback, evidence, retention, and closeout policy;
- pin decision, scenario, runtime, owner projection, schema, trust admission,
  ABI, and compiler provenance in `PlanSnapshot`;
- emit content-addressed canonical JSON such that identical exact inputs
  produce identical bytes.

The compiler selects no runtime adapter, executes no model or tool, grants no
approval, produces no eval verdict, and retains no memory. Those effects
remain with their runtime, policy, proof, and memory owners.

## Rationale

An immutable admitted package makes wheel consumers independent of sibling
checkout layout while keeping the owner revision and trust chain visible.
Exact reviewed bindings reject silent scenario drift. A versioned
runtime-neutral compiler gives agents one reusable Agent OS planning surface
without turning the SDK into a daemon, workflow author, or executor.

## Consequences

- Python and CLI consumers can replay one route-to-plan transformation without
  an `aoa-playbooks` checkout.
- Tampered, stale, mixed-owner, incomplete, or unadmitted contour inputs fail
  closed.
- Updating the owner ABI or supported contours requires an explicit pin
  refresh and SDK validation.
- The wheel carries a bounded generated owner projection and schema whose
  source lock must remain inspectable.
- C2 supports the admitted contour catalog only; it does not infer arbitrary
  playbook prose.
- C3 must implement adapter selection and `AoARunner` lifecycle separately.
- A valid plan proves compilation integrity, not execution, benefit, cost
  reduction, compatibility exit, consumer-zero, or archival readiness.

## Source Surfaces

- `src/aoa_sdk/contracts/control_plane.py`
- `src/aoa_sdk/control_plane/api.py`
- `src/aoa_sdk/control_plane/planning/compiler.py`
- `src/aoa_sdk/control_plane/planning/snapshot.py`
- `src/aoa_sdk/control_plane/planning/data/`
- `src/aoa_sdk/cli/route.py`
- `mechanics/boundary-bridge/parts/plan-compilation-control-plane/`
- `sdk/source_home.manifest.json`

## Follow-Up Route

Land C3 as a separate `AoARunner` and runtime-adapter selection slice. Keep
runtime execution and approval authority outside the compiler, and verify the
complete chain through bounded agent-in-loop trials before making benefit or
cost claims.

## Verification

Run the C2 part suite and deterministic example parity check, combined
R2/C1/C2 contract tests, SDK source-home and mechanics topology validators,
decision-index builder/check, typing, full repository tests, package build and
wheel-resource smoke, release check, and GitHub CI.
