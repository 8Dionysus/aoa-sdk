# Incarnation Identity Runtime Helper Contracts

## Role

`incarnation-identity-runtime-helper-contracts` keeps Titan runtime receipt,
incarnation, identity ledger, session ingress, and gate helper contracts in one
SDK-owned route.

## Input

- runtime receipt and ingress payloads
- Forge and Delta gate payloads
- bearer identity and lineage command inputs

## Output

- `docs/` runtime, incarnation, identity, and ingress notes
- `schemas/` receipt, runtime-event, incarnation, ingress, and gate contracts
- `examples/` receipt, ingress, and gate examples
- `scripts/titanctl.py`, `scripts/titan_incarnation.py`, `scripts/titan_lineage.py`
- `tests/test_titanctl_runtime.py` and `tests/test_titan_incarnation_spine.py`

## Owner

`aoa-sdk` owns helper shape, script wrappers, examples, and validation. Titan
role owners and runtime owners keep bearer identity truth, live activation,
gate authority, and accepted lineage meaning.

## Next Route

Valid helper payloads route to Titan role/runtime owners. They do not summon a
live cohort or accept a gate by themselves.

## Validation

Use `VALIDATION.md`.
