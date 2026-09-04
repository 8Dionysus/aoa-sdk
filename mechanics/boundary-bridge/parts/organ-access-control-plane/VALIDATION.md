# Validation

Run:

```bash
python mechanics/boundary-bridge/parts/organ-access-control-plane/scripts/generate_organ_access_schemas.py --check
python mechanics/boundary-bridge/parts/organ-access-control-plane/scripts/generate_organ_access_example.py --check
pytest -q mechanics/boundary-bridge/parts/organ-access-control-plane/tests
mypy src/aoa_sdk/contracts/organs.py src/aoa_sdk/organs src/aoa_sdk/cli/organs.py
ruff check src/aoa_sdk/contracts/organ_registry_v2.py src/aoa_sdk/contracts/admission_keeper.py src/aoa_sdk/contracts/tasks.py src/aoa_sdk/organs/registry_v2.py src/aoa_sdk/organs/admission_keeper.py src/aoa_sdk/organs/task_store.py mechanics/boundary-bridge/parts/organ-access-control-plane/tests/test_mcp_next_control_plane.py
```

Schema parity also enforces owner placement: v2 contour, Keeper, and TaskStore
schemas are part-local, while only the established v1 compatibility family
remains under the root schema district.

The tests cover strict schemas, effect-policy matching, isolated credential
contours, secret rejection, admission gates, deterministic projection,
suspension, catalog byte budgets, explicit workspace configuration,
candidate-only activation, schema drift, approvals, exact external targets,
typed owner payloads, owner-bounded result review, content-addressed review
receipts, CLI discovery, resumable admission, idempotent replay, typed stops,
owner/proof/acceptance separation, registry drift, separate owner/operator
decisions, non-mutating transition authorization, and projection-owned index
evidence, plus current-versus-expired baseline auditing.
The focused MCP-next cases additionally cover v1-to-v2 preservation,
shadow-only contour supplements, non-admitting runtime overlays, immutable and
incremental Keeper reuse with expiry downgrade, TaskStore principal binding,
CAS/idempotency, cancellation, TTL, quota, payload bounds, and restart-visible
state. Adversarial storage cases reject caller-supplied symlink roots and
symlinked internal directories, while a concurrent event/timer case proves two
Keeper triggers serialize into revisions one and two without duplicate node
publication or a lost CAS update.

Runtime deployment, consumer pairing, live freshness, grounded results,
central proof, owner acceptance, and rollback are separate evidence axes and
are not claimed here. The admission tests prove transaction behavior with
synthetic owner-issued receipts; actual contour admission still requires live
owner-native evidence.
TaskStore tests likewise prove storage mechanics only, not MCP Tasks client
support, owner work completion, or production readiness. The aggregate-status
case reopens the store, reports bounded load/cancellation/expiry/quota facts,
and proves that neither task IDs nor principal IDs enter the projection.

The repository-wide topology gate is owned by [root `VALIDATION.md`](../../../../VALIDATION.md#focused-repository-checks).
