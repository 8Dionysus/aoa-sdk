# AGENTS.md

## Applies to

`mechanics/questbook/`.

## Role

Route the shared Questbook mechanic for SDK quest source records and durable
followthrough obligations without turning quest candidates into owner
acceptance.

## Read before editing

- `mechanics/AGENTS.md`
- `mechanics/questbook/README.md`
- `quests/`
- `mechanics/agon/README.md`

## Boundaries

- Stay on the control plane.
- Keep quest source records in `quests/`.
- Do not make a quest candidate an accepted Agon helper or owner landing.

## Validation

```bash
python scripts/validate_mechanics_topology.py
python -m pytest -q tests/test_mechanics_topology.py
```

## Closeout

Report quest source, index, helper handoff, or owner-followthrough changes.
