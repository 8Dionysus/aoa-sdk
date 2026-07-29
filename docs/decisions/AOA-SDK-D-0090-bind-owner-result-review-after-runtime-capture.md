# Bind Owner Result Review After Runtime Capture

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0090
- Original date: 2026-07-28
- Surface classes: control-plane contract, result evidence, owner review
- SDK facets: control-plane, compatibility, boundary bridge
- Mechanic parents: boundary-bridge
- Guard families: owner boundary, exact binding, freshness, no acceptance inference
- Posture: accepted

## Context

An authenticated MCP canary can prove that the runtime reached one exact tool
and captured a bounded structured result. It cannot determine whether that
result satisfies the organ owner's schema, refers to current owner state, or
deserves acceptance. Keeping only a result digest also prevents the owner from
independently reviewing the exact payload.

OS Abyss therefore needs a portable handoff between a private runtime capture
and each organ's own verifier. That handoff must let central evals use positive
grounding or freshness evidence without letting the SDK, stack, or eval layer
invent owner meaning.

## Options Considered

- Let `abyss-stack` validate payload meaning while capturing the result.
- Let `aoa-evals` infer grounding and freshness from a successful canary.
- Preserve an untrusted content-addressed result artifact, then require the
  source or acceptance owner to issue a separately bound review receipt.

## Decision

Choose the third option.

`aoa-sdk` defines a transport-neutral `OwnerResultCapture`,
`OwnerResultReviewStatement`, and content-addressed
`OwnerResultReviewReceipt`. The receipt binds one runtime-owner capture to the
exact organ, capability, primitive, result digest, runtime receipt, artifact,
observed server and primitive schemas, owner source revision, owner payload
schema, freshness policy, watermark, evidence, and expiry.

The runtime owner captures bytes and supplies capture identity only. The organ
source or acceptance owner inspects the exact artifact and selects
`grounded`, `rejected`, or `blocked` plus a separate freshness state.
`aoa-sdk` validates shape, owner relationships, time bounds, and receipt
identity; it neither executes the verifier nor creates the assessment.

Every receipt keeps `owner_accepted`, central proof, admission,
cross-organ proof, and rollback structurally false. Those axes require their
own owners and evidence. A valid review may support `result_grounded` and
`freshness_satisfied` only when the consuming proof layer also verifies the
exact capture and owner receipt bindings.

## Rationale

The SDK is the narrow owner for a shared transport-neutral evidence contract,
while payload meaning and freshness remain local to each organ. Separating
capture from review makes the payload independently inspectable and prevents a
successful call, runtime self-report, or central eval from silently becoming
owner truth.

## Consequences

- Each participating organ needs a verifier for its own canonical read result.
- Private result artifacts remain untrusted data with no instruction authority.
- Owner review expiry cannot outlive the runtime capture it assesses.
- Central evals can compose exact positive evidence without accepting the
  organ or admitting it.
- Organs with federated acceptance owners remain blocked until that owner
  defines a verifier and review route.

## Source Surfaces

- `src/aoa_sdk/contracts/organs.py`
- `src/aoa_sdk/organs/review.py`
- `schemas/organ-access/organ-owner-result-review.schema.json`
- `mechanics/boundary-bridge/parts/organ-access-control-plane/`
- `repo:abyss-stack/mcp/services/abyss-stack-mcp/src/abyss_stack_mcp/canary.py`

## Follow-Up Route

Implement owner-local verifiers in each participating organ repository.
Route private capture and lifecycle to `abyss-stack`, exact evidence
composition and verdicts to `aoa-evals`, and owner acceptance to the named
acceptance owner.

## Verification

Run organ-access schema parity, focused contract tests, decision-index parity,
nested-agent validation, mechanics topology validation, and each owner
verifier's independent negative tests.
