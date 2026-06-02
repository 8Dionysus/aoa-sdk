# AGENTS.md

## Applies to

`mechanics/agon/parts/` and every nested Agon part.

## Role

This district holds functioning Agon SDK operation parts.

Parts are active work nodes for SDK-owned candidate helpers, adapters,
registries, schemas, examples, generated companions, scripts, tests, config,
and helper contracts. Questbook source records route through root `quests/`.
They are not Agon doctrine, owner verdicts, runtime activation routes, or
old-path route homes.

## Read before editing

1. Root `AGENTS.md`
2. `mechanics/AGENTS.md`
3. `mechanics/agon/AGENTS.md`
4. `mechanics/agon/PARTS.md`
5. `mechanics/agon/PROVENANCE.md`
6. The nearest part `README.md`, `CONTRACT.md`, and `VALIDATION.md`

## Boundaries

- Stay on the control plane.
- Keep each active part tied to one row in `mechanics/agon/PARTS.md`.
- Keep stronger Agon meaning in the owner repositories.
- Keep old root paths in `mechanics/agon/PROVENANCE.md` or package-local
  legacy indexes, not as active routes.
- Keep `src/aoa_sdk/` as the importable SDK source home.

## Validation

Use the nearest part `VALIDATION.md`, then the package route:

```bash
python scripts/validate_mechanics_topology.py
```

## Closeout

Report the active part, artifact lanes moved, old root path status, and
validator evidence.
