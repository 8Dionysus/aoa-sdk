# Titan Mechanic

Status: skeleton.

## Mechanic Card

### Operation

Expose bounded Titan runtime harness, console, appserver bridge, identity,
memory, session, and swarm helper surfaces.

### Trigger

Use this mechanic when Titan CLI scripts, SDK Titan modules, Titan schemas,
examples, runtime harness docs, console docs, appserver docs, or Memory Loom
docs change.

### SDK owns

- typed Titan control-plane helper APIs
- CLI helper scripts and examples
- schema/example validation for Titan helper packets
- local docs that state SDK stop-lines

### Stronger owner split

Titan runtime, role authority, identity truth, memory truth, and operational
approval remain outside SDK ownership.

### Current source surfaces

- `docs/TITAN_RUNTIME_HARNESS.md`
- `docs/TITAN_OPERATOR_CONSOLE.md`
- `examples/titan_console_state.example.json`
- `schemas/titan_console_state.schema.json`
- `scripts/titanctl.py`
- `src/aoa_sdk/titans/`
- `tests/test_titan_console.py`
- `tests/test_titanctl_runtime.py`

### Candidate parts

- runtime-harness
- operator-console
- appserver-bridge
- memory-loom
- session-replay
- swarm-ledger

### Must not claim

This mechanic must not present helper packets as live Titan runtime state or
accepted operator decisions.

### Validation

```bash
python -m pytest -q tests/test_titan_console.py tests/test_titanctl_runtime.py
```

### Next route

Runtime authority changes route to the Titan owner layer; SDK keeps bounded
helpers, docs, contracts, and tests.
