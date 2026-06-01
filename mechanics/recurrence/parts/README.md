# Recurrence Parts

These are the active SDK-owned recurrence parts. They implement the SDK side of
the cross-repo recurrence control plane without claiming owner truth.

| Part | Active role |
| --- | --- |
| [component-manifest-gate](component-manifest-gate/README.md) | scan component and adjacent manifests, quarantine mixed shapes, and keep manifest compatibility explicit |
| [hook-observation-pack](hook-observation-pack/README.md) | define hook binding sets, hook run reports, and technique publication observations as observation-only producers |
| [graph-closure-snapshot](graph-closure-snapshot/README.md) | build graph snapshots, closure reports, and graph delta evidence |
| [live-observation-producers](live-observation-producers/README.md) | collect live owner-surface observations without scheduling or mutation |
| [beacon-candidate-pressure](beacon-candidate-pressure/README.md) | turn observations into soft beacon pressure and candidate ledgers |
| [owner-review-surface](owner-review-surface/README.md) | prepare review queues, dossiers, summaries, and usage-gap visibility |
| [review-decision-closure](review-decision-closure/README.md) | close review queues into owner decisions, ledgers, and suppression memory |
| [downstream-projection-guard](downstream-projection-guard/README.md) | emit routing, stats, and KAG projections with guard reports |
| [wiring-rollout-handoff](wiring-rollout-handoff/README.md) | describe propagation plans, connectivity diagnostics, wiring snippets, rollout windows, and return handoffs |
| [recursor-readiness](recursor-readiness/README.md) | scan recursor readiness and no-spawn boundaries without activation |

Old root paths route through `mechanics/recurrence/PROVENANCE.md`.
