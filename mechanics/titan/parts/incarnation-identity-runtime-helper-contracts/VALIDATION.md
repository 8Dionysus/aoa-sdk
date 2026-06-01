# Incarnation Identity Runtime Helper Contracts Validation

Run:

```bash
python -m pytest -q mechanics/titan/parts/incarnation-identity-runtime-helper-contracts/tests/test_titanctl_runtime.py mechanics/titan/parts/incarnation-identity-runtime-helper-contracts/tests/test_titan_incarnation_spine.py
python mechanics/titan/parts/incarnation-identity-runtime-helper-contracts/scripts/titanctl.py roster --json
python mechanics/titan/parts/incarnation-identity-runtime-helper-contracts/scripts/titan_lineage.py --help
python scripts/validate_mechanics_topology.py
```
