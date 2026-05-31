# AGENTS.md

## Applies to

`mechanics/titan/`.

## Role

Route the shared Titan mechanic for runtime harness, operator console,
appserver bridge, identity, Memory Loom, session replay, and swarm helpers.

## Read before editing

- `mechanics/AGENTS.md`
- `mechanics/titan/README.md`
- `docs/TITAN_*.md`
- `src/aoa_sdk/titans/`
- `scripts/titan*.py`
- Titan schemas and examples

## Boundaries

- Stay on the control plane.
- Do not turn SDK Titan helpers into Titan runtime, role, identity, or memory
  authority.
- Keep launch, approval, and replay artifacts explicit and inspectable.

## Validation

```bash
python scripts/validate_mechanics_topology.py
python -m pytest -q tests/test_titan_console.py tests/test_titanctl_runtime.py
```

## Closeout

Report which Titan helper surface changed and which runtime or owner authority
remains outside SDK.
