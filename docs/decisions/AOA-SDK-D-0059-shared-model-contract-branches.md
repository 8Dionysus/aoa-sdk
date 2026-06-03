# Shared Model Contract Branches

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0059
- Original date: 2026-06-03
- Surface classes: source-topology, models, implementation, validation
- SDK facets: importable implementation, typed contracts, compatibility re-export
- Mechanic parents: boundary-bridge, checkpoint, recurrence, runtime-seam
- Guard families: source topology, public import compatibility, typed contract routing
- Posture: accepted

## Context

`src/aoa_sdk/models.py` had become a shared typed-contract monolith. It carried
routing hints, compatibility rules, skills, playbooks, memo, evals,
techniques, agents, KAG, governed runs, stats, project-core skill surfaces,
workspace bootstrap reports, surface detection, checkpoint/session-growth
contracts, Codex projection status, and reviewed closeout runner reports.

That file was useful as a stable import surface, but it was no longer a good
place to add new contracts. A future contract change needed a route owner
before it reached the compatibility import layer.

## Options Considered

- Keep `models.py` as the single typed-contract module.
- Split only the largest class cluster.
- Move models into the behavior packages that use them.
- Keep `models.py` as a compatibility re-export and split typed contracts by
  SDK route family.

## Decision

Keep `src/aoa_sdk/models.py` as the public compatibility re-export surface.

Move shared model definitions into `src/aoa_sdk/contracts/`:

- `routing.py` owns routing hints, stats regrounding hints, registry entries,
  and surface compatibility contracts.
- `skills.py` owns skill card, disclosure, activation, session, dispatch, and
  detection contracts.
- `playbooks.py` owns playbook registry, activation, composition, review, and
  landing-governance contracts.
- `memo.py` owns memo surfaces, capsules, section bundles, and writeback
  contracts.
- `evals.py` owns eval cards, capsules, sections, comparisons, and runtime
  candidate intake contracts.
- `techniques.py` owns technique promotion readiness contracts.
- `agents.py` owns agent phase binding and artifact envelope contracts.
- `kag.py` owns KAG registry, federation, tiny bundle, regrounding, inspect,
  and query-mode contracts.
- `governed_runs.py` owns governed run review packet, audit, and handoff
  contracts.
- `stats.py` owns stats summary, source coverage, route progression,
  automation pipeline, and regrounding signal contracts.
- `project_core.py` owns project-core kernel, outer ring, risk ring, and
  foundation profile contracts.
- `workspace.py` owns workspace bootstrap report contracts.
- `checkpoints.py` owns checkpoint lineage, checkpoint notes, checkpoint
  capture/review/hook/boundary, and checkpoint-closeout bridge contracts.
- `surfaces.py` owns surface opportunity, surface detection, and reviewed
  surface closeout handoff contracts.
- `codex.py` owns Codex projection live rollout status contracts.
- `closeout.py` owns reviewed closeout runner, publisher, stats refresh,
  owner follow-through, and inbox/status report contracts.

## Rationale

The split keeps the high-value public import path stable while giving future
contracts a route owner. It avoids turning behavior packages into import-cycle
traps and avoids forcing every caller to migrate at once.

`models.py` is now a compatibility layer, not the place where new model
families should be authored.

## Consequences

- Existing `from aoa_sdk.models import ...` imports remain stable.
- New shared contracts should land in `contracts/<route>.py`.
- `models.py` should only re-export, not define new contract families.
- Source topology now points agents toward the contract branch that owns the
  packet family.

## Source Surfaces

- `src/aoa_sdk/models.py`
- `src/aoa_sdk/contracts/`
- `src/aoa_sdk/cli/`
- `src/aoa_sdk/checkpoints/`
- `src/aoa_sdk/closeout/`
- `src/aoa_sdk/recurrence/`
- `src/aoa_sdk/surfaces/`
- `mechanics/topology.json`
- `generated/source_topology.min.json`
- `tests/test_mechanics_topology.py`
- `tests/test_source_topology_index.py`

## Follow-Up Route

Do not add new class families directly to `models.py`. Add them to the owning
`contracts/*` route and re-export them from `models.py` only when public import
compatibility is needed.

## Verification

```bash
python -m ruff check src/aoa_sdk
python -m mypy src/aoa_sdk
python -m pytest -q mechanics/boundary-bridge/parts/owner-layer-signal-handoff/tests/test_owner_layer_signal_handoff.py mechanics/boundary-bridge/parts/owner-layer-signal-handoff/tests/test_owner_layer_signal_handoff_cli.py mechanics/boundary-bridge/parts/skill-runtime-bridge/tests/test_skill_reference_contracts.py mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_session_growth_checkpoint_cycle_api.py mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_session_growth_checkpoint_cycle_cli.py mechanics/checkpoint/parts/reviewed-session-handoff-runner/tests/test_reviewed_session_handoff_runner.py mechanics/recurrence/parts/downstream-projection-guard/tests/test_recurrence_downstream_projection_seed.py mechanics/recurrence/parts/live-observation-producers/tests/test_recurrence_live_observation_seed.py
python scripts/build_source_topology_index.py --check
python scripts/validate_source_topology_index.py
python -m pytest -q tests/test_source_topology_index.py
python scripts/release_check.py
```
