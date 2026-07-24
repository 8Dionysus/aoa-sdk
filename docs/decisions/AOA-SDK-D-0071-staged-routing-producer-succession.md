# Stage Routing Producer Succession Into the SDK Control Plane

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0071
- Original date: 2026-07-23
- Surface classes: ownership, control-plane, compatibility, repository succession, runtime boundary
- SDK facets: control-plane, public interface, facade boundary, runtime entry, distribution
- Mechanic parents: boundary-bridge, runtime-seam, release-support
- Guard families: owner succession, ABI compatibility, runtime boundary, rollback, consumer-zero
- Posture: accepted

## Context

The live R0 baseline found one canonical routing producer in `aoa-routing`,
one runnable implementation, two active repository control planes, fourteen
root routing outputs, fourteen direct producer input repositories, and a
runtime mirror that was both stale and false-green. A normal routing change
therefore crosses a producer repository, an SDK consumer, sibling-source
inputs, runtime synchronization, and separate validation and release contours.

The useful routing function is already control-plane work: consume
owner-qualified source projections, derive deterministic navigation, preserve
an ABI, and hand the result to runtime consumers. Keeping that function in a
separate permanent control plane would preserve the coordination cost that the
SDK is meant to remove. Moving the whole predecessor tree or its domain-shaped
mechanics would instead copy historical form and risk making the SDK a source
or runtime owner.

The accepted program requires a durable distinction between the target and
the live state. `aoa-routing` remains canonical until shadow parity and an
explicit G5 owner-switch receipt. Accepting this decision does not itself
change the producer, runtime mirror, artifact trust record, or public ABI.

## Options Considered

- Keep `aoa-routing` as a permanent producer and keep `aoa-sdk` as a typed
  consumer. This preserves the present boundary but also preserves two
  control-plane release and validation contours, cross-repository
  synchronization, and the stale-mirror failure mode.
- Extract a shared routing library while both repositories remain runnable
  producers. This reduces some code duplication but creates ambiguous
  producer authority and leaves two places able to publish the same ABI.
- Copy the predecessor repository topology into the SDK and switch in one
  release. This shortens the visible migration but combines owner transfer,
  ABI risk, runtime synchronization, and rollback risk while importing
  historical scaffolding that the SDK does not need.
- Transfer the function rather than the repository form: define the target
  authority, rehearse the migration, run an SDK shadow producer, prove parity,
  switch canonical ownership atomically, then retire duplicate mechanics.
  This is the accepted path.

## Decision

Adopt staged succession of the routing producer into `aoa-sdk`.

After the G5 owner switch, `aoa-sdk` owns:

- the canonical routing producer and routing ABI;
- deterministic route resolution and structured route explanation;
- scenario binding and runtime-neutral `RunPlan` compilation;
- lifecycle contracts, runtime adapter protocol, event correlation, and the
  `AoARunner` lifecycle client.

Preserve the fourteen public routing output paths and
`aoa_routing_thin_router_v1` ABI epoch during the owner-only switch. An
incompatible semantic or schema change requires its own later versioned
decision and must not be hidden inside succession.

Keep source-organ meaning with its current owners. Keep approval authority
with the authority named by the plan and runtime policy. Keep activation and
model/tool execution with the selected runtime owner. Keep verdicts with
`aoa-evals` or a stronger proof owner, and durable retention with
`aoa-memo` and session-memory owners. The SDK may correlate references to
those artifacts without acquiring their authority.

`AoARunner` is a lifecycle client. It may prepare a plan, negotiate an
adapter, carry approvals, consume typed events, coordinate pause or recovery,
and assemble closeout references. It must not execute models or tools without
a runtime adapter.

The succession states are:

1. `predecessor_canonical`: `aoa-routing` is the only canonical and runnable
   producer.
2. `sdk_shadow`: `aoa-routing` remains canonical while the SDK implementation
   produces non-publishing parity evidence.
3. `sdk_canonical`: an explicit G5 receipt makes the SDK the only canonical
   producer; the predecessor becomes compatibility and rollback only.
4. `archive_ready`: consumer-zero, the compatibility exit conditions, and
   rollback retirement are proved.
5. `archived`: only an exact, separate operator approval may cause the hosting
   action.

After `sdk_canonical`, new routing features land only in `aoa-sdk`.
`aoa-routing` may receive compatibility, security, rollback, or deprecation
maintenance until the window closes. Repository archival remains outside this
decision's effect authority.

This decision is paired with `AOA-RT-D-0004` in `aoa-routing`. Both records
must be present before G5.

## Rationale

The selected path turns two active repository control planes into one without
pretending there were two canonical producers at baseline. It preserves the
public routing contract while allowing the implementation and its validation,
release, compatibility, and control-plane APIs to share one SDK owner.

Shadow parity keeps the owner switch observable and reversible. A distinct
switch receipt prevents a target architecture note from becoming accidental
live authority. Function-first migration avoids importing the predecessor's
entire mechanics tree and keeps the SDK subordinate to source organs, proof
owners, memory owners, and runtime bodies.

The authority split also gives future Agent OS work a stable seam:
`RouteIntent -> RouteDecision -> RouteExplanation -> RunPlan` belongs to the
control plane, while activation and execution begin only through an explicit
runtime adapter.

## Consequences

- Root SDK route law, design, roadmap, boundaries, and versioning surfaces
  distinguish accepted target ownership from current producer authority.
- R2 must define typed control-plane and lifecycle contracts before producer
  code moves.
- R3 and M1 must prove clean-build, rollback, and byte or explained semantic
  parity without publishing from the SDK.
- The G5 landing changes producer provenance and ownership, not the public ABI.
- A temporary second runnable implementation is allowed only in shadow mode;
  it never becomes a second canonical producer.
- The predecessor remains available for rollback until the compatibility exit
  conditions and consumer-zero are proved.
- Runtime, approval, verdict, memory, and source-organ boundaries remain
  explicit even though the SDK becomes a stronger control plane.
- The combined SDK becomes larger, so reduced repository, CI, release,
  synchronization, and agent-context cost must be measured rather than
  inferred from consolidation.
- Archive readiness is a verifiable state. Archive execution still requires a
  separate exact operator approval naming the repository.

## Source Surfaces

- `AGENTS.md`
- `README.md`
- `DESIGN.md`
- `ROADMAP.md`
- `docs/boundaries.md`
- `docs/versioning.md`
- `mechanics/boundary-bridge/parts/consumed-surface-posture-gate/docs/routing-succession-r0-baseline.md`
- `mechanics/boundary-bridge/parts/consumed-surface-posture-gate/docs/routing-succession-r1-target-operating-model.md`
- `mechanics/boundary-bridge/parts/consumed-surface-posture-gate/evidence/routing-succession-r1-target-operating-model.json`

## Follow-Up Route

R2 routes typed public contracts through `sdk/public-interface/` and
`src/aoa_sdk/contracts/`. Producer rehearsal and shadow implementation route
through the smallest SDK mechanic and implementation homes established after
contract review. Runtime integration routes through a versioned adapter to the
live runtime owner, not through an SDK executor.

Do not update current producer metadata before the G5 receipt. Do not archive
`aoa-routing` without the separate irreversible-action approval.

## Verification

Run the decision-index checks, the R1 target-model test, SDK source-home and
mechanics topology checks, nested-agent validation, repository tests, and the
release gate. G1 validation proves only target-authority coherence; it does
not prove shadow parity or authorize G5.
