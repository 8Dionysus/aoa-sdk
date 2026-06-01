# Governance Runtime Helper Contracts Validation

Run:

```bash
python -m pytest -q mechanics/experience/parts/governance-runtime-helper-contracts/tests/test_governance_runtime_helper_contracts.py
python scripts/validate_mechanics_topology.py
```

For broader Experience routing, also run:

```bash
python -m pytest -q tests/test_docs_routes.py mechanics/release-support/parts/public-support-ci-posture/tests/test_public_support_ci_posture.py
```
