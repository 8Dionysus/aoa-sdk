# Consumed Surface Posture Gate

## Role

`consumed-surface-posture-gate` is the Boundary Bridge part that checks
whether sibling-owned surfaces are safe to read before SDK facades trust them.

## Input

- sibling generated surfaces and owner-local mechanics paths
- `src/aoa_sdk/compatibility/` rules
- `aoa compatibility check ...` CLI calls
- typed facade readers under `src/aoa_sdk/agents`, `evals`,
  `governed_runs`, `kag`, `memo`, `playbooks`, `routing`, and `stats`
- workspace fixture surfaces used for compatibility regression tests

## Output

- compatibility reports and fail-closed mismatch errors
- typed SDK readouts that preserve source-owner authority
- routing action checks that reject unmapped surface reads
- facade regression tests bound to part-local validation
- read-only succession baselines that pin consumed producer, consumer,
  runtime, trust, cost, and disposition evidence without switching authority
- the accepted routing succession target model, authority matrix,
  compatibility policy, and repository state machine without moving producer
  code or switching live authority
- the R2 strict route, plan, approval, lifecycle, event, evidence-reference,
  and runtime-adapter contracts plus golden-scenario and threat-model evidence,
  without implementing runtime execution
- the R3 disposable producer-migration rehearsal, including byte/schema/count
  parity, installed-wheel construction without an `aoa-routing` checkout,
  rollback, exact PR order, admitted M1 integration debt, and cleanup evidence
- the M1 packaged, typed, non-publishing SDK shadow producer, strict validator,
  dual-producer sidecar, pinned predecessor parity CI, and installed-wheel gate

## Owner

`aoa-sdk` owns the read gate, typed handles, compatibility rules, and local
truth labels. Sibling repositories own the meaning, freshness, and lifecycle of
the consumed surfaces.

## Next Route

When a sibling surface changes shape, update the owning sibling repo and its
public contract first, then update this gate, facade models, fixtures, and
compatibility expectations.

For the proposed `aoa-routing` succession, start with
[`docs/routing-succession-r0-baseline.md`](docs/routing-succession-r0-baseline.md).
Then read the accepted
[`docs/routing-succession-r1-target-operating-model.md`](docs/routing-succession-r1-target-operating-model.md).
Then read the checked
[`docs/routing-succession-r2-agent-os-contracts.md`](docs/routing-succession-r2-agent-os-contracts.md).
Then read the completed
[`docs/routing-succession-r3-migration-rehearsal.md`](docs/routing-succession-r3-migration-rehearsal.md).
Then read the implemented
[`docs/routing-succession-m1-shadow-producer.md`](docs/routing-succession-m1-shadow-producer.md).
M1 makes the successor executable in non-publishing shadow posture. It does
not pass G4, authorize canonical publication, mutate runtime, switch an owner,
or authorize archival action.

## Validation

Use `VALIDATION.md`.
