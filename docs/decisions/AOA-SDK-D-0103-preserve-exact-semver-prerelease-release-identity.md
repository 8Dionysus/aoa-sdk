# Preserve Exact SemVer Prerelease Release Identity

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0103
- Original date: 2026-08-22
- Surface classes: compatibility/validation/workflow
- SDK facets: release-support
- Mechanic parents: release-support
- Guard families: release audit/publish, SemVer identity
- Posture: accepted

## Context

The shared release contour parsed only stable `X.Y.Z` changelog headings. That
rejected the approved Dionysus prerelease `0.4.0-alpha.1` before the owner
release route could perform its nonmutating preflight and dry-run checks. The
same narrow version consumer would also discard a prerelease suffix if it were
present in the SDK CLI surface.

## Options Considered

- Alias the prerelease to a stable `0.4.0` version.
- Loosen the parser to arbitrary digit-and-dot strings.
- Parse strict SemVer 2.0.0 and carry the exact identity through audit,
  publish, and postpublish checks.

## Decision

Use one strict SemVer 2.0.0 matcher for release headings and the SDK CLI
version surface. Derive the tag as `v` plus the exact parsed version. Pass the
GitHub `--prerelease` flag only when the parsed version has a prerelease
component, and require postpublish GitHub tag and prerelease state to match
that exact version. Stable versions keep their existing behavior.

## Rationale

This admits approved prereleases without weakening stable validation or
inventing a second version identity. It keeps changelog, tag, CLI, and GitHub
Release state reconciled at the owner helper boundary while leaving actual
publication authority with GitHub and the sibling owner repository.

## Consequences

- The shared audit and dry-run route can prove `0.4.0-alpha.1` without
  creating a tag or Release.
- Malformed SemVer and prerelease/stable identity drift remain fail-closed.
- Future prerelease publication remains an explicit owner-authorized action;
  this decision does not publish or tag any repository.

## Source Surfaces

- `src/aoa_sdk/release/api.py`
- `mechanics/release-support/parts/release-audit-publish-helper/tests/test_release_audit_publish_helper.py`
- `docs/RELEASING.md`
- `mechanics/release-support/parts/release-audit-publish-helper/docs/release-runbook.md`

## Follow-Up Route

Keep future release identity changes in the SDK release-support owner surface;
the Dionysus owner and GitHub remain authoritative for publication, tag, and
Release state.

## Verification

Run the focused release-support tests, `scripts/release_check.py`, the
decision-index check, and the nested-AGENTS validator before landing.
