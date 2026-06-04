# Checkpoint Mechanic

Status: active topology with part-local payload.

## Mechanic Card

### Operation

Capture session-growth checkpoint notes, guard git boundaries, require semantic
review, build explicit review-context bundles, route child-task re-entry
packets, attach session-memory archive refs, and carry reviewed closeout
context without minting owner truth. Audit checkpoint lifecycle state so
`current/` means active-now or still-blocked review work, while reviewed
closeout scopes can be closed and archived without deleting evidence. Reconcile
runtime sessions that ended without reviewed closeout by reading
aoa-session-memory archive refs and archiving checkpoint evidence with an
explicit no-closeout lifecycle event. Audit the remaining checkpoint backlog as
read-only navigation so pending review, stale scopes, runtime trace gaps,
session-memory refs, and next routes are visible before archive movement.
Derive candidate-intelligence route evidence from checkpoint action facets so
repeated actions, wrapper gaps, and owner pressure can be reviewed without
making the SDK an accepted wrapper owner.

### Trigger

Use this mechanic when checkpoint CLI behavior, hook integration, pending
review gates, active-session aggregation, review-context construction,
reviewed session handoff, child-task re-entry packets, or reviewed closeout
context carry changes.

### SDK owns

- session-local checkpoint capture
- active-session git boundary checks
- review-note and promotion fail-closed gates
- mechanical review-context bundle assembly
- checkpoint lifecycle audit and close/archive routing for nonpending reviewed
  closeout scopes
- checkpoint backlog audit and generated navigation for open current/no-closeout
  pressure
- checkpoint session reconciliation for session-memory-backed no-closeout
  endings
- candidate-intelligence action signatures, repetition clusters, wrapper-gap
  navigation, and generated candidate index writing
- read-only session-memory archive attachment for checkpoint closeout
- reviewed session handoff request/inbox/manifest assembly
- child-task checkpoint and re-entry packet assembly
- reviewed closeout context carry schemas, examples, and advisory maps

### Stronger owner split

Durable memory, proof verdicts, progression movement, harvest claims, and owner
status remain outside SDK checkpoint authority.

### Current source surfaces

- `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/docs/session-growth-checkpoint-cycle.md`
- `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/docs/reviewed-checkpoint-note-promotion.md`
- `mechanics/checkpoint/parts/reviewed-session-handoff-runner/docs/reviewed-session-handoff-runner.md`
- `mechanics/checkpoint/parts/child-task-reentry/docs/summon-return-checkpoint.md`
- `mechanics/checkpoint/parts/child-task-reentry/docs/return-reentry.md`
- `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/`
- `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/git-boundary-hook-templates/`
- `mechanics/checkpoint/parts/reviewed-session-handoff-runner/`
- `mechanics/checkpoint/parts/reviewed-session-handoff-runner/closeout-inbox-user-units/`
- `mechanics/checkpoint/parts/reviewed-closeout-context-carry/`
- `src/aoa_sdk/checkpoints/`
- `src/aoa_sdk/checkpoints/lifecycle.py`
- `src/aoa_sdk/checkpoints/backlog.py`
- `src/aoa_sdk/checkpoints/backlog_indexes.py`
- `src/aoa_sdk/checkpoints/reconcile.py`
- `src/aoa_sdk/checkpoints/indexes.py`
- `src/aoa_sdk/checkpoints/candidate_intelligence.py`
- `src/aoa_sdk/checkpoints/candidate_indexes.py`
- `src/aoa_sdk/closeout/`
- `src/aoa_sdk/a2a/`
- `mechanics/checkpoint/parts/child-task-reentry/`
- `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_session_growth_checkpoint_cycle_cli.py`
- `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_session_growth_checkpoint_cycle_api.py`
- `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_session_growth_checkpoint_cycle_dirty_gate.py`
- `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_checkpoint_session_memory.py`
- `mechanics/checkpoint/parts/reviewed-session-handoff-runner/tests/test_reviewed_session_handoff_runner.py`

### Candidate parts

- session-growth-checkpoint-cycle
- reviewed-session-handoff-runner
- child-task-reentry
- reviewed-closeout-context-carry

### Must not claim

This mechanic must not treat `agent_review=pending` as reviewed closeout or
allow promotion while semantic checkpoint review is still pending.
It must not close or archive a pending-review checkpoint scope even when a
closeout artifact exists nearby.
It must not treat `archived_without_closeout` as reviewed closeout or mutate
aoa-session-memory while resolving archive refs.
It must not treat candidate-intelligence output as an accepted skill,
playbook, technique, eval, memo entry, SDK-local checkpoint mechanic,
owner-local wrapper, or promotion authority.
It must not treat carrier-intelligence output as an accepted ecosystem
mechanic, installed tool, registered MCP service, installed hook, script,
daemon, service, generated-index authority, RAG/GraphRAG authority, or owner
verdict.

### Validation

Use the touched part `VALIDATION.md` for executable checks. For package-wide
route changes, use `mechanics/topology.json` for the active validation list
and then run the mechanics topology gate from the root route card.

### Next route

If checkpoint evidence survives review, route it through closeout, memory,
proof, progression, or owner surfaces rather than strengthening the checkpoint
ledger or reviewed carry packet itself.
Use lifecycle audit when `current/` no longer looks like active work; use
close/archive only after pending review is clear and reviewed closeout execution
exists, or when moving nonpending stale scopes as archive evidence without
marking them closed. Use reconcile/sweep only when aoa-session-memory proves
the runtime session ended without closeout; that route preserves evidence and
does not claim reviewed closeout happened. Use backlog audit before reconcile
when the question is what remains open, which runtime traces are resolved, and
which scopes need session-memory freshness/import/recovery before movement.
Use candidate intelligence when the question is whether repeated checkpoint
actions suggest a wrapper gap or owner review lane; treat its generated index
as navigation only. Use carrier intelligence when the question is whether
repeated action pressure suggests a mechanic, tool, MCP, hook, script, daemon,
service, or index carrier; keep install, registration, execution, memory,
proof, RAG/GraphRAG, and owner acceptance with the owning route.
