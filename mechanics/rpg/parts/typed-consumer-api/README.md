# Typed Consumer API

This part owns the SDK route that makes RPG owner surfaces readable through
typed Python helpers.

## Role

Input: vocabulary overlay, agent build snapshots, reputation ledgers, quest
run results, and frontend projection bundles from stronger owner surfaces.

Output: stable Python objects and helper methods for reading those surfaces.

Owner: `aoa-sdk` owns the typed consumer API and tests. `Agents-of-Abyss` and
runtime owners keep RPG doctrine, generated surface meaning, gameplay,
frontend behavior, progression truth, and runtime state.

## Active Surfaces

- [Typed Consumer API Boundary](docs/typed-consumer-api-boundary.md)
- [Typed Consumer API Tests](tests/test_typed_consumer_api.py)
- `src/aoa_sdk/rpg/`

## Next Route

Route gameplay, runtime, quest, progression, UI, or owner-surface changes to
their source owners. Keep SDK changes to typed reading and path helpers.
