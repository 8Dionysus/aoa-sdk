# Release Audit Publish Helper Contract

## Allowed Outputs

- Release audit reports.
- Dry-run and confirm publish reports.
- Changelog-derived GitHub Release bodies.
- Preflight and postpublish checks over existing release surfaces.
- GitHub-native release artifact and cadence audit workflow contracts.

## Stop-Lines

- Do not invent versions, changelog prose, tags, or release notes.
- Do not treat dry runs as publication.
- Do not claim sibling releases happened until their owner repos, tags, and
  GitHub Releases verify.
- Do not bypass protected branch, CI, or package publication checks.

## Owner Split

The SDK owns helper behavior and route readability. GitHub, package indexes,
and sibling repositories own actual release state and release authority.
