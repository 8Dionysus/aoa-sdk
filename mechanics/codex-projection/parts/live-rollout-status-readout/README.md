# Live Rollout Status Readout

## Role

`live-rollout-status-readout` is the Codex Projection part that turns
deploy-local rollout evidence into one bounded SDK status snapshot.

## Input

- live workspace root `.codex/generated/rollout/` artifacts
- external 8Dionysus rollout filenames documented in `CONTRACT.md`

## Output

- `CodexProjectionLiveRolloutStatusSnapshot`
- `schemas/live-rollout-status-snapshot.schema.json`
- `examples/live-rollout-status-snapshot.example.json`

## Owner

`aoa-sdk` owns the typed readout shape, validation, and route documentation.
Host/Codex rollout owners keep trust decisions, rollout execution, rollback
authority, and deploy history truth.

## Next Route

If the readout shows drift, route to the host/Codex rollout owner. Do not
repair deployment state inside this part.

## Validation

Use `VALIDATION.md`.
