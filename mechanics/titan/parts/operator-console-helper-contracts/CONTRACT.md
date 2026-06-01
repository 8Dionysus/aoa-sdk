# Operator Console Helper Contracts Contract

## Contract

The part validates SDK-visible Titan console helper state without becoming the
operator authority.

## SDK-Owned Active Names

- part route: `titan/operator-console-helper-contracts`
- docs: `docs/operator-console.md`
- script: `scripts/titan_console.py`
- schemas: console state, console event, and operator approval schemas
- examples: console state and event-stream examples
- tests: `tests/test_titan_console.py`

## Stop-Lines

- Do not treat console state validity as live operator approval.
- Do not widen appserver-plan output into Codex projection authority.
- Do not keep console helper artifacts in root technical districts.
