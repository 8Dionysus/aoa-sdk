# Surface Detection Provenance

## Source Surfaces

- `docs/aoa-surface-detection-first-wave.md`
- `docs/aoa-surface-detection-second-wave.md`
- `docs/aoa-surface-detection-heuristics.md`
- `docs/aoa-surface-detection-closeout-handoff.md`
- `src/aoa_sdk/surfaces/`
- `tests/test_surfaces.py`
- `tests/test_surfaces_cli.py`

## Stronger Owners

Detected owner-layer candidates belong to the owning sibling repository after
review. SDK detection only makes the candidate visible.

## Notes

This mechanic is SDK-local because it protects the SDK-specific split between
skill routing and broader owner-layer hints.
