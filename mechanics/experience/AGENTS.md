# AGENTS.md

## Applies to

`mechanics/experience/`.

## Role

Route the shared Experience mechanic for SDK API helper contracts across
adoption, deployment, governance, watchtower, rollback, release, and related
call surfaces.

## Read before editing

- `mechanics/AGENTS.md`
- `mechanics/experience/README.md`
- `docs/EXPERIENCE_*.md`
- `docs/ADOPTION_*.md`
- `schemas/sdk_*_call_v1.json`
- `examples/sdk_*_call.example.json`

## Boundaries

- Stay on the control plane.
- Keep API helper calls as contracts, not operational decisions.
- Do not absorb Experience owner truth into SDK examples or schemas.

## Validation

```bash
python scripts/validate_mechanics_topology.py
python -m pytest -q tests/test_experience_wave2_seed_contracts.py tests/test_experience_wave3_seed_contracts.py tests/test_experience_wave4_seed_contracts.py tests/test_experience_wave5_seed_contracts.py
```

## Closeout

Report which API helper contract family changed and which owner decision layer
remains outside SDK.
