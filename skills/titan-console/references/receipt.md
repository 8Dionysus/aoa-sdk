# Receipt mode

Use one local Titan receipt as a witness for an intended or observed boundary.
It cannot prove a Titan, process, or child was launched.

1. Require explicit receipt intent, bounded path, workspace, event identity,
   source refs, and recorder attribution. Never infer a human or operator
   identity. If none was supplied, use the literal helper-field value
   `unattributed-local-recorder` and report that attribution is unresolved.
2. For a new intent or observation witness, run:

   `python <owner_root>/mechanics/titan/parts/incarnation-identity-runtime-helper-contracts/scripts/titanctl.py witness-init --workspace <workspace> --recorder <recorder-attribution> --event-id <event-id> --intent <intent> --lane <lane> --source-ref <source-ref> --out <receipt>`

   Require `surface_role: titan_receipt_witness`,
   `runtime_execution_state: not_run`, `transport_state: not_sent`,
   `authority: witness_only`, and no `summon` event. Use the historical
   `summon` command only when the input is an explicit summon receipt request;
   never use it as a generic JSON constructor.
3. Use `note` or `closeout` only for the explicitly requested operation on an
   existing receipt. A gate update belongs to `approval-witness`; for a request
   spanning receipt creation and approval recording, build a two-node
   task-local DAG and load that mode only after the receipt exists.
4. Run:

   `python <owner_root>/mechanics/titan/parts/incarnation-identity-runtime-helper-contracts/scripts/titanctl.py validate --receipt <receipt>`

5. Return the receipt path, state, source refs, recorder attribution,
   `operator_field_authenticated: false`, validation, actual file effects,
   `runtime_execution_state: unknown_or_not_run`, and owner handoff.

Do not treat a schema-valid receipt as runtime, proof, role, or memory truth.
