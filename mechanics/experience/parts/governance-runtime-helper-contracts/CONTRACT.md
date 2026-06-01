# Governance Runtime Helper Contracts Contract

## Contract

The part validates SDK helper contracts for governance runtime surfaces while
keeping governance authority outside `aoa-sdk`.

## SDK-Owned Active Names

- part route: `experience/governance-runtime-helper-contracts`
- docs: `docs/governance-api.md`, `docs/constitution-runtime-api.md`, queue, sealing, and replay notes
- schemas: `schemas/*_v1.json`
- examples: `examples/*.example.json`
- tests: `tests/test_governance_runtime_helper_contracts.py`

## Stop-Lines

- Do not treat schema validity as council approval, appeal success, veto force,
  or sealed-vote truth.
- Do not absorb governance queue ownership into SDK docs.
- Do not keep active governance runtime contracts in root technical districts.
