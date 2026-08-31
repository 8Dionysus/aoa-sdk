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
