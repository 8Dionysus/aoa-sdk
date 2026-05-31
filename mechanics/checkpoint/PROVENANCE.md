# Checkpoint Provenance

## Source Surfaces

- `docs/session-growth-checkpoints.md`
- `docs/checkpoint-note-promotion.md`
- `githooks/`
- `schemas/checkpoint_lineage_hint.schema.json`
- `src/aoa_sdk/checkpoints/`
- `tests/test_checkpoint_cli.py`
- `tests/test_checkpoints.py`

## Stronger Owners

Reviewed memory belongs to `aoa-memo`; proof belongs to `aoa-evals`;
progression and quest verdicts belong to their owner layers. The SDK checkpoint
mechanic only captures and gates local evidence.

## Notes

This shared name matches the recurring AoA checkpoint shape but keeps SDK
behavior limited to session-local control-plane support.
