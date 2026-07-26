# Authorize the Receipt-bound Routing G5 Owner Switch

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0075
- Original date: 2026-07-26
- Surface classes: ownership, routing succession, release trust, runtime boundary, repository lifecycle
- SDK facets: control-plane, facade boundary, runtime entry, distribution
- Mechanic parents: boundary-bridge, release-support
- Guard families: owner succession, release provenance, byte parity, runtime admission, rollback, archive stop line
- Posture: accepted

## Context

The staged succession established an SDK-native producer, exact shadow parity,
consumer canaries, rollback proof, and an immutable public `v0.7.0` release
candidate while `aoa-routing` remained canonical. The public asset is bound to
SDK source `15f8239c6467ee99da0f6f9615bcb9a44270b574` and SHA-256
`adf38173306baef7fc47595fc7f44b46bb107fbc48b493adf4b665a22520bee2`.

That asset proves which routing bytes were publicly released, but deliberately
carries no G5 authority. The runtime owner has now landed
`ABYSS-STACK-D-0086` at
`fac82c75d860dd2433cfc1e391f4b6ba117425d7`, defining the receipt that a live
cutover must consume. The remaining SDK-side problem is to authorize one
canonical producer without changing the already-reviewed routing assembly or
silently authorizing runtime execution, consumer-zero, or repository archival.

Embedding the final release archive digest in a receipt stored inside that same
archive would be self-referential. Rebuilding the routing corpus from newer
inputs would also mix ownership succession with an unreviewed data change.

## Options Considered

- Keep `aoa-routing` canonical indefinitely and treat the SDK as a permanent
  shadow.
- Rebuild routing from current sibling heads and switch ownership in one
  release.
- Put the final canonical archive digest inside its own owner-switch receipt.
- Reproduce the exact public `v0.7.0` assembly, prove byte parity, and add a
  separate receipt and provenance envelope in `v0.8.0`.

## Decision

Release `v0.8.0` as the receipt-bound SDK-canonical G5 envelope.

The canonical builder must:

- rebuild from the exact producer inputs used by `v0.7.0`;
- require every routing assembly member to equal the immutable public release
  asset byte for byte;
- bind the SDK release source, retained predecessor ref, public release ref and
  digest, runtime contract ref, ABI epoch, and compatibility-window start;
- emit `succession/routing-g5-owner-switch.json` with schema
  `aoa_sdk_routing_g5_owner_switch_receipt_v1`;
- emit separate canonical provenance and an
  `aoa-sdk-g5-canonical` artifact manifest;
- authorize the canonical producer switch, SDK canonical posture, predecessor
  maintenance-only posture, compatibility-window start, and later
  receipt-gated runtime mutation;
- record `live_cutover_executed=false` in the release provenance because the
  SDK release is authorization, not runtime execution;
- keep `archive_authorized=false` and retain `aoa-routing` as the exact rollback
  source.

The immutable `v0.7.0` release digest is the byte-parity trust root. The
`v0.8.0` source ref and its GitHub attestation identify the owner-switch
envelope. These are deliberately separate identities and avoid a
self-referential digest.

## Rationale

This is the smallest atomic owner change that preserves the proven routing
corpus. It turns `aoa-sdk` from a shadow implementation into the single
canonical producer while keeping the release bytes, runtime mutation, and
archive decision independently reviewable.

Separating authorization from execution also preserves owner routing:
`aoa-sdk` owns producer authority, `abyss-machine` owns durable artifact
admission, and `abyss-stack` owns live runtime cutover. None may infer the
others' completion from a tag or a green test.

## Consequences

- New routing producer work belongs in `aoa-sdk` after this release.
- `aoa-routing` enters compatibility, security, rollback, and deprecation-only
  maintenance after its paired M3 receipt lands.
- `abyss-machine` must add and validate the exact canonical admission profile
  before the runtime consumer may materialize the artifact.
- `abyss-stack` may execute the live cutover only from the admitted exact
  receipt and must record a separate execution receipt.
- Consumer-zero and compatibility exit remain future measured conditions.
- Archival remains forbidden without those conditions and separate exact
  operator approval.

## Source Surfaces

- `src/aoa_sdk/control_plane/routing/canonical.py`
- `src/aoa_sdk/control_plane/routing/schemas/routing-g5-owner-switch-receipt.schema.json`
- `src/aoa_sdk/control_plane/routing/schemas/routing-g5-canonical-provenance.schema.json`
- `sdk/distribution/manifests/routing_g5_canonical.input-lock.json`
- `mechanics/release-support/parts/release-audit-publish-helper/scripts/build_routing_g5_canonical.py`
- `mechanics/boundary-bridge/parts/consumed-surface-posture-gate/docs/routing-succession-g5-owner-switch.md`
- `.github/workflows/release-artifacts.yml`

## Follow-Up Route

Land the exact `aoa-sdk-g5-canonical` policy in `abyss-machine`, admit and
materialize the published `v0.8.0` artifact, execute the receipt-gated
`abyss-stack` cutover, and then land the paired `aoa-routing` M3 maintenance
receipt.

Do not combine the G5 owner switch with the later Agent OS Runner release.
Do not archive `aoa-routing` without separate exact operator approval.

## Verification

Run decision-index generation, focused canonical positive and negative tests,
the clean installed-wheel canonical probe, deterministic public-release
byte-parity reconstruction, release workflow contract tests, the full SDK
release check, and GitHub attestation verification for the published
`v0.8.0` canonical archive.
