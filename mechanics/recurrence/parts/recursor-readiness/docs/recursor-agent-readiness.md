# Recurrence Recursor Agent Readiness

This SDK seam reads recursor readiness surfaces from `aoa-agents` and emits
compact workspace projections for recurrence. It is read-only.

## Executable route

Readiness, boundary-check, and projection-candidate modes are owned by the
recurrence CLI and the part-local readiness script. Their canonical operator
and test route is `../VALIDATION.md`.

## Boundary

The SDK may report:

- recursor readiness status;
- projection candidate status;
- boundary violations;
- missing source diagnostics.

The SDK must not:

- spawn recursors;
- install Codex agents;
- open Agon;
- issue verdicts;
- write scars;
- mutate rank;
- run hidden schedules.
