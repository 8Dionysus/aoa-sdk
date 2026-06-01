# Antifragility Mechanic

Status: active topology with part-local payload.

## Mechanic Card

### Operation

Keep SDK stress-posture dispatch, reviewed stress closeout carry, and via
negativa pruning bounded, inspectable, and weaker than owner remediation.

### Trigger

Use this mechanic when SDK stress dispatch examples, reviewed stress closeout
carry, via negativa checklists, or antifragility route cards change.

### SDK owns

- public-safe stress-posture dispatch examples
- SDK antifragility control-plane posture docs
- reviewed stress closeout carry route docs and example manifest
- via negativa checklist routing

### Stronger owner split

Owner repositories decide remediation, deletion, proof, runtime response, and
durable memory.

### Current source surfaces

- `mechanics/antifragility/parts/stress-posture-dispatch-gate/`
- `mechanics/antifragility/parts/reviewed-stress-closeout-carry/`
- `mechanics/antifragility/parts/via-negativa/`

### Candidate parts

- stress-posture-dispatch-gate
- reviewed-stress-closeout-carry
- via-negativa

### Must not claim

This mechanic must not treat stress fixtures as proof verdicts, deletion
approval, runtime activation, or owner-local remediation.

### Validation

```bash
python -m pytest -q mechanics/antifragility/parts/stress-posture-dispatch-gate/tests/test_stress_posture_dispatch_gate.py mechanics/antifragility/parts/reviewed-stress-closeout-carry/tests/test_reviewed_stress_closeout_carry.py mechanics/antifragility/parts/via-negativa/tests/test_via_negativa_checklist.py
```

### Next route

Proof routes to `aoa-evals`; memory routes to `aoa-memo`; owner remediation
routes to the affected repository.
