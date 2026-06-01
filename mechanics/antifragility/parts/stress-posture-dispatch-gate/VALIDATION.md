# Stress Posture Dispatch Gate Validation

Run the narrow part test after touching this part:

```bash
python -m pytest -q mechanics/antifragility/parts/stress-posture-dispatch-gate/tests/test_stress_posture_dispatch_gate.py
```

Run the topology gate after moving or renaming any active surface:

```bash
python scripts/validate_mechanics_topology.py
```
