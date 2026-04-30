# AoA Surface Detection Closeout Handoff

Wave one adds one reviewed-only handoff contract for surviving surface notes.
It exists so reviewed sessions can preserve owner-layer follow-through without
pretending those candidates were activated during the live route.

## Boundary

- `sdk.surfaces.build_closeout_handoff(...)` requires `reviewed=True`
- `aoa surfaces handoff` refuses `--not-reviewed`
- the handoff does not auto-run from `aoa closeout run`
- the handoff may feed `aoa-checkpoint-closeout-bridge`, but that bridge must
  still reread the reviewed artifact and any receipt evidence
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
- optional `checkpoint_note_ref`
- `surviving_items`
- optional `surviving_checkpoint_clusters`
- `handoff_targets`
- `notes`

When `surviving_checkpoint_clusters` are present, each cluster may also carry a
provisional `lineage_hint` with `cluster_ref`, owner hypothesis, owner shape,
nearest wrong target, evidence refs, axis pressure, supersession metadata, and
status posture. That carry is still control-plane only and does not mint
`candidate_ref`, `seed_ref`, or `object_ref`.

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
- `aoa-session-donor-harvest` also stays valid when the surviving reviewed
  object is a checkpoint note cluster rather than only a surface item
- `aoa-automation-opportunity-scan` for surviving playbook-shaped recurring
  route items
- `aoa-session-self-diagnose` for router-only risk-gate honesty notes or
  `actionability_gaps`
- `aoa-quest-harvest` for `candidate-later` playbook or technique items with a
  promotion hint

`aoa-session-route-forks`, `aoa-session-self-repair`, and
`aoa-session-progression-lift` remain legal targets in the schema, but wave one
does not auto-generate them without a later deterministic signal.

Reviewed checkpoint closeout may later derive one sibling
`followthrough_decision` inside `closeout-context.json` after the reread.
That decision is not emitted by `aoa surfaces handoff`, and it does not
auto-run any kernel skill by itself.
When reviewed closeout needs to preserve component-refresh drift instead of a
next owner-status landing, use the companion carry in
`docs/COMPONENT_DRIFT_HINTS.md`.
`aoa surfaces handoff` does not auto-emit that packet, and it does not auto-run
owner refresh.

## Commands

```bash
aoa surfaces handoff /srv/AbyssOS/aoa-sdk/.aoa/surface-detection/aoa-sdk.closeout.latest.json \
  --session-ref session:2026-04-07-surface-first-wave \
  --reviewed \
  --root /srv/AbyssOS/aoa-sdk \
  --json
```
