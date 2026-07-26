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
- a minimal typed result envelope around owner-specific payloads.

## Owner

`aoa-sdk` owns the transport-neutral models, compiler, discovery API, and
candidate plan. The configured OS workspace owns the private registry
instance. Organ repositories retain source meaning; `abyss-stack` retains
deploy/runtime/lifecycle; `aoa-evals` retains proof; the relevant organ retains
acceptance.

## Next route

Read [the detailed contract](docs/organ-access.md), then validate the
public-safe shadow example. Runtime observation and execution move to
`abyss-stack`; owner admission needs stronger owner evidence and must not be
inferred from this SDK projection.

## Validation

Use [VALIDATION.md](VALIDATION.md). A green local suite proves SDK contract
behavior only. It does not prove a live endpoint, grounded result, owner
acceptance, or production admission.
