# Agon Verdict Retention Rank Review Helpers

## Role

This part owns requested-only SDK helper candidates for VDS, retention, rank,
and review-bundle surfaces.

## Input

- `config/agon_vds_sdk_helper_candidates.seed.json`
- `config/agon_retention_rank_sdk_helpers.seed.json`
- VDS and retention/rank docs under `docs/`

## Output

- `generated/agon_vds_sdk_helper_candidates.min.json`
- `generated/agon_retention_rank_sdk_helpers.min.json`

## Owner

`aoa-sdk` owns candidate helper registries, schemas, examples, builders,
validators, and tests. Quest source records route through root `quests`.
Agon, eval, memo, stats, and owner repos
retain verdict, scar, retention, rank, proof, and memory authority.

## Start Here

- [CONTRACT](CONTRACT.md)
- [VALIDATION](VALIDATION.md)
- [docs](docs/)

## Next Route

Accepted verdict, retention, or rank meaning routes to stronger owners. This
part exports only reviewable candidate handles.
