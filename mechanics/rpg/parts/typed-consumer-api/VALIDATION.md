# Typed Consumer API Validation

Run the narrow part test after touching this part:

```bash
python -m pytest -q mechanics/rpg/parts/typed-consumer-api/tests/test_typed_consumer_api.py
```

Run the topology gate after moving or renaming any active surface:

```bash
python scripts/validate_mechanics_topology.py
```
