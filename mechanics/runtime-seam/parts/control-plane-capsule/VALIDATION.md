# Control Plane Capsule Validation

Run:

```bash
python scripts/build_workspace_control_plane.py --check
python scripts/validate_workspace_control_plane.py
python -m pytest -q mechanics/runtime-seam/parts/control-plane-capsule/tests/test_control_plane_capsule.py
python scripts/validate_mechanics_topology.py
```
