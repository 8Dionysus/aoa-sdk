# Via Negativa Validation

Run the narrow part test after touching this part:

```bash
python -m pytest -q mechanics/antifragility/parts/via-negativa/tests/test_via_negativa_checklist.py
```

Run the topology gate after moving or renaming any active surface:

```bash
python scripts/validate_mechanics_topology.py
```
