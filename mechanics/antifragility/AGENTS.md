# AGENTS.md

## Applies to

`mechanics/antifragility/`.

## Role

Route the shared Antifragility mechanic for SDK stress-context helpers,
degraded-mode posture, via negativa pruning, and closeout stress carry.

## Read before editing

- `mechanics/AGENTS.md`
- `mechanics/antifragility/README.md`
- `docs/antifragility-control-plane.md`
- `docs/antifragility-closeout-seam.md`
- `docs/VIA_NEGATIVA_CHECKLIST.md`
- `tests/fixtures/antifragility/`

## Boundaries

- Stay on the control plane.
- Do not make stress fixtures proof verdicts or cleanup approval.
- Keep pruning and degraded-mode pressure reviewable and owner-routed.

## Validation

```bash
python scripts/validate_mechanics_topology.py
python -m pytest -q tests/test_antifragility_public_surface.py
```

## Closeout

Report stress-context, degraded-mode, via negativa, or closeout-seam changes.
