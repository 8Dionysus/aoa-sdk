# Skill Environment Inspector Validation

Manual trials are the behavioral authority. Re-run current-owner, missing,
drifted, duplicate-scope, unadmitted-repository, legacy-workspace, exact-node,
and environment-override trials before changing the contract.

The retained regression checks cover only the invariants established by those
trials:

```bash
python -m pytest -q mechanics/boundary-bridge/parts/skill-environment-inspector/tests/test_skill_environment_inspector.py mechanics/boundary-bridge/parts/skill-environment-inspector/tests/test_skill_environment_inspector_cli.py
python scripts/validate_mechanics_topology.py
```

For current-host parity, also inspect the live user root with `aoa skills
inspect` and verify prompt visibility separately through the host runtime.
