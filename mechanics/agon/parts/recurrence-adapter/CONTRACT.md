# Agon Recurrence Adapter Contract

## Function

Build and validate candidate-only SDK views over Agon recurrence adapter and
review-lane surfaces.

## May

- read the part-local config seeds;
- generate deterministic compact registries under `generated/`;
- validate generated output against part-local schemas and stop-lines;
- reference public-safe recurrence examples as review surfaces;
- expose candidate-only quest follow-through for owner review.

## Must Not

- open an arena session;
- execute Agon recurrence;
- issue verdicts;
- mutate rank, scar, memory, retention, or Tree of Sophia state;
- run a hidden scheduler;
- treat generated companions as source authority;
- treat old root paths as active routes.

## Inputs

- `config/agon_recurrence_adapter.seed.json`
- `config/agon_recurrence_prebinding_review_lanes.seed.json`

## Outputs

- `generated/agon_recurrence_adapter_registry.min.json`
- `generated/agon_recurrence_prebinding_review_lanes.min.json`

## Validation

Executable proof lives in [VALIDATION](VALIDATION.md).
