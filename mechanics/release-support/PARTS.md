# Release Support Parts

## Candidate Parts

| Part | Current surfaces | Future payload condition |
| --- | --- | --- |
| changelog | `CHANGELOG.md` | only if changelog sections become generated read models |
| release-audit | `src/aoa_sdk/release/`, release tests | only if audit packets need schema examples |
| ci-posture | `.github/workflows/`, `docs/RELEASE_CI_POSTURE.md` | only if CI posture gets package-local checks |
| package-build | `pyproject.toml`, `python -m build` | only if build metadata needs contract tests |
| publication | `docs/RELEASING.md`, release publish helper | only if publication dry-runs need stable fixtures |
