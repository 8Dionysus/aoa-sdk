# Session Praxis Replay Helper Contracts

## Role

`session-praxis-replay-helper-contracts` keeps visible-session replay, phase
graph, packet, compaction source, and learning-delta helper contracts in one
SDK-owned route.

## Input

- visible Codex session exports
- visible command rows, dialogue, tool calls, and compaction markers

## Output

- replay docs and visible-session example
- phase graph, packet, compaction source, and learning-delta schemas
- `scripts/titan_session_replay.py`
- `tests/test_titan_session_replay.py`

## Owner

`aoa-sdk` owns visible replay helper shape. Session-memory and memo owners keep
hidden transcript truth, durable memory truth, and accepted learning meaning.

## Next Route

Valid replay packets route to review and memory-owner verification. They do
not infer hidden reasoning or compacted replacement history.

## Validation

Use `VALIDATION.md`.
