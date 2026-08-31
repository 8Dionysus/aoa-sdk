# AGENTS.md

## Applies to

`mechanics/experience/`.

## Role

Route the shared Experience mechanic for SDK helper contracts. This package
keeps helper shape, examples, docs, and regression checks local to active parts;
it does not own adoption, governance, deployment, office, or release decisions.

## Relevant routes

Start with root `AGENTS.md`, then this nearest card. Open only the owner source, README, DESIGN, CONTRACT, VALIDATION, release, generated, or sibling-owner surface required by the touched path, semantic question, or requested operation. This is a conditional route, not an unconditional reading inventory. The conditional references retained from this card are: `mechanics/AGENTS.md`, `mechanics/experience/README.md`, `mechanics/experience/ROADMAP.md`, `mechanics/experience/PARTS.md`, `mechanics/experience/PROVENANCE.md`, `mechanics/experience/parts/`.

## Boundaries

- Stay on the control plane.
- Keep API helper calls as contracts, not operational decisions.
- Keep active Experience artifacts under `mechanics/experience/parts/<part>/`.
- Do not reintroduce root active homes for Experience docs, examples, schemas,
  or tests.
- Do not absorb Experience owner truth into SDK examples or schemas.

## Validation route

Use the nearest applicable `VALIDATION.md` when the touched path, semantic question, or requested operation requires executable checks. For repository-wide, release-facing, generated, or cross-owner work, follow root `VALIDATION.md`. The machine gate remains `scripts/release_check.py`; the owner claim/evidence manifest, accepted validation graph, and serial completeness oracle remain authoritative.

## Closeout

Report which Experience helper contract route changed and which owner decision
layer remains outside SDK.
