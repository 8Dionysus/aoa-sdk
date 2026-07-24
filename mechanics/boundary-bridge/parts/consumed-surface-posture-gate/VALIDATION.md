# Consumed Surface Posture Gate Validation

Run:

```bash
python -m pytest -q mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests
python -m mypy src/aoa_sdk/control_plane/routing
python mechanics/boundary-bridge/parts/consumed-surface-posture-gate/scripts/compare_routing_shadow_producers.py --predecessor-root /path/to/aoa-routing-at-7e2fe467
python -m build
python mechanics/boundary-bridge/parts/consumed-surface-posture-gate/scripts/verify_routing_shadow_wheel.py
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
`test_routing_succession_r1_target_operating_model.py` proves accepted target
ownership remains distinct from live authority, every lifecycle operation has
one owner, the owner-only switch preserves the routing ABI and namespace, and
archive execution remains operator-gated.
`test_routing_succession_r2_control_plane_contracts.py` proves strict JSON
round-trip, one contract family across all three golden scenarios, a closed
lifecycle graph, exact snapshot/ABI/approval scope, command replay
idempotency, event-chain integrity, runtime-neutral plans, and separation of
runtime success from eval, memory, and closeout.
`test_routing_succession_r3_migration_rehearsal.py` proves all fourteen
artifacts stayed byte/schema/count compatible, the installed SDK wheel built
without an `aoa-routing` checkout, rollback remained available, the disposable
candidate was removed, M1 integration debt stayed explicit, and G3 did not
silently authorize G5.
`test_routing_shadow_producer.py` and `test_routing_shadow_bundle.py` prove the
typed compiler, negative cases, deterministic reconstruction, strict packaged
schemas, dual-producer provenance, non-publishing guard, and substitution
denial. They also prove that compact fixture archives reject traversal and
link members before test extraction. `verify_routing_shadow_wheel.py` proves
those surfaces are present and functional in the built wheel rather than only
in the source checkout.

For full Boundary Bridge coverage, also run:

```bash
python -m pytest -q mechanics/boundary-bridge/parts/skill-environment-inspector/tests/test_skill_environment_inspector.py mechanics/boundary-bridge/parts/technique-promotion-readiness-reader/tests/test_technique_promotion_readiness_reader.py mechanics/boundary-bridge/parts/owner-layer-signal-handoff/tests/test_owner_layer_signal_handoff.py mechanics/boundary-bridge/parts/owner-layer-signal-handoff/tests/test_owner_layer_signal_handoff_cli.py
```
