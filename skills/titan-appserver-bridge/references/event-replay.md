# Event-replay mode

Choose the helper by the declared visible source kind.

## Bridge event file

1. Require bridge session and a bounded event file with source provenance.
2. Run:

   `python <owner_root>/mechanics/titan/parts/appserver-bridge-helper-contracts/scripts/titan_appserver_bridge.py replay --session <session> --file <events>`

3. Validate the resulting bridge session and compare the derived state with
   any supplied current witness.
4. For a newly initialized local session, verify the witness/authority,
   no-runtime, no-transport, and helper-projection fields. Reject an
   unexplained `active` Titan state as runtime ambiguity.

## Visible Codex session export

1. Require an explicitly visible export. Do not use this route for hidden
   `.aoa` transcript evidence.
2. Use only the requested `segment`, `packets`, or `lessons` operation from:

   `python <owner_root>/mechanics/titan/parts/session-praxis-replay-helper-contracts/scripts/titan_session_replay.py`

3. Mark lesson output `candidate_only` and preserve the helper's
   visible-source limitation.

For both source kinds, return ordering gaps, omitted material, source refs,
`hidden_history_access: false`, derived artifact paths, verification, and the
next review or memory-owner route. A replay is never runtime proof or durable
memory.
