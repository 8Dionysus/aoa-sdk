# Validation

Run:

```bash
PYTHONPATH=src python -m pytest -q mechanics/runtime-seam/parts/programmatic-tool-execution/tests
python -m ruff check src/aoa_sdk/contracts/programmatic_execution.py src/aoa_sdk/models.py mechanics/runtime-seam/parts/programmatic-tool-execution
python scripts/validate_mechanics_topology.py
python scripts/validate_source_topology_index.py
```

The focused suite proves default-off activation, exact request binding,
provider-neutral mode selection, effect-ceiling rejection, economy
observation validation, and explicit missingness handling. A green SDK suite
does not prove runtime activation, live provider execution, eval quality, or
promotion.
