# Checkpoint Mechanic

Status: active topology with part-local payload.

## Mechanic Card

### Operation

Capture session-growth checkpoint notes, guard git boundaries, require semantic
review, build explicit review-context bundles, route child-task re-entry
packets, and carry reviewed closeout context without minting owner truth.

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
- `src/aoa_sdk/closeout/`
- `src/aoa_sdk/a2a/`
- `mechanics/checkpoint/parts/child-task-reentry/`
- `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_session_growth_checkpoint_cycle_cli.py`
- `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_session_growth_checkpoint_cycle_api.py`
- `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_session_growth_checkpoint_cycle_dirty_gate.py`
- `mechanics/checkpoint/parts/reviewed-session-handoff-runner/tests/test_reviewed_session_handoff_runner.py`

### Candidate parts

- session-growth-checkpoint-cycle
- reviewed-session-handoff-runner
- child-task-reentry
- reviewed-closeout-context-carry

### Must not claim

This mechanic must not treat `agent_review=pending` as reviewed closeout or
allow promotion while semantic checkpoint review is still pending.

### Validation

Use the touched part `VALIDATION.md` for executable checks. For package-wide
route changes, use `mechanics/topology.json` for the active validation list
and then run the mechanics topology gate from the root route card.

### Next route

If checkpoint evidence survives review, route it through closeout, memory,
proof, progression, or owner surfaces rather than strengthening the checkpoint
ledger or reviewed carry packet itself.
