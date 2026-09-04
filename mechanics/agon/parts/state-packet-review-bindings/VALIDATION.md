# Agon State Packet Review Bindings Validation

## Narrow Checks

```bash
python mechanics/agon/parts/state-packet-review-bindings/scripts/build_agon_sdk_state_packet_bindings.py --check
python mechanics/agon/parts/state-packet-review-bindings/scripts/validate_agon_sdk_state_packet_bindings.py
python -m pytest -q mechanics/agon/parts/state-packet-review-bindings/tests/test_agon_sdk_state_packet_bindings.py
```

## Topology Check


The repository-wide topology gate is owned by [root `VALIDATION.md`](../../../../VALIDATION.md#focused-repository-checks).
