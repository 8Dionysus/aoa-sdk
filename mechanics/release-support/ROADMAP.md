# Release Support Roadmap

This roadmap owns future pressure for the SDK Release Support mechanic.

## Current Contour

Release Support owns changelog, release audit, CI posture, build validation,
publication helper behavior, public support posture, and sibling canary
support. It helps prepare and verify releases without claiming publication
state before external proof exists.

## Next Work

- Keep README, changelog, release docs, release-support parts, generated
  companions, and GitHub validation aligned.
- Keep sibling canaries drift-aware and explicit about what they do not prove.
- Keep audit and dry-run helpers below tag, GitHub Release, and package index
  truth.

## When Time Comes

- Add release-support parts only when a repeated release operation needs a
  reviewable artifact and validator coverage.
- Widen publication helpers only after current release audit, CI, build, and
  verification posture remain stable.

## Out Of Scope

- GitHub tag or release truth before it exists;
- package publication truth before external verification;
- sibling release ownership;
- release history outside `CHANGELOG.md`.

## Update Trigger

Update this roadmap when release-support helper scope, public support posture,
CI posture, sibling canary meaning, or future publication support changes.
