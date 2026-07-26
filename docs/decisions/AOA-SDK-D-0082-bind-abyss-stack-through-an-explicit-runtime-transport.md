# Bind abyss-stack Through an Explicit Runtime Transport

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0082
- Original date: 2026-07-26
- Surface classes: public API, runtime boundary, adapter protocol, integration
- SDK facets: control-plane, public interface, runtime entry, distribution
- Mechanic parents: boundary-bridge, runtime-seam
- Guard families: explicit adapter, owner provenance, no execution, approval integrity
- Posture: accepted

## Context

C3 leaves every post-prepare lifecycle transition and all plan-step execution
behind a caller-supplied adapter. `abyss-stack` already owns a governed
execution lane for the `AOA-P-0011` bounded-change scenario, including
fail-closed policy, isolated preview, two approval milestones, mutation,
verification, rollback, and runtime evidence.

The two surfaces cannot be connected by translating a `RunPlan` back into an
untyped goal. That would discard the exact plan, hide compatibility
assumptions, and let the SDK infer runtime policy. Importing stack internals
directly into the SDK would invert runtime ownership. A new network daemon
would add deployment and exposure cost before the contract needs it.

## Options Considered

- Execute governed-runner steps directly inside `aoa-sdk`.
- Import the `abyss-stack` implementation into the SDK process.
- Add a permanently running HTTP or MCP runtime service.
- Use an explicit, caller-configured subprocess transport to a runtime-owned
  bridge with durable runtime state and an exact compatibility manifest.

## Decision

Add an optional `AbyssStackRuntimeAdapter` client that implements
`RuntimeAdapterProtocol` but executes no plan step itself. The caller must
supply:

- the exact `RuntimeProfile` published by `abyss-stack`;
- an exact runtime binding naming the governed request artifact and every
  local delivery coordinate needed to observe the plan snapshot;
- an explicit transport instance and executable path;
- for the Python bridge, an absolute interpreter path that is invoked in
  isolated mode.

The SDK client serializes typed control-plane objects, invokes one
`abyss-stack` JSON bridge operation without a shell, and parses the typed
response. It performs no executable discovery, adapter selection, goal
inference, policy evaluation, or fallback.

The Python transport form invokes the exact interpreter with `-I`. An
executable path alone is insufficient because an `/usr/bin/env` shebang and
inherited Python source routing can select a different installed SDK ABI.

The SDK also supplies an owner-exact profile loader. It accepts only an
explicit absolute runtime-profile descriptor and complete explicit delivery
coordinates for its declared constraints, hashes those artifacts, and builds
the typed `RuntimeProfile`. It does not search for stack or policy paths.

`abyss-stack` owns the bridge ABI, durable lifecycle state, real execution,
request policy, approval milestone mapping, evidence artifacts, and runtime
outcome. The first admitted compatibility contour is exact
`bounded_change_safe` / `AOA-P-0011`. Its manifest must bind the accepted
`aoa-playbooks` contour ABI and map governed-runner phases to the exact
`RunPlan` step IDs.

The `plan_freeze` and `landing` gates remain two distinct runtime milestones.
They must map to two explicit `ApprovalRequirement.operation` values. The
adapter may not invent an undeclared approval or bypass a declared one.

Runtime completion may return runtime-owned evidence while eval verdict and
memory receipt references remain absent. C5 must attach those stronger-owner
references through a separate closeout-chain contract; C4 must not synthesize
them or relabel runtime success as proof.

## Rationale

An explicit subprocess transport preserves the source/runtime split without
introducing a daemon, port, service lifecycle, or hidden activation. Exact
request and snapshot bindings make file paths delivery coordinates rather
than identity. A runtime-owned compatibility manifest makes the relationship
between a generic `RunPlan` and the existing governed runner reviewable and
versioned instead of heuristic.

## Consequences

- `aoa-sdk` gains a production adapter client but not a production executor.
- Basic SDK imports remain independent of `abyss-stack` and live services.
- The first production contour is intentionally narrow; unsupported plans
  fail before dispatch.
- `abyss-stack` must persist receipts, events, approvals, status, and outcomes
  strongly enough for `AoARunner.restore()`.
- Cross-repository tests must pin both adapter ABI and exact source refs.
- C4 can prove runtime execution before C5 proves eval, retention, and final
  closeout composition.

## Source Surfaces

- `src/aoa_sdk/runtime_adapters/`
- `src/aoa_sdk/contracts/control_plane.py`
- `src/aoa_sdk/control_plane/runner/`
- `mechanics/boundary-bridge/parts/runner-lifecycle-control-plane/`
- `mechanics/runtime-seam/`
- `repo:abyss-stack/docs/decisions/ABYSS-STACK-D-0088-agent-os-subprocess-runtime-adapter.md`

## Follow-Up Route

Implement the runtime-owned bridge and compatibility manifest in
`abyss-stack`, then implement the no-shell SDK transport client. Prove one
bounded-change execution in a disposable target before expanding the admitted
scenario set. Route eval, memo/checkpoint, and closeout assembly through C5.

## Verification

Run the focused C3/C4 adapter suites, exact ABI/profile fixture checks,
subprocess transport negative tests, clean-target governed-run integration,
installed-wheel verification, and both owner repositories' topology and
release gates before the final landing wave.
