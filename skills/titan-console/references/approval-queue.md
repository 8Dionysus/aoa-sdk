# Approval-queue mode

Use for one visible app-server approval request. Queue state is replayable
witness data, not operator authentication.

1. Select `inspect` or `decide`. Both require a bridge session path and exact
   request id. `inspect` is read-only and does not require an operator
   decision. `decide` additionally requires the current queue entry, exact
   external operator decision ref, explicit decision, and bounded summary.
2. For `inspect`, read the bounded session, run the owner helper `validate`
   and `metrics` commands, and return the matching queue entry plus visible
   request or decision events. Report missing thread, turn, receipt, gate, or
   actor identity; do not invent a mapping. These commands inspect local data
   and do not launch a Titan, agent, app-server, or transport. Run them unless
   the user explicitly forbids local helper commands, rather than interpreting
   a no-runtime or no-send boundary as a ban on read-only validation.
3. For `decide`, inspect the bridge before writing. If the external decision
   ref or explicit decision is absent, return
   `blocked_missing_external_approval` and do not call
   `approval-decision`. A missing ref does not block `inspect`.
4. In `decide`, record only the supplied decision:

   `python <owner_root>/mechanics/titan/parts/appserver-bridge-helper-contracts/scripts/titan_appserver_bridge.py approval-decision --session <session> --request-id <id> --decision <accept|acceptForSession|decline|cancel> --decision-ref <external-ref> --decided-by <supplied-label> --summary <summary>`

5. After a decision write, rerun `validate` and `metrics` and compare the
   before and after entry. Require the witness itself to preserve
   `decision_ref`, `decided_by`, `decided_by_authenticated: false`, and
   `authority: witness_only`; the label is attribution, not authentication.
6. Return operation, queue state, visible request/decision evidence, external
   decision ref when applicable, witness artifact, owner validation, metrics,
   actual file effects, and `runtime_execution_state: not_run`.

Never infer approval from queue presence or from the helper accepting a
synthetic decision.
