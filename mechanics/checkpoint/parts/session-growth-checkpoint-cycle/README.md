# Session Growth Checkpoint Cycle

## Role

`session-growth-checkpoint-cycle` is the Checkpoint part that captures
session-local checkpoint notes, gates review, preserves promotion stop-lines,
attaches read-only session-memory archive refs, and carries reviewed
checkpoint evidence toward final session handoff. It also exposes lifecycle
audit and close/archive routing so old `current/` checkpoint scopes stop
pretending to be active work once review and closeout evidence prove their
next state. When an operator closes a Codex session without running the
reviewed closeout cycle, it can reconcile the checkpoint scope against
read-only aoa-session-memory archive refs and move the scope to archive
evidence without claiming reviewed closeout happened.
It also audits the open checkpoint backlog as a read-only navigation layer,
including runtime trace gaps where the SDK-local runtime-session trace exists
but aoa-session-memory has not yet exposed a matching archive ref.

## Input

- `aoa skills enter` / `aoa skills guard` checkpoint capture signals
- explicit `aoa checkpoint mark`, `append`, `after-commit`, and `review-note`
  calls
- active runtime-session checkpoint ledgers
- aoa-session-memory session registry, manifest, index, and raw-block refs
- reviewed closeout context and execution artifacts for lifecycle closure
- session-memory-backed evidence that a runtime session ended without reviewed
  checkpoint closeout

## Output

- session-local checkpoint note ledger and snapshots
- lifecycle audit and dry-run/apply close/archive reports
- dry-run/apply session reconciliation reports for no-closeout session ends
- generated checkpoint lifecycle navigation indexes under
  `.aoa/session-growth/indexes/`
- read-only checkpoint backlog audit reports and generated backlog navigation
  indexes under `.aoa/session-growth/indexes/`
- session-memory attachment refs for closeout context
- reviewed checkpoint note promotion targets
- review-context inputs for final reviewed session handoff

## Owner

`aoa-sdk` owns the local checkpoint control plane and CLI behavior. Harvest,
memory, proof, progression, quest, stats, and owner status surfaces remain
outside SDK checkpoint authority.

## Next Route

After review, route surviving evidence to the reviewed session handoff runner,
owner follow-through, memory, proof, progression, quest, or stats surfaces.
After reviewed closeout execution, route the checkpoint scope to lifecycle
close/archive so `current/` remains active-now or still-blocked review work.
After session-memory proves that a runtime session ended without reviewed
closeout, use `aoa checkpoint reconcile-sessions` or
`aoa checkpoint sweep-closed-sessions`; these commands preserve and archive the
checkpoint evidence, but never run closeout or mint memory/proof/progression
truth.
When runtime-session traces exist but no session-memory archive ref is present
yet, use `aoa checkpoint backlog-audit` first. It names the next route, such as
reviewing a pending note, recovering a session-memory archive, reconciling a
no-closeout scope, or inspecting a missing runtime trace.

## Validation

Use `VALIDATION.md`.
