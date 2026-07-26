# Use a Cross-zlib Canonical Release Carrier

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0074
- Original date: 2026-07-25
- Surface classes: release trust, determinism, archive carrier, CI
- SDK facets: distribution, control-plane
- Mechanic parents: release-support, boundary-bridge
- Guard families: release provenance, artifact trust, reproducibility
- Posture: accepted

## Context

The `v0.7.0` full-corpus release candidate produced identical normalized tar
bytes in a local clean build and GitHub Actions, but their gzip digests
differed. `gzip.GzipFile` fixed header metadata while still delegating DEFLATE
encoding to the environment's zlib implementation. Same-environment tests
therefore passed without proving cross-runner carrier identity.

Attaching either carrier would make the public release digest depend on the
build environment even though every release subject was identical.

## Options Considered

- Accept content-equivalent tar streams with different gzip digests.
- Pin one zlib implementation and version in every producer environment.
- Define one minimal gzip encoding whose bytes do not depend on zlib.

## Decision

Encode deterministic release tar streams with a fixed gzip header, canonical
stored DEFLATE blocks of at most 65,535 bytes, and explicit CRC32 and input
size fields. Do not call a platform compression library for release-carrier
encoding.

Immutable-tag replay may use a newer reviewed implementation of this carrier,
but it must read the input lock, SDK source, and all release subjects from the
exact tag checkout. The workflow revision remains separate attestation
provenance and never becomes the release source ref.

## Rationale

Stored blocks trade compression ratio for a small, auditable format whose
output depends only on the normalized tar bytes. This makes exact independent
digest comparison portable and preserves the immutable release boundary.

## Consequences

- Local and CI builds over equal tar input produce the same gzip digest.
- Release candidates are larger than zlib-compressed carriers.
- Replay tooling and immutable subject source are separate, explicitly
  reviewable inputs.
- Existing attestations over noncanonical carriers remain historical evidence
  and must not be promoted as the public release asset.

## Source Surfaces

- `src/aoa_sdk/control_plane/routing/release_candidate.py`
- `.github/workflows/release-artifacts.yml`
- `mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_routing_g5_release_candidate.py`
- `mechanics/release-support/parts/release-audit-publish-helper/tests/test_release_audit_publish_helper.py`

## Follow-Up Route

Use the stronger-owner trust route to promote only the exact final attached
digest. Keep the earlier content-equivalent carrier outside the release
registry.

## Verification

Prove a fixed gzip digest across a payload spanning multiple stored-block
boundaries, round-trip the carrier through a standard gzip decoder, compare
independent local and GitHub Actions archive bytes, and verify GitHub OIDC
attestation against the exact final digest.
