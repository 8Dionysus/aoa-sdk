# Compatibility Provenance

## Source Surfaces

- `docs/versioning.md`
- `docs/boundaries.md`
- `scripts/run_sibling_canary.py`
- `scripts/sibling_canary_matrix.json`
- `src/aoa_sdk/compatibility/`
- `tests/test_compatibility.py`
- `tests/test_sibling_canary.py`

## Stronger Owners

Sibling repos own canonical physical paths and semantics. SDK compatibility
owns the check over the surfaces it consumes.

## Notes

This is SDK-local because the compatibility matrix is a consumer-side promise,
not a sibling-owned mechanic.
