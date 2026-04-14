# Recurrence First-Wave Insert

This is the practical insert note for the seed.

## File families

- code: `src/aoa_sdk/recurrence/`
- docs: `docs/RECURRENCE_*`
- schemas: `schemas/*recurrence*`
- examples: `examples/recurrence/`
- tests: `tests/test_recurrence_seed.py`

## Minimal integration patch

- register `RecurrenceAPI` on `AoASDK`
- register `recur_app` on the main Typer CLI

## Persistence layout

Reports persist under the `aoa-sdk` control-plane tree:

```text
aoa-sdk/.aoa/recurrence/signals/
aoa-sdk/.aoa/recurrence/plans/
aoa-sdk/.aoa/recurrence/doctor/
aoa-sdk/.aoa/recurrence/handoffs/
```

## First planted owner manifests

- `8Dionysus/manifests/recurrence/component.codex-plane.shared-root.json`
- `aoa-agents/manifests/recurrence/component.codex-subagents.projection.json`

These are enough to start matching and planning. They are not enough to close every downstream owner boundary. The doctor should expose the remaining open seams.
