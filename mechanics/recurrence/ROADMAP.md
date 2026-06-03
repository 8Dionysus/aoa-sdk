# Recurrence Roadmap

Recurrence is the SDK control-plane route for observing return pressure,
reviewing it, and handing it to the owner route. It does not run hidden
schedulers, mutate owner surfaces, or claim live protocol execution.

## Current Contour

- Keep component manifest gates, hook observation packs, graph closure
  snapshots, live observation producers, beacon candidate pressure, owner review
  surfaces, review decision closure, downstream projection guards, wiring
  rollout handoff, and recursor readiness routed through active `parts/`.
- Keep observation separate from activation.
- Keep graph closure snapshots derived from source manifests and observed
  surfaces.
- Keep owner review surfaces explicit about who accepts or rejects recurrence
  pressure.
- Keep downstream projection guarded by source owner and compatibility checks.

## Next Work

- Tighten review-decision closure only where repeated recurrence evidence proves
  stable fields and owner outcomes.
- Keep rollout handoff and projection guards bounded to owner-routed evidence.
- Keep recursor readiness as readiness posture, not recursor activation.

## When Time Comes

- Add a recurrence part when a repeated recurrence route cannot stay in
  manifest, observation, graph, review, projection, rollout, or readiness.
- Promote recursor behavior only after owner review, rollback posture, and
  hidden-scheduler stop lines are explicit.
- Add generated recurrence views only after source manifests and review records
  remain stronger than the view.

## Out Of Scope

- Hidden scheduler action.
- Automatic owner mutation.
- Live protocol execution.
- Source-owner acceptance.
- Ambient continuity claims.
