# Session Growth Checkpoint Cycle Contract

## Contract

The part captures and reviews local checkpoint evidence during a session. It
keeps checkpoint notes below harvest verdicts and fails closed when semantic
review is still pending. It audits lifecycle state for checkpoint scopes under
`current/` and can close/archive only reviewed, nonpending scopes with reviewed
closeout execution evidence. Nonpending stale scopes may be archived as stale
evidence without being marked closed.

## SDK-Owned Active Names

- part route: `checkpoint/session-growth-checkpoint-cycle`
- cycle doc: `docs/session-growth-checkpoint-cycle.md`
- promotion doc: `docs/reviewed-checkpoint-note-promotion.md`
- source module: `src/aoa_sdk/checkpoints/`
- lifecycle module: `src/aoa_sdk/checkpoints/lifecycle.py`

## Stop-Lines

- Do not treat `agent_review=pending` as reviewed.
- Do not close or stale-archive a pending-review scope.
- Do not auto-run handoff, harvest, push, merge, or release logic from capture.
- Do not mutate aoa-session-memory when attaching or reporting session-memory
  archive refs.
- Do not mint memory, proof, progression, quest, stats, or owner verdicts from
  checkpoint notes.
