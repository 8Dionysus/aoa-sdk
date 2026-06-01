# Agon Verdict Retention Rank Review Helpers Validation

## Narrow Checks

```bash
python mechanics/agon/parts/verdict-retention-rank-review-helpers/scripts/build_agon_vds_sdk_helper_candidates.py --check
python mechanics/agon/parts/verdict-retention-rank-review-helpers/scripts/validate_agon_vds_sdk_helper_candidates.py
python mechanics/agon/parts/verdict-retention-rank-review-helpers/scripts/build_agon_retention_rank_sdk_helpers.py --check
python mechanics/agon/parts/verdict-retention-rank-review-helpers/scripts/validate_agon_retention_rank_sdk_helpers.py
python -m pytest -q mechanics/agon/parts/verdict-retention-rank-review-helpers/tests/test_agon_vds_sdk_helper_candidates.py mechanics/agon/parts/verdict-retention-rank-review-helpers/tests/test_agon_retention_rank_sdk_helpers.py
```

## Topology Check

```bash
python scripts/validate_mechanics_topology.py
```
