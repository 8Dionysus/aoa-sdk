# Consumed Surface Posture Gate Validation

Run:

```bash
python -m pytest -q mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_agent_phase_binding_surface_reader.py mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_consumed_surface_compatibility_gate.py mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_consumed_surface_posture_cli.py mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_eval_surface_reader.py mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_governed_run_surface_reader.py mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_kag_surface_reader.py mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_memo_surface_reader.py mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_playbook_surface_reader.py mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_routing_surface_actions.py mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_routing_succession_r0_baseline.py mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_stats_surface_reader.py mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_workspace_control_plane_compatibility.py
python scripts/validate_mechanics_topology.py
```

`test_consumed_surface_compatibility_gate.py` also proves the
`abyss-stack` diagnostic catalog resolves through the part-local
diagnostic-spine path and does not fall back to the old root `generated/`
copy.
`test_workspace_control_plane_compatibility.py` proves the SDK compatibility
gate fails closed when the workspace control-plane artifact identity stops
being an object.
`test_routing_succession_r0_baseline.py` proves the proposed succession
baseline stays pinned, covers every root producer output, preserves the
false-green runtime and trust-denial findings, and has no unclassified G0
dependency.

For full Boundary Bridge coverage, also run:

```bash
python -m pytest -q mechanics/boundary-bridge/parts/skill-environment-inspector/tests/test_skill_environment_inspector.py mechanics/boundary-bridge/parts/technique-promotion-readiness-reader/tests/test_technique_promotion_readiness_reader.py mechanics/boundary-bridge/parts/owner-layer-signal-handoff/tests/test_owner_layer_signal_handoff.py mechanics/boundary-bridge/parts/owner-layer-signal-handoff/tests/test_owner_layer_signal_handoff_cli.py
```
