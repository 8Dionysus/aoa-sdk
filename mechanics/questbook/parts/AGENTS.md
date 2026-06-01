# AGENTS.md

## Applies to

This card applies to `mechanics/questbook/parts/`.

## Role

Questbook parts keep root quest source records, the public index, lifecycle
posture, and future dispatch readers structurally separate.

Stay on the control plane. Part edits here change route law; they do not
complete quest work or activate helper payload.

## Validation

```bash
python scripts/validate_mechanics_topology.py
python -m pytest -q tests/test_mechanics_topology.py tests/test_design_surfaces.py
```
