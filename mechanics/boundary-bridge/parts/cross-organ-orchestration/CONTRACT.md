# Cross-Organ Orchestration Contract

## Exact chain

The request pins exactly five stage contracts:

| Stage | Owner | Input | Output | Ceiling | Effect |
| --- | --- | --- | --- | --- | --- |
| KAG evidence | evidence owner | orchestration intent | KAG evidence | read | observe |
| memo candidate | memory owner | KAG evidence | memo candidate | candidate | prepare candidate |
| eval request | proof owner | memo candidate | eval request | candidate | prepare candidate |
| eval result | proof owner | eval request | eval result | read | validate |
| owner acceptance | acceptance owner | eval result | owner acceptance | internal effect | accept source |

Every output schema identity includes its owner, repo-relative schema ref,
SHA-256, source revision, and schema version. Every artifact has a typed ref,
digest, owner, source revision, authority ceiling, creation time, and expiry.

## Transition law

Each `orchestration-advance` accepts exactly one observation and must prove:

- its stage and owner match the next pinned contract;
- its input is byte-identical in identity to the previous output;
- its output schema, source revision, authority ceiling, and effect class are
  pinned by the request;
- owner-qualified evidence is current at observation time;
- the output and receipt do not outlive the request;
- the receipt binds run ID, host ID, previous snapshot, input digest, output
  digest, stage, outcome, and issue time;
- the receipt digest covers every receipt field except itself;
- the transition either names the exact next owner or terminates.

`exact` and `compatible_drift` may proceed before the final owner stage.
`stale_readable`, `blocked`, `unknown`, and `rollback_required` must stop or
deny. Owner acceptance requires `exact` freshness.

## Owner acceptance

An accepted or rejected terminal state is valid only when the acceptance owner
supplies:

- an explicit acceptance decision;
- an owner-qualified review ref;
- an exact typed owner receipt included in the host receipt;
- an output using the pinned acceptance schema;
- `accept_source/applied` for acceptance or `accept_source/denied` for
  rejection.

Model confidence is fixed to `false` as acceptance authority. An eval result,
including a passed receipt, cannot close the chain by itself.

## Stop lines

- No MCP tool execution by `aoa-sdk`.
- No hidden server-to-server chaining.
- No hidden shared context.
- No KAG-to-memory write.
- No candidate-to-durable-memory promotion.
- No eval source mutation or SDK-computed verdict.
- No runtime or external effect.
- No acceptance inferred from confidence, schema validity, endpoint success,
  or a preceding stage.
- No advance after a terminal state.

The workspace MCP exposes organ discovery only. It does not expose this state
machine or a general organ proxy.
