# Release Audit Publish Helper Contract

## Allowed Outputs

- Release audit reports.
- Dry-run and confirm publish reports.
- Changelog-derived GitHub Release bodies.
- Preflight and postpublish checks over existing release surfaces.
- GitHub-native release artifact and cadence audit workflow contracts.
- Exact routing G5 release-candidate archives, checksums, and verification
  handoff metadata with every owner-switch authority flag false and every
  manifest subject byte-resolved by the stronger owner. The gzip carrier must
  be reproducible across zlib versions, not merely within one runner.

## Repo-local verifier discovery

Preflight accepts the first existing executable-owner surface in this order:

1. `scripts/release_check.py`
2. `scripts/release_gate/release_check.py`

The family-scoped path supports repositories whose script-topology contract
forbids root-level Python commands. Both routes remain repo-owned and must pass
without leaving tracked drift.

## Stop-Lines

- Do not invent versions, changelog prose, tags, or release notes.
- Do not treat dry runs as publication.
- Do not move or recreate an existing release tag to repair failed release
  evidence; replay from the exact tag through a reviewed workflow revision.
- Do not substitute newer SDK source while using newer reviewed orchestration
  or archive tooling to replay evidence from an immutable tag.
- Do not claim sibling releases happened until their owner repos, tags, and
  GitHub Releases verify.
- Do not bypass protected branch, CI, or package publication checks.
- Do not treat a release-candidate archive, checksum, attestation, or public
  trust record as the G5 owner-switch receipt or normal runtime admission.
- Preserve the exact strict SemVer heading and derived tag identity, including
  prerelease components; never alias a prerelease to a stable version.
- Keep GitHub's `latest` pointer on a stable Release; a prerelease may be
  published and audited without becoming latest.

## Owner Split

The SDK owns helper behavior and route readability. GitHub, package indexes,
and sibling repositories own actual release state and release authority.
