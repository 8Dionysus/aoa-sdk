# AGENTS.md

## Applies to

`mechanics/runtime-seam/legacy/`.

## Role

Legacy preserves former Runtime Seam mechanics parent names and migration
receipts after their active route has been distilled into canonical parts.

## Read before editing

- `mechanics/AGENTS.md`
- `mechanics/runtime-seam/AGENTS.md`
- `mechanics/runtime-seam/PROVENANCE.md`
- `mechanics/runtime-seam/legacy/INDEX.md`

## Boundaries

- Stay on the control plane.
- Do not treat former parent names as active route ids.
- Do not delete provenance just to make the active tree look cleaner.
- Do not add a legacy entry without naming the active Runtime Seam part it now
  pressures.

## Validation

```bash
python scripts/validate_mechanics_topology.py
python -m pytest -q tests/test_mechanics_topology.py
```

## Closeout

Report legacy index changes, active Runtime Seam routes consulted, and whether
any former parent name remains outside a legacy district.
