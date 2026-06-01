# Recurrence Parts

## Candidate Parts

Parts are the active route map for SDK-owned recurrence carry. They are not
additional parent mechanics.

| Part | Active role | Stronger owner route |
| --- | --- | --- |
| [component-manifest-gate](parts/component-manifest-gate/README.md) | discover recurrence manifest districts, load valid components, and expose diagnostics for mixed shapes | component owner repos own manifest meaning |
| [hook-observation-pack](parts/hook-observation-pack/README.md) | keep hook bindings, hook run reports, and technique publication observations observation-only | hook source owners and technique owners own local follow-through |
| [graph-closure-snapshot](parts/graph-closure-snapshot/README.md) | produce graph snapshots, closure reports, and deltas as review evidence | routing and owner repos decide any action |
| [live-observation-producers](parts/live-observation-producers/README.md) | collect owner-surface observations without scheduling or mutation | owner repos decide status changes |
| [beacon-candidate-pressure](parts/beacon-candidate-pressure/README.md) | convert observations into soft beacon pressure and candidate ledgers | owner review decides promotion, acceptance, or suppression |
| [owner-review-surface](parts/owner-review-surface/README.md) | package review queues, dossiers, summaries, and usage-gap visibility | target owner repo owns review outcome |
| [review-decision-closure](parts/review-decision-closure/README.md) | record explicit review decisions, ledgers, and suppression memory | owner decision remains stronger than SDK closure |
| [downstream-projection-guard](parts/downstream-projection-guard/README.md) | emit routing, stats, and KAG projection packets with guard checks | projection consumers keep their own authority ceilings |
| [wiring-rollout-handoff](parts/wiring-rollout-handoff/README.md) | shape propagation, connectivity, rollout, wiring, and return handoff packets | adopting repo owns installation and repair |
| [recursor-readiness](parts/recursor-readiness/README.md) | scan recursor readiness and no-spawn boundaries without activation | `aoa-agents` owns roles; `aoa-evals` owns proof |

## Active Part Contract

Every part keeps:

- `README.md`: use route, output, next route.
- `CONTRACT.md`: inputs, outputs, stop-lines.
- `VALIDATION.md`: narrow checks.

## Provenance Bridge

Use [PROVENANCE](PROVENANCE.md) for former root paths, chronological history,
and source accounting. Active route names should stay role-bearing and current.
