# AGENTS.md

## Applies to

`mechanics/experience/`.

## Role

Route the shared Experience mechanic for SDK helper contracts. This package
keeps helper shape, examples, docs, and regression checks local to active parts;
it does not own adoption, governance, deployment, office, or release decisions.

## Relevant routes

The conditional references retained from this card are: `mechanics/AGENTS.md`, `mechanics/experience/README.md`, `mechanics/experience/ROADMAP.md`, `mechanics/experience/PARTS.md`, `mechanics/experience/PROVENANCE.md`, `mechanics/experience/parts/`.

## Boundaries

- Stay on the control plane.
- Keep API helper calls as contracts, not operational decisions.
- Keep active Experience artifacts under `mechanics/experience/parts/<part>/`.
- Do not reintroduce root active homes for Experience docs, examples, schemas,
  or tests.
- Do not absorb Experience owner truth into SDK examples or schemas.

## Validation

Validation for Experience paths belongs to the nearest active Experience part `VALIDATION.md`; broader checks inherit root `VALIDATION.md`.

## Closeout

Report which Experience helper contract route changed and which owner decision
layer remains outside SDK.
