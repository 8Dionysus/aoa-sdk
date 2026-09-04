# Validation

Repository-wide source-home, workspace-capsule, package-build, release, and full-suite checks are owned by [root `VALIDATION.md`](../../../../VALIDATION.md#focused-repository-checks) and [its release-facing lane](../../../../VALIDATION.md#release-facing-and-full-owner-checks).

Run:

```bash
python -m pytest -q mechanics/boundary-bridge/parts/evidence-closeout-chain/tests
python -m ruff check src/aoa_sdk/contracts/evidence_chain.py src/aoa_sdk/control_plane/evidence_chain.py src/aoa_sdk/control_plane/runner mechanics/boundary-bridge/parts/evidence-closeout-chain
python -m mypy src/aoa_sdk/contracts/evidence_chain.py src/aoa_sdk/control_plane/evidence_chain.py src/aoa_sdk/control_plane/runner/core.py
python mechanics/boundary-bridge/parts/evidence-closeout-chain/scripts/verify_evidence_chain_wheel.py
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

The repository-wide topology gate is owned by [root `VALIDATION.md`](../../../../VALIDATION.md#focused-repository-checks).


Runner lifecycle coverage is owned by [the Runner validation surface](../runner-lifecycle-control-plane/VALIDATION.md).
