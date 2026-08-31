# AGENTS.md

## Applies To

Root `scripts/`.

## Role

Root scripts are repo-wide builders, validators, release gates, and shared
control-plane utilities.

## Relevant routes

Start with root `AGENTS.md`, then this nearest card. Open only the owner source, README, DESIGN, CONTRACT, VALIDATION, release, generated, or sibling-owner surface required by the touched path, semantic question, or requested operation. This is a conditional route, not an unconditional reading inventory. The conditional references retained from this card are: `AGENTS.md`, `DESIGN.md`, `mechanics/README.md`, `VALIDATION.md`.

## Boundaries

- Keep single-mechanic scripts under
  `mechanics/<parent>/parts/<part>/scripts/`.
- Keep root scripts deterministic and runnable from the repository root.
- Route moved mechanic payload through its current part-local owner path.
- Builders must name their source inputs and generated outputs.
- Keep source-home validators repo-wide when they protect top-level homes such
  as `sdk/`.

## Validation route

Use the nearest applicable `VALIDATION.md` when the touched path, semantic question, or requested operation requires executable checks. For repository-wide, release-facing, generated, or cross-owner work, follow root `VALIDATION.md`. The machine gate remains `scripts/release_check.py`; the owner claim/evidence manifest, accepted validation graph, and serial completeness oracle remain authoritative.

## Closeout

State whether the script is repo-wide or part-owned. If part-owned, move it
under the part and update package `PROVENANCE.md`, part `VALIDATION.md`, and
`mechanics/topology.json` in the same change.
