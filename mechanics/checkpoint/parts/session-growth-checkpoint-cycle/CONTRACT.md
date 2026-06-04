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
The part also derives candidate-intelligence route evidence from checkpoint
action facets: action signatures, repetition clusters, existing-wrapper fit,
wrapper readiness, wrapper gaps, and bounded sample-audit targets. These
classifier outputs are generated navigation only; they do not accept a
wrapper, assign owner truth, or promote a single event.
The part also exposes a read-only checkpoint backlog audit for no-closeout and
stale `current/` pressure. It names runtime trace gaps, session-memory archive
presence, required actions, and next routes without moving checkpoint files,
running closeout, mutating aoa-session-memory, or making RAG/GraphRAG truth.
The part also derives carrier-intelligence route evidence from those action
signatures: carrier kind, owner scope, existing-carrier fit, execution risk,
installability, execution posture, and sample-audit targets. These outputs are
generated ecosystem route evidence only; they do not create accepted mechanics,
install tools, register MCP services, install hooks, start scripts, daemons, or
services, mint memory/proof, or grant RAG/GraphRAG authority.

## SDK-Owned Active Names

- part route: `checkpoint/session-growth-checkpoint-cycle`
- cycle doc: `docs/session-growth-checkpoint-cycle.md`
- promotion doc: `docs/reviewed-checkpoint-note-promotion.md`
- source module: `src/aoa_sdk/checkpoints/`
- lifecycle module: `src/aoa_sdk/checkpoints/lifecycle.py`
- reconcile module: `src/aoa_sdk/checkpoints/reconcile.py`
- backlog module: `src/aoa_sdk/checkpoints/backlog.py`
- candidate-intelligence module:
  `src/aoa_sdk/checkpoints/candidate_intelligence.py`
- carrier-intelligence module:
  `src/aoa_sdk/checkpoints/carrier_intelligence.py`
- generated lifecycle index:
  `.aoa/session-growth/indexes/checkpoint-lifecycle-navigation.min.json`
- generated backlog index:
  `.aoa/session-growth/indexes/checkpoint-backlog-navigation.min.json`
- generated candidate-intelligence index:
  `.aoa/session-growth/indexes/checkpoint-candidate-intelligence.min.json`
- generated carrier-intelligence index:
  `.aoa/session-growth/indexes/checkpoint-carrier-candidate-intelligence.min.json`

## Stop-Lines

- Do not treat `agent_review=pending` as reviewed.
- Do not close or stale-archive a pending-review scope.
- Do not reconcile/archive a session-closed pending-review scope until the
  required review action is explicit.
- Do not auto-run handoff, harvest, push, merge, or release logic from capture.
- Do not mutate aoa-session-memory when attaching or reporting session-memory
  archive refs.
- Do not treat `archived_without_closeout` as `closed`.
- Do not treat runtime trace refs as proof that aoa-session-memory archived a
  session.
- Do not treat action signatures, repetition clusters, or wrapper gaps as
  reviewed memory, proof, owner verdict, accepted wrapper, or promotion
  authority.
- Do not treat carrier candidates as accepted mechanics, installed tools,
  registered MCP services, installed hooks, scripts, daemons, services, index
  authority, RAG/GraphRAG authority, or owner verdicts.
- Do not let a single weak event become draftable or promoted.
- Do not mint memory, proof, progression, quest, stats, or owner verdicts from
  checkpoint notes.
