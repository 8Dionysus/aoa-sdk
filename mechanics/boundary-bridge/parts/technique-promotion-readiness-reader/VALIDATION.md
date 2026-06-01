# Technique Promotion Readiness Reader Validation

Run:

```bash
python -m pytest -q mechanics/boundary-bridge/parts/technique-promotion-readiness-reader/tests/test_technique_promotion_readiness_reader.py
python scripts/validate_mechanics_topology.py
```

For broader Boundary Bridge facade coverage, also run:

```bash
python -m pytest -q mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_consumed_surface_compatibility_gate.py mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_routing_surface_actions.py mechanics/boundary-bridge/parts/skill-runtime-bridge/tests/test_skill_runtime_bridge.py mechanics/boundary-bridge/parts/owner-layer-signal-handoff/tests/test_owner_layer_signal_handoff.py
```
