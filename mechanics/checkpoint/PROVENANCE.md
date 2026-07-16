# Checkpoint Provenance

## Source Surfaces

- `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/docs/session-growth-checkpoint-cycle.md`
- `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/docs/reviewed-checkpoint-note-promotion.md`
- `mechanics/checkpoint/parts/child-task-reentry/docs/summon-return-checkpoint.md`
- `mechanics/checkpoint/parts/child-task-reentry/docs/return-reentry.md`
- `mechanics/checkpoint/parts/reviewed-closeout-context-carry/`
- `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/git-boundary-hook-templates/`
- `src/aoa_sdk/checkpoints/`
- `src/aoa_sdk/checkpoints/lifecycle.py`
- `src/aoa_sdk/a2a/`
- `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_session_growth_checkpoint_cycle_cli.py`
- `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_session_growth_checkpoint_cycle_api.py`
- `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_session_growth_checkpoint_cycle_dirty_gate.py`
- `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_checkpoint_lifecycle_indexes.py`
- `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_checkpoint_session_memory.py`
- `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_checkpoint_candidate_intelligence.py`
- `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_checkpoint_carrier_intelligence.py`

## Stronger Owners

Reviewed memory belongs to `aoa-memo`; proof belongs to `aoa-evals`;
progression and quest verdicts belong to their owner layers. The SDK checkpoint
mechanic only captures and gates local evidence.

## Notes

This shared name matches the recurring AoA checkpoint shape but keeps SDK
behavior limited to session-local control-plane support.
Session-memory archive refs are consumed as route evidence for reviewed
closeout context, not as reviewed memory truth.
Checkpoint lifecycle audit consumes those refs read-only. Close/archive may
move checkpoint files from `current/` to `archive/`, but it does not mutate
aoa-session-memory or turn archive indexes into reviewed truth.

Former parent-name candidates for this package live only in
`legacy/INDEX.md`. Active Checkpoint routes name the operation: session-local
review and evidence materialization, child-task re-entry, and reviewed context
carry.

The former `reviewed-session-handoff-runner`, its user units, inferred
publisher scripts, queue contracts, and `src/aoa_sdk/closeout/` source family
were retired by AOA-SDK-D-0068. Their history remains in git and the decision
record; they are not active compatibility routes.

Former root closeout-carry docs, schemas, examples, and tests moved into
`mechanics/checkpoint/parts/reviewed-closeout-context-carry/`. Old root names
such as `docs/CANDIDATE_LINEAGE_CARRY.md`,
`docs/closeout-followthrough-map.md`, `docs/COMPONENT_DRIFT_HINTS.md`,
`docs/SELF_AGENCY_CONTINUITY_CARRY.md`,
`docs/SESSION_GROWTH_KERNEL_SIGNAL_RULES.md`,
`schemas/checkpoint_lineage_hint.schema.json`, root closeout-carry schemas,
root closeout-carry examples, and the candidate/component carry tests are
provenance only, not active routes.
