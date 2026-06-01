# Owner Rollout Reference Handoff Contract

## Contract

This part may surface typed references for source-owned rollout campaign
cadence. It must keep the route back to the source owner explicit.

## Allowed Carried Refs

- `campaign_ref`
- `review_ref`
- `rollback_ref`
- deploy receipt refs
- doctor, smoke, drift, and rollback packet refs when stronger source surfaces
  already define them

## Stop-Lines

- Do not decide campaign truth inside `aoa-sdk`.
- Do not declare reanchor or rollback follow-through complete from SDK-local
  state.
- Do not treat typed helper output as stronger than source-owned cadence
  windows.
