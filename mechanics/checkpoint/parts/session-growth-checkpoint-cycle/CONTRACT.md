# Session Growth Checkpoint Cycle Contract

## Contract

The part captures and reviews local checkpoint evidence during a session. It
keeps checkpoint notes below harvest verdicts and fails closed when semantic
review is still pending. It audits lifecycle state for checkpoint scopes under
`current/` and can close/archive only reviewed, nonpending scopes with reviewed
closeout execution evidence. Nonpending stale scopes may be archived as stale
evidence without being marked closed. When aoa-session-memory has preserved a
runtime session that ended without reviewed closeout, the part can reconcile
that checkpoint scope as `session_closed_reviewed_no_closeout` or
`session_closed_collecting_no_closeout` and archive it with a
`checkpoint_session_archived_without_closeout_v1` event. This event preserves
evidence; it does not close the note, run closeout, or promote the contents.

## SDK-Owned Active Names

- part route: `checkpoint/session-growth-checkpoint-cycle`
- cycle doc: `docs/session-growth-checkpoint-cycle.md`
- promotion doc: `docs/reviewed-checkpoint-note-promotion.md`
- source module: `src/aoa_sdk/checkpoints/`
- lifecycle module: `src/aoa_sdk/checkpoints/lifecycle.py`
- reconcile module: `src/aoa_sdk/checkpoints/reconcile.py`
- generated lifecycle index:
  `.aoa/session-growth/indexes/checkpoint-lifecycle-navigation.min.json`

## Stop-Lines

- Do not treat `agent_review=pending` as reviewed.
- Do not close or stale-archive a pending-review scope.
- Do not reconcile/archive a session-closed pending-review scope until the
  required review action is explicit.
- Do not auto-run handoff, harvest, push, merge, or release logic from capture.
- Do not mutate aoa-session-memory when attaching or reporting session-memory
  archive refs.
- Do not treat `archived_without_closeout` as `closed`.
- Do not mint memory, proof, progression, quest, stats, or owner verdicts from
  checkpoint notes.
