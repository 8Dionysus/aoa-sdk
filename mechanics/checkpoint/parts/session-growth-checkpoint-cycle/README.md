# Session Growth Checkpoint Cycle

## Role

`session-growth-checkpoint-cycle` is the Checkpoint part that captures
session-local checkpoint notes, gates review, preserves promotion stop-lines,
and carries reviewed checkpoint evidence toward final session handoff.

## Input

- `aoa skills enter` / `aoa skills guard` checkpoint capture signals
- explicit `aoa checkpoint mark`, `append`, `after-commit`, and `review-note`
  calls
- active runtime-session checkpoint ledgers

## Output

- session-local checkpoint note ledger and snapshots
- reviewed checkpoint note promotion targets
- review-context inputs for final reviewed session handoff

## Owner

`aoa-sdk` owns the local checkpoint control plane and CLI behavior. Harvest,
memory, proof, progression, quest, stats, and owner status surfaces remain
outside SDK checkpoint authority.

## Next Route

After review, route surviving evidence to the reviewed session handoff runner,
owner follow-through, memory, proof, progression, quest, or stats surfaces.

## Validation

Use `VALIDATION.md`.
