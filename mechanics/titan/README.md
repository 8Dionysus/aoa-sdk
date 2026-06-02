# Titan Mechanic

Status: active topology with part-local payload.

## Mechanic Card

### Operation

Expose bounded Titan SDK helper contracts for incarnation/runtime receipts,
operator console, appserver bridge, memory loom and recall, visible session
replay, and swarm closeout.

### Trigger

Use this mechanic when Titan SDK source modules, helper scripts, docs, schemas,
examples, or tests change.

### SDK owns

- typed Titan control-plane helper APIs
- part-local CLI helper scripts and public-safe examples
- schema/example validation for Titan helper packets
- local docs that state SDK stop-lines
- part-local route cards for each active helper family

### Stronger owner split

Titan runtime, role authority, identity truth, memory truth, proof verdicts,
operator approval, and live service-cohort acceptance remain outside SDK
ownership.

### Current source surfaces

- `src/aoa_sdk/titans/`
- `mechanics/titan/parts/incarnation-identity-runtime-helper-contracts/`
- `mechanics/titan/parts/operator-console-helper-contracts/`
- `mechanics/titan/parts/appserver-bridge-helper-contracts/`
- `mechanics/titan/parts/memory-loom-recall-helper-contracts/`
- `mechanics/titan/parts/session-praxis-replay-helper-contracts/`
- `mechanics/titan/parts/swarm-ledger-closeout-helper-contracts/`

### Active parts

- incarnation-identity-runtime-helper-contracts
- operator-console-helper-contracts
- appserver-bridge-helper-contracts
- memory-loom-recall-helper-contracts
- session-praxis-replay-helper-contracts
- swarm-ledger-closeout-helper-contracts

### Candidate parts

No active Titan helper family remains in root technical districts. Future
candidate parts must name a distinct SDK helper contract route and must not
reuse root script names as route names.

### Must not claim

This mechanic must not present helper packets as live Titan runtime state,
accepted operator decisions, accepted memory, role truth, or proof verdicts.

### Validation

Use the touched part `VALIDATION.md` for executable checks. For package-wide
route changes, use `mechanics/topology.json` for the active validation list
and then run the mechanics topology gate from the root route card.

### Next route

Runtime, role, memory, proof, and operator authority changes route to their
stronger owner layers; SDK keeps bounded helpers, docs, contracts, scripts,
and tests.
