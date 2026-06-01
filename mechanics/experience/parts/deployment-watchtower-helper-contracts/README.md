# Deployment Watchtower Helper Contracts

## Role

`deployment-watchtower-helper-contracts` is the Experience part that keeps
certification, deployment, regression, release-candidate, rollback, and
watchtower helper calls in one bounded SDK contract bundle.

## Input

- certification helper examples
- deployment, rollback, and watchtower call examples
- regression runner and release-candidate helper notes

## Output

- `docs/` deployment and watchtower helper notes
- `schemas/*_v1.json`
- `examples/*.example.json`
- `tests/test_deployment_watchtower_helper_contracts.py`

## Owner

`aoa-sdk` owns helper shape and regression checks. Experience release owners
keep deployment truth, certification force, watchtower meaning, rollback
authority, and release acceptance.

## Next Route

Valid helper payloads route to release/watchtower owners for review. They do
not deploy, roll back, certify, or release anything by themselves.

## Validation

Use `VALIDATION.md`.
