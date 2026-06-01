# Appserver Bridge Helper Contracts

## Role

`appserver-bridge-helper-contracts` keeps Titan app-server bridge session,
event replay, launch-plan, approval, and metrics helper contracts in one
SDK-owned route.

## Input

- Codex app-server style JSON-RPC messages
- bridge session state
- launch-plan and replay examples

## Output

- appserver bridge docs
- bridge schemas and examples
- `scripts/titan_appserver_bridge.py`
- `tests/test_titan_appserver_bridge.py`

## Owner

`aoa-sdk` owns helper shape and bridge replay validation. Codex projection and
runtime owners keep live app-server authority, approval decisions, and rollout
meaning.

## Next Route

Valid bridge payloads route to the runtime/Codex owner. They do not approve
commands or steer live Codex sessions by themselves.

## Validation

Use `VALIDATION.md`.
