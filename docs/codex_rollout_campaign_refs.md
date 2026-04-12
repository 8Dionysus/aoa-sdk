# Codex Rollout Campaign Refs

`aoa-sdk` may surface typed pass-through refs for the shared-root Codex rollout
campaign cadence.

The narrow seam is:

- `campaign_ref`
- `review_ref`
- `rollback_ref`

These refs stay source-owned in `8Dionysus` cadence windows and may also appear
in weaker derived `aoa-stats` summaries.

## Acceptable seam

- carry the refs for orientation and handoff
- pass them through alongside deploy-status snapshots or stronger source refs
- keep the route back to `8Dionysus` explicit

## Unacceptable seam

- deciding campaign truth inside `aoa-sdk`
- declaring reanchor complete from sdk-local state
- declaring rollback follow-through closed from sdk-local state
- treating typed helper output as stronger than source-owned cadence windows
