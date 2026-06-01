# Office Release Train Helper Contracts

## Role

`office-release-train-helper-contracts` is the Experience part that keeps
installation, operator-console, sovereign release, handoff graph, office
registry, and office train helper contracts in one SDK-owned bundle.

## Input

- install, console, and release helper examples
- handoff graph, office registry, and office train examples
- office/release-train API notes

## Output

- `docs/` office and release-train helper notes
- `schemas/sdk_*_api_call_v1.json`
- `examples/sdk_*_api_call_v1.example.json`
- `tests/test_office_release_train_helper_contracts.py`

## Owner

`aoa-sdk` owns helper contract shape, examples, and regression checks. Office
and release owners keep installation approval, operator authority, office
activation, handoff meaning, and release-train acceptance.

## Next Route

Valid helper contracts route to office/release owners. They do not install,
activate, approve, or write runtime office state.

## Validation

Use `VALIDATION.md`.
