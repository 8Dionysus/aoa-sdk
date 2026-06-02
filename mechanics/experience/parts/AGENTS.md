# AGENTS.md

## Applies to

`mechanics/experience/parts/` and every nested Experience part.

## Role

This district holds functioning Experience SDK helper-contract parts.

## Read before editing

1. Root `AGENTS.md`
2. `mechanics/AGENTS.md`
3. `mechanics/experience/AGENTS.md`
4. `mechanics/experience/PARTS.md`
5. `mechanics/experience/PROVENANCE.md`
6. The nearest part `README.md`, `CONTRACT.md`, and `VALIDATION.md`

## Boundaries

- Stay on the control plane.
- Keep Experience helper surfaces as reviewable SDK contracts, not live
  operations.
- Keep old root paths in provenance or package-local legacy indexes, not as
  active routes.

## Validation

Use the nearest part `VALIDATION.md`, then:

```bash
python scripts/validate_mechanics_topology.py
```
