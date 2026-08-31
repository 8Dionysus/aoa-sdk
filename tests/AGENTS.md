# AGENTS.md

## Applies To

Root `tests/`.

## Role

Root tests prove repo-wide routes, generated indexes, design surfaces, topology
validators, smoke import, and cross-mechanic docs contracts.

## Relevant routes

The conditional references retained from this card are: `AGENTS.md`, `DESIGN.AGENTS.md`, `mechanics/README.md`, `VALIDATION.md`.

## Boundaries

- Keep single-mechanic regressions under
  `mechanics/<parent>/parts/<part>/tests/`.
- Keep root tests focused on repo-wide behavior or cross-mechanic route
  contracts.
- Do not use root test filenames as active compatibility aliases after a move.

## Closeout

Name whether the test is root-wide or part-local. If part-local, move it and
update the part `VALIDATION.md`, package `PROVENANCE.md`, and
`mechanics/topology.json`.
