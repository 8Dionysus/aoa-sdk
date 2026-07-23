# Console mode

Use for one visible console witness. Read the owner helper README and command
help before execution.

1. Require explicit workspace, output path, and Titan intent. Treat `operator`
   as local attribution, never authentication. When the user has not supplied
   an externally sourced operator label, use the literal
   `unattributed-local-operator` and report the attribution unresolved.
2. Create state only when requested:

   `python <owner_root>/mechanics/titan/parts/operator-console-helper-contracts/scripts/titan_console.py new --workspace <workspace> --operator <operator> --out <state>`

3. Require a new state to carry `surface_role: titan_console_witness`,
   `authority: witness_only`, `runtime_execution_state: not_run`,
   `transport_state: not_sent`, `state_semantics: helper_projection_only`, and
   `operator_field_authenticated: false`. Require Atlas, Sentinel, and Mneme
   to begin `declared`, Forge and Delta `locked`, and the active digest empty.
4. For an update, inspect current state first and add only the requested event.
   Valid actors are `operator`, `console`, Atlas, Sentinel, Mneme, Forge, and
   Delta. Use `console` for a helper-produced observation; do not invent an
   operator or Titan actor. Never use a console event to imply runtime action.
5. Use `digest` for a derived summary and `close` only on explicit close intent.
6. Run `validate --state <state>` after every write.
7. Return the state path, event or digest summary, validation result,
   `execution_state: not_run`, actual file effects, and the stronger owner
   needed for any live action.

Do not call `gate` in this mode. Approval recording belongs to
`approval-witness`.
