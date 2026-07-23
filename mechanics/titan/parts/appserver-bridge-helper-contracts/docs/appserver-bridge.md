# Titan App-Server Bridge

Local-first witness helper for Codex app-server style JSON-RPC. It emits
unsent launch-message data, replays visible event streams, tracks approval
witnesses, preserves Titan gate records, and derives metrics from receipts.

New bridge sessions declare Atlas, Sentinel, and Mneme in helper state; they do
not mark any Titan active. The artifact carries `witness_only`,
`runtime_execution_state: not_run`, `transport_state: not_sent`, and
`helper_projection_only` explicitly. None of these fields is runtime proof.
Initialization also requires a visible `source_kind` and `source_ref`; every
subsequent helper write preserves them.

Approval requests remain pending witness records until an explicit decision is
recorded with an external `decision_ref`. The supplied `decided_by` value is an
unauthenticated attribution label, not proof of operator identity. A recorded
decision cannot be overwritten.

Gate witnesses use the same provenance law: `gate` requires an external
decision reference and an unauthenticated approver-attribution label. An
`active` bridge roster entry remains helper projection state, not runtime
execution.
