# AGENTS.md

## Applies to

`mechanics/antifragility/`.

## Role

Route the shared Antifragility mechanic for SDK stress-posture dispatch gates,
reviewed stress closeout carry, and via negativa pruning.

## Read before editing

- `mechanics/AGENTS.md`
- `mechanics/antifragility/README.md`
- `mechanics/antifragility/ROADMAP.md`
- `mechanics/antifragility/parts/README.md`
- `mechanics/antifragility/parts/stress-posture-dispatch-gate/README.md`
- `mechanics/antifragility/parts/reviewed-stress-closeout-carry/README.md`
- `mechanics/antifragility/parts/via-negativa/README.md`

## Boundaries

- Stay on the control plane.
- Do not make stress fixtures proof verdicts or cleanup approval.
- Keep pruning and degraded-mode pressure reviewable and owner-routed.

## Validation

```bash
python scripts/validate_mechanics_topology.py
python -m pytest -q mechanics/antifragility/parts/stress-posture-dispatch-gate/tests/test_stress_posture_dispatch_gate.py mechanics/antifragility/parts/reviewed-stress-closeout-carry/tests/test_reviewed_stress_closeout_carry.py mechanics/antifragility/parts/via-negativa/tests/test_via_negativa_checklist.py
```

## Closeout

Report stress-posture dispatch, reviewed stress closeout carry, or via
negativa pruning changes.
