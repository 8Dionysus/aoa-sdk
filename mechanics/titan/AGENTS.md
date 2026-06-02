# AGENTS.md

## Applies to

`mechanics/titan/`.

## Role

Route the shared Titan mechanic for SDK helper contracts around incarnation,
runtime receipts, operator console, appserver bridge, memory loom, visible
session replay, and swarm closeout.

## Read before editing

- `mechanics/AGENTS.md`
- `mechanics/titan/README.md`
- `mechanics/titan/PARTS.md`
- `mechanics/titan/PROVENANCE.md`
- `mechanics/titan/parts/`
- `src/aoa_sdk/titans/`

## Boundaries

- Stay on the control plane.
- Keep active Titan artifacts under `mechanics/titan/parts/<part>/`.
- Do not turn SDK Titan helpers into Titan runtime, role, identity, or memory authority.
- Do not turn SDK Titan helpers into operator authority.
- Keep launch, approval, replay, recall, and closeout artifacts explicit and
  inspectable.

## Validation

```bash
python scripts/validate_mechanics_topology.py
python -m pytest -q mechanics/titan/parts/incarnation-identity-runtime-helper-contracts/tests/test_titanctl_runtime.py mechanics/titan/parts/incarnation-identity-runtime-helper-contracts/tests/test_titan_incarnation_spine.py
python -m pytest -q mechanics/titan/parts/operator-console-helper-contracts/tests/test_titan_console.py mechanics/titan/parts/appserver-bridge-helper-contracts/tests/test_titan_appserver_bridge.py mechanics/titan/parts/memory-loom-recall-helper-contracts/tests/test_titan_memory_loom.py mechanics/titan/parts/session-praxis-replay-helper-contracts/tests/test_titan_session_replay.py mechanics/titan/parts/swarm-ledger-closeout-helper-contracts/tests/test_titan_swarm_ledger.py mechanics/titan/parts/swarm-ledger-closeout-helper-contracts/tests/test_titan_closeout_audit.py
```

## Closeout

Report which Titan helper route changed and which runtime, memory, proof, or
owner authority remains outside SDK.
