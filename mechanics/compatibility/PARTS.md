# Compatibility Parts

## Candidate Parts

| Part | Current surfaces | Future payload condition |
| --- | --- | --- |
| canonical-path-policy | `src/aoa_sdk/compatibility/policy.py`, `docs/boundaries.md` | only if compatibility policy becomes large enough to split by owner |
| sibling-canary | `scripts/sibling_canary_matrix.json`, `scripts/run_sibling_canary.py` | only with package-local canary fixtures |
| version-posture | `docs/versioning.md`, `docs/RELEASE_CI_POSTURE.md` | only if release claims need separate compatibility manifests |
