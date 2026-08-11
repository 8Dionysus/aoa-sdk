# Release Support Parts

## Candidate Parts

| Part | Current surfaces | Future payload condition |
| --- | --- | --- |
| release-audit-publish-helper | `mechanics/release-support/parts/release-audit-publish-helper/`, `src/aoa_sdk/release/`, `scripts/release_check.py`, `sdk/distribution/manifests/`, `.github/workflows/release-artifacts.yml`, `.github/workflows/release-cadence-audit.yml` | active; verifies canonical SDK release surfaces and package trust while retaining older routing candidates as explicit immutable replay inputs |
| public-support-ci-posture | `mechanics/release-support/parts/public-support-ci-posture/`, `docs/RELEASE_CI_POSTURE.md`, `.github/workflows/` | active; keeps support, release semantics, sibling-canary drift detection, and CI tiers short and checkable |
| validation-evidence-graph | `mechanics/release-support/parts/validation-evidence-graph/`, `scripts/release_check.py`, `.github/workflows/repo-validation.yml`, `evals/suites/aoa-validation-evidence-graph.suite.md` | active pilot; preserves the full owner battery while comparing dependency-aware scheduling, static sharding, shadow routing, and exact receipt boundaries |
