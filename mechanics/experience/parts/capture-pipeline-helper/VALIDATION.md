# Experience Capture Pipeline Helper Validation

## Narrow Checks

```bash
python -m pytest -q mechanics/experience/parts/capture-pipeline-helper/tests/test_capture_pipeline_helper.py
```

## Topology Check

```bash
python scripts/validate_mechanics_topology.py
```

## What This Proves

- the helper example matches its part-local schema;
- the doc still names the seed zips and stop-lines;
- the old root `docs/`, `schemas/`, `examples/`, and `tests/` paths are not
  active helper homes.
