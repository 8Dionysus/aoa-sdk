# Export the reference validation scheduler with an explicit owner root

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0098
- Original date: 2026-08-11
- Surface classes: validation guard, workflow, compatibility boundary
- SDK facets: validation, release support, control-plane
- Mechanic parents: release-support
- Guard families: owner authority, runner identity, claim/evidence sufficiency
- Posture: accepted

## Context

The SDK validation pilot established a bounded claim/evidence scheduler, but
the remaining AbyssOS repositories must not acquire separate copies that drift
in timeout, identity, dependency, or sufficiency behavior. They also must not
import the SDK claim set or let a shared runner become sibling proof authority.

A portable invocation therefore needs to distinguish three identities: the
SDK source checkout that supplies the scheduler, the owner repository whose
commands and source are being validated, and the owner-authored manifest that
maps claims to evidence.

## Options Considered

- Copy the complete scheduler into every repository.
- Move all repository claims into one central SDK manifest.
- Publish an installed service that decides validation centrally.
- Keep the reference implementation in the SDK mechanic and permit a pinned
  source checkout to execute an owner-local manifest through an explicit
  `--repo-root` boundary.

## Decision

Keep one reference scheduler implementation under the SDK release-support
mechanic and expose an explicit `--repo-root` argument for sibling pilots.

The manifest must reside inside that owner root. Receipts bind the owner Git
identity and the SDK runner source Git identity separately, including the
runner file digest and before/after state. Missing or changing runner source
identity makes the receipt insufficient.

Only scheduling mechanics and receipt shape are reusable. Each sibling owner
must define its own claims, risks, evidence providers, serial completeness
oracle, runner pin, resource limit, comparative admission rule, and rollback.
Partial routing and cross-run reuse remain non-authoritative.

## Rationale

One implementation prevents security and behavior drift in the scheduler.
Explicit owner and runner identities prevent that reuse from hiding which
source executed which repository's evidence. Keeping manifests owner-local
preserves the authority boundary demonstrated by the SDK pilot.

The external-owner regression executes a committed temporary owner manifest,
binds its repository independently from the SDK runner checkout, and produces
a sufficient full receipt. Negative regressions reject a manifest outside the
owner root and make unavailable runner source identity insufficient.

## Consequences

- Sibling workflows need a pinned SDK source checkout until a separately
  trusted distribution route exists.
- A runner update is visible in every receipt and can be admitted or rolled
  back independently by each owner.
- The SDK does not decide whether a sibling claim set is complete or whether
  that sibling may land.
- The common ABI can evolve once while owner manifests and comparative evidence
  remain independent.

## Source Surfaces

- `mechanics/release-support/parts/validation-evidence-graph/scripts/validation_graph.py`
- `mechanics/release-support/parts/validation-evidence-graph/tests/test_validation_graph.py`
- `mechanics/release-support/parts/validation-evidence-graph/CONTRACT.md`
- `mechanics/release-support/parts/validation-evidence-graph/README.md`
- `mechanics/release-support/parts/validation-evidence-graph/VALIDATION.md`

## Follow-Up Route

Pilot the ABI in one high-cost sibling owner with a pinned SDK checkout, exact
serial oracle, hosted A/B comparison, retained receipts, and owner-local
decision. Do not infer adoption for other repositories from that result.

## Verification

Run the validation-graph contract tests, decision-index checks, nested-agent
validation, mechanics topology, Ruff, the SDK full graph, and hosted Repo
Validation. The first sibling pilot must additionally prove its own full
evidence parity and post-merge gate.
