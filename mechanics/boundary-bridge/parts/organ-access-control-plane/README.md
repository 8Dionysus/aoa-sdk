# Organ Access Control Plane

## Role

This Boundary Bridge part exposes protocol-independent, owner-bounded organ
discovery and candidate-plan compilation without becoming a semantic gateway
or runtime executor.

## Inputs

- an explicitly configured OS-private registry source;
- owner-authored organ, capability, schema, freshness, and handoff references;
- stack-observed deploy and endpoint identities;
- proof and acceptance evidence references owned elsewhere.

## Outputs

- strict typed contracts and deterministic JSON Schema;
- a secret-free, content-addressed registry projection;
- bounded catalog, organ inspection, and capability inspection;
- compatibility observations;
- immutable activation candidates with `execution_authorized=false`;
- a minimal typed result envelope around owner-specific payloads;
- a content-addressed owner-result review contract that binds one private
  runtime capture to an owner schema and freshness assessment;
- a resumable, content-addressed admission receipt chain and exact registry
  transition preview for one organ capability contour;
- a separate owner-plus-operator authorization receipt that still performs no
  registry write or effect activation.
- a multi-contour v2 registry projection with non-admitting migration,
  supplement, and runtime-overlay boundaries;
- an incremental Admission Keeper evidence graph that plans and records owner-
  issued evidence without issuing it;
- a durable protocol-independent TaskStore for owner-bounded long operations,
  without MCP extension authority;
- a private aggregate TaskStore status for active load, quotas, outstanding
  input, pending cancellation, unpersisted expiry, and bounded orphan
  candidates, without task or principal enumeration.

The v2 contour, Keeper, and TaskStore JSON Schemas live in this part's
`schemas/` directory. The generator retains only the pre-existing v1 organ
access schemas in the legacy root `schemas/organ-access/` surface and rejects
any competing v2 copy there.

## Owner

`aoa-sdk` owns the transport-neutral models, compiler, discovery API, and
candidate plan. The configured OS workspace owns the private registry
instance. Organ repositories retain source meaning; `abyss-stack` retains
deploy/runtime/lifecycle; `aoa-evals` retains proof; the relevant organ retains
grounding, freshness, and acceptance. An owner-result review can assert only
the first two; acceptance stays a separate axis.

## Next route

Read [the detailed contract](docs/organ-access.md), then validate the
public-safe shadow example. Runtime observation and execution move to
`abyss-stack`; owner admission needs stronger owner evidence and must not be
inferred from this SDK projection. The admission transaction validates
externally issued owner/runtime/proof receipts; it never runs those validators
or issues their verdicts.

The v2 registry and Keeper remain compatible control-plane additions. An
expired predecessor can become fresh desired state only through the explicit
shadow rebase: it preserves declared contour shape and boundaries while
removing every admission, endpoint, runtime, freshness, consumer, proof,
acceptance, maturity, and last-good claim. It cannot reset a still-current
source or mint an expiry longer than the bounded rebase TTL. A source-owner
shape revision may replace one exact predecessor contour by digest, but the
replacement is also forced to bare shadow and cannot carry any cleared claim.
A contour enters `admitted` only through a separately content-addressed
operator revision bound by compare-and-swap to that exact shadow. The SDK
checks evidence owners and lifetimes for all non-cross-organ maturity axes,
requires distinct proof, owner acceptance, rollback, consumer, and operator
receipts, and records a compatible last-good target. It still performs no
owner tool call, registry publication, rollback, or effect activation.
A live
runtime overlay may bind exact package/process/endpoint identity but cannot
repair expired source, proof, acceptance, consumer, or registry evidence. The
Keeper serializes each complete import/plan/state transaction so concurrent
event and timer triggers cannot both win the same CAS boundary; its root,
internal stores, and lock must remain regular non-symlink paths. The
TaskStore persists and reauthorizes a handle for owner work; the owner run and
its result remain authoritative outside the SDK store. Its aggregate status is
operational evidence only: it emits no task ID or principal ID and cannot turn
a completed task into owner acceptance, proof, or admission. TaskStore roots,
record/audit directories, and the opened lock descriptor are likewise checked
fail-closed against symlink substitution.

## Validation

Use [VALIDATION.md](VALIDATION.md). A green local suite proves SDK contract
behavior only. It does not prove a live endpoint, grounded result, owner
acceptance, or production admission. Even a structurally valid review schema
does not prove that an owner verifier actually inspected a captured result.
