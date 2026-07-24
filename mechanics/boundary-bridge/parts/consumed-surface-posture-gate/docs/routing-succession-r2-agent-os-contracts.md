# Routing Succession R2 Agent OS Contracts

Status: G2 contract design implemented and locally testable; producer migration
and runtime execution are not authorized.

Machine-readable design:
[`../evidence/routing-succession-r2-agent-os-contracts.json`](../evidence/routing-succession-r2-agent-os-contracts.json).

Typed source:
[`src/aoa_sdk/contracts/control_plane.py`](../../../../../src/aoa_sdk/contracts/control_plane.py).

## Why R2 Exists

R1 accepted the future control-plane role but deliberately left behavior
undefined. R2 supplies the smallest typed language that can carry:

```text
RouteIntent
  -> RouteDecision
  -> RouteExplanation
  -> ScenarioBinding
  -> runtime-neutral RunPlan
  -> SessionHandle
  -> ExecutionEvent*
  -> RunOutcome
  -> CloseoutBundleRef
```

The language is useful only if it keeps every stronger owner visible. An agent,
capability, scenario, runtime profile, approval, eval verdict, memory receipt,
and runtime result therefore remains an owner-qualified reference with exact
artifact, source, digest, and schema provenance.

R2 does not move the routing producer. `aoa-routing` remains canonical. It does
not add working `AoASDK.control_plane` or `AoASDK.runner` facades. The protocol
shapes exist so C1 through C3 can implement those surfaces without changing
the contract meaning or hiding an executor in the SDK.

## API Archaeology Result

The current public SDK has typed, read-oriented facades such as
`sdk.routing`, `sdk.playbooks`, `sdk.evals`, and `sdk.memo`. Its historical
blueprint mentioned an optional fluent `sdk.runtime` shape, but no current
public runner or lifecycle API implements that proposal.

R2 therefore does not preserve a nonexistent behavior API. It adds a new
contract branch, re-exports the public models through `aoa_sdk.models`, and
reserves these protocol meanings:

```python
control_plane.resolve(intent) -> RouteDecision
control_plane.explain(decision) -> RouteExplanation
control_plane.compile(decision, scenario_binding, runtime_profile) -> RunPlan

runner.prepare(plan) -> SessionHandle
runner.start(session, adapter, command) -> RunStatus
runner.pause(session, adapter, command) -> RunStatus
runner.approve(session, approval) -> RunStatus
runner.resume(session, adapter, command) -> RunStatus
runner.cancel(session, adapter, command) -> RunStatus
runner.recover(session, adapter, command) -> RunStatus
runner.closeout(session, outcome, bundle) -> RunStatus
```

`ControlPlaneProtocol`, `AoARunnerProtocol`, and `RuntimeAdapterProtocol` are
typing contracts. They are not instantiated by `AoASDK` at R2.

## Contract Families

### Owner-qualified objects

- `AgentRef` points to an `aoa-agents` artifact.
- `ResolvedAgentProfile` is an SDK projection and keeps the agent source plus
  its projection provenance.
- `CapabilityRef` points to an `aoa-skills` capability artifact.
- `ScenarioRef` points to an `aoa-playbooks` scenario artifact.
- `RuntimeProfile` points to a runtime-owner contract and declares adapter,
  plan, event, effect, and constraint compatibility.

The SDK may correlate these objects. It may not author their domain meaning.

### Routing objects

- `RouteIntent` records the caller, objective, scenario, owner constraints,
  and correlation identity.
- `RouteCandidate` records compatibility, policy posture, rank, reasons, and
  evidence. Candidate status is not approval.
- `RouteDecision` is `resolved`, `degraded`, or `blocked`. A selected candidate
  must be listed, compatible, and not forbidden.
- `RouteExplanation` accounts for every considered candidate and has a
  hard-coded `fallback_used=false` field in v1. Hidden fallback is not part of
  the ABI.

The resolver implementation and producer ownership do not move until the later
succession gates.

### Planning objects

- `ScenarioBinding` binds exact scenario, agent, capability, input, and
  decision references. It does not copy scenario prose into SDK source truth.
- `PlanSnapshot` pins every owner artifact and routing ABI by source ref and
  digest.
- `PlanStep` carries abstract operation, effects, dependencies, refs, expected
  output kinds, and approval IDs. It has no shell command, tool arguments,
  model prompt, transport call, or runtime-specific executable field.
- `RunPlan` combines the binding, runtime profile, snapshot, step DAG,
  approvals, checkpoint policy, retry behavior, rollback owner, evidence,
  eval, retention, and closeout requirements.

Pydantic `extra="forbid"` makes injected runtime commands or hidden tool
arguments invalid. `assert_run_plan_digest` checks the content address before
adapter dispatch.

### Approval objects

`ApprovalRequirement` names the approval owner, exact operation, risk class,
steps, evidence, expiry, and renewal posture. `ApprovalRequest` binds the
requirement to session, correlation, plan digest, snapshot digest, and time
window. `ApprovalDecision` repeats that exact scope and points to the deciding
authority plus the concrete deciding identity.

`assert_approvals_satisfied` rejects:

- absent, rejected, or expired approval;
- duplicate decisions for one requirement;
- another session or correlation;
- another plan or source snapshot;
- a decision timestamp from the future.

The SDK carries and checks approval. It does not invent the decision.

### Lifecycle objects

`SessionHandle` is the stable identity returned by `prepare`. `RunStatus` is a
revisioned lifecycle observation. Keeping them separate prevents a stale
handle from pretending to be current state.

The v1 state graph is:

| Before | Trigger | After | Meaning |
| --- | --- | --- | --- |
| `prepared` | `start` | `running` | adapter accepted a plan with no pending gate |
| `prepared` | `approval_required` | `awaiting_approval` | start stopped before an effect |
| `awaiting_approval` | `approval_granted` | `running` | exact plan approval passed |
| `awaiting_approval` | `approval_rejected` | `cancelled` | rejected work cannot execute |
| `awaiting_approval` | `approval_expired` | `paused` | a fresh gate is required |
| `running` | `pause` | `paused` | runtime acknowledged pause |
| `paused` | `resume` | `running` | snapshot, approval, and cursor revalidated |
| `running`, `paused`, `awaiting_approval` | `runtime_interrupted` | `recoverable_failure` | interruption has a recovery cursor |
| `recoverable_failure` | `recover` | `paused` | recovery restores inspectable state, not execution |
| `running` | `runtime_failed` | `failed` | non-recoverable execution terminal |
| `running` | `runtime_completed` | `completed` | execution terminal, not eval verdict |
| non-terminal state | `cancel` | `cancelled` | explicit terminal cancellation |
| `failed`, `completed`, `cancelled` | `closeout` | `closed` | required reference bundle assembled |

There is no `recoverable_failure -> running` shortcut. Recovery first returns
to `paused`; a separate `resume` must recheck snapshot, approval, cursor, and
adapter state. There is no closeout from a non-terminal execution state.

`failed`, `completed`, and `cancelled` are execution-terminal states. `closed`
is the lifecycle-terminal state. A closed `RunStatus` is invalid without a
`CloseoutBundleRef`.

### Commands and replay

`StartCommand`, `PauseCommand`, `ResumeCommand`, `CancelCommand`, and
`RecoverCommand` all carry:

- command and idempotency IDs;
- session and correlation IDs;
- exact plan digest;
- expected state revision;
- issuer provenance;
- timezone-aware issue time;
- explicit reason.

Resume and recovery also pin event cursors. Recovery requires owner evidence.
A cancel request says explicitly whether rollback is requested.

The duplicate rule is:

```text
same session + same idempotency key + identical command digest
    -> return the prior receipt and create no new effect

same idempotency key + different command content
    -> reject replay mismatch
```

`CommandReceipt.status=duplicate` is therefore an observation of prior
application, not a second transition.

### Events

`ExecutionEvent` is append-only in meaning and binds:

- stream, session, and correlation IDs;
- monotonic sequence;
- previous-event digest;
- self digest;
- runtime-owner provenance;
- a typed event kind and kind-specific required fields.

The chain validator rejects gaps, reordering, cross-session events, broken
digest links, content substitution, malformed state transitions, and a reused
event ID with different content. Identical event redelivery is collapsed
before chain validation.

Runtime event payloads remain references. The SDK does not make an opaque event
payload into domain truth.

### Outcome and evidence

`RunOutcome` records runtime execution status and a runtime-owned result ref.
It may correlate:

- `EvidenceBundleRef`;
- `EvalVerdictRef`;
- `MemoryReceiptRef`;
- `CloseoutBundleRef`.

These are distinct types with distinct provenance owners. Successful runtime
execution may have zero eval verdict or memory receipt references; it never
creates either one implicitly. Closeout policy decides which references are
required before `closed`. Each reference names the plan requirement IDs it
satisfies; `assert_closeout_ready` rejects missing terminal evidence, eval
verdict, memory receipt, closeout requirement, cross-session outcome, or a ref
whose provenance owner does not match the requirement owner.

## Snapshot, ABI, and Drift Rules

Every plan pins:

- owner repository;
- artifact path;
- exact source ref;
- artifact digest;
- schema ref and version;
- routing ABI ID, version, schema, source ref, and digest.

Before first dispatch, resume, retry, or recovery, observed sources and ABI
must match the pinned set exactly. A missing, additional, stale, spoofed, or
version-shifted input fails closed. The caller must resolve and compile a new
plan rather than silently updating the existing plan.

During routing owner succession, the pinned routing ABI remains
`aoa_routing_thin_router_v1`. Producer provenance changes only at G5; an ABI
version change remains a separate decision.

## Retry, Recovery, and Rollback

`RetryPolicy` bounds attempts and names retryable failure codes. Every retry
must verify both source snapshot and event cursor. A retry is not a license to
reuse an idempotency key for different work.

`RollbackPolicy` names the runtime or mutation owner, trigger codes, and exact
rollback artifact. A required rollback without an artifact ref is invalid.
Rollback failure is terminal in v1 and must produce a failed outcome plus
evidence; it cannot be reported as recovered.

An adapter outage before acknowledgement leaves the command eligible for
identical replay. An outage after an acknowledged effect requires status and
event reconciliation before any retry.

## Golden Scenario 1: Bounded Repository Change

One contract-only plan expresses:

```text
inspect
  -> approved mutate
  -> validate
  -> checkpoint
  -> evaluate
  -> retain
  -> closeout
```

The plan pins the repository/scenario/capability/runtime sources, mutation
approval, validation evidence, rollback owner, eval owner, memory owner, and
closeout requirements. Runtime execution does not satisfy validation, eval,
memory, or closeout on its own.

## Golden Scenario 2: Multi-Agent Summon and Return

The same `RunPlan` and `PlanStep` types express:

```text
summon
  -> bounded return
  -> validate
  -> closeout
```

Parent and child remain `AgentRef` values from `aoa-agents`; the summon
capability remains an `aoa-skills` reference; scenario composition remains an
`aoa-playbooks` reference. A return is an expected artifact, not trusted proof.
The parent resumes only after the return packet and validation evidence are
correlated.

## Golden Scenario 3: Runtime Degradation

The same contract family expresses:

```text
running
  -> runtime_interrupted
  -> recoverable_failure
  -> recover
  -> paused
  -> resume
  -> running
  -> completed or failed
  -> closed
```

The degradation plan has bounded retry codes, checkpoint-on-failure, exact
event cursors, recovery evidence, and a rollback route. No hidden instruction
is needed to decide whether replay, recovery, resume, or closeout is legal.

## Threat Controls

| Threat | Fail-closed control |
| --- | --- |
| ambiguous intent | explicit `blocked` or `degraded` decision plus ambiguity codes |
| route conflict | every candidate gets a disposition; selected candidate must be listed |
| missing capability | blocked decision; no fallback field can become true |
| stale or spoofed artifact | exact owner/path/source/digest/schema snapshot comparison |
| owner provenance drift | source and ABI sets must match the pinned plan |
| forbidden activation | forbidden candidate cannot be selected; adapter owns activation |
| missing or stale approval | exact plan/session/snapshot/time approval guard |
| duplicate execution | idempotency key plus full command digest and prior receipt |
| event loss or reordering | sequence and previous-digest chain |
| malicious/incomplete event | strict event kind shape, transition table, producer provenance |
| invalid child return | return remains an artifact ref and requires validation |
| hidden inherited context | plan accepts only explicit `context_refs` |
| runtime unavailable | recoverable failure plus cursor, bounded retry, or explicit fail |
| partial adapter outage | reconcile command receipt, status, and event cursor before retry |
| rollback failure | terminal failed outcome with evidence |
| partial closeout | `closed` requires bundle; plan names eval, memory, and evidence requirements |
| early predecessor retirement | R2 changes no producer authority and G5 remains closed |

## Schema Evolution

The contract family is `aoa_control_plane_v1`; lifecycle is
`aoa_run_lifecycle_v1`; runtime adapters negotiate
`aoa_runtime_adapter_v1`.

All models forbid unknown fields. Additive data therefore requires a new
recognized model field and test. A semantic change to state transitions,
digest scope, approval scope, event order, runtime neutrality, or owner
authority requires a versioned contract decision. Adapters declare supported
plan and event versions instead of assuming compatibility.

## G2 Verdict

G2 passes only for contract and rehearsal entry when all of the following are
green:

- strict JSON round-trip for the core object chain;
- the three golden scenarios use the same models;
- lifecycle coverage and forbidden shortcuts are tested;
- plan and event content digests are checked;
- stale source and ABI observations fail;
- missing, mismatched, future, or expired approval fails;
- duplicate command and event redelivery is safe while substitution fails;
- runtime-specific executable fields are rejected;
- runtime success remains distinct from eval, memory, and closeout;
- all repository release gates remain green.

G2 authorizes R3 disposable migration rehearsal only. It does not authorize
shadow publication, G5 owner switch, a production adapter, runtime mutation,
or predecessor retirement.
