# Titan Runtime Harness

The Titan runtime harness is a small local-first receipt and gate layer for the named service cohort.

## Components

- `schemas/titan_session_receipt.schema.json`
- `schemas/titan_runtime_event.schema.json`
- `examples/titan_session_receipt.example.json`
- `scripts/titanctl.py`

## Runtime lifecycle

```text
roster
  -> summon receipt
    -> optional gate for Forge or Delta
      -> work
        -> closeout
          -> memory candidate review
          -> derived stats
```

## Default state

- Atlas: active
- Sentinel: active
- Mneme: active
- Forge: locked
- Delta: locked

## Gate state

Forge can only be activated by a mutation gate. Delta can only be activated by a judgment gate.

## Receipt discipline

Receipts are local artifacts. They are not memory truth, proof truth, or governance truth. They are session witnesses.
