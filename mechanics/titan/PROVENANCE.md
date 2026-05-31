# Titan Provenance

## Source Surfaces

- `docs/TITAN_RUNTIME_HARNESS.md`
- `docs/TITAN_OPERATOR_CONSOLE.md`
- `examples/titan_console_state.example.json`
- `schemas/titan_console_state.schema.json`
- `scripts/titanctl.py`
- `src/aoa_sdk/titans/`
- `tests/test_titan_console.py`
- `tests/test_titanctl_runtime.py`

## Stronger Owners

Titan runtime, identity, memory, role, and approval authority remain outside
the SDK.

## Notes

This shared mechanic name is preserved because Titan helper packages recur
across AoA topology, while this SDK only exposes control-plane handles.
