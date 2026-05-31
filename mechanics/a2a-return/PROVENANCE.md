# A2A Return Provenance

## Source Surfaces

- `docs/A2A_WAVE5_CODEX_RETURN_CHECKPOINT.md`
- `docs/RETURN_REENTRY_SEAM.md`
- `examples/a2a/`
- `src/aoa_sdk/a2a/`
- `tests/test_a2a_sdk_api.py`
- `tests/test_a2a_wave5_checkpoint_and_return.py`
- `tests/test_a2a_wave5_e2e_fixture.py`

## Stronger Owners

Agent role authority, memo truth, proof verdicts, and progression truth remain
outside SDK A2A packet helpers.

## Notes

This is SDK-local because it is the SDK's packet assembly and return seam,
while cross-agent authority lives elsewhere.
