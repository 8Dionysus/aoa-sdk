# Make Organ Admission Resumable and Non-Mutating

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0092
- Original date: 2026-08-01
- Surface classes: organ admission, private registry, transition receipt
- SDK facets: control-plane, compatibility, CLI
- Mechanic parents: boundary-bridge
- Guard families: deny by default, content addressing, owner boundary, compare and swap, rollback
- Posture: accepted implementation contract

## Context

The v1 organ registry made admission strict but left the operator to replay a
long evidence sequence manually. It also required `registry_indexed` evidence
inside an already `admitted` source record, even though indexing happens only
after the compiler reads that record. That circularity prevents an honest
preview-before-write transaction. Multi-contour organs additionally need every
capability admission to remain independently reviewable.

## Options Considered

- Continue assembling each admitted record manually from runtime notes.
- Let `abyss-stack` or `aoa-sdk` discover evidence and mutate the registry.
- Add a pure, resumable SDK transaction over externally issued owner-native
  receipts, followed by separate owner/operator decisions and a non-writing
  compare-and-swap authorization.

## Decision

Choose the third option.

One admission request pins the current registry and one exact capability
contour. Fifteen ordered receipt stages bind owner source, reviewed revision,
package, deploy, runtime, schema, auth, consumer, canary, grounding/freshness,
central proof, owner acceptance, and rollback. Every receipt binds the prior
snapshot and a pinned owner-native validator. Exact replay is idempotent;
conflicting replay, missing stages, wrong issuers, expiry, or drift fails
closed.

An MCP-exported primitive can additionally carry its exact `mcp_name`, so the
proposal retains the owner primitive-to-server binding instead of inferring it
from discovery during admission.

A complete run emits only a content-addressed registry transition preview.
Separate acceptance-owner and OS-operator decision receipts are required
before the SDK can emit an expiring compare-and-swap authorization for one
exact owner-authored target record. The SDK never writes the registry or
activates an effect.

The request names `consumer_owner` independently from `operator_owner`.
Consumer-registration evidence must come from the former; the final registry
decision must come from the latter. A consumer receipt therefore cannot
authorize its own admission.

`registry_indexed` becomes derived projection evidence. The source record need
not assert it before admission; deterministic registry compilation attaches an
expiring `aoa-sdk` index receipt bound to the exact source digest.

## Rationale

This makes admission repeatable and restart-safe without making the SDK a
runtime observer, proof owner, acceptance owner, or registry operator. Owner
schemas remain stronger than the shared carrier: the transaction stores their
exact refs, revisions, digests, validator identities, and receipts rather than
flattening their payload meaning.

## Consequences

- Admission can be resumed from immutable snapshots and audited stage by
  stage.
- The current registry entry is compared at start, candidate build, and final
  authorization.
- An incomplete or stale chain cannot produce a candidate or registry update
  authorization.
- Owner and operator decisions remain separate even when one organization
  fills both roles.
- Live admission still requires real owner/runtime/proof receipts; synthetic
  contract tests prove mechanics only.
- Post-write compilation and consumer verification remain workspace/runtime
  responsibilities.

## Source Surfaces

- `src/aoa_sdk/contracts/organ_admission.py`
- `src/aoa_sdk/organs/admission.py`
- `src/aoa_sdk/organs/registry.py`
- `src/aoa_sdk/cli/organs.py`
- `mechanics/boundary-bridge/parts/organ-access-control-plane/`

## Follow-Up Route

Use the transaction first against the already admitted `aoa-kag` baseline,
then `abyss-stack-mcp.read`, then one cognitive read contour. Runtime evidence
comes from `abyss-stack`, proof from `aoa-evals`, and acceptance from each
named organ owner. Keep candidate and effect contours independent.

## Verification

Use the organ-access schema generator/check, focused part tests, mypy over the
organ contract and implementation modules, the mechanics topology validator,
and generated decision-index parity check.
