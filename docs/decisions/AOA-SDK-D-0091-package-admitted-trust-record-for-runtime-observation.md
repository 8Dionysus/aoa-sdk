# Package the Admitted Trust Record for Runtime Observation

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0091
- Original date: 2026-07-29
- Surface classes: control-plane, provenance, artifact trust, package data
- SDK facets: plan compilation, snapshot, runtime entry
- Mechanic parents: boundary-bridge, runtime-seam
- Guard families: snapshot trust, artifact trust, portability, exact binding
- Posture: accepted

## Context

AOA-SDK-D-0088 correctly separated the playbook trust record's logical
`record_id` from the digest of its delivered JSON bytes. A fresh installed
wheel runtime cycle exposed a remaining delivery gap: the exact registry
record was generated host state under the `aoa-playbooks` checkout, not a Git
object or published runtime input. A clean federation could compile the plan
from the packaged source lock but could not deliver that source ref to the
runtime without reconstructing ephemeral bytes.

## Options Considered

- Require every runtime host to rebuild the old registry record byte-for-byte.
- Teach runtime adapters a special network or host-registry lookup for this one
  source kind.
- Remove the admitted record from the plan snapshot.
- Package the exact public-safe record selected during pinning and keep its
  upstream owner, logical identity, byte digest, and trust controls explicit.

## Decision

Choose the fourth option.

The C2 pinning step copies the exact admitted registry record into SDK package
data beside the contour, schema, and source lock. Snapshot loading verifies
the packaged bytes against `record_artifact_digest` and checks their record
identity, upstream source owner, subject-store admission, lifecycle posture,
and required controls against the source lock.

`PlanCompilationSnapshot.admission_provenance` names `aoa-sdk` as the delivery
owner of that immutable package resource while retaining the upstream
`record_id` as `source_ref`. The record body and source lock continue to name
`aoa-playbooks` and `abyss-machine` as the semantic and trust authorities.
Runtime observation therefore reads normal installed package bytes and needs
no provenance rewrite, host-generated registry, or predecessor checkout.

## Rationale

The SDK already packages the exact admitted owner contour and schema required
by its compiler. Packaging the matching public trust record completes that
same immutable input envelope. It makes the runtime source set portable
without turning SDK packaging into trust admission, playbook meaning, or an
eval verdict.

## Consequences

- Clean installed-wheel execution can materialize every plan snapshot source.
- Record tampering or a lock/record mismatch fails before compilation.
- Repinning changes package data whenever the admitted record bytes change,
  even when its logical `record_id` is stable.
- The package copy is a delivery projection only; upstream trust admission and
  playbook authority remain external.

## Source Surfaces

- `src/aoa_sdk/control_plane/planning/snapshot.py`
- `src/aoa_sdk/control_plane/planning/data/playbook-plan-contours-source-lock.v1.json`
- `src/aoa_sdk/control_plane/planning/data/playbook-plan-contours-trust-record.v1.json`
- `mechanics/boundary-bridge/parts/plan-compilation-control-plane/scripts/pin_playbook_plan_contours.py`
- `mechanics/boundary-bridge/parts/plan-compilation-control-plane/tests/`
- `repo:abyss-stack/mechanics/governed-execution/parts/agent-os-adapter/`

## Follow-Up Route

Keep the installed-wheel compiler-to-runtime cycles mandatory. Any future
external non-Git snapshot input must either have a durable consumer fetch
contract or be packaged as an exact lower-authority delivery projection.

## Verification

Run exact owner pin parity, decision-index parity, C2 focused tests, installed
wheel checks, all three fresh compiler-to-runtime lifecycle cycles, and the
full SDK and runtime-owner release gates.
