# Checkpoint Mechanic

Status: skeleton.

## Mechanic Card

### Operation

Capture session-growth checkpoint notes, guard git boundaries, require semantic
review, build explicit closeout context, and route A2A return/re-entry packets.

### Trigger

Use this mechanic when checkpoint CLI behavior, hook integration, pending
review gates, active-session aggregation, closeout-context construction,
reviewed closeout, or A2A return/re-entry packets change.

### SDK owns

- session-local checkpoint capture
- active-session git boundary checks
- review-note and promotion fail-closed gates
- mechanical closeout-context bundle assembly
- reviewed closeout request/inbox/manifest assembly
- A2A checkpoint and return packet assembly

### Stronger owner split

Durable memory, proof verdicts, progression movement, harvest claims, and owner
status remain outside SDK checkpoint authority.

### Current source surfaces

- `docs/session-growth-checkpoints.md`
- `docs/checkpoint-note-promotion.md`
- `docs/session-closeout.md`
- `docs/A2A_WAVE5_CODEX_RETURN_CHECKPOINT.md`
- `docs/RETURN_REENTRY_SEAM.md`
- `githooks/`
- `schemas/checkpoint_lineage_hint.schema.json`
- `src/aoa_sdk/checkpoints/`
- `src/aoa_sdk/closeout/`
- `src/aoa_sdk/a2a/`
- `tests/test_checkpoint_cli.py`
- `tests/test_checkpoints.py`

### Candidate parts

- capture
- git-boundary
- review-note
- closeout-context
- closeout-bridge
- return-reentry

### Must not claim

This mechanic must not treat `agent_review=pending` as reviewed closeout or
allow promotion while semantic checkpoint review is still pending.

### Validation

```bash
python -m pytest -q tests/test_checkpoint_cli.py tests/test_checkpoints.py tests/test_closeout.py tests/test_a2a_wave5_checkpoint_and_return.py
```

### Next route

If checkpoint evidence survives review, route it through closeout, memory,
proof, progression, or owner surfaces rather than strengthening the checkpoint
ledger itself.
