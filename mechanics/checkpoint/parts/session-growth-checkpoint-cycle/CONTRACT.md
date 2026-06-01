# Session Growth Checkpoint Cycle Contract

## Contract

The part captures and reviews local checkpoint evidence during a session. It
keeps checkpoint notes below harvest verdicts and fails closed when semantic
review is still pending.

## SDK-Owned Active Names

- part route: `checkpoint/session-growth-checkpoint-cycle`
- cycle doc: `docs/session-growth-checkpoint-cycle.md`
- promotion doc: `docs/reviewed-checkpoint-note-promotion.md`
- source module: `src/aoa_sdk/checkpoints/`

## Stop-Lines

- Do not treat `agent_review=pending` as reviewed.
- Do not auto-run handoff, harvest, push, merge, or release logic from capture.
- Do not mint memory, proof, progression, quest, stats, or owner verdicts from
  checkpoint notes.
