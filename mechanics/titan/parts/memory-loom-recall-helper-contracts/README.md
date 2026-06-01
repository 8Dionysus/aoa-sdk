# Memory Loom Recall Helper Contracts

## Role

`memory-loom-recall-helper-contracts` keeps Titan Memory Loom, recall, record,
retention, and redaction helper contracts in one SDK-owned route.

## Input

- local memory index and record payloads
- recall queries and recall results
- retention and redaction requests

## Output

- memory and recall docs
- memory/recall schemas and examples
- `scripts/titan_memory_loom.py`
- `tests/test_titan_memory_loom.py`

## Owner

`aoa-sdk` owns helper shape and local validation. `aoa-memo` and source owners
keep memory truth, recall authority, and durable remembrance meaning.

## Next Route

Valid recall results route to source verification or memo owner review. They
are not memory truth.

## Validation

Use `VALIDATION.md`.
