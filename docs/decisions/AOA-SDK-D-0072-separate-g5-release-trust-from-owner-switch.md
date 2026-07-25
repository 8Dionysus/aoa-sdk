# Separate G5 Release Trust From Owner-Switch Authority

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0072
- Original date: 2026-07-25
- Surface classes: ownership, release trust, artifact admission, repository succession, runtime boundary
- SDK facets: control-plane, facade boundary, runtime entry, distribution
- Mechanic parents: boundary-bridge, release-support
- Guard families: owner succession, release provenance, artifact trust, runtime admission, rollback
- Posture: accepted

## Context

The non-publishing SDK G5 candidate and its authorized canary proved native SDK
producer identity, stronger-owner artifact handling, runtime consumption, and
exact rollback while `aoa-routing` remained canonical. That candidate
deliberately uses local or host-managed trust and a manual lifecycle. A
production-grade runtime record instead needs an exact public release asset,
public provenance, and release lifecycle.

Treating public release proof as the G5 receipt would collapse two independent
claims: which bytes were published and which repository owns canonical
generation. Reusing the local candidate profile would hide the different trust
root. Switching ownership before publication would make the new canonical
producer depend on evidence that did not yet exist.

## Options Considered

- Reuse the manually verified canary record as production release evidence.
- Switch canonical ownership first and publish the SDK routing asset afterward.
- Publish a separately profiled release candidate, admit its exact public bytes,
  and keep all owner-switch authority false until a later G5 receipt.

## Decision

Use a distinct `aoa-sdk-g5-release-candidate` admission profile and a
deterministic public release envelope around the independently valid
non-publishing candidate.

The release envelope binds the exact SDK commit, predecessor commit, fourteen
producer-input commits, nested candidate manifest and provenance, release
manifest and provenance, all routing outputs, runtime schemas, and runtime
boundary documents. The release workflow must use the exact stronger-owner
verifier commit recorded in the input lock and attest the archive digest.

Public release admission may serve `release_consumer` and `runtime_canary`
intents. It must deny normal `runtime`, keep `aoa-routing` canonical, and keep
all six G5 authority flags false. Canonical SDK publication requires a later,
separate G5 policy and receipt landing after public asset, durable trust,
runtime, and rollback evidence agree.

## Rationale

Release trust answers “are these the exact publicly published bytes?” Owner
succession answers “which repository may now generate canonical routing?”
Keeping them separate allows production-grade evidence to exist before the
atomic switch without letting a tag, attestation, registry record, or green
consumer become implicit authority.

## Consequences

- `v0.7.0` can carry an exact SDK routing release-candidate archive and public
  attestation without claiming G5.
- The release candidate has its own lifecycle, provenance schema, installed
  wheel probe, stronger-owner policy profile, and release workflow.
- Normal runtime remains fail-closed until the later owner-switch change.
- The final G5 landing can refer to immutable public evidence instead of
  creating trust and authority in one action.
- `aoa-routing` remains canonical and rollback-capable through this stage.

## Source Surfaces

- `src/aoa_sdk/control_plane/routing/release_candidate.py`
- `sdk/distribution/manifests/routing_g5_release_candidate.input-lock.json`
- `mechanics/boundary-bridge/parts/consumed-surface-posture-gate/docs/routing-succession-g5-release-candidate.md`
- `mechanics/release-support/parts/release-audit-publish-helper/scripts/build_routing_g5_release_candidate.py`
- `.github/workflows/release-artifacts.yml`
- `scripts/release_check.py`

## Follow-Up Route

After the exact public release asset, GitHub attestation, stronger-owner
registry record, release-consumer allow verdict, normal-runtime deny verdict,
and rollback evidence agree, land a separate G5 switch across `aoa-sdk`,
`aoa-routing`, `abyss-machine`, and `abyss-stack`.

Do not mark the predecessor maintenance-only, start the compatibility window,
or authorize archive execution from this decision.

## Verification

Run decision-index generation, the focused release-candidate tests, the clean
installed-wheel release-candidate probe, mechanics and SDK source-home
validators, the full release check, and the exact stronger-owner verifier
against the built release envelope.
