# Delegate Run Lifecycle Through Explicit Adapters

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0079
- Original date: 2026-07-26
- Surface classes: public API, lifecycle contract, runtime boundary, adapter protocol
- SDK facets: control-plane, public interface, runtime entry, distribution
- Mechanic parents: boundary-bridge
- Guard families: lifecycle integrity, snapshot freshness, idempotency, event chain, no execution
- Posture: accepted

## Context

R2 defines lifecycle, command, approval, event, outcome, and adapter types, and
C2 produces immutable runtime-neutral plans. A concrete Runner still needs to
coordinate those objects without becoming a runtime state authority or
silently selecting an executor.

The original minimal protocol did not expose the runtime observation needed to
prove a pinned plan was still current before dispatch. It also did not expose
approval persistence, terminal outcomes, or enough durable adapter state for a
fresh Runner to reconstruct a session after interruption.

## Options Considered

- Keep Runner state and lifecycle transitions entirely inside the SDK.
- Let the SDK discover an adapter from `RuntimeProfile.adapter_id`.
- Make the first production runtime adapter part of the same landing.
- Require a caller-supplied adapter, keep runtime lifecycle truth in that
  adapter, and make the Runner validate observations and reconcile the exact
  returned chain.

## Decision

Implement C3 as `aoa_control_plane_runner_v1`.

`AoARunner` prepares a `SessionHandle` and keeps only a verified local read
model. The caller must supply the adapter explicitly. The Runner requires the
adapter profile to equal the plan profile and requires a runtime-owner
`RuntimeSnapshotObservation` matching every pinned source and ABI before
start, resume, and recovery.

Every post-prepare lifecycle transition belongs to the adapter. The Runner
admits it only when command receipt, append-only `ExecutionEvent` slice,
resulting `RunStatus`, approval state, runtime-owned `RunOutcome`, and owner
scope agree. `restore()` reconstructs the same verified read model from the
exact plan, handle, events, applied receipts, approvals, outcome, and adapter
status.

Extend the adapter protocol only with the observation and durable read
surfaces necessary for that validation: snapshot observation, current
approval requests and decisions, applied command receipts, outcome, approval
application, renewal, and closeout.

Ship an SDK-owned `DeterministicReferenceAdapter` as the C3 protocol witness.
It may model lifecycle state and events, but it declares
`executes_plan_steps=false` and exposes no model, tool, shell, MCP, skill, or
step-execution operation. It is never selected automatically. A production
adapter remains a separate C4 owner landing.

## Rationale

Keeping runtime status and event persistence behind the adapter prevents the
SDK from becoming a hidden runtime. Requiring an explicit adapter prevents
profile metadata from becoming implicit activation. Exact observation before
effectful transitions closes the drift gap left by the R2 shape. A
non-executing deterministic adapter proves lifecycle and replay semantics
without conflating simulation with production invocation.

## Consequences

- `AoASDK.runner` becomes a stateful lifecycle client while
  `AoASDK.control_plane.compile()` remains pure and runtime-neutral.
- Runtime adapters must persist enough typed state for event, approval,
  receipt, outcome, and restore reads.
- Exact command replay creates no new effect; reused idempotency content fails
  closed even after Runner restoration.
- Approval rejection and expiry remain explicit lifecycle outcomes.
- Recovery still returns to `paused`; resume separately rechecks cursor,
  snapshot, approval, and adapter state.
- Each recovery consumes one bounded retry attempt; non-retryable failure codes
  and attempts beyond `RunPlan.retry_policy.max_attempts` fail before dispatch.
- The reference adapter proves protocol behavior only. It is not evidence of
  production execution, task quality, cost reduction, or runtime readiness.
- C4 must implement the first production adapter in the runtime owner's
  authority and may not weaken this explicit binding or reconciliation law.

## Source Surfaces

- `src/aoa_sdk/contracts/control_plane.py`
- `src/aoa_sdk/control_plane/runner/`
- `src/aoa_sdk/api.py`
- `src/aoa_sdk/models.py`
- `mechanics/boundary-bridge/parts/runner-lifecycle-control-plane/`
- `sdk/source_home.manifest.json`

## Follow-Up Route

Land C4 as a separate production adapter in the selected runtime owner, then
land C5 correlation of runtime events with eval, memo/checkpoint, and closeout
references. Agent-in-the-loop trials remain later passported evidence and
cannot replace deterministic validators.

## Verification

Run the C3 part suite, combined R2/C2 tests, SDK source-home and mechanics
topology validators, decision-index builder/check, typing, full repository
tests, package build, installed-wheel Runner probe, release check, and GitHub
CI.
