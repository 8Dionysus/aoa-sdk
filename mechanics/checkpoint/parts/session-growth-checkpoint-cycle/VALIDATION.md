# Session Growth Checkpoint Cycle Validation

Run:

```bash
python -m pytest -q mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_session_growth_checkpoint_cycle_cli.py mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_session_growth_checkpoint_cycle_api.py mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_session_growth_checkpoint_cycle_dirty_gate.py mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_checkpoint_session_memory.py
python scripts/validate_mechanics_topology.py
```

For lifecycle audit and close/archive compatibility, also run:

```bash
aoa checkpoint lifecycle-audit /srv/AbyssOS/aoa-sdk --root /srv/AbyssOS --json
aoa checkpoint close-archive /srv/AbyssOS/aoa-sdk --root /srv/AbyssOS --dry-run --json
```

For route docs and generated control-plane refs, also run:

```bash
python scripts/build_workspace_control_plane.py --check
python scripts/validate_workspace_control_plane.py
python -m pytest -q tests/test_docs_routes.py mechanics/runtime-seam/parts/control-plane-capsule/tests/test_control_plane_capsule.py
```
