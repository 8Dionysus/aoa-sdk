# AGENTS.md

## Applies To

Root `tests/`.

## Role

Root tests prove repo-wide routes, generated indexes, design surfaces, topology
validators, smoke import, and cross-mechanic docs contracts.

## Read Before Editing

1. Root `AGENTS.md`
2. `DESIGN.AGENTS.md`
3. `mechanics/ARTIFACT_TOPOLOGY.md`
4. The owning part `VALIDATION.md` when a regression belongs to one mechanic

## Boundaries

- Keep single-mechanic regressions under
  `mechanics/<parent>/parts/<part>/tests/`.
- Keep root tests focused on repo-wide behavior or cross-mechanic route
  contracts.
- Do not use root test filenames as active compatibility aliases after a move.

## Validation

```bash
python -m pytest -q tests
python scripts/validate_mechanics_topology.py
```

## Closeout

Name whether the test is root-wide or part-local. If part-local, move it and
update the part `VALIDATION.md` plus `mechanics/ARTIFACT_TOPOLOGY.md`.
