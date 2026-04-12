# Codex Deploy Operation Boundary Note

`aoa-sdk` may surface typed references related to Codex-plane rollout operations.

It does not own:

- rollout success authority
- trust decisions
- rollback decisions
- deployment history truth

Acceptable seam:

- consume source-owned rollout campaign refs
- consume deploy-receipt refs
- surface deploy-status snapshots
- pass through doctor, smoke, drift, or rollback packet refs when stronger
  source surfaces already define them

Unacceptable seam:

- declaring a rollout stabilized by sdk-local state alone
- treating typed helper output as stronger than checked-in rollout history
- minting rollout campaign truth inside `aoa-sdk`
