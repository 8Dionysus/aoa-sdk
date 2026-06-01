# Codex Projection Artifact Localization

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0008
- Original date: 2026-05-31
- Surface classes: topology, mechanics, artifact placement, validation guard
- SDK facets: mechanics topology, artifact localization, codex projection, root technical districts
- Mechanic parents: codex-projection
- Guard families: mechanics topology, nested agents, part validation, schema validation
- Posture: accepted

## Context

The first artifact-localization slice moved Agon recurrence-adapter payload into
a functioning part home. Codex Projection still had SDK-owned docs, schema,
example, and tests in root technical districts while active topology already
identified `codex-projection` as the owning parent.

Those root paths also carried historical plane wording in SDK-owned active
surface names. The external rollout artifacts still use 8Dionysus
`codex_plane_*` filenames, but those are compatibility inputs, not active SDK
route names.

## Decision

Move SDK-owned Codex Projection payload into part-local homes:

- `mechanics/codex-projection/parts/live-rollout-status-readout/`
- `mechanics/codex-projection/parts/portability-boundary/`
- `mechanics/codex-projection/parts/owner-rollout-reference-handoff/`

Rename the SDK-owned snapshot contract to
`CodexProjectionLiveRolloutStatusSnapshot` with schema version
`aoa_sdk_codex_projection_live_rollout_status_snapshot_v1`.

Former root paths and former parent names stay in
`mechanics/codex-projection/legacy/INDEX.md`.

## Rationale

The active route should tell an agent what the surface does:

- read live rollout evidence;
- emit a bounded status snapshot;
- preserve portability boundaries;
- hand off owner rollout refs without claiming rollout truth.

That is clearer than keeping SDK-owned docs and schemas under root paths whose
names imply a local Codex plane owner.

## Consequences

- Root `docs/`, `schemas/`, `examples/`, and `tests/` no longer own the Codex
  Projection live rollout status contract.
- External 8Dionysus rollout artifact names remain readable inputs and are
  documented in the part contract.
- `src/aoa_sdk/codex/` remains the importable SDK source surface.
- Tests and docs now route through the part-local paths.

## Source Surfaces

- `mechanics/codex-projection/parts/AGENTS.md`
- `mechanics/codex-projection/parts/README.md`
- `mechanics/codex-projection/parts/live-rollout-status-readout/README.md`
- `mechanics/codex-projection/parts/live-rollout-status-readout/CONTRACT.md`
- `mechanics/codex-projection/parts/live-rollout-status-readout/VALIDATION.md`
- `mechanics/codex-projection/parts/live-rollout-status-readout/docs/live-rollout-status-readout.md`
- `mechanics/codex-projection/parts/live-rollout-status-readout/schemas/live-rollout-status-snapshot.schema.json`
- `mechanics/codex-projection/parts/live-rollout-status-readout/examples/live-rollout-status-snapshot.example.json`
- `mechanics/codex-projection/parts/live-rollout-status-readout/tests/test_live_rollout_status_readout.py`
- `mechanics/codex-projection/parts/portability-boundary/docs/portability-boundary.md`
- `mechanics/codex-projection/parts/owner-rollout-reference-handoff/docs/deploy-operation-boundary-note.md`
- `mechanics/codex-projection/parts/owner-rollout-reference-handoff/docs/rollout-campaign-refs.md`
- `src/aoa_sdk/codex/registry.py`
- `src/aoa_sdk/models.py`
- `mechanics/codex-projection/legacy/INDEX.md`
- `mechanics/ARTIFACT_TOPOLOGY.md`

## Follow-Up Route

Continue auditing root technical districts for remaining single-mechanic-owned
payload. Recurrence examples and A2A fixtures with external `codex-plane`
component refs need separate owner/compat accounting before any rename.

## Verification

```bash
python scripts/generate_decision_indexes.py --check
python scripts/validate_mechanics_topology.py
python -m pytest -q mechanics/codex-projection/parts/live-rollout-status-readout/tests/test_live_rollout_status_readout.py mechanics/codex-projection/parts/workspace-mcp-server/tests/test_workspace_mcp_server.py tests/test_docs_routes.py mechanics/release-support/parts/public-support-ci-posture/tests/test_public_support_ci_posture.py
```
