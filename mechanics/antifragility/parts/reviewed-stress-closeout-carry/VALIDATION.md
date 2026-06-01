# Reviewed Stress Closeout Carry Validation

Run the narrow part test after touching this part:

```bash
python -m pytest -q mechanics/antifragility/parts/reviewed-stress-closeout-carry/tests/test_reviewed_stress_closeout_carry.py
```

Run the topology gate after moving or renaming any active surface:

```bash
python scripts/validate_mechanics_topology.py
```
