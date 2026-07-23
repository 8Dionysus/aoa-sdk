# Titan Runtime Harness

The Titan runtime harness is a small local-first receipt and gate layer for the named service cohort.

## Components

- `../schemas/titan_session_receipt.schema.json`
- `../schemas/titan_runtime_event.schema.json`
- `../examples/titan_session_receipt.example.json`
- `../scripts/titanctl.py`

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

For an intent or observation that must remain explicitly outside runtime,
initialize a witness instead:

```text
witness-init
  -> validate
    -> owner review or bounded candidate ingest
```

`witness-init` records `runtime_execution_state=not_run`,
`transport_state=not_sent`, and `authority=witness_only`; it never writes a
`summon` event. Atlas, Sentinel, and Mneme remain `declared`, while Forge and
Delta remain `locked`; a witness contains no `active` incarnation.

## Default state

- Atlas: active
- Sentinel: active
- Mneme: active
- Forge: locked
- Delta: locked

## Gate state

Forge uses a mutation gate and Delta uses a judgment gate. Every local gate
record preserves an external decision reference and unauthenticated approver
attribution. On a summon-style helper receipt the gate changes the helper
projection to active; on a `witness-init` receipt it records the decision while
leaving the incarnation locked. Neither form proves runtime activation.

## Receipt discipline

Receipts are local artifacts. They are not memory truth, proof truth,
governance truth, operator authentication, or runtime execution evidence.
