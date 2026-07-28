# Validation

Run:

```bash
python mechanics/boundary-bridge/parts/cross-organ-orchestration/scripts/generate_cross_organ_schemas.py --check
python mechanics/boundary-bridge/parts/cross-organ-orchestration/scripts/generate_cross_organ_examples.py --check
pytest -q mechanics/boundary-bridge/parts/cross-organ-orchestration/tests
mypy src/aoa_sdk/contracts/organ_orchestration.py src/aoa_sdk/organs src/aoa_sdk/cli/organs.py
python scripts/validate_mechanics_topology.py
```

The focused tests cover deterministic reconstruction, exact five-stage order,
receipt and snapshot tamper denial, stale-evidence stop, explicit owner review,
exact owner decision receipt, false model-confidence authority, terminal
closure, part-local schema parity, and CLI round trips.

The generated `accepted-shape` fixture proves only that a complete synthetic
chain satisfies the contract. It does not prove MCP invocation, durable memory,
an eval verdict, owner acceptance, runtime deployment, or user benefit.
