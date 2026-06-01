# Agon Provenance

## Source Surfaces

- `mechanics/agon/parts/center-law-preview-helpers/`
- `mechanics/agon/parts/state-packet-review-bindings/`
- `mechanics/agon/parts/recurrence-adapter/`
- `mechanics/agon/parts/duel-kernel-review-bindings/`
- `mechanics/agon/parts/verdict-retention-rank-review-helpers/`
- `mechanics/agon/parts/epistemic-kag-review-helpers/`
- `mechanics/agon/parts/school-lineage-campaign-review-helpers/`
- `mechanics/agon/parts/sophian-threshold-review-helpers/`

## Moved Root Families

- `config/agon_recurrence_adapter.seed.json` -> `mechanics/agon/parts/recurrence-adapter/config/agon_recurrence_adapter.seed.json`
- `config/agon_recurrence_prebinding_review_lanes.seed.json` -> `mechanics/agon/parts/recurrence-adapter/config/agon_recurrence_prebinding_review_lanes.seed.json`
- `docs/AGON_RECURRENCE_ADAPTER*.md`, `docs/AGON_RECURRENCE_REVIEW_LANES.md`, `docs/AGON_RECURRENCE_STOP_LINES.md`, and `docs/prebinding-review-lanes.md` -> `mechanics/agon/parts/recurrence-adapter/docs/`
- `schemas/agon_recurrence_adapter.schema.json`, `schemas/agon-recurrence-adapter-registry.schema.json`, and `schemas/agon-recurrence-prebinding-review-lanes.schema.json` -> `mechanics/agon/parts/recurrence-adapter/schemas/`
- `generated/agon_recurrence_adapter_registry.min.json` and `generated/agon_recurrence_prebinding_review_lanes.min.json` -> `mechanics/agon/parts/recurrence-adapter/generated/`
- recurrence adapter builders, validators, and tests -> `mechanics/agon/parts/recurrence-adapter/{scripts,tests}/`
- CCS helper candidate config, docs, schemas, example, generated registry,
  quest, builder, validator, and test -> `mechanics/agon/parts/center-law-preview-helpers/`
- state-packet, sealed-commit, packet stop-line, schema, example, generated,
  quest, builder, validator, and test surfaces -> `mechanics/agon/parts/state-packet-review-bindings/`
- duel-kernel and mechanical-trial config, docs, schemas, examples, generated
  registries, quests, builders, validators, and tests -> `mechanics/agon/parts/duel-kernel-review-bindings/`
- VDS plus retention/rank config, docs, schemas, examples, generated
  registries, quests, builders, validators, and tests -> `mechanics/agon/parts/verdict-retention-rank-review-helpers/`
- epistemic plus KAG config, docs, schemas, examples, generated registries,
  quests, builders, validators, and tests -> `mechanics/agon/parts/epistemic-kag-review-helpers/`
- SLC config, docs, schemas, example, generated registry, quest, builder,
  validator, and test -> `mechanics/agon/parts/school-lineage-campaign-review-helpers/`
- Sophian threshold config, docs, schemas, example, generated registry, quest,
  builder, validator, and test -> `mechanics/agon/parts/sophian-threshold-review-helpers/`

These paths are provenance and migration receipts only. The active route is
the part-local home.

## Stronger Owners

Agon owners decide helper acceptance and domain truth. SDK Agon surfaces are
candidate helper contracts and generated control-plane readers.

## Notes

This shared mechanic name is kept because the same Agon package pressure is
visible across the refactored AoA repos.

Agon helper quest source records live under root `quests/agon/ready/`; helper
contracts live with the part that owns the candidate helper route. Public
Questbook routing remains responsible for cross-owner
follow-through semantics, not for active helper artifact homes.
