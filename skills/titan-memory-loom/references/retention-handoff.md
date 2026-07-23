# Retention-handoff mode

Prepare an effect-free owner review request. Do not redact, mask, tombstone,
prune, or delete anything in this mode.

1. Require explicit Titan intent, concrete index and record id, requested
   action, reason, source refs, sensitivity posture, and desired scope.
2. Validate and recall the record read-only. Preserve its current state and
   digest.
3. Do **not** call `titan_memory_loom.py redact`. Manual execution established
   that this helper mutates immediately and does not prove `aoa-memo`
   acceptance.
4. Produce `titan-retention-review-request-v1` containing record identity,
   current digest and state, requested action, reason, source refs, risk,
   rollback or recovery need, and explicit `actual_effects: []`.
5. Mark the next owner route as `aoa-memo` review/evolve. Preparing a request
   means `submission_state: prepared_not_submitted`: do not invoke an
   `aoa-memo` tool, MCP, or mutation unless the user separately asks to submit
   the prepared request. Never claim acceptance until that owner returns it.
6. Return `disposition: owner_handoff`, skipped mutation, memo route, and stop
   line.

A local tombstone would change only the helper index; it would not prove source
deletion, durable-memory removal, or legal erasure.
