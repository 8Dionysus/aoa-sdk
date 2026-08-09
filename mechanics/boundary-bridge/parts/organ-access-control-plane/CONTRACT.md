# Organ Access Control-Plane Contract

## SDK owns

- strict organ, result-envelope, registry, compatibility, and activation-plan
  models;
- optional exact `mcp_name` bindings from owner primitive identity to the
  server-visible tool, resource, template, or prompt name;
- strict runtime-capture and owner-result-review models plus deterministic
  receipt addressing;
- explicit registry-path resolution without repository/process discovery;
- deterministic, secret-free projection and digests;
- progressive catalog/inspect/capability discovery with context bounds;
- fail-closed policy, credential-class, schema, freshness, maturity, consumer,
  precondition, approval, expiry, and rollback checks;
- a protocol-independent direct-owner connection descriptor with no execution
  method;
- immutable admission request, evidence, run, candidate, decision, and
  authorization contracts for one exact organ capability contour;
- deterministic replay, resume, expiry, owner/issuer, current-registry
  compare-and-swap, and transition-preview checks;
- separate consumer-registration and final registry-operator owners, so a
  consumer receipt cannot stand in for operator authorization;
- projection-owned `registry_indexed` evidence, avoiding a circular source
  claim before the compiler has actually indexed the record.
- a v2 registry whose admission identity is `(organ_id, contour_id)`, with
  separate endpoint, credential, authority, evidence, currentness, rollback,
  and last-good state for every contour;
- compatibility migration that preserves v1 claims and expiry, plus
  shadow-only contour supplements and evidence-bound runtime overlays that
  cannot refresh proof, acceptance, or admission;
- an explicit expired-source shadow rebase that retains declared contour
  shape and authority boundaries while clearing every current/admitted claim,
  and refuses both current predecessors and unbounded replacement TTLs;
- a source-owner contour shape revision with exact predecessor CAS that can
  correct tool bindings or declared contour shape only by producing a new
  bare shadow with no inherited current/admitted claim;
- a content-addressed, operator-issued contour admission revision that CAS
  binds one shadow predecessor or one already-expired admitted predecessor,
  rejects refresh of a still-current admitted contour, and requires independently owner-qualified
  source, runtime, consumer, proof, acceptance, rollback, and currentness
  evidence while keeping effect and cross-organ authority false;
- immutable content-addressed Admission Keeper nodes, dependency-aware reuse,
  incremental plans, resumable cycles, one exclusive cycle lock across the
  import/plan/state transaction, and compare-and-swap state publication;
- a protocol-independent, principal-bound durable TaskStore with opaque IDs,
  CAS transitions, idempotency, bounded payloads, quota, TTL, cancellation,
  recovery, append-only audit records, and non-symlink store/lock boundaries.

## Stronger owner split

- Agents-of-Abyss: constitutional admission law;
- owner repository: capabilities, schemas, payload meaning, freshness, and
  acceptance;
- configured OS workspace: concrete private registry desired state;
- abyss-stack: package/deploy/process/endpoint/lifecycle observations and
  effect execution;
- aoa-evals: central proof verdict;
- consumer/host: explicit orchestration and final execution authorization.

## Stop lines

- No scan-based admission.
- No credential material in source or projection.
- No automatic activation after discovery.
- No owner tool proxying or hidden server chaining.
- No effect through a read or candidate contour.
- No security decision from MCP annotations, descriptions, `_meta`, or
  self-reported server identity.
- No maturity-axis inference from another axis.
- No owner truth, proof, memory, source, or effect acceptance by the SDK.
- No owner-result review from a runtime capture alone. The runtime owner
  captures bytes; the source or acceptance owner reviews their meaning.
- No `owner_accepted`, central-proof, admission, cross-organ, execution, or
  rollback claim from an owner grounding/freshness review.
- No central proof or owner acceptance issued by `aoa-sdk`.
- No registry mutation from an incomplete, blocked, expired, replay-conflicted,
  or drifted admission run.
- No registry write from an admission candidate. A target record requires
  separate owner and operator decisions and exact compare-and-swap validation.
- No effect activation from read, candidate, admission, or registry-transition
  authorization.
- No admission/currentness refresh from a runtime overlay, live process, or
  Keeper execution alone.
- No owner result, proof verdict, acceptance, or registry write minted by the
  Keeper.
- No authorization or admission inference from a task ID or terminal task
  state.
