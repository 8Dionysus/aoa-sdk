# AGENTS.md

## Applies to

`mechanics/checkpoint/legacy/`.

## Role

Legacy preserves former Checkpoint mechanics parent names and migration
receipts after their active route has been distilled into canonical parts.

## Read before editing

- `mechanics/AGENTS.md`
- `mechanics/checkpoint/AGENTS.md`
- `mechanics/checkpoint/PROVENANCE.md`
- `mechanics/checkpoint/legacy/INDEX.md`

## Boundaries

- Stay on the control plane.
- Keep checkpoint notes session-local until reviewed promotion.
- Do not treat former parent names as active route ids.
- Do not add a legacy entry without naming the active Checkpoint part it now
  pressures.

## Validation

```bash
python scripts/validate_mechanics_topology.py
python -m pytest -q tests/test_mechanics_topology.py
```

## Closeout

Report legacy index changes, active Checkpoint routes consulted, and whether
any former parent name remains outside a legacy district.
