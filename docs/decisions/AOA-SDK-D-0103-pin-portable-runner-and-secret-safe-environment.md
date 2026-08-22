# Pin the Portable Validation Runner and Bind a Secret-Safe Environment

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0103
- Original date: 2026-08-21
- Surface classes: validation, compatibility, owner-boundary
- SDK facets: release support, control-plane validation
- Mechanic parents: release-support, validation-evidence-graph
- Guard families: source identity, environment drift, fail-closed sufficiency
- Posture: accepted

## Context

The bounded claim/evidence graph already binds the owner repository and the
reference runner as separate identities, but an external owner manifest did
not declare which exact SDK runner source it expected. Its environment receipt
also exposed only selected values rather than binding the complete inherited
execution environment. A successful external graph could therefore be
portable in scheduling mechanics while remaining ambiguous about runner
source or environment drift.

## Options Considered

- Keep runner identity and the selected environment fields as receipt-only
  observations.
- Require external owners to pin the exact SDK runner path, source commit, and
  file digest, and bind the complete inherited environment through a
  secret-safe before/after digest.
- Move runner admission, sibling claim meaning, or environment policy into a
  central SDK or proof owner.

## Decision

Version the external-owner runner contract as
`aoa_validation_runner_pin_v1`. Every external owner manifest must declare
the SDK runner's exact repository-relative path, source commit, and file
digest; a missing or mismatched pin makes the receipt insufficient. The
SDK-local manifest keeps the pin null because its owner and runner source
checkout are the same.

The runner hashes the complete inherited environment without serializing its
keys or values, records the secret-safe identity before and after execution,
and fails closed on drift. This slice remains an owner-local provenance and
interoperability guard: it does not author sibling claims, centralize
evidence meaning, select proof verdicts, or authorize runtime or publication.

## Rationale

An exact pin gives an external owner a portable runner ABI with independently
checkable source provenance while preserving the owner-root boundary. The
complete environment digest closes the gap between a partial environment
observation and a stable execution context without exposing credentials or
other environment values in receipts. Keeping the pin null only for the
same-checkout SDK run avoids inventing a cross-repository boundary where none
exists.

## Consequences

- External owner manifests must migrate to the versioned `runner_pin` field.
- Runner path, source commit, file digest, and environment drift are explicit
  fail-closed receipt blockers.
- A dirty SDK source checkout is not silently asserted clean; the declared
  runner file digest and observed source identity remain visible for the
  owning adoption or admission decision.
- Sibling owners still define their own claims, evidence, sufficiency, and
  admission. `aoa-evals`, `aoa-stats`, `abyss-machine`, runtime, and GitHub
  retain their separate authority boundaries.

## Source Surfaces

- `mechanics/release-support/parts/validation-evidence-graph/scripts/validation_graph.py`
- `mechanics/release-support/parts/validation-evidence-graph/config/validation_graph.json`
- `mechanics/release-support/parts/validation-evidence-graph/tests/test_validation_graph.py`
- `mechanics/release-support/parts/validation-evidence-graph/CONTRACT.md`
- `mechanics/release-support/parts/validation-evidence-graph/VALIDATION.md`
- `mechanics/release-support/ROADMAP.md`

## Follow-Up Route

The next owner adoption surface is each sibling repository's own manifest and
admission gate: it must pin the SDK runner at the commit and file digest it
actually reviewed. `aoa-evals` may compare the resulting owner receipts only
after its own proof contract admits them. Do not treat the pin or environment
receipt as runtime health, central proof, or publication acceptance.

## Verification

The part-local validation graph tests cover missing and mismatched external
pins, secret-safe environment hashing, and environment drift. Run the
decision-index and nested-agent validators, the focused graph suite, and the
full `release_check.py` graph after commit.
