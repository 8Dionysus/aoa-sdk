# Release Support Mechanic

Status: active topology with part-local payload.

## Mechanic Card

### Operation

Keep changelog, release audit, CI posture, build, and publication helper
surfaces bounded and reproducible.

### Trigger

Use this mechanic when `CHANGELOG.md`, release docs, CI workflows, release API,
release checks, package build behavior, or publication helper behavior changes.

### SDK owns

- human changelog contour for SDK releases
- release audit and dry-run publish helper behavior
- release CI posture docs
- release check orchestration
- package build validation

### Stronger owner split

GitHub tags/releases, package index publication, and sibling releases remain
outside SDK helper truth until actually performed.

### Current source surfaces

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
- `src/aoa_sdk/release/`
- `mechanics/release-support/parts/release-audit-publish-helper/tests/test_release_audit_publish_helper.py`
- `mechanics/release-support/parts/public-support-ci-posture/tests/test_public_support_ci_posture.py`
- `mechanics/release-support/parts/public-support-ci-posture/tests/test_sibling_canary.py`

### Candidate parts

- release-audit-publish-helper
- public-support-ci-posture

### Must not claim

This mechanic must not treat a dry run, changelog entry, or release audit as a
published GitHub Release or package upload.

### Validation

Use the touched part `VALIDATION.md` for executable checks. For package-wide
route changes, use `mechanics/topology.json` for the active validation list
and then run the mechanics topology gate from the root route card. Release
publication still follows the repository release route.

### Next route

Actual publication routes through the repository release protocol, GitHub
checks, tag, and release verification.
