# Checkpoint Mechanic

Status: skeleton.

## Mechanic Card

### Operation

Capture session-growth checkpoint notes, guard git boundaries, require semantic
review, and build explicit closeout context.

### Trigger

Use this mechanic when checkpoint CLI behavior, hook integration, pending
review gates, active-session aggregation, or closeout-context construction
changes.

### SDK owns

- session-local checkpoint capture
- active-session git boundary checks
- review-note and promotion fail-closed gates
- mechanical closeout-context bundle assembly

### Stronger owner split

Durable memory, proof verdicts, progression movement, harvest claims, and owner
status remain outside SDK checkpoint authority.

### Current source surfaces

- `docs/session-growth-checkpoints.md`
- `docs/checkpoint-note-promotion.md`
- `githooks/`
- `schemas/checkpoint_lineage_hint.schema.json`
- `src/aoa_sdk/checkpoints/`
- `tests/test_checkpoint_cli.py`
- `tests/test_checkpoints.py`

### Candidate parts

- capture
- git-boundary
- review-note
- closeout-context

### Must not claim

This mechanic must not treat `agent_review=pending` as reviewed closeout or
allow promotion while semantic checkpoint review is still pending.

### Validation

```bash
python -m pytest -q tests/test_checkpoint_cli.py tests/test_checkpoints.py
```

### Next route

If checkpoint evidence survives review, route it through closeout, memory,
proof, progression, or owner surfaces rather than strengthening the checkpoint
ledger itself.
