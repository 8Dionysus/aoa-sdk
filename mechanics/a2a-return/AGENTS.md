# AGENTS.md

## Applies to

`mechanics/a2a-return/`.

## Role

Route the SDK-local A2A return mechanic for summon target packets, checkpoint
bridge plans, reviewed closeout requests, and return transition decisions.

## Read before editing

- `mechanics/AGENTS.md`
- `mechanics/a2a-return/README.md`
- `docs/A2A_WAVE5_CODEX_RETURN_CHECKPOINT.md`
- `docs/RETURN_REENTRY_SEAM.md`
- `examples/a2a/`
- `src/aoa_sdk/a2a/`

## Boundaries

- Stay on the control plane.
- Do not make return packets role, memo, proof, progression, or stress truth.
- Keep reviewed closeout explicit before return transition claims.

## Validation

```bash
python scripts/validate_mechanics_topology.py
python -m pytest -q tests/test_a2a_sdk_api.py tests/test_a2a_wave5_checkpoint_and_return.py tests/test_a2a_wave5_e2e_fixture.py
```

## Closeout

Report which A2A packet family or return seam changed.
