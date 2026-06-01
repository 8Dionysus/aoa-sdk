# AGENTS.md

## Applies to

`mechanics/recurrence/`.

## Role

Route the SDK recurrence mechanic control plane across manifest gates, observation
producers, graph readouts, review surfaces, downstream projections, rollout
handoffs, and recursor readiness scans.

## Read before editing

- `mechanics/AGENTS.md`
- `mechanics/recurrence/README.md`
- `mechanics/recurrence/PARTS.md`
- `mechanics/recurrence/parts/AGENTS.md`
- `src/aoa_sdk/recurrence/`

## Boundaries

- Stay on the control plane.
- Keep component truth with owner surfaces.
- Keep eval-suite proof in `aoa-evals`.
- Do not make recurrence projections hidden routing, stats, KAG, or owner authority.
- Use route-role names for active recurrence surfaces; historical chronology
  belongs only in provenance or migration accounting.

## Validation

```bash
python scripts/validate_mechanics_topology.py
python mechanics/recurrence/parts/component-manifest-gate/scripts/validate_recurrence_manifests.py --workspace-root /srv/AbyssOS --json
python -m pytest -q mechanics/recurrence/parts/component-manifest-gate/tests/test_recurrence_registry.py mechanics/recurrence/parts/component-manifest-gate/tests/test_recurrence_seed.py
```

## Closeout

Report which part changed and whether manifest compatibility, hooks, graph,
observations, beacons, review, projections, wiring, or readiness behavior
changed.
