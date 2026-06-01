# AGENTS.md

## Applies to

`mechanics/rpg/`.

## Role

Route the shared RPG mechanic for the typed consumer slice and RPG surface-path
helper boundary.

## Read before editing

- `mechanics/AGENTS.md`
- `mechanics/rpg/README.md`
- `mechanics/rpg/parts/README.md`
- `mechanics/rpg/parts/typed-consumer-api/README.md`
- `mechanics/rpg/parts/surface-path-transport/README.md`
- `src/aoa_sdk/rpg/`

## Boundaries

- Stay on the control plane.
- Do not make SDK helpers gameplay, frontend, or RPG runtime authority.
- Keep surface paths explicit and typed.

## Validation

```bash
python scripts/validate_mechanics_topology.py
python -m pytest -q mechanics/rpg/parts/typed-consumer-api/tests/test_typed_consumer_api.py mechanics/rpg/parts/surface-path-transport/tests/test_surface_path_transport.py
```

## Closeout

Report whether registry, model, or surface-path helper behavior changed.
