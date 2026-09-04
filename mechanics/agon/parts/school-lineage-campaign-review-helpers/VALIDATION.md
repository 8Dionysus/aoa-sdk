# Agon School Lineage Campaign Review Helpers Validation

## Narrow Checks

```bash
python mechanics/agon/parts/school-lineage-campaign-review-helpers/scripts/build_agon_slc_sdk_helpers.py --check
python mechanics/agon/parts/school-lineage-campaign-review-helpers/scripts/validate_agon_slc_sdk_helpers.py
python -m pytest -q mechanics/agon/parts/school-lineage-campaign-review-helpers/tests/test_agon_slc_sdk_helpers.py
```

## Topology Check


The repository-wide topology gate is owned by [root `VALIDATION.md`](../../../../VALIDATION.md#focused-repository-checks).
