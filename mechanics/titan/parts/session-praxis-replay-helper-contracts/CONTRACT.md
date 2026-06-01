# Session Praxis Replay Helper Contracts Contract

## Contract

The part validates SDK-visible replay helper surfaces derived from visible
session exports only.

## SDK-Owned Active Names

- part route: `titan/session-praxis-replay-helper-contracts`
- docs: `docs/praxis-replay.md`
- script: `scripts/titan_session_replay.py`
- schemas: phase graph, agent packet, compaction source, and learning delta schemas
- examples: `examples/titan_visible_session_excerpt.example.md`
- tests: `tests/test_titan_session_replay.py`

## Stop-Lines

- Do not consume hidden reasoning or hidden transcript payloads.
- Do not turn replay learning deltas into accepted memory.
- Do not keep replay helper artifacts in root technical districts.
