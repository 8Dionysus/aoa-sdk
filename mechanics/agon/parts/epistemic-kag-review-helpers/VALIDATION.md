# Agon Epistemic KAG Review Helpers Validation

## Narrow Checks

```bash
python mechanics/agon/parts/epistemic-kag-review-helpers/scripts/build_agon_epistemic_sdk_helpers.py --check
python mechanics/agon/parts/epistemic-kag-review-helpers/scripts/validate_agon_epistemic_sdk_helpers.py
python mechanics/agon/parts/epistemic-kag-review-helpers/scripts/build_agon_kag_sdk_helpers.py --check
python mechanics/agon/parts/epistemic-kag-review-helpers/scripts/validate_agon_kag_sdk_helpers.py
python -m pytest -q mechanics/agon/parts/epistemic-kag-review-helpers/tests/test_agon_epistemic_sdk_helpers.py mechanics/agon/parts/epistemic-kag-review-helpers/tests/test_agon_kag_sdk_helpers.py
```

## Topology Check

```bash
python scripts/validate_mechanics_topology.py
```
