# Incarnation Identity Runtime Helper Contracts Contract

## Contract

The part validates SDK-visible Titan runtime receipt, incarnation, identity,
ingress, and gate helper surfaces without owning live Titan authority.

## SDK-Owned Active Names

- part route: `titan/incarnation-identity-runtime-helper-contracts`
- docs: `docs/runtime-harness.md`, `docs/incarnation-spine.md`, `docs/identity-ledger.md`, `docs/session-ingress.md`
- scripts: `scripts/titanctl.py`, `scripts/titan_incarnation.py`, `scripts/titan_lineage.py`
- schemas: `schemas/titan_*.schema.json`
- examples: `examples/titan_*.example.json`
- tests: `tests/test_titanctl_runtime.py`, `tests/test_titan_incarnation_spine.py`

## Stop-Lines

- Do not treat helper receipts as live runtime state.
- Use `titanctl.py witness-init` rather than `summon` when no live summon is
  being represented; witness receipts must carry explicit no-runtime and
  no-transport fields and contain no summon event.
- Do not treat gate payload validity as operator acceptance.
- Every gate event requires an external decision reference and an explicitly
  unauthenticated approver-attribution label. Recording a gate against a
  witness receipt leaves its incarnation locked and does not claim execution.
- Do not make SDK lineage commands the owner of Titan bearer identity truth.
