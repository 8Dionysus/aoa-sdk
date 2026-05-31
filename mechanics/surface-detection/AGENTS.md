# AGENTS.md

## Applies to

`mechanics/surface-detection/`.

## Role

Route the SDK-local surface-detection mechanic for additive non-skill owner
candidate detection and reviewed handoff.

## Read before editing

- `mechanics/AGENTS.md`
- `mechanics/surface-detection/README.md`
- `docs/aoa-surface-detection-first-wave.md`
- `docs/aoa-surface-detection-second-wave.md`
- `src/aoa_sdk/surfaces/`

## Boundaries

- Stay on the control plane.
- Keep detection additive and advisory until reviewed handoff.
- Do not change `aoa skills ...` meaning.
- Do not make owner-layer candidates executable-now authority.

## Validation

```bash
python scripts/validate_mechanics_topology.py
aoa surfaces detect /srv/AbyssOS/aoa-sdk --phase ingress
python -m pytest -q tests/test_surfaces.py tests/test_surfaces_cli.py
```

## Closeout

Report whether heuristics, shortlist, receipt context, or reviewed handoff
changed.
