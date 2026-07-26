# Validation

Run:

```bash
python -m pytest -q mechanics/boundary-bridge/parts/runner-lifecycle-control-plane/tests
python -m pytest -q mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_routing_succession_r2_control_plane_contracts.py mechanics/boundary-bridge/parts/plan-compilation-control-plane/tests/test_plan_compilation_control_plane.py
python -m mypy src/aoa_sdk/contracts/control_plane.py src/aoa_sdk/control_plane src/aoa_sdk/api.py
python -m ruff check src/aoa_sdk/contracts/control_plane.py src/aoa_sdk/control_plane src/aoa_sdk/api.py mechanics/boundary-bridge/parts/runner-lifecycle-control-plane
python scripts/validate_mechanics_topology.py
python scripts/validate_sdk_source_home.py
python -m build
python mechanics/boundary-bridge/parts/runner-lifecycle-control-plane/scripts/verify_runner_wheel.py
```

The focused suite covers:

- all three C2 golden plans through one Runner/reference-adapter contract;
- normal completion and owner-complete closeout;
- rejected and expired approvals plus renewal;
- pause/resume;
- duplicate start, command, and approval;
- repeat of a rejected command with no new event or receipt;
- idempotency payload mismatch;
- partial failure;
- disconnect before and after command acknowledgement;
- out-of-order, tampered, or receipt-inconsistent runtime evidence;
- exact approval request/decision event-reference correlation;
- exact runtime-outcome event-reference correlation;
- restored receipt-to-event-slice and acknowledgement correlation;
- exact snapshot drift rejection before dispatch;
- stale observation-time rejection before dispatch;
- recoverable failure, recover-to-paused, resume, completion, and closeout;
- retryable-code and maximum-attempt enforcement before recovery dispatch;
- explicit cancellation with a typed terminal outcome;
- restoration of verified status, events, approvals, and command replay from a
  `SessionHandle` plus durable adapter state;
- rejection of partial closeout.

The installed-wheel probe compiles a plan from packaged C2 resources, runs the
non-executing C3 lifecycle, reconciles a typed outcome, and restores a fresh
Runner without importing the source checkout or requiring an
`aoa-playbooks` checkout.

These checks do not select a production adapter, execute a plan step, call a
model or tool, produce an eval verdict, retain memory, prove task benefit,
measure cost reduction, establish consumer-zero, or authorize archival.
