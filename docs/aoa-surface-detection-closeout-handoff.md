# AoA Surface Detection Closeout Handoff

Wave one adds one reviewed-only handoff contract for surviving surface notes.
It exists so reviewed sessions can preserve owner-layer follow-through without
pretending those candidates were activated during the live route.

## Boundary

- `sdk.surfaces.build_closeout_handoff(...)` requires `reviewed=True`
- `aoa surfaces handoff` refuses `--not-reviewed`
- the handoff does not auto-run from `aoa closeout run`
- surviving items keep their existing truth labels

Persisted handoffs land under:

```text
aoa-sdk/.aoa/surface-detection/{label}.closeout-handoff.latest.json
```

## Handoff shape

`SurfaceCloseoutHandoff` includes:

- `session_ref`
- `reviewed`
- `surface_detection_report_ref`
- `surviving_items`
- `handoff_targets`
- `notes`

All seven session-growth targets remain valid schema values:

- `aoa-session-donor-harvest`
- `aoa-automation-opportunity-scan`
- `aoa-session-route-forks`
- `aoa-session-self-diagnose`
- `aoa-session-self-repair`
- `aoa-session-progression-lift`
- `aoa-quest-harvest`

## Deterministic auto-emission in wave one

The generator only auto-emits targets when the signals are explicit:

- `aoa-session-donor-harvest` for any surviving non-activated items
- `aoa-automation-opportunity-scan` for surviving playbook-shaped recurring
  route items
- `aoa-session-self-diagnose` for router-only risk-gate honesty notes or
  `actionability_gaps`
- `aoa-quest-harvest` for `candidate-later` playbook or technique items with a
  promotion hint

`aoa-session-route-forks`, `aoa-session-self-repair`, and
`aoa-session-progression-lift` remain legal targets in the schema, but wave one
does not auto-generate them without a later deterministic signal.

## Commands

```bash
aoa surfaces handoff /srv/aoa-sdk/.aoa/surface-detection/aoa-sdk.closeout.latest.json \
  --session-ref session:2026-04-07-surface-first-wave \
  --reviewed \
  --root /srv/aoa-sdk \
  --json
```
