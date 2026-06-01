# Reviewed Closeout Context Carry Validation

Run the narrow part tests after touching this part:

```bash
python -m pytest -q mechanics/checkpoint/parts/reviewed-closeout-context-carry/tests/test_reviewed_closeout_context_carry.py mechanics/checkpoint/parts/reviewed-closeout-context-carry/tests/test_component_refresh_followthrough.py
```

Run the topology gate after moving or renaming any active surface:

```bash
python scripts/validate_mechanics_topology.py
```
