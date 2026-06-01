# Swarm Ledger Closeout Helper Contracts

## Role

`swarm-ledger-closeout-helper-contracts` keeps Titan task, report, finding,
grade, timeout, swarm ledger, and closeout audit helper contracts in one
SDK-owned route.

## Input

- task contracts and reports
- finding, grade, timeout, and closeout audit payloads
- closeout memory candidate traces

## Output

- swarm and closeout docs
- ledger/closeout schemas and examples
- `scripts/titan_swarm.py`
- `tests/test_titan_swarm_ledger.py` and `tests/test_titan_closeout_audit.py`

## Owner

`aoa-sdk` owns helper shape and local validation. Titan, memo, eval, and source
owners keep participation meaning, memory acceptance, proof verdicts, and
owner truth.

## Next Route

Valid ledger records route to review and memory-owner verification. They do
not make reports true or memory candidates accepted.

## Validation

Use `VALIDATION.md`.
