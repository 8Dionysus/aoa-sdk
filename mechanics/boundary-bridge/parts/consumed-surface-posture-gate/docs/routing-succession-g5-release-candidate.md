# Routing Succession G5 Release Candidate

## Status

This is the public-release evidence stage immediately before the separate G5
owner switch. It packages and attests exact SDK-produced routing bytes while
`aoa-routing` remains canonical and normal runtime consumption remains denied.

It is not the G5 receipt.

## Why This Stage Exists

The non-publishing G5 candidate and authorized canary proved native SDK
producer identity, stronger-owner verification, consumer loading, and exact
rollback. Their local or host-managed trust roots cannot honestly stand in for
an immutable public release.

The final owner switch should consume already existing public evidence rather
than create release trust and canonical authority atomically. This stage
therefore establishes the release root first and carries no switch authority.

## Exact Envelope

`aoa_sdk.control_plane.routing.release_candidate` wraps a complete, separately
valid non-publishing candidate under `candidate/`. The outer envelope adds:

- `artifact.bundle.json` with explicit
  `producer_admission_profile_id: aoa-sdk-g5-release-candidate`;
- `succession/routing-g5-release-candidate-provenance.json`;
- a `github_release` lifecycle beginning at `release-ready`;
- 29 bound subjects: 27 candidate assembly files, the nested candidate
  provenance, and the release provenance.

The input lock binds the predecessor, the fourteen producer inputs, and the
exact `abyss-machine` verifier. The SDK ref is `SELF` and resolves to the clean
release checkout commit. The archive writer normalizes path, owner, mode, and
time metadata so two builds over the same inputs are byte-identical.

## Public Release And Trust Route

The release workflow:

1. checks out every input at the lock's exact Git ref;
2. builds and validates the wheel;
3. proves the installed wheel can build the release envelope;
4. builds the exact full-corpus envelope and deterministic archive;
5. verifies its ABI, SBOM, SLSA/in-toto, release posture, and authority stop
   line with the pinned stronger-owner source;
6. produces the archive checksum and GitHub artifact attestation;
7. exports the archive, checksum, and verification sidecars for attachment to
   the matching GitHub Release.

After publication, `abyss-machine` may promote the exact asset under
`public_release` trust and admit `release_consumer`. The same durable record
must deny normal `runtime` before G5.

## Authority Stop Line

This stage keeps false:

- `canonical_producer_switch_authorized`;
- `sdk_canonical`;
- `live_runtime_mutation_authorized`;
- `predecessor_maintenance_only`;
- `compatibility_window_started`;
- `archive_authorized`.

It does not change canonical generation, the live runtime, predecessor posture,
the compatibility window, consumer-zero state, or repository archival
authority.

## Next Route

Only after the public asset, attestation, stronger-owner record,
release-consumer verdict, normal-runtime denial, and rollback evidence agree
may the separate G5 switch PR sequence begin.

The G5 switch must update canonical owner policy explicitly; it must not reuse
release publication as the switch receipt.

## Validation

The command authority is the release-support runbook. The focused source tests
prove exact nesting, deterministic archives, substitution denial, lifecycle,
consumer intent, and false authority. The installed-wheel probe proves those
surfaces are package data rather than checkout-only behavior.
