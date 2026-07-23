# Approval-witness mode

Record only an already explicit, externally attributable operator decision.
The SDK helper does not authenticate the operator.

1. Require the exact external decision ref, approver-attribution label, target
   lane, gate kind, bounded intent, ledger kind (`console`, `receipt`, or
   `bridge`), and exact ledger path.
2. Require `Forge + mutation` or `Delta + judgment`; reject crossed or merged
   gates.
3. Inspect the target state before writing. If the external decision ref is
   missing or ambiguous, return `blocked_missing_external_approval`.
4. Select exactly one owner helper and pass explicit `--decision-ref` and
   `--approved-by`:

   - Console ledger:

     `python <owner_root>/mechanics/titan/parts/operator-console-helper-contracts/scripts/titan_console.py gate --state <state> --titan <Forge|Delta> --gate <mutation|judgment> --reason <bounded-reason> --decision-ref <external-ref> --approved-by <attribution>`

   - Receipt ledger:

     `python <owner_root>/mechanics/titan/parts/incarnation-identity-runtime-helper-contracts/scripts/titanctl.py gate --receipt <receipt> --agent <Forge|Delta> --kind <mutation|judgment> --intent <bounded-intent> --decision-ref <external-ref> --approved-by <attribution> <explicit-payload-fields>`

     For Forge require mutation surface, one or more scopes, expected files,
     rollback note, and test plan. For Delta require claim, criteria, evidence
     refs, and verdict scope. Do not use helper-generated placeholder payload
     values. On a `witness-init` receipt the gate event is recorded but the
     incarnation must remain locked.

   - Bridge ledger:

     `python <owner_root>/mechanics/titan/parts/appserver-bridge-helper-contracts/scripts/titan_appserver_bridge.py gate --session <session> --titan <Forge|Delta> --gate <mutation|judgment> --reason <bounded-reason> --decision-ref <external-ref> --approved-by <attribution>`

5. Validate with the matching owner helper and require the written approval or
   gate record itself to preserve `decision_ref`, `approved_by`,
   `approved_by_authenticated: false`, and `authority: witness_only`.
6. Report ledger kind, before and after state, `approval_state: witness_only`,
   actual file effects, and runtime-owner handoff. The record neither
   authorizes nor enforces runtime action.
