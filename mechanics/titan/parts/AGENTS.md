# AGENTS.md

## Applies to

`mechanics/titan/parts/`.

## Role

Route active Titan SDK helper parts. Each part owns its local docs, schemas,
examples, scripts, tests, contract, and validation note.

## Boundaries

- Stay on the control plane.
- Keep Titan role, runtime, memory, approval, and proof authority outside SDK.
- Do not add root active Titan docs, schemas, examples, scripts, or tests.

## Validation route

Use the nearest applicable `VALIDATION.md` when the touched path, semantic question, or requested operation requires executable checks. For repository-wide, release-facing, generated, or cross-owner work, follow root `VALIDATION.md`. The machine gate remains `scripts/release_check.py`; the owner claim/evidence manifest, accepted validation graph, and serial completeness oracle remain authoritative.
