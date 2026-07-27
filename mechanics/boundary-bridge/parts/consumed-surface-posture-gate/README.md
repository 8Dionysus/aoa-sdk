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
- the passed G4 evidence chain: immutable release and predecessor-consumer
  pins, compact package proof, full 170-route canonical replay, package trust,
  rollback, and isolated runtime-mirror content/consumer readiness without
  live mutation or premature provenance closure
- the packaged, non-publishing G5 candidate posture: exact clean input refs,
  SDK producer identity, complete artifact/runtime assembly, stronger-owner
  trust handoff, and an installed-wheel gate while every switch-authority flag
  remains false
- the exact public G5 release-candidate envelope: separately profiled release
  lifecycle and trust, deterministic archive, exact verifier/input lock, and
  installed-wheel proof while `aoa-routing` remains canonical and normal
  runtime stays denied
- the receipt-bound G5 canonical envelope: exact public-release byte parity,
  owner-switch receipt, SDK canonical producer authority, compatibility-window
  start, runtime-contract handoff, retained predecessor rollback, and explicit
  denial of archive authority
- the post-G5 compatibility posture: SDK-bundle-first reads, optional
  predecessor discovery, and no active paired CI or release dependency
- the E1 cost comparison: pinned structural CI/release/context reduction,
  unlike-latency stop lines, and a provisional G13 result pending landed CI

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
Then read the passed
[`docs/routing-succession-g4-evidence.md`](docs/routing-succession-g4-evidence.md).
Then read the executable
[`docs/routing-succession-g5-candidate.md`](docs/routing-succession-g5-candidate.md).
Then read the public-trust-only
[`docs/routing-succession-g5-release-candidate.md`](docs/routing-succession-g5-release-candidate.md).
Then read the receipt-bound
[`docs/routing-succession-g5-owner-switch.md`](docs/routing-succession-g5-owner-switch.md).
Then read the measured
[`docs/routing-succession-e1-cost-comparison.md`](docs/routing-succession-e1-cost-comparison.md).
G4 proves the released shadow successor and isolated runtime content path. The
G5 candidate adds native SDK producer identity for trust and canary review.
The release candidate adds exact public release trust without switch
authority. The G5 receipt makes the SDK canonical and starts the compatibility
window. Stronger-owner admission and live cutover have completed; consumer-zero,
rollback retirement, and archival action remain separate.

## Validation

Use `VALIDATION.md`.
