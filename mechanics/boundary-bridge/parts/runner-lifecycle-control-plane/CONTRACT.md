# Runner Lifecycle Control-Plane Contract

## SDK owns

- the versioned `aoa_control_plane_runner_v1` lifecycle client;
- immutable `RunPlan -> SessionHandle` preparation;
- caller-explicit adapter-profile binding;
- validation of runtime snapshot observations, receipts, events, status,
  approvals, outcomes, recovery cursors, and closeout readiness;
- a verified local read model that can be reconstructed from the plan,
  handle, and adapter;
- the SDK-owned deterministic reference adapter used only as a no-effect
  protocol witness.

## Stronger owner split

- the caller chooses and supplies the adapter;
- the runtime owner observes deployed inputs, persists runtime lifecycle,
  acknowledges commands, executes work, and emits runtime outcomes;
- the approval owner decides each `ApprovalDecision`;
- `aoa-evals` owns verdicts;
- evidence producers own evidence bundles;
- `aoa-memo` owns retention receipts;
- checkpoint and closeout owners retain their existing authority.

## Admission order

```text
validated RunPlan
  -> prepared SessionHandle
  -> exact caller-supplied adapter profile
  -> exact runtime snapshot observation
  -> runtime command receipt
  -> append-only ExecutionEvent slice
  -> matching RunStatus
  -> typed runtime RunOutcome
  -> owner-complete closeout refs
  -> closed
```

Start, resume, and recovery fail before dispatch when the observed source or
ABI set differs from the plan snapshot or the observation predates the latest
verified lifecycle state. No latest-version lookup or hidden adapter fallback
is allowed.

## Idempotency

The Runner and adapter key commands by session plus idempotency key and full
command digest.

- Exact replay returns the already verified status and creates no new event or
  receipt.
- Reusing a key with different content fails closed.
- A fresh Runner restored from durable adapter state reloads applied receipts
  before admitting replay.
- Exact approval-decision replay creates no new event; the same decision ID
  with different content is rejected.

## Lifecycle and recovery

The R2 `aoa_run_lifecycle_v1` graph remains authoritative. Recovery is always:

```text
recoverable_failure -> recover -> paused -> resume -> running
```

`recover` and `resume` both pin exact event cursors. `resume` also rechecks
snapshot freshness and every current approval. There is no
`recoverable_failure -> running` shortcut.

Each admitted `recover` consumes one retry attempt after the initial attempt.
The current failure code must be present in
`RunPlan.retry_policy.retryable_failure_codes`, and the resulting attempt
number may not exceed `max_attempts`. Exact replay of the same already applied
recovery consumes no additional attempt.

## Event and outcome integrity

- Runtime events are sequence-ordered, previous-digest linked,
  content-addressed, runtime-owner emitted, and state-continuous.
- Adapter status must name the exact verified event cursor and may not change
  without an event.
- An applied command must have one exact `command_ack`; its receipt binds the
  entire emitted event slice.
- A terminal status must expose one matching runtime-owned `RunOutcome`.
- Runtime success never synthesizes eval, evidence, memory, or closeout refs.
- `closed` is admitted only after `assert_closeout_ready()` passes and the
  adapter records the exact closeout bundle.

## Reference-adapter stop line

The reference adapter mutates only its in-memory protocol state. Supporting a
plan effect class means it can validate lifecycle compatibility for that
class; it does not mean it executed the effect. It exposes no model, tool,
shell, MCP, skill, or step-dispatch operation.

## Not in C3

- production runtime transport or deployment;
- adapter discovery, ranking, or implicit selection;
- step execution;
- eval interpretation or verdict production;
- memo retention;
- checkpoint production;
- cross-owner closeout assembly;
- performance or cost-benefit claims.
