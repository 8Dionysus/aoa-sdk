# Release Support Part Localization

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0018
- Original date: 2026-06-01
- Surface classes: topology, mechanics, artifact placement, validation guard
- SDK facets: mechanics topology, release support, release audit, public support posture
- Mechanic parents: release-support
- Guard families: mechanics topology, part validation, docs routes, active naming, release check
- Posture: accepted

## Context

After the Boundary Bridge skill-runtime slice, Release Support still carried
detailed release payload in root districts:

- detailed release runbook content under `docs/RELEASING.md`
- detailed public support and CI posture under `docs/RELEASE_CI_POSTURE.md`
- release audit/publish helper tests under `tests/test_release.py`

Root `docs/RELEASING.md` remains a federation preflight door, so deleting or
fully removing that route would break the repo-level release contract. The
right move is to keep the root route thin and put detailed release-support
payload in functioning parts.

## Decision

Localize detailed release-support payload into:

- `mechanics/release-support/parts/release-audit-publish-helper/`
- `mechanics/release-support/parts/public-support-ci-posture/`

Keep `docs/RELEASING.md` as the repo-level release preflight route door and
`docs/RELEASE_CI_POSTURE.md` as the short public route door. Keep
`scripts/release_check.py` as the root repo-wide release gate and keep
`src/aoa_sdk/release/` as importable SDK source.

## Rationale

The detailed runbook and posture docs are mechanic-owned payload because they
describe repeatable release support operations, stop-lines, owner split, and
validation. The root docs are still legitimate active surfaces, but only as
public route doors required by release audit and quick onboarding.

This keeps active naming explicit:

- `release-audit-publish-helper`: verifies and publishes existing release
  surfaces without inventing release truth
- `public-support-ci-posture`: names support claims, release semantics, and CI
  tiers without becoming product support or publication truth

## Consequences

- Root release docs remain active route doors, not legacy fallbacks.
- Detailed release-support docs and release API tests now live in part-local
  homes.
- `scripts/release_check.py` remains root-owned as a repo-wide validation gate.
- GitHub-native release workflows remain under `.github/workflows/`, but their
  owning mechanics route is release-support.
- GitHub tags/releases, package publication, and sibling releases remain
  outside SDK truth until verified.

## Source Surfaces

- `mechanics/release-support/README.md`
- `mechanics/release-support/PARTS.md`
- `mechanics/release-support/PROVENANCE.md`
- `mechanics/release-support/parts/release-audit-publish-helper/`
- `mechanics/release-support/parts/public-support-ci-posture/`
- `docs/RELEASING.md`
- `docs/RELEASE_CI_POSTURE.md`
- `.github/workflows/repo-validation.yml`
- `.github/workflows/release-artifacts.yml`
- `.github/workflows/release-cadence-audit.yml`
- `mechanics/ARTIFACT_TOPOLOGY.md`
- `mechanics/topology.json`
- `README.md`
- `ROADMAP.md`

## Follow-Up Route

Continue root technical district audit for Checkpoint test placement, Questbook
payload, and cross-mechanic public contracts.

## Verification

The executable decision-index and owning-surface checks are routed through
`docs/decisions/AGENTS.md` and the nearest source-owner validation surface.
