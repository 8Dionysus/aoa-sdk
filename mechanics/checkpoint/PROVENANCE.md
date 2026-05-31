# Checkpoint Provenance

## Source Surfaces

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

## Stronger Owners

Reviewed memory belongs to `aoa-memo`; proof belongs to `aoa-evals`;
progression and quest verdicts belong to their owner layers. The SDK checkpoint
mechanic only captures and gates local evidence.

## Notes

This shared name matches the recurring AoA checkpoint shape but keeps SDK
behavior limited to session-local control-plane support.

The first SDK skeleton incorrectly promoted `closeout` and `a2a-return` to
parent mechanics. They are Checkpoint parts: closeout bridge and return
re-entry.
