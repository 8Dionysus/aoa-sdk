# Validation

Run:

```bash
python mechanics/boundary-bridge/parts/agent-incarnation-binding/scripts/generate_agent_incarnation_schema.py --check
python -m pytest -q mechanics/boundary-bridge/parts/agent-incarnation-binding/tests
python -m ruff check src/aoa_sdk/contracts/incarnation.py src/aoa_sdk/control_plane/incarnation.py src/aoa_sdk/runtime_adapters mechanics/boundary-bridge/parts/agent-incarnation-binding
python -m mypy src/aoa_sdk/contracts/incarnation.py src/aoa_sdk/control_plane/incarnation.py src/aoa_sdk/runtime_adapters/abyss_stack.py
python scripts/validate_mechanics_topology.py
python scripts/validate_sdk_source_home.py
```

The focused tests prove digest binding, owner separation, exact plan/task/role
matching, continuation completeness, effect ceilings, model-record hashing,
runtime-profile owner projection, stale plan-digest rejection, and generated
schema parity. Runtime execution remains paired proof in `abyss-stack`.
