# AGENTS.md

## Applies to

`mechanics/recurrence/`.

## Role

Route the shared recurrence mechanic for manifests, hooks, graph closure,
review decisions, downstream projections, live observations, and recursor
readiness.

## Read before editing

- `mechanics/AGENTS.md`
- `mechanics/recurrence/README.md`
- `docs/RECURRENCE_CONTROL_PLANE.md`
- `manifests/recurrence/`
- `src/aoa_sdk/recurrence/`
- `examples/recurrence/`

## Boundaries

- Stay on the control plane.
- Keep component truth with owner surfaces.
- Keep eval-suite proof in `aoa-evals`.
- Do not make recurrence projections hidden routing or stats authority.

## Validation

```bash
python scripts/validate_mechanics_topology.py
python scripts/validate_recurrence_manifests.py --workspace-root /srv/AbyssOS
python -m pytest -q tests/test_recurrence_registry.py tests/test_recurrence_seed.py
```

## Closeout

Report whether manifest compatibility, graph, review, projection, observation,
or readiness behavior changed.
