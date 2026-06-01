# Adoption Federation Helper Contracts

## Role

`adoption-federation-helper-contracts` is the Experience part that keeps
owner-local adoption calls, shadow runs, federation signals, harvest records,
pattern candidates, and dossier readouts in one SDK-owned contract bundle.

## Input

- adoption request, dashboard, rollback, and shadow-run payloads
- cross-repo signal and harvest payloads
- KAG, ToS, and pattern registry dossier payloads

## Output

- `docs/` helper API notes
- `schemas/sdk_*_call_v1.json`
- `examples/sdk_*_call.example.json`
- `tests/test_adoption_federation_helper_contracts.py`

## Owner

`aoa-sdk` owns typed helper contract shape, examples, and regression checks.
Experience owners keep adoption consent, federation meaning, KAG/ToS judgment,
and uptake authority.

## Next Route

Valid helper payloads route to the local Experience owner for review. They do
not authorize adoption or cross-repo propagation.

## Validation

Use `VALIDATION.md`.
