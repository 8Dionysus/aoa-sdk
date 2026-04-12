# Codex Deploy Operation Boundary Note

`aoa-sdk` may surface typed references related to Codex-plane rollout operations.

It does not own:

- rollout success authority
- trust decisions
- rollback decisions
- deployment history truth

Acceptable seam:

- consume source-owned rollout campaign refs
- consume source-owned campaign cadence refs such as `campaign_ref`,
  `review_ref`, and `rollback_ref`
- consume deploy-receipt refs
- surface deploy-status snapshots
- pass through doctor, smoke, drift, or rollback packet refs when stronger
  source surfaces already define them

Unacceptable seam:

- declaring a rollout stabilized by sdk-local state alone
- declaring campaign review, reanchor, or rollback closure by sdk-local state
- treating typed helper output as stronger than checked-in rollout history
- minting rollout campaign truth inside `aoa-sdk`
