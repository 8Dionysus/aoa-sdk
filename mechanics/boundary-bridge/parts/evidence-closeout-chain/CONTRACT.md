# Unified Evidence and Closeout Chain Contract

## Immutable execution boundary

The runtime-owned `RunOutcome` is terminal and immutable. The C5 chain rejects
an outcome that already contains eval, memory, or closeout refs. Those
artifacts are produced later by stronger owners and are attached only to the
SDK projection:

```text
RouteIntent
  -> RouteDecision
  -> RouteExplanation
  -> RunPlan
  -> SessionHandle
  -> verified ExecutionEvents
  -> runtime-owned RunOutcome
  -> owner eval verdict refs
  -> owner memory receipt refs
  -> reviewed checkpoint refs
  -> owner closeout bundle ref
```

The chain embeds only SDK control-plane objects and runtime events. It keeps
external evidence, proof, memory, checkpoint, and closeout payloads as
owner-qualified references with schema, source, digest, and requirement
coverage.

The verified stream must contain the exact runtime outcome once. A
correlated `command_ack` may follow it because a production adapter can
acknowledge the same terminal dispatch after recording its outcome. A new
transition, second outcome, or other runtime activity after that point is
rejected.

## Partial and complete

`partial` is an explicit terminal composition state, not a disguised success.
It names every missing required ref and cannot close the runtime lifecycle.
A lifecycle closeout bundle is admitted only after all required runtime
evidence, eval, retention, checkpoint, closeout-kind, and closeout-owner
conditions are complete.

Optional missing refs remain visible in `unresolved_optional_refs` without
turning a requirement into a blocker.

Checkpoint coverage is policy-specific:

- reviewed or closed receipts must come from the plan checkpoint owner;
- every required step must be covered;
- a run that entered `paused` needs explicit pause coverage when required;
- a run that entered `recoverable_failure` needs explicit recovery coverage
  when required.

## Runner compatibility window

`AoARunner.closeout()` accepts either:

- the existing `CloseoutBundleRef`, validated through the v1 legacy
  owner-completeness route; or
- a complete `EvidenceChain`, whose external owner refs are validated outside
  the immutable runtime outcome.

The runtime adapter receives only the exact final `CloseoutBundleRef` and
validates session, outcome, and closeout-owner scope. It does not reinterpret
eval or memory artifacts.

## Durable projection

`EvidenceChainRepository` requires one explicit absolute root. It writes
content-addressed immutable chain objects and one atomic index.

- partial revisions may advance only by preserving execution identity and
  adding owner refs;
- a complete revision is immutable;
- removing or replacing a prior ref is rejected;
- exact replay returns the prior index entry;
- session and closeout lookup validate both index and object digest;
- index refs may not escape the repository root.

The repository is a recovery projection, not proof, memory, checkpoint, or
runtime authority.
