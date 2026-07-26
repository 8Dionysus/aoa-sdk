# Replay Release Evidence From an Immutable Tag

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0073
- Original date: 2026-07-25
- Surface classes: release trust, recovery, provenance, CI, immutable tags
- SDK facets: distribution, control-plane
- Mechanic parents: release-support
- Guard families: release provenance, artifact trust, rollback
- Posture: accepted

## Context

The `v0.7.0` source, package, and full-corpus routing candidate built
successfully in the original tag workflow, but the exact stronger-owner
package exposed an integration defect before attestation: its setuptools
console entry point called `main()` without the required `argv`, while the
module entry point remained valid. The public tag and GitHub Release already
existed, but no routing archive or attestation had been published.

Moving the tag to a workflow repair commit would change the release source.
Recreating the tag would weaken the immutable release boundary. Building from
newer `main` would produce a different SDK source ref even if the operational
repair did not change routing behavior.

## Options Considered

- Move or recreate the existing release tag on a workflow repair commit.
- Publish locally built bytes without the required GitHub OIDC attestation.
- Land a reviewed workflow repair, then replay evidence from the exact
  immutable tag while keeping the workflow revision independently visible.

## Decision

Keep an explicit `workflow_dispatch.release_tag` recovery route in Release
Artifacts.

When `release_tag` is supplied, the workflow must:

- accept only an exact semantic-version tag name that exists on the remote;
- check out that tag as the repository source used for tests, package build,
  and release subject construction;
- check out the same tag as the nested `aoa-sdk` producer input;
- retain every sibling and stronger-owner exact ref from the release input
  lock;
- check out the reviewed replay workflow revision separately when a newer
  orchestration or canonical carrier repair is required;
- invoke the exact stronger-owner verifier through its valid Python module
  entry point;
- use only the immutable tag's subject bytes and input lock while the reviewed
  replay tooling byte-checks every subject, rebuilds the deterministic
  archive, attests it through GitHub OIDC, and uploads evidence under the
  original tag name.

The workflow revision that performs the replay may be newer than the release
tag. GitHub attestation provenance exposes that workflow revision separately;
it does not become the artifact source ref.

## Consequences

- A CI integration repair no longer requires mutable tags or a replacement
  release version merely to recover missing evidence.
- The release source remains the public tag commit, while orchestration
  provenance remains independently inspectable.
- A carrier or orchestration repair can be newer than the tag without
  substituting SDK source, producer inputs, or release subject bytes.
- Manual workflow dispatch without `release_tag` keeps its ordinary package
  validation behavior and does not enter the public routing release path.
- Evidence replay remains weaker than G5 and cannot change canonical owner,
  runtime, compatibility-window, predecessor, consumer-zero, or archive
  authority.

## Source Surfaces

- `.github/workflows/release-artifacts.yml`
- `src/aoa_sdk/control_plane/routing/release_candidate.py`
- `mechanics/release-support/parts/release-audit-publish-helper/docs/release-runbook.md`
- `mechanics/release-support/parts/release-audit-publish-helper/tests/test_release_audit_publish_helper.py`

## Follow-Up Route

Repair the stronger-owner console entry point in its own repository route.
Keep the SDK verifier pin unchanged for this immutable release because its
module implementation and policy profile are the exact reviewed verifier.

## Verification

Run decision-index generation, workflow syntax parsing, the release-helper
workflow contract test, the full SDK release check, and one dispatch against
the existing tag. Confirm that the replayed archive digest matches an
independent clean build from the same tag and that GitHub attestation
verification succeeds.
