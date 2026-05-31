# AGENTS.md

## Applies to

`mechanics/agon/`.

## Role

Route the shared Agon mechanic for SDK helper candidates, registries,
recurrence adapters, state-packet bridges, and quest seeds.

## Read before editing

- `mechanics/AGENTS.md`
- `mechanics/agon/README.md`
- `config/`
- `docs/AGON_*.md`
- `generated/agon_*.min.json`
- `quests/`

## Boundaries

- Stay on the control plane.
- Keep Agon helper material candidate-only unless reviewed owner surfaces say
  otherwise.
- Do not turn SDK helper registries into Agon doctrine or verdict authority.

## Validation

```bash
python scripts/validate_mechanics_topology.py
python -m pytest -q tests/test_agon_recurrence_adapter.py tests/test_agon_wave7_recurrence_lanes.py
```

## Closeout

Report which Agon helper family, registry, generated companion, or quest seed
changed.
