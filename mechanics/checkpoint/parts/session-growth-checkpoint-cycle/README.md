# Session Growth Checkpoint Cycle

## Role

`session-growth-checkpoint-cycle` is the Checkpoint part that captures
session-local checkpoint notes, gates review, preserves promotion stop-lines,
attaches read-only session-memory archive refs, and carries reviewed
checkpoint evidence toward final session handoff. It also exposes lifecycle
audit and close/archive routing so old `current/` checkpoint scopes stop
pretending to be active work once review and closeout evidence prove their
next state.

## Input

- `aoa skills enter` / `aoa skills guard` checkpoint capture signals
- explicit `aoa checkpoint mark`, `append`, `after-commit`, and `review-note`
  calls
- active runtime-session checkpoint ledgers
- aoa-session-memory session registry, manifest, index, and raw-block refs
- reviewed closeout context and execution artifacts for lifecycle closure

## Output

- session-local checkpoint note ledger and snapshots
- lifecycle audit and dry-run/apply close/archive reports
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

## Validation

Use `VALIDATION.md`.
