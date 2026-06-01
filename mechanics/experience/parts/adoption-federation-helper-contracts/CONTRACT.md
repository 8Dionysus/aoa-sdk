# Adoption Federation Helper Contracts Contract

## Contract

The part validates SDK helper calls that describe adoption and federation work
without executing that work or claiming owner acceptance.

## SDK-Owned Active Names

- part route: `experience/adoption-federation-helper-contracts`
- docs: `docs/adoption-api.md`, `docs/federation-api.md`, dossier and harvest helper notes
- schemas: `schemas/sdk_*_call_v1.json`
- examples: `examples/sdk_*_call.example.json`
- tests: `tests/test_adoption_federation_helper_contracts.py`

## Stop-Lines

- Do not turn a valid adoption helper call into adoption approval.
- Do not let KAG, ToS, or pattern dossier payloads mint meaning authority.
- Do not move this part back into root `docs/`, `schemas/`, `examples/`, or
  `tests/` as an active surface.
