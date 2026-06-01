# Agon Center Law Preview Helpers Validation

## Narrow Checks

```bash
python mechanics/agon/parts/center-law-preview-helpers/scripts/build_agon_ccs_sdk_helper_candidates.py --check
python mechanics/agon/parts/center-law-preview-helpers/scripts/validate_agon_ccs_sdk_helper_candidates.py
python -m pytest -q mechanics/agon/parts/center-law-preview-helpers/tests/test_agon_ccs_sdk_helper_candidates.py
```

## Topology Check

```bash
python scripts/validate_mechanics_topology.py
```
