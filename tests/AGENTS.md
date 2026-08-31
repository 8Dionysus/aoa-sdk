# AGENTS.md

## Applies To

Root `tests/`.

## Role

Root tests prove repo-wide routes, generated indexes, design surfaces, topology
validators, smoke import, and cross-mechanic docs contracts.

## Relevant routes

Start with root `AGENTS.md`, then this nearest card. Open only the owner source, README, DESIGN, CONTRACT, VALIDATION, release, generated, or sibling-owner surface required by the touched path, semantic question, or requested operation. This is a conditional route, not an unconditional reading inventory. The conditional references retained from this card are: `AGENTS.md`, `DESIGN.AGENTS.md`, `mechanics/README.md`, `VALIDATION.md`.

## Boundaries

- Keep single-mechanic regressions under
  `mechanics/<parent>/parts/<part>/tests/`.
- Keep root tests focused on repo-wide behavior or cross-mechanic route
  contracts.
- Do not use root test filenames as active compatibility aliases after a move.

## Validation route

Use the nearest applicable `VALIDATION.md` when the touched path, semantic question, or requested operation requires executable checks. For repository-wide, release-facing, generated, or cross-owner work, follow root `VALIDATION.md`. The machine gate remains `scripts/release_check.py`; the owner claim/evidence manifest, accepted validation graph, and serial completeness oracle remain authoritative.

## Closeout

Name whether the test is root-wide or part-local. If part-local, move it and
update the part `VALIDATION.md`, package `PROVENANCE.md`, and
`mechanics/topology.json`.
