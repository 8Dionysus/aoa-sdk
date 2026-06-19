# Release Support Provenance

## Source Surfaces

- `CHANGELOG.md`
- `docs/RELEASING.md`
- `docs/RELEASE_CI_POSTURE.md`
- `mechanics/release-support/parts/release-audit-publish-helper/`
- `mechanics/release-support/parts/public-support-ci-posture/`
- `.github/workflows/repo-validation.yml`
- `.github/workflows/latest-sibling-canary.yml`
- `.github/workflows/release-artifacts.yml`
- `.github/workflows/release-cadence-audit.yml`
- `scripts/release_check.py`
- `sdk/distribution/manifests/python_distribution.bundle.json`
- `mechanics/release-support/parts/release-audit-publish-helper/scripts/validate_abyss_machine_package_artifact_bundle.py`
- `src/aoa_sdk/release/`
- `mechanics/release-support/parts/release-audit-publish-helper/tests/test_release_audit_publish_helper.py`
- `mechanics/release-support/parts/public-support-ci-posture/tests/test_public_support_ci_posture.py`
- `mechanics/release-support/parts/public-support-ci-posture/tests/test_sibling_canary.py`

## Stronger Owners

GitHub, package publication targets, and sibling repositories own actual
publication state. SDK release support owns checks and dry-run helpers.

## Notes

This shared mechanic name matches the refactored AoA release-support package
pattern while keeping publication truth external until verified.

Detailed release runbook and support/CI posture moved into release-support
parts. Root `docs/RELEASING.md` and `docs/RELEASE_CI_POSTURE.md` remain
repo-level public route doors, not compatibility fallbacks. Former root payload
and `tests/test_release.py` are accounted for in this package provenance,
active part route cards, and `mechanics/topology.json`.

Former root roadmap parity regression `tests/test_roadmap_parity.py` moved
into `mechanics/release-support/parts/public-support-ci-posture/`; the old root
name is provenance only, not an active route.

Former root sibling-canary script, matrix, and regression moved into
`mechanics/release-support/parts/public-support-ci-posture/`; the old
`scripts/` and root `tests/` paths are provenance only.

OS Abyss package artifact bundle validation is part-local to
`release-audit-publish-helper`; root `scripts/release_check.py` only
orchestrates it after `python -m build`.
