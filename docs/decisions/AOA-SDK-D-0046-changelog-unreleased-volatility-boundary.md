# Changelog Unreleased Volatility Boundary

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0046
- Original date: 2026-06-02
- Surface classes: docs, release, route-law, validation
- SDK facets: changelog, release posture, root docs
- Mechanic parents: release-support
- Guard families: changelog drift, release readiness, docs routes
- Posture: accepted

## Context

The root `CHANGELOG.md` carried live reconciliation details in `Unreleased`:
first-parent commit totals, changed-path totals, PR ranges, and GitHub check
handles. Those values drift after every landing. They made the changelog look
release-ready while its measured claims were already stale.

The refactored sibling repositories keep a cleaner split. `Unreleased` records
durable route and behavior changes. Exact reconciliation spans are rebuilt
during release prep and written into the dated release section, where the
comparison window is fixed.

## Options Considered

- Keep updating live totals after every landing.
- Remove all reconciliation language from the changelog.
- Keep `Unreleased` as a durable change contour and reserve exact span counts
  for dated release sections.

## Decision

`Unreleased` must not carry live first-parent commit totals, changed-path
totals, merged-PR ranges, PR numbers, or remote check handles.

Those details belong in a dated release section created during release prep,
after the comparison window is fixed. Release prep should reconstruct the
span from git history, merged PR metadata, decision records, route cards,
compatibility policy, workspace fixtures, and the release gate.

## Rationale

Live counters are true only until the next landing. Keeping them in
`Unreleased` creates guaranteed drift and trains tests to preserve stale
claims. A dated release section can own exact reconciliation because the
release window is closed.

The changelog still needs to help future agents understand what changed. It
does that by listing stable route, owner, validation, and behavior changes
without pretending the moving branch has a fixed release span.

## Consequences

- `Unreleased` remains readable and does not require a count refresh after
  every PR.
- Release prep still records exact reconciliation details, but only once the
  release window is closed.
- `tests/test_docs_routes.py` rejects live counters and PR/check handles in
  `Unreleased`.
- GitHub validation evidence stays in PR metadata until a dated release
  section names the final release validation.

## Source Surfaces

- `CHANGELOG.md`
- `ROADMAP.md`
- `tests/test_docs_routes.py`
- `mechanics/release-support/parts/public-support-ci-posture/tests/test_public_support_ci_posture.py`

## Follow-Up Route

Future release-prep work should create or update the dated release section
with the exact span and final validation evidence. Ordinary post-release
landings should update `Unreleased` only with stable change descriptions.

## Verification

The executable decision-index and owning-surface checks are routed through
`docs/decisions/AGENTS.md` and the nearest source-owner validation surface.
