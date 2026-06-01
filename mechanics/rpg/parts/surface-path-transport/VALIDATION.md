# Surface Path Transport Validation

Run the narrow part test after touching this part:

```bash
python -m pytest -q mechanics/rpg/parts/surface-path-transport/tests/test_surface_path_transport.py
```

Run the topology gate after moving or renaming any active surface:

```bash
python scripts/validate_mechanics_topology.py
```
