# Release Support Roadmap

Release Support is the SDK route for preparing, checking, and explaining
release-facing transitions. It can support audit, CI posture, build checks,
publication helpers, public-support posture, and sibling canaries; it cannot
claim publication state before external proof exists.

## Current Contour

- Keep release audit and publish helper behavior, public support CI posture,
  build validation, changelog support, and sibling canary support routed through
  active `parts/`.
- Keep README, changelog, release docs, release-support parts, generated
  companions, and GitHub validation aligned without duplicating chronology.
- Keep sibling canaries drift-aware and explicit about what they do not prove.
- Keep audit and dry-run helpers below tags, GitHub Releases, package indexes,
  and owner release truth.

## Next Work

- Tighten public-claim checks only where supportable evidence exists.
- Keep release helpers explicit about rollback, return, external verification,
  and skipped proof.
- Route sibling release claims back to sibling evidence instead of making the
  SDK a release ledger.

## When Time Comes

- Add release-support parts when a repeated release operation needs a reviewable
  artifact and validator coverage.
- Widen publication helpers only after current release audit, CI, build, and
  verification posture remain stable.
- Add stronger closeout automation only after checkpoint, questbook, release
  support, and owner evidence repeat cleanly.

## Out Of Scope

- GitHub tag or release truth before it exists.
- Package publication truth before external verification.
- Sibling release ownership.
- Release history outside `CHANGELOG.md`.
- Treating dry-run output as publication.
