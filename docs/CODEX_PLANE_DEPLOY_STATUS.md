# Codex Plane Deploy Status

`aoa-sdk` owns the typed live read over deploy-local Codex-plane rollout
artifacts.

It does not own rollout authority.

## Inputs

Read from the live workspace root:

- `/.codex/generated/rollout/codex_plane_trust_state.current.json`
- `/.codex/generated/rollout/codex_plane_regeneration_report.latest.json`
- `/.codex/generated/rollout/codex_plane_rollout_receipt.latest.json`

These artifacts are deploy-local runtime evidence. They are not source-owned
surfaces inside `aoa-sdk`.

## Output

Expose one bounded status snapshot with:

- `trust_posture`
- `rollout_state`
- `project_config_active`
- `hooks_active`
- `active_mcp_servers`
- `drift_detected`
- `next_action`

The snapshot is for control-plane orientation and review. It is not a
permission surface and it does not overrule the live trust-state or rollout
receipt that it reads.

For checked-in rollout campaign history, drift windows, rollback windows, and
other typed pass-through refs that remain source-owned, see
`docs/CODEX_DEPLOY_OPERATION_BOUNDARY_NOTE.md` and
`docs/codex_rollout_campaign_refs.md`.

## Next-action posture

The typed reader keeps the next move small and explicit:

- `none` when the latest rollout is already verified and trusted
- `run_doctor` when apply finished but doctor or verify still needs a fresh pass
- `rerender` when the trust posture shows root or config mismatch before a
  trustworthy rollout exists
- `rerollout` when render succeeded but rollout is still only partial or drifted
- `rollback` when the live trust posture or doctor outcome makes rollback the
  honest next move
