# Validation

Run:

```bash
python -m pytest -q mechanics/boundary-bridge/parts/evidence-closeout-chain/tests
python -m pytest -q mechanics/boundary-bridge/parts/runner-lifecycle-control-plane/tests
python -m ruff check src/aoa_sdk/contracts/evidence_chain.py src/aoa_sdk/control_plane/evidence_chain.py src/aoa_sdk/control_plane/runner mechanics/boundary-bridge/parts/evidence-closeout-chain
python -m mypy src/aoa_sdk/contracts/evidence_chain.py src/aoa_sdk/control_plane/evidence_chain.py src/aoa_sdk/control_plane/runner/core.py
python -m build
python mechanics/boundary-bridge/parts/evidence-closeout-chain/scripts/verify_evidence_chain_wheel.py
python scripts/validate_mechanics_topology.py
python scripts/validate_sdk_source_home.py
```

The focused suite proves partial-to-complete monotonicity, exact lookup by
session and closeout IDs, runtime-outcome immutability, owner separation,
checkpoint recovery coverage, repository tamper closure, Runner closeout, and
exact closeout replay. The installed-wheel probe composes both revisions,
persists and resolves them, and closes the deterministic no-execution Runner
without importing C5 implementation modules from the checkout.

These checks validate chain structure and SDK behavior. They do not prove an
external eval verdict, memory acceptance, reviewed checkpoint judgment, or
production closeout-owner invocation.
