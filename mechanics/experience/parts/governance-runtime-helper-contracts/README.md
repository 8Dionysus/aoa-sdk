# Governance Runtime Helper Contracts

## Role

`governance-runtime-helper-contracts` is the Experience part that keeps council,
appeal, veto, constitution-runtime, queue, sealing, and replay helper contracts
as SDK-owned typed surfaces.

## Input

- governance, council, appeal, and veto contract examples
- constitution runtime call examples
- queue, sealing, and replay helper API notes

## Output

- `docs/` governance runtime helper notes
- `schemas/*_v1.json`
- `examples/*.example.json`
- `tests/test_governance_runtime_helper_contracts.py`

## Owner

`aoa-sdk` owns shape, example safety, and validation. Governance owners keep
decision authority, council meaning, veto force, vote sealing truth, and replay
acceptance.

## Next Route

Valid helper contracts route to the governance owner. They do not enact a
decision or seal a vote.

## Validation

Use `VALIDATION.md`.
