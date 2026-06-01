# Reviewed Session Handoff Runner

## Role

`reviewed-session-handoff-runner` is the Checkpoint part that turns reviewed
session artifacts and owner-local receipt bundles into explicit closeout
manifests, inbox processing, reports, and stats refresh handoff.

## Input

- reviewed session artifact
- owner-local receipt files
- closeout request or manifest
- optional user-level inbox path unit

## Output

- canonical closeout request and manifest files
- queue/inbox reports
- owner-local publisher invocations
- deterministic next-step brief after stats refresh

## Owner

`aoa-sdk` owns the reviewed-session handoff runner control plane, manifest assembly, queue
processing, and operator scripts. Skill meaning, proof verdicts, technique
promotion, durable memory, stats truth, and owner follow-through remain in their
own repositories.

## Next Route

Surviving candidates route to owner status surfaces, proof routes to
`aoa-evals`, memory routes to `aoa-memo`, and stats refresh remains a derived
readout.

## Validation

Use `VALIDATION.md`.
