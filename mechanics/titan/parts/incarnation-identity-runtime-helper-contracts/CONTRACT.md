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
- Do not treat gate payload validity as operator acceptance.
- Do not make SDK lineage commands the owner of Titan bearer identity truth.
