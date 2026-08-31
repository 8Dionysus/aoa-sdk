# AGENTS.md

## Applies to

`mechanics/recurrence/parts/`.

## Role

Route recurrence payload by active owner part. Do not use root `docs/`,
`schemas/`, `examples/`, `manifests/`, `scripts/`, or `tests/` as the active
home for recurrence-only artifacts.

## Boundaries

- Keep owner truth with the component owner repository.
- Keep recurrence outputs review-only until an owner accepts follow-through.
- Keep old root paths, chronological names, and migration history in provenance surfaces,
  not in active route names.
- Keep `src/aoa_sdk/recurrence/` as the importable SDK source package.

## Validation route

Use the nearest applicable `VALIDATION.md` when the touched path, semantic question, or requested operation requires executable checks. For repository-wide, release-facing, generated, or cross-owner work, follow root `VALIDATION.md`. The machine gate remains `scripts/release_check.py`; the owner claim/evidence manifest, accepted validation graph, and serial completeness oracle remain authoritative.
