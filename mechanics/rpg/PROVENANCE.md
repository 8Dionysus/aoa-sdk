# RPG Provenance

## Source Surfaces

- Former root `docs/RPG_SDK_ADDENDUM.md` now routes to
  `mechanics/rpg/parts/typed-consumer-api/docs/typed-consumer-api-boundary.md`.
- Former root `docs/RPG_SURFACE_PATHS.md` now routes to
  `mechanics/rpg/parts/surface-path-transport/docs/surface-path-transport.md`.
- `src/aoa_sdk/rpg/`
- Former root `tests/test_rpg_api.py` now routes to
  `mechanics/rpg/parts/typed-consumer-api/tests/test_typed_consumer_api.py`.

## Stronger Owners

The RPG owner decides gameplay and runtime semantics. The SDK owns typed
consumer readability and path expectation tests.

## Notes

This shared name is kept because RPG surface-path helper pressure can recur
across AoA repos, while the SDK remains a consumer layer.
