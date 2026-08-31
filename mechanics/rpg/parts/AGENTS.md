# AGENTS.md

## Applies to

Functioning RPG parts under `mechanics/rpg/parts/`.

## Role

These parts hold active SDK RPG payload after it leaves root districts. They
route typed consumer APIs and transport path expectations while `src/aoa_sdk/rpg`
remains the importable source home.

## Boundaries

- Stay on the control plane.
- Do not turn typed reads into gameplay, frontend, runtime, quest, progression,
  or state authority.
- Keep canonical owner refs and generated transport paths visible.
- Keep old root paths in `mechanics/rpg/PROVENANCE.md` or package-local
  legacy indexes, not as active routes.

## Validation route

Use the nearest applicable `VALIDATION.md` when the touched path, semantic question, or requested operation requires executable checks. For repository-wide, release-facing, generated, or cross-owner work, follow root `VALIDATION.md`. The machine gate remains `scripts/release_check.py`; the owner claim/evidence manifest, accepted validation graph, and serial completeness oracle remain authoritative.

## Closeout

Report whether typed consumer behavior, surface-path transport expectations,
owner refs, or validation changed.
