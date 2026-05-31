# AGENTS.md

## Applies to

`mechanics/rpg/`.

## Role

Route the shared RPG mechanic for the typed consumer slice and RPG surface-path
helper boundary.

## Read before editing

- `mechanics/AGENTS.md`
- `mechanics/rpg/README.md`
- `docs/RPG_SDK_ADDENDUM.md`
- `docs/RPG_SURFACE_PATHS.md`
- `src/aoa_sdk/rpg/`

## Boundaries

- Stay on the control plane.
- Do not make SDK helpers gameplay, frontend, or RPG runtime authority.
- Keep surface paths explicit and typed.

## Validation

```bash
python scripts/validate_mechanics_topology.py
python -m pytest -q tests/test_rpg_api.py
```

## Closeout

Report whether registry, model, or surface-path helper behavior changed.
