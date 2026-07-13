# Distribution

`sdk/distribution/` owns SDK route posture for package shape, release flow,
and public support claims.

## Families

| Family | Role | Next route |
| --- | --- | --- |
| `package-contract/` | package metadata and build posture | `pyproject.toml`, `src/aoa_sdk/`, build checks |
| `manifests/` | OS Abyss artifact bundle manifests for built package outputs | package build owner and `mechanics/release-support/parts/release-audit-publish-helper/` |
| `release-posture/` | release audit and publication helper posture | `CHANGELOG.md`, `docs/RELEASING.md`, release-support mechanics |
| `public-support/` | support and CI tier posture | `docs/RELEASE_CI_POSTURE.md`, CI workflows |

## Stop Lines

- Build success is not package publication.
- Generated artifact sidecars prove built package subjects; they do not prove
  external package-index or GitHub Release publication.
- Dry-run release output is not a GitHub Release.
- Support claims must stay tied to tested public surfaces.
