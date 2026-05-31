# Release Support Mechanic

Status: skeleton.

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
- `.github/workflows/repo-validation.yml`
- `scripts/release_check.py`
- `src/aoa_sdk/release/`
- `tests/test_release.py`
- `tests/test_roadmap_parity.py`

### Candidate parts

- changelog
- release-audit
- ci-posture
- package-build
- publication

### Must not claim

This mechanic must not treat a dry run, changelog entry, or release audit as a
published GitHub Release or package upload.

### Validation

```bash
python scripts/release_check.py
python -m pytest -q tests/test_release.py tests/test_roadmap_parity.py
```

### Next route

Actual publication routes through the repository release protocol, GitHub
checks, tag, and release verification.
