# Using Cross-Organ Orchestration

## Host flow

The host performs each owner call outside the SDK:

1. Build a request that pins the five owner schemas, exact revisions, expiry,
   owners, root intent, and source evidence.
2. Run `aoa organs orchestration-start REQUEST.json --output RUN.json`.
3. Call only the required owner surface for the reported `next_stage_kind` and
   `next_owner`.
4. Wrap the result in a typed observation. The host receipt must bind the
   current `snapshot_digest`, exact input and output digests, run ID, stage,
   host ID, time, and outcome.
5. Run
   `aoa organs orchestration-advance RUN.json OBSERVATION.json --output NEXT.json`.
6. Repeat only when the returned run names a next stage.
7. Run `aoa organs orchestration-validate RUN.json` at handoff and closeout.

The SDK does not perform step 3. That separation keeps credential use,
authorization, transport selection, owner-tool invocation, and failure
recovery visible to the host.

## Receipt digest

The host computes `receipt_digest` as canonical sorted JSON SHA-256 over the
typed receipt excluding only `receipt_digest`. Python hosts can use
`aoa_sdk.contracts.control_plane.canonical_digest(receipt,
exclude={"receipt_digest"})`. Computing the digest does not turn the SDK into
the receipt issuer; `host_id` and `receipt_ref` still identify the issuer.

## Schema pins

The public example pins the owner source state inspected on 2026-07-26:

| Stage | Owner revision | Schema SHA-256 |
| --- | --- | --- |
| KAG result | `58ab52ffc06bab5cc28842a0b4336c6efa16b6ff` | `1516bc25755b26c156a58709c5e7600e276daa21f115d7cdc61031cbd67162d5` |
| memo candidate | `e0d3653c11d948f962bcb033749c86c52388ec5f` | `6a33ac41ac90d4af29827a637b8f3cea24ecb45ca259d866e79000a2a784c0d9` |
| eval request | `4d03125d0961dbc0b15332f1a146cd0f7f08eb23` | `751dd78f0280dc2cd089e30b3a7275182656e8350cf84c458f98734d16b4fad1` |
| eval result receipt | `4d03125d0961dbc0b15332f1a146cd0f7f08eb23` | `786c3bd7902fe78224adfc5ac76ed7a43b49f78bb6a5ade140a416458339a82a` |
| reviewed memo landing receipt | `e0d3653c11d948f962bcb033749c86c52388ec5f` | `e3a1e93846340f4d850028eeb722a32458cff6527fe38a6366052edf86a1239f` |

These values are example inputs, not evergreen aliases. A production request
must repin current owner source and schema bytes and fail closed on drift.

## Terminal interpretation

- `accepted`: the explicit acceptance owner returned an exact reviewed
  receipt and the host bound it into the chain.
- `rejected`: the acceptance owner explicitly rejected the object.
- `stopped`: evidence, freshness, or another precondition cannot support the
  next transition.
- `denied`: policy or owner authority forbids the transition.

No terminal state says that the SDK itself invoked an owner, computed proof,
wrote durable memory, or authorized runtime execution.
