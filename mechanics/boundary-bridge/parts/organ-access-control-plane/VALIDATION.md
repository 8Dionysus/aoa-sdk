# Validation

Run:

```bash
python mechanics/boundary-bridge/parts/organ-access-control-plane/scripts/generate_organ_access_schemas.py --check
python mechanics/boundary-bridge/parts/organ-access-control-plane/scripts/generate_organ_access_example.py --check
pytest -q mechanics/boundary-bridge/parts/organ-access-control-plane/tests
mypy src/aoa_sdk/contracts/organs.py src/aoa_sdk/organs src/aoa_sdk/cli/organs.py
python scripts/validate_mechanics_topology.py
```

The tests cover strict schemas, effect-policy matching, isolated credential
contours, secret rejection, admission gates, deterministic projection,
suspension, catalog byte budgets, explicit workspace configuration,
candidate-only activation, schema drift, approvals, exact external targets,
typed owner payloads, owner-bounded result review, content-addressed review
receipts, CLI discovery, resumable admission, idempotent replay, typed stops,
owner/proof/acceptance separation, registry drift, separate owner/operator
decisions, non-mutating transition authorization, and projection-owned index
evidence, plus current-versus-expired baseline auditing.

Runtime deployment, consumer pairing, live freshness, grounded results,
central proof, owner acceptance, and rollback are separate evidence axes and
are not claimed here. The admission tests prove transaction behavior with
synthetic owner-issued receipts; actual contour admission still requires live
owner-native evidence.
