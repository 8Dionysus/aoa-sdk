# AGENTS.md

## Applies to

`mechanics/recurrence/`.

## Role

Route the SDK recurrence mechanic control plane across manifest gates, observation
producers, graph readouts, review surfaces, downstream projections, rollout
handoffs, and recursor readiness scans.

## Relevant routes

The conditional references retained from this card are: `mechanics/AGENTS.md`, `mechanics/recurrence/README.md`, `mechanics/recurrence/ROADMAP.md`, `mechanics/recurrence/PARTS.md`, `mechanics/recurrence/parts/AGENTS.md`, `src/aoa_sdk/recurrence/`.

## Boundaries

- Stay on the control plane.
- Keep component truth with owner surfaces.
- Keep eval-suite proof in `aoa-evals`.
- Do not make recurrence projections hidden routing, stats, KAG, or owner authority.
- Use route-role names for active recurrence surfaces; historical chronology
  belongs only in provenance or migration accounting.

## Validation

Validation for Recurrence paths belongs to the nearest active recurrence part `VALIDATION.md`; broader checks inherit root `VALIDATION.md`.

## Closeout

Report which part changed and whether manifest compatibility, hooks, graph,
observations, beacons, review, projections, wiring, or readiness behavior
changed.
