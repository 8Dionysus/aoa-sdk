# Bridge mode

Use one visible bridge session as an inspectable local witness.

1. Require explicit workspace, bridge path, source kind, source refs, and
   requested operation.
2. Read the owner bridge README and command help.
3. Use `init` only to create a requested local session, passing the exact
   visible provenance:

   `python <owner_root>/mechanics/titan/parts/appserver-bridge-helper-contracts/scripts/titan_appserver_bridge.py init --workspace <workspace> --source-kind <kind> --source-ref <ref> --out <session>`

   Use `render`, `replay`, `metrics`, `validate`, or `close` only on that
   bounded session.
4. If the request is only an approval queue status or decision, hand it to
   `titan-console/approval-queue`; do not continue this mode.
   If it is an explicit Forge or Delta gate decision for the bridge ledger,
   hand it to `titan-console/approval-witness`.
5. If `emit` is requested, write the local event witness and report
   `transport_state: unsent`; the helper has no network send authority.
6. Run:

   `python <owner_root>/mechanics/titan/parts/appserver-bridge-helper-contracts/scripts/titan_appserver_bridge.py validate --session <session>`

7. Return visible source refs, normalized state, approval witness posture,
   metrics when requested, actual local file effects,
   `execution_state: not_run`, and runtime-owner handoff.

For a newly initialized local bridge, require
`surface_role: titan_appserver_bridge_witness`, `authority: witness_only`,
`runtime_execution_state: not_run`, `transport_state: not_sent`, and
`state_semantics: helper_projection_only`. The ungated roster must be
`declared`, not `active`. Recheck that `source_kind` and `source_ref` remain
exact after every helper write.

Never call a process launcher, child-agent interface, or live steering route.
