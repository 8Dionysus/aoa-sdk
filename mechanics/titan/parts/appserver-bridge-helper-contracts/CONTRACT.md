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
- Preserve an explicit external decision reference and an unauthenticated
  attribution label in every local gate or approval-decision witness. Never
  overwrite an existing decision.
- Do not make bridge launch messages a live app-server rollout.
- Keep new bridge sessions witness-only: declared roster membership is not
  runtime activation, and local replay is not transport.
- Require an explicit visible source kind and source ref when a bridge session
  is initialized, and preserve both through every helper read-write cycle.
- Do not keep appserver bridge helper artifacts in root technical districts.
