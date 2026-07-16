# Stress Posture Dispatch Gate Validation

Run the narrow part test after touching this part:

```bash
python -m pytest -q mechanics/antifragility/parts/stress-posture-dispatch-gate/tests/test_stress_posture_dispatch_gate.py
```

The permanent check is justified by the stable public `A2AAPI` contract. It
must follow a manual baseline-versus-stressed replay and must never emulate or
restore the retired `SkillsAPI.dispatch` path.

Run the topology gate after moving or renaming any active surface:

```bash
python scripts/validate_mechanics_topology.py
```
