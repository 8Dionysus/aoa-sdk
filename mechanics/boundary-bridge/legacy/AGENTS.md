# AGENTS.md

## Applies to

`mechanics/boundary-bridge/legacy/`.

## Role

Legacy preserves former Boundary Bridge mechanics parent names and migration
receipts after their active route has been distilled into canonical parts.

## Read before editing

- `mechanics/AGENTS.md`
- `mechanics/boundary-bridge/AGENTS.md`
- `mechanics/boundary-bridge/PROVENANCE.md`
- `mechanics/boundary-bridge/legacy/INDEX.md`

## Boundaries

- Stay on the control plane.
- Do not make a facade a source owner.
- Do not treat former parent names as active route ids.
- Do not add a legacy entry without naming the active Boundary Bridge part it
  now pressures.

## Validation

```bash
python scripts/validate_mechanics_topology.py
python -m pytest -q tests/test_mechanics_topology.py
```

## Closeout

Report legacy index changes, active Boundary Bridge routes consulted, and
whether any former parent name remains outside a legacy district.
