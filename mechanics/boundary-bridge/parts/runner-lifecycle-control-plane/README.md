# Runner Lifecycle Control Plane

## Role

This Boundary Bridge part implements C3 of the Agent OS control plane:
`AoARunner` prepares an immutable `RunPlan`, binds one caller-supplied runtime
adapter, carries exact approvals, and reconciles runtime-owned status, command
receipts, events, outcomes, recovery, and closeout.

The SDK never selects an adapter implicitly. The runtime adapter owns every
lifecycle transition after `prepare`; the Runner accepts a transition only
after its exact snapshot observation, event chain, status, receipt, and owner
scope agree.

## Public routes

- `AoASDK.runner`
- `AoARunner.prepare()`, `start()`, `pause()`, `approve()`, `resume()`,
  `cancel()`, `recover()`, `sync()`, `outcome()`, and `closeout()`
- `AoARunner.restore()` for rebuilding a verified local observation from a
  `RunPlan`, `SessionHandle`, and durable adapter state
- `GoalLifecycleRequest`, `GoalLifecycleContext`, `GoalLifecycleDecision`, and
  `resolve_goal_lifecycle()` for owner-side Goal transition admission;
  `GoalLifecycleAdapterProtocol` and `GoalLifecycleExecutionReceipt` define
  the runtime-neutral execution seam
- `DeterministicReferenceAdapter` and `reference_runtime_profile()` for
  no-effect lifecycle verification

## Exact boundary

`AoARunner` owns client-side admission and reconciliation:

- exact plan/session/command scope;
- exact adapter-profile binding;
- fresh runtime-owner observation of every pinned source and ABI before
  start, resume, and recovery;
- approval request/decision correlation;
- idempotency-key and command-digest replay checks;
- retryable-failure and maximum-attempt enforcement before recovery dispatch;
- append-only event order, digest linkage, owner, state continuity, and status
  reconciliation;
- runtime-outcome identity and closeout readiness checks.

The adapter owns runtime lifecycle persistence, command acknowledgement,
approval acknowledgement, execution events, runtime result references, and
terminal outcome. Approval authorities still decide approval. Eval, memo,
checkpoint, evidence, and closeout owners still produce their own refs.

## Reference adapter

The SDK-owned reference adapter is a deterministic state-machine witness. It
can acknowledge commands, emit typed events, model interruptions, expose a
typed outcome, and preserve state for `restore()`. It declares
`executes_plan_steps=false` and has no operation that invokes a model, tool,
shell, MCP endpoint, skill, or plan step.

Its profile is explicit and SDK-owned. Passing the adapter is still a caller
choice; `AoASDK.runner` never discovers or selects it automatically.

## Next route

C4 may add one production adapter only in the runtime owner's repository and
through this exact protocol. C5 may correlate the verified Runner chain with
eval, memo/checkpoint, and closeout receipts without copying their truth into
the SDK.

## Validation

Use [VALIDATION.md](VALIDATION.md). Green C3 checks prove lifecycle semantics
and installed-package usability with a non-executing adapter. They do not
prove production runtime invocation, task benefit, cost reduction,
consumer-zero, or archival readiness.
