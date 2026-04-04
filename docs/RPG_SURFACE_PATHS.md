# RPG Surface Paths

This note records the expected generated transport paths used by the SDK RPG
addendum.

These are consumer expectations, not owner-side doctrine.

## Upstream owner surfaces

### `Agents-of-Abyss`

- surface id: `Agents-of-Abyss.dual_vocabulary_overlay`
- relative path: `generated/dual_vocabulary_overlay.json`
- shape: one `dual_vocabulary_overlay_v1` object

### `abyss-stack`

- surface id: `abyss-stack.rpg_build_snapshots`
- relative path: `generated/rpg/agent_build_snapshots.json`
- shape: one `agent_build_snapshot_collection_v1` object with a `builds` array

- surface id: `abyss-stack.rpg_reputation_ledgers`
- relative path: `generated/rpg/reputation_ledgers.json`
- shape: one `reputation_ledger_collection_v1` object with a `ledgers` array

- surface id: `abyss-stack.rpg_quest_run_results`
- relative path: `generated/rpg/quest_run_results.json`
- shape: one `quest_run_result_collection_v1` object with a `runs` array

- surface id: `abyss-stack.rpg_frontend_projection_bundles`
- relative path: `generated/rpg/frontend_projection_bundles.json`
- shape: one `frontend_projection_bundle_collection_v1` object with a
  `bundles` array

## Fragment posture

When a string ref needs to point at one item inside a collection wrapper, use
JSON-fragment style IDs:

- `.../agent_build_snapshots.json#<snapshot_id>`
- `.../reputation_ledgers.json#<ledger_id>`
- `.../quest_run_results.json#<run_id>`
- `.../frontend_projection_bundles.json#<bundle_id>`

The SDK may keep fragment refs as strings or resolve them through helper
methods. It should not rewrite them silently.

## Staging rule

Until live builders exist, tests may stage these transport files by wrapping
the RFC example objects into the collection shapes listed above.

That staging is a reader-path convenience only.
