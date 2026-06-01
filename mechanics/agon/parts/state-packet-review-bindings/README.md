# Agon State Packet Review Bindings

## Role

This part owns requested-only SDK bindings for state packet review, sealed
commit drafts, reveal views, and packet stop-line inspection.

## Input

- `config/agon_sdk_state_packet_bindings.seed.json`
- `docs/state-packet-sdk-bridge.md`
- `docs/sealed-commit-helper-candidates.md`

## Output

- `generated/agon_sdk_state_packet_bindings.min.json`

## Owner

`aoa-sdk` owns the binding registry, schemas, example, builders, validators,
tests, and quest record. Agon and actor/runtime owners retain packet grammar,
session body, arena execution, and live commit authority.

## Start Here

- [CONTRACT](CONTRACT.md)
- [VALIDATION](VALIDATION.md)
- [docs](docs/)

## Next Route

Accepted packet meaning routes to Agon and runtime owners; this part stays
pre-runtime and review-only.
