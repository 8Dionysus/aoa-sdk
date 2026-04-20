# Wiring and Rollout Insert

Land this after the review queue pack.

## Files added or changed

- `src/aoa_sdk/recurrence/wiring.py`
- `src/aoa_sdk/recurrence/rollout.py`
- `src/aoa_sdk/recurrence/models.py`
- `src/aoa_sdk/recurrence/api.py`
- `src/aoa_sdk/recurrence/io.py`
- `src/aoa_sdk/recurrence/cli.py`
- schemas, examples, and snippet templates

## Operational sequence

1. `aoa recur wiring-plan`
2. inspect and selectively copy the template snippets
3. `aoa recur rollout-bundle`
4. keep drift and rollback windows explicit while the planted control-plane widens
