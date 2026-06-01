# Agon State Packet Review Bindings Contract

## Function

Build and validate candidate SDK bindings for packet review tooling.

## May

- load the part-local state-packet binding seed;
- generate deterministic compact bindings;
- validate candidate binding count, ids, no-write posture, and stop-lines;
- keep sealed commit drafts local and reviewable.

## Must Not

- create a live arena session;
- execute a move;
- issue a verdict;
- submit sealed commits to runtime;
- mutate rank, scar, retention, Tree of Sophia state, or owner repositories;
- treat old root paths as active routes.

## Validation

Executable proof lives in [VALIDATION](VALIDATION.md).
