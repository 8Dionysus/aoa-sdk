# Component Manifest Seed Route

This note names the initial SDK recurrence manifest route after localization.

## File families

- code: `src/aoa_sdk/recurrence/`
- docs: `mechanics/recurrence/parts/*/docs/`
- schemas: `mechanics/recurrence/parts/*/schemas/`
- examples: `mechanics/recurrence/parts/*/examples/`
- manifests: `mechanics/recurrence/parts/*/manifests/`
- tests: `mechanics/recurrence/parts/*/tests/`

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
