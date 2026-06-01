# Titan Provenance

## Source Surfaces

- `src/aoa_sdk/titans/`
- `mechanics/titan/parts/incarnation-identity-runtime-helper-contracts/`
- `mechanics/titan/parts/operator-console-helper-contracts/`
- `mechanics/titan/parts/appserver-bridge-helper-contracts/`
- `mechanics/titan/parts/memory-loom-recall-helper-contracts/`
- `mechanics/titan/parts/session-praxis-replay-helper-contracts/`
- `mechanics/titan/parts/swarm-ledger-closeout-helper-contracts/`

## Stronger Owners

Titan runtime, identity, role, memory, proof, operator approval, and live
service-cohort authority remain outside the SDK.

## Moved Root Families

- `docs/TITAN_RUNTIME_HARNESS.md`, `docs/TITAN_INCARNATION_SPINE.md`, `docs/TITAN_IDENTITY_LEDGER.md`, `docs/TITAN_SESSION_INGRESS.md`, related schemas, examples, scripts, and tests -> `mechanics/titan/parts/incarnation-identity-runtime-helper-contracts/`
- `docs/TITAN_OPERATOR_CONSOLE.md`, console schemas, examples, script, and test -> `mechanics/titan/parts/operator-console-helper-contracts/`
- `docs/TITAN_APPSERVER_BRIDGE.md`, `docs/TITAN_APPSERVER_EVENT_REPLAY.md`, bridge schemas, examples, script, and test -> `mechanics/titan/parts/appserver-bridge-helper-contracts/`
- `docs/TITAN_MEMORY_LOOM.md`, `docs/TITAN_MEMORY_RECALL_PROTOCOL.md`, memory/recall schemas, examples, script, and test -> `mechanics/titan/parts/memory-loom-recall-helper-contracts/`
- `docs/TITAN_PRAXIS_REPLAY.md`, replay schemas, visible-session example, script, and test -> `mechanics/titan/parts/session-praxis-replay-helper-contracts/`
- `docs/TITAN_SWARM_LEDGER.md`, `docs/TITAN_CLOSEOUT_AUDIT.md`, swarm/closeout schemas, examples, script, and tests -> `mechanics/titan/parts/swarm-ledger-closeout-helper-contracts/`

## Notes

This shared mechanic name is preserved because Titan helper packages recur
across AoA topology, while this SDK only exposes control-plane handles.
