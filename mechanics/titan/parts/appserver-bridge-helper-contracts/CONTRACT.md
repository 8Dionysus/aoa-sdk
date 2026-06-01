# Appserver Bridge Helper Contracts Contract

## Contract

The part validates SDK-visible Titan app-server bridge helper surfaces without
owning Codex app-server execution.

## SDK-Owned Active Names

- part route: `titan/appserver-bridge-helper-contracts`
- docs: `docs/appserver-bridge.md`, `docs/appserver-event-replay.md`
- script: `scripts/titan_appserver_bridge.py`
- schemas: bridge session, event, approval, metrics, and launch-plan schemas
- examples: bridge session, event-stream, launch-plan, and seed examples
- tests: `tests/test_titan_appserver_bridge.py`

## Stop-Lines

- Do not treat replayed approvals as operator decisions.
- Do not make bridge launch messages a live app-server rollout.
- Do not keep appserver bridge helper artifacts in root technical districts.
