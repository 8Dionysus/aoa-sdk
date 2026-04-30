# Recurrence Recursor Agent Readiness

This SDK seam reads recursor readiness surfaces from `aoa-agents` and emits
compact workspace projections for recurrence. It is read-only.

## Commands to wire later

```bash
aoa recur agents readiness --root /srv/AbyssOS/workspace --json
aoa recur agents boundary-check --root /srv/AbyssOS/workspace --json
aoa recur agents projection-candidates --root /srv/AbyssOS/workspace --json
```

The fallback script included in this seed already supports the same three modes:

```bash
python scripts/recursor_agent_readiness.py readiness --workspace-root /srv/AbyssOS/workspace --json
python scripts/recursor_agent_readiness.py boundary-check --workspace-root /srv/AbyssOS/workspace --json
python scripts/recursor_agent_readiness.py projection-candidates --workspace-root /srv/AbyssOS/workspace --json
```

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
