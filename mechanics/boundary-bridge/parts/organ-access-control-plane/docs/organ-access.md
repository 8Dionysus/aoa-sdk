# OS Abyss Organ Access

`aoa-sdk` provides the protocol-independent control-plane contract for
connecting OS Abyss organs. MCP is one possible direct-owner adapter. The SDK
does not deploy MCP servers, proxy their tools, provision credentials, execute
effects, or decide that owner output is true.

## Authority path

```text
owner contract + OS-private desired state + stack observations + eval refs
  -> strict source validation
  -> deterministic, secret-free registry projection
  -> bounded catalog
  -> organ inspection
  -> capability and primitive inspection
  -> content-addressed candidate activation plan
  -> separate runtime-owner authorization and direct owner connection
  -> private content-addressed runtime capture
  -> source/acceptance-owner grounding and freshness review
  -> owner-qualified result envelope and runtime receipt
```

The concrete registry instance belongs to the configured OS workspace or
operator. It is never discovered by scanning repositories, packages,
processes, or endpoints. Configure exactly one source with either:

```toml
[organ_access]
registry_source = "/private/os-abyss/organ-registry.json"
```

or `AOA_SDK_ORGAN_REGISTRY`. The environment override wins. Registry JSON must
contain no credential material; it carries only distinct credential *class*
identifiers. Source and projection schemas live under
`schemas/organ-access/`.

## Progressive discovery

Use the smallest surface that can answer the task:

1. `aoa organs catalog` returns compact owner and capability cards. It never
   loads input/output schemas, hides suspended/deprecated/retired records, and
   enforces result and byte bounds.
2. `aoa organs inspect ORGAN_ID` returns the declared organ contract and
   maturity vector.
3. `aoa organs capability ORGAN_ID CAPABILITY_ID` reveals primitive schemas,
   effect classes, policy family, eval refs, and rollback posture.
4. `aoa organs plan REQUEST.json` compiles immutable candidate intent only.
   Every plan has `execution_authorized: false`.

`catalog` defaults to the `read` policy ceiling and can additionally filter by
owner, freshness, effect class, and explicit organ/capability allowlists.
Read, candidate,
internal-effect, and external-effect credentials must be distinct. An effect
primitive must be a tool, require explicit approval, name a rollback route,
and match its effect-policy family. External effects additionally require an
exact target.

## Admission and truth labels

The registry defaults to deny and models each maturity claim independently:
declared, owner-reviewed, packaged, exported, deployed, process alive,
endpoint ready, registry indexed, consumer registered, schema observed, call
succeeded, result grounded, freshness satisfied, owner accepted, cross-organ
proven, and rollback proven. Presence or a successful call never implies the
other axes.

Only `admitted` records can produce candidate activation plans. Admission
requires exact source/package/deploy/schema identities, evidenced supported
consumer compatibility, activation preconditions, exact owner freshness, and
the required maturity evidence including rollback proof. Schema or deploy
drift blocks compilation.

`OrganResultEnvelope[T]` normalizes only access metadata: owners, revisions,
schema digests, watermark, freshness/TTL/cache policy, evidence, effect state,
warnings, receipt, and trace ID. `T` remains the organ owner's typed payload;
the envelope cannot upgrade self-reported output into proof, memory, source,
or acceptance authority.

## Owner review after runtime capture

The runtime owner may preserve one bounded MCP result as an untrusted,
content-addressed private artifact. That proves capture only. The source or
acceptance owner must independently validate the exact artifact against its
owner payload schema and freshness policy before `result_grounded` or
`freshness_satisfied` can gain evidence.

`OwnerResultReviewReceipt` binds:

- the runtime-owner capture receipt and result artifact identities;
- organ, capability, and primitive;
- captured result, server schema, and primitive schema digests;
- owner source revision and owner payload schema digest;
- owner-qualified grounding evidence, freshness policy, watermark, and expiry.

`aoa-sdk` validates this shared shape and its content address. It does not run
the owner verifier or choose `grounded`, `rejected`, or `blocked`. The receipt
has structurally false claims for owner acceptance, central proof, admission,
cross-organ proof, and rollback. `aoa-evals` may consume a verified receipt as
one exact evidence input, but must not infer those other axes.

## Reproducible example

`../examples/organ_registry.wave1-shadow.example.json` is a public-safe,
non-admitted example for `aoa-kag`, `aoa-stats`, and `aoa-decisions`. Its
deterministic projection is checked beside it. These fixtures demonstrate
shape only; they are not the private OS registry and do not prove deployment,
compatibility, or benefit.

Regeneration and verification commands live in the part-owned
[`VALIDATION.md`](../VALIDATION.md).
