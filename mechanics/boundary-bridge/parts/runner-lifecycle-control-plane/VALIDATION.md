# Validation

Repository-wide source-home, workspace-capsule, package-build, release, and full-suite checks are owned by [root `VALIDATION.md`](../../../../VALIDATION.md#focused-repository-checks) and [its release-facing lane](../../../../VALIDATION.md#release-facing-and-full-owner-checks).

Run:

```bash
python -m pytest -q mechanics/boundary-bridge/parts/runner-lifecycle-control-plane/tests
python -m pytest -q mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_routing_succession_r2_control_plane_contracts.py mechanics/boundary-bridge/parts/plan-compilation-control-plane/tests/test_plan_compilation_control_plane.py
python -m mypy src/aoa_sdk/contracts/control_plane.py src/aoa_sdk/contracts/goal_lifecycle.py src/aoa_sdk/control_plane src/aoa_sdk/api.py
python -m ruff check src/aoa_sdk/contracts/control_plane.py src/aoa_sdk/contracts/goal_lifecycle.py src/aoa_sdk/control_plane src/aoa_sdk/api.py mechanics/boundary-bridge/parts/runner-lifecycle-control-plane
python mechanics/boundary-bridge/parts/runner-lifecycle-control-plane/scripts/verify_runner_wheel.py
PATH_TO_WHEEL_VENV/bin/python mechanics/boundary-bridge/parts/runner-lifecycle-control-plane/scripts/verify_isolated_runtime_lifecycle.py --chain PATH_TO_TYPED_ROUTE_PLAN_CHAIN.json --output PATH_TO_SESSION_LOCAL_RECEIPT.json
```

The focused suite covers:

- all three C2 golden plans through one Runner/reference-adapter contract;
- normal completion and owner-complete closeout;
- sequential multiple approvals, rejected and expired approvals, plus renewal;
- pause/resume;
- owner-resolved Goal lifecycle legitimacy for delegation yield and accepted
  return, including stale-state rejection and exact adapter scope;
- duplicate start, command, and approval;
- repeat of a rejected command with no new event or receipt;
- idempotency payload mismatch;
- partial failure;
- disconnect before and after command acknowledgement, including durable
  receipt import before replay;
- out-of-order, tampered, or receipt-inconsistent runtime evidence;
- cross-slice event-ID reuse and status timestamps older than accepted events;
- exact approval request/decision event-reference correlation;
- exclusive approval-TTL boundary enforcement;
- exact runtime-outcome event-reference correlation;
- atomic rollback after invalid approval, outcome, receipt, or closeout views;
- restored ordered receipt-to-event-slice and acknowledgement correlation;
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

The isolated-runtime verifier accepts a separately validated typed
route-to-plan chain, derives an explicitly labelled retry-policy test
variation, and exercises duplicate commands, multiple approvals, pause/resume,
disconnect, interruption, bounded recovery, 64 progress events,
`SessionHandle` restoration, terminal outcome, and closeout. Its JSON receipt
retains the base and test plan digests and never claims the test variation was
compiler output.

These checks do not select a production adapter, execute a plan step, call a
model or tool, produce an eval verdict, retain memory, prove task benefit,
measure cost reduction, establish consumer-zero, or authorize archival.

The repository-wide topology gate is owned by [root `VALIDATION.md`](../../../../VALIDATION.md#focused-repository-checks).
