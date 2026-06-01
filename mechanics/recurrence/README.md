# Recurrence Mechanic

Status: active topology with part-local payload.

## Mechanic Card

### Operation

Keep the SDK side of recurrence as a typed, review-only control plane: manifest
gate, hook observation, technique publication observation boundaries, graph
closure, live observations, beacon pressure, owner review surfaces, decision
closure, downstream projection guards, wiring handoffs, and recursor readiness
scans.

### Trigger

Use this mechanic when a recurrence component, observation producer, graph,
beacon, review queue, owner decision closure, projection, rollout handoff, or
recursor readiness helper changes.

### SDK owns

- manifest loading, compatibility diagnostics, and mixed-shape quarantine
- hook and live observation readouts
- graph snapshot and closure helpers
- beacon pressure, review queue packaging, and closure ledgers
- downstream projection builders and guard reports
- wiring, rollout, and return handoff packet shapes
- read-only recursor readiness scans

### Stronger owner split

Component owners own source truth and accepted follow-through. `aoa-evals` owns
bounded proof. `aoa-routing`, `aoa-stats`, and `aoa-kag` consume only thin
advisory projections.

### Current source surfaces

- `src/aoa_sdk/recurrence/`
- `mechanics/recurrence/parts/`
- `mechanics/recurrence/parts/component-manifest-gate/manifests/`
- `mechanics/recurrence/parts/hook-observation-pack/docs/technique-publication-observation-boundary.md`
- `mechanics/recurrence/parts/*/schemas/`
- `mechanics/recurrence/parts/*/examples/`
- `mechanics/recurrence/parts/*/scripts/`
- `mechanics/recurrence/parts/*/tests/`

### Candidate parts

These are active SDK parts, not candidate parent mechanics:

- `component-manifest-gate`
- `hook-observation-pack`
- `graph-closure-snapshot`
- `live-observation-producers`
- `beacon-candidate-pressure`
- `owner-review-surface`
- `review-decision-closure`
- `downstream-projection-guard`
- `wiring-rollout-handoff`
- `recursor-readiness`

### Must not claim

This mechanic must not make recurrence outputs source truth, hidden schedulers,
owner decisions, routing authority, stats authority, KAG canon, or recursor
activation.

### Validation

```bash
python mechanics/recurrence/parts/component-manifest-gate/scripts/validate_recurrence_manifests.py --workspace-root /srv/AbyssOS --json
python -m pytest -q mechanics/recurrence/parts/component-manifest-gate/tests/test_recurrence_registry.py mechanics/recurrence/parts/component-manifest-gate/tests/test_recurrence_seed.py
```

### Next route

Projection or proof changes route to the owning downstream repository or
`aoa-evals`; owner follow-through routes to the target owner repo.
