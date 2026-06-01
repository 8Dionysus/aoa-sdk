# Agon Recurrence Adapter Validation

## Narrow Checks

```bash
python mechanics/agon/parts/recurrence-adapter/scripts/build_agon_recurrence_adapter_registry.py --check
python mechanics/agon/parts/recurrence-adapter/scripts/validate_agon_recurrence_adapter.py
python mechanics/agon/parts/recurrence-adapter/scripts/build_agon_recurrence_prebinding_review_lanes.py --check
python mechanics/agon/parts/recurrence-adapter/scripts/validate_agon_recurrence_prebinding_review_lanes.py
python -m pytest -q mechanics/agon/parts/recurrence-adapter/tests/test_agon_recurrence_adapter.py mechanics/agon/parts/recurrence-adapter/tests/test_agon_recurrence_prebinding_review_lanes.py
```

## Topology Check

```bash
python scripts/validate_mechanics_topology.py
```

## What This Proves

- part-local generated companions match their part-local config inputs;
- schemas, stop-lines, owner repositories, and no-runtime flags still hold;
- the old root paths are not required as active builder, validator, or test
  homes;
- the mechanics topology knows this part-local artifact placement.
