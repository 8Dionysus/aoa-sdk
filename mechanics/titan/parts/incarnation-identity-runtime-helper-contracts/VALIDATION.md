# Incarnation Identity Runtime Helper Contracts Validation

Run:

```bash
python -m pytest -q mechanics/titan/parts/incarnation-identity-runtime-helper-contracts/tests/test_titanctl_runtime.py mechanics/titan/parts/incarnation-identity-runtime-helper-contracts/tests/test_titan_incarnation_spine.py
python mechanics/titan/parts/incarnation-identity-runtime-helper-contracts/scripts/titanctl.py roster --json
python mechanics/titan/parts/incarnation-identity-runtime-helper-contracts/scripts/titan_lineage.py --help
```

The repository-wide topology gate is owned by [root `VALIDATION.md`](../../../../VALIDATION.md#focused-repository-checks).
