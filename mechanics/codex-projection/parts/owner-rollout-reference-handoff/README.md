# Owner Rollout Reference Handoff

## Role

`owner-rollout-reference-handoff` carries source-owned rollout campaign refs
through SDK docs without turning them into SDK-owned truth.

## Input

- source-owned campaign, review, rollback, deploy receipt, doctor, smoke,
  drift, and rollback refs

## Output

- `docs/deploy-operation-boundary-note.md`
- `docs/rollout-campaign-refs.md`

## Owner

`aoa-sdk` owns pass-through readability. 8Dionysus and host/Codex rollout
owners keep campaign truth, trust decisions, rollback decisions, and deployment
history.

## Validation

Use `VALIDATION.md`.
