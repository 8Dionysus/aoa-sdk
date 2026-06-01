# AGENTS.md

## Applies to

`mechanics/recurrence/parts/`.

## Role

Route recurrence payload by active owner part. Do not use root `docs/`,
`schemas/`, `examples/`, `manifests/`, `scripts/`, or `tests/` as the active
home for recurrence-only artifacts.

## Boundaries

- Keep owner truth with the component owner repository.
- Keep recurrence outputs review-only until an owner accepts follow-through.
- Keep old root paths, chronological names, and migration history in provenance surfaces,
  not in active route names.
- Keep `src/aoa_sdk/recurrence/` as the importable SDK source package.

## Validation

Run the narrow part command listed in each `VALIDATION.md`, then run:

```bash
python scripts/validate_mechanics_topology.py
python -m pytest -q tests/test_mechanics_topology.py
```
