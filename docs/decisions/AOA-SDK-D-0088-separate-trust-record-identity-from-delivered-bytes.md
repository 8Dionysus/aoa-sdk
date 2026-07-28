# Separate Trust Record Identity from Delivered Bytes

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0088
- Original date: 2026-07-26
- Surface classes: control-plane, provenance, artifact trust, runtime boundary
- SDK facets: plan compilation, snapshot, runtime entry
- Mechanic parents: boundary-bridge, runtime-seam
- Guard families: snapshot trust, artifact trust, exact binding, runtime admission
- Posture: accepted

## Context

The playbook plan-contour source lock retained the latest admitted
`record_id` from the `abyss-machine` artifact trust gate. The compiler then
placed that ID in both `ProvenanceRef.source_ref` and
`ProvenanceRef.artifact_digest` for the trust-record source.

Those fields are not interchangeable. The registry derives `record_id` from
the artifact class, bundle subject digest, and bundle manifest ref. The
registry JSON file contains additional mutable trust and subject-store
evidence, so its byte SHA-256 is intentionally different. Runtime snapshot
observation hashes delivered files. Treating the logical ID as a byte digest
therefore made an otherwise valid public compiler plan impossible to observe
without rewriting provenance after compilation.

## Options Considered

- Rewrite the compiled plan digest in the runtime integration fixture.
- Teach the runtime adapter that one `artifact_digest` has special non-byte
  semantics.
- Remove the trust record from `PlanSnapshot`.
- Preserve both identities explicitly and keep runtime observation uniformly
  byte-addressed.

## Decision

The plan-contour source lock retains two exact values:

- `record_id` is the stable logical identity selected by the trust gate;
- `record_artifact_digest` is SHA-256 over the exact registry-record bytes
  read during pinning.

The pinning script must read the bounded record path selected by `record_id`,
verify that its JSON object equals the trust-gate return, and record its byte
digest. `PlanCompilationSnapshot.admission_provenance` uses `record_id` as
`source_ref` and `record_artifact_digest` as `artifact_digest`.

Both values participate in snapshot identity. The runtime continues to
observe every source with the same file-byte SHA-256 rule; it gains no
trust-record exception.

## Rationale

Separating logical identity from delivered bytes preserves the
`abyss-machine` registry contract and the SDK/runtime provenance contract at
the same time. It removes a hidden fixture-only transformation and lets an
installed public SDK plan pass exact owner-source observation unchanged.

## Consequences

- Positive: a public compiler plan can reach runtime with its original
  snapshot and plan digests intact.
- Positive: record selection and byte freshness remain independently
  auditable.
- Positive: runtime source verification keeps one uniform rule.
- Tradeoff: repinning is required when trust-record bytes change even if its
  logical `record_id` stays stable.
- Stop line: a passing trust gate does not make generated host state a Git
  artifact or an eval verdict.

## Source Surfaces

- `src/aoa_sdk/control_plane/planning/snapshot.py`
- `src/aoa_sdk/control_plane/planning/data/playbook-plan-contours-source-lock.v1.json`
- `mechanics/boundary-bridge/parts/plan-compilation-control-plane/scripts/pin_playbook_plan_contours.py`
- `mechanics/boundary-bridge/parts/plan-compilation-control-plane/tests/`
- `repo:abyss-machine/src/abyss_machine/artifact_bundles.py`

## Follow-Up Route

Keep the installed-wheel runtime integration test fail-closed: it may
materialize pinned fragment bytes, but it must never modify a compiled
`ProvenanceRef`, `PlanSnapshot`, or `RunPlan`.

## Verification

Run the exact owner pin check, deterministic example check, focused compiler
suite, installed-wheel golden chain, paired `abyss-stack` public
compiler-to-runtime cycles, and the full SDK and stack gates.
