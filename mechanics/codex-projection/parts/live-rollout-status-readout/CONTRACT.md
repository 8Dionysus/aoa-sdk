# Live Rollout Status Readout Contract

## Contract

The part reads three deploy-local rollout evidence files from the live
workspace root and emits one SDK-owned status snapshot.

## SDK-Owned Active Names

- part route: `codex-projection/live-rollout-status-readout`
- model: `CodexProjectionLiveRolloutStatusSnapshot`
- schema: `schemas/live-rollout-status-snapshot.schema.json`
- example: `examples/live-rollout-status-snapshot.example.json`

## External Compatibility Inputs

The following filenames are external 8Dionysus rollout artifact tokens. They
remain readable inputs for compatibility and provenance; they are not active
SDK route names:

- `codex_plane_trust_state.current.json`
- `codex_plane_regeneration_report.latest.json`
- `codex_plane_rollout_receipt.latest.json`
- source refs under `8Dionysus:config/codex_plane/...`

## Stop-Lines

- Do not mint rollout success, trust, rollback, or campaign truth inside
  `aoa-sdk`.
- Do not rename external rollout artifacts from this SDK part.
- Do not keep SDK-owned schema, example, docs, or tests in root technical
  districts when the part-local path is the active home.
