# Agon Duel Kernel Review Bindings Validation

## Narrow Checks

```bash
python mechanics/agon/parts/duel-kernel-review-bindings/scripts/build_agon_duel_kernel_sdk_bindings.py --check
python mechanics/agon/parts/duel-kernel-review-bindings/scripts/validate_agon_duel_kernel_sdk_bindings.py
python mechanics/agon/parts/duel-kernel-review-bindings/scripts/build_agon_mechanical_trial_sdk_helpers.py --check
python mechanics/agon/parts/duel-kernel-review-bindings/scripts/validate_agon_mechanical_trial_sdk_helpers.py
python -m pytest -q mechanics/agon/parts/duel-kernel-review-bindings/tests/test_agon_duel_kernel_sdk_bindings.py mechanics/agon/parts/duel-kernel-review-bindings/tests/test_agon_mechanical_trial_sdk_helpers.py
```

## Topology Check

```bash
python scripts/validate_mechanics_topology.py
```
