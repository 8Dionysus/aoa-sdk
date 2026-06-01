# Skill Runtime Bridge Validation

```bash
python -m pytest -q mechanics/boundary-bridge/parts/skill-runtime-bridge/tests/test_skill_runtime_bridge.py mechanics/boundary-bridge/parts/skill-runtime-bridge/tests/test_skill_runtime_bridge_cli.py mechanics/boundary-bridge/parts/skill-runtime-bridge/tests/test_skill_reference_contracts.py
python -m pytest -q tests/test_docs_routes.py
python scripts/validate_mechanics_topology.py
```
