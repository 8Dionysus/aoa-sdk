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
  -> resumable owner/runtime/proof admission evidence chain
  -> immutable registry transition preview
  -> separate owner and operator decision receipts
  -> exact compare-and-swap authorization with no SDK write
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

`registry_indexed` is deliberately projection-owned. An owner source record
cannot prove that a compiler has indexed itself. During deterministic
compilation, `aoa-sdk` replaces that one projection axis with an expiring
source-digest-bound index receipt; all semantic, runtime, proof, freshness,
acceptance, and rollback axes remain externally owner-issued.

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

## Resumable admission transaction

`aoa organs admission-audit ORGAN_ID CAPABILITY_ID` first reports whether the
current registry state is genuinely current, distinguishing an absent
capability, non-admitted state, missing axes, and expired evidence without
refreshing anything.

`aoa organs admission-*` carries one explicit organ capability contour through
the required receipt sequence:

```text
owner source -> reviewed revision -> package -> deploy manifest
-> deployed bytes -> process -> endpoint -> observed schema -> auth contour
-> consumer registration -> authenticated canary -> owner grounding/freshness
-> central proof -> owner result acceptance -> rollback proof
-> registry transition candidate
```

Every stage is content-addressed, binds the previous run snapshot, names its
issuer and owner-native validator, carries exact subject/evidence/schema
digests, and expires no later than the request. Exact replay is idempotent;
conflicting replay, wrong order, wrong owner, stale evidence, registry drift,
or a blocked/rejected receipt fails closed. A persisted run can be reloaded and
rebuilt without calling any owner.

The candidate is only a comparison against the current registry entry. It has
`registry_update_authorized=false`, records no mutation, and cannot activate
an effect. A later authorization requires two independently addressed receipts:
one from the acceptance owner and one from the OS operator. It also validates
the exact owner-authored admitted `OrganRecord` and current registry digest.
Even then, the SDK returns a short-lived compare-and-swap authorization with
`registry_mutation_performed=false`; the workspace owner performs the write and
must verify the post-update projection separately.

The shared transaction schema transports references to owner-native validators
and receipts. It does not replace owner payload, proof, acceptance, deployment,
or rollback schemas.

## Registry v2 bootstrap after expiry

`registry-migrate-v2` is a compatibility transform: it preserves the v1
claims and expiry and therefore cannot make an expired registry current. Use
`registry-rebase-expired-v2` only when the configured predecessor has already
expired and the workspace owner has explicitly authorized a claim reset:

The owner command is `aoa organs registry-rebase-expired-v2`; its CLI help
names the required migration decision, owner decision, bounded lifetime, and
private candidate output arguments.

The result is fresh *desired shape*, not refreshed admission. Every contour is
`shadow`; endpoint, runtime evidence, proof, acceptance, consumer observation,
freshness, maturity assertions, activation preconditions, and last-good state
are absent. Stronger owners must issue new evidence before the workspace owner
can admit one exact contour. A runtime overlay may add observed identity after
the reset, but cannot restore any cleared claim. Apply one still-live overlay
through the separate checked boundary:

The separate checked boundary is `aoa organs
registry-runtime-overlay-apply`; its CLI help owns the exact source, overlay,
and candidate-output arguments.

The command rejects missing, symlinked, future-dated, or expired overlays.

If an expired predecessor's declared contour shape is itself stale, the source
owner must issue an `aoa_organ_contour_shape_revision_v1`. Apply it with
`registry-contour-shape-apply`. The revision is compare-and-swap bound to the
exact predecessor contour digest and its owner evidence must bind the new
source revision. Even a valid replacement is forced to bare `shadow`; this is
a shape correction, never an admission refresh.

## Registry v2 contour admission

V1 organ-level authorization cannot mutate a v2 contour. For v2, first issue a
content-addressed operator decision against the exact shadow contour digest:

The operator command is `aoa organs
registry-contour-admission-operator-decision`; its CLI help owns the exact
registry, organ, contour, decision reference, expiry, and private-output
arguments.

The runtime owner may then compose, but not issue, an
`aoa_organ_contour_admission_revision_v1` from exact live source, runtime,
consumer, current canary, central proof, owner acceptance, and separately
grounded last-known-good/rollback evidence plus that operator receipt. Apply
the revision only while every referenced receipt is current:

The apply command is `aoa organs registry-contour-admission-apply`; its CLI
help owns the exact predecessor, revision, and candidate-output arguments.

The transition is content-addressed and compare-and-swap bound. It asserts all
required read-contour maturity axes except `cross_organ_proven`, retains
`effect_authorized=false`, and writes no production registry itself. A
separate operator-controlled publication and postcondition check remain
required.

## Reproducible example

`../examples/organ_registry.wave1-shadow.example.json` is a public-safe,
non-admitted example for `aoa-kag`, `aoa-stats`, and `aoa-decisions`. Its
deterministic projection is checked beside it. These fixtures demonstrate
shape only; they are not the private OS registry and do not prove deployment,
compatibility, or benefit.

Regeneration and verification commands live in the part-owned
[`VALIDATION.md`](../VALIDATION.md).
