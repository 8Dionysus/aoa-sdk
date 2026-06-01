# Memory Loom Recall Helper Contracts Contract

## Contract

The part validates SDK-visible Titan memory and recall helper surfaces without
turning candidates into durable memory.

## SDK-Owned Active Names

- part route: `titan/memory-loom-recall-helper-contracts`
- docs: `docs/memory-loom.md`, `docs/memory-recall-protocol.md`
- script: `scripts/titan_memory_loom.py`
- schemas: memory index, memory record, recall, and retention schemas
- examples: memory index, receipt, and record examples
- tests: `tests/test_titan_memory_loom.py`

## Stop-Lines

- Do not treat recall results as source truth.
- Do not treat memory records as accepted `aoa-memo` memory.
- Do not keep memory helper artifacts in root technical districts.
