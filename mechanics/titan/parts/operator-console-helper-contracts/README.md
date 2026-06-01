# Operator Console Helper Contracts

## Role

`operator-console-helper-contracts` keeps Titan console state, event stream,
gate approval, digest, close, validation, and appserver-plan helper contracts
in one SDK-owned route.

## Input

- console state and event payloads
- local operator gate reasons
- appserver-plan prompt inputs

## Output

- `docs/operator-console.md`
- console schemas and examples
- `scripts/titan_console.py`
- `tests/test_titan_console.py`

## Owner

`aoa-sdk` owns helper shape and script behavior. Titan/runtime owners keep
operator consent, role authority, and live console meaning.

## Next Route

Valid console helper state routes to the operator/runtime owner. It does not
activate a Titan or approve a gate by itself.

## Validation

Use `VALIDATION.md`.
