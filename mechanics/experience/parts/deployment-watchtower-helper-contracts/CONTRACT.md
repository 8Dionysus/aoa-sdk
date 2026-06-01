# Deployment Watchtower Helper Contracts Contract

## Contract

The part validates SDK helper contracts for deployment, regression, rollback,
watchtower, and certification readouts without owning operational execution.

## SDK-Owned Active Names

- part route: `experience/deployment-watchtower-helper-contracts`
- docs: `docs/deployment-api.md`, `docs/watchtower-api.md`, certification, regression, release, and rollback notes
- schemas: `schemas/*_v1.json`
- examples: `examples/*.example.json`
- tests: `tests/test_deployment_watchtower_helper_contracts.py`

## Stop-Lines

- Do not treat helper validity as deployment approval, rollback authority, or
  certification truth.
- Do not collapse watchtower readouts into release decisions.
- Do not keep active deployment/watchtower contracts in root technical
  districts.
