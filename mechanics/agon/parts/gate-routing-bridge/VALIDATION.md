# Agon Gate Routing Bridge Validation

## Narrow Checks

```bash
python mechanics/agon/parts/gate-routing-bridge/scripts/build_agon_gate_routing_registry.py --check
python mechanics/agon/parts/gate-routing-bridge/scripts/validate_agon_gate_routing.py
python -m pytest -q mechanics/agon/parts/gate-routing-bridge/tests
```

The validator checks the packaged registry, deterministic rebuild parity,
schema and owner-dispatch contracts, stop-lines, the pinned succession
receipt, and optional center lawful-move drift without requiring the
predecessor checkout.

When the center checkout is available, add the owner-source drift check:

```bash
python mechanics/agon/parts/gate-routing-bridge/scripts/validate_agon_gate_routing.py \
  --center-root /srv/AbyssOS/Agents-of-Abyss
```

## Installed Wheel

```bash
python -m build
python mechanics/agon/parts/gate-routing-bridge/scripts/verify_agon_gate_routing_wheel.py
```

The clean-wheel probe must load and rebuild the registry without either an
`aoa-routing` or `Agents-of-Abyss` checkout.

## Topology and Release

```bash
python scripts/validate_mechanics_topology.py
python scripts/release_check.py
```
