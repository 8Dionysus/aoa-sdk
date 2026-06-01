# Release Support Parts

## Candidate Parts

| Part | Current surfaces | Future payload condition |
| --- | --- | --- |
| release-audit-publish-helper | `mechanics/release-support/parts/release-audit-publish-helper/`, `src/aoa_sdk/release/`, `scripts/release_check.py`, `.github/workflows/release-artifacts.yml`, `.github/workflows/release-cadence-audit.yml` | active; verifies and publishes release surfaces without inventing release state |
| public-support-ci-posture | `mechanics/release-support/parts/public-support-ci-posture/`, `docs/RELEASE_CI_POSTURE.md`, `.github/workflows/` | active; keeps support, release semantics, sibling-canary drift detection, and CI tiers short and checkable |
