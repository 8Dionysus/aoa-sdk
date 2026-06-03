# Checkpoint Route-Role Implementation Branches

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0052
- Original date: 2026-06-03
- Surface classes: source-topology, checkpoint, implementation, validation
- SDK facets: importable implementation, checkpoint control-plane, route-role branches
- Mechanic parents: checkpoint
- Guard families: source topology, checkpoint route roles, session-growth state
- Posture: accepted

## Context

`src/aoa_sdk/checkpoints/registry.py` had stopped being only the public
checkpoint facade. It also owned runtime-session lookup, managed Git hook
templates, reviewed promotion target writers, checkpoint note rendering,
after-commit review helpers, ledger assembly, and reviewed closeout bridge
helpers.

The generated source-topology index made the pressure measurable: checkpoint
registry was the largest SDK implementation module and carried high split
pressure. The path-topology cut proved the safe direction, but leaving the
remaining helper families in the facade would keep agents entering a broad
monolith.

## Options Considered

- Keep `registry.py` as the single checkpoint implementation module.
- Split by file size only.
- Move the public `CheckpointsAPI` into a new package.
- Keep `CheckpointsAPI` stable and split implementation helpers by route role.

## Decision

Keep `src/aoa_sdk/checkpoints/registry.py` as the public `CheckpointsAPI`
facade and route-role orchestrator.

Move implementation helper families into named checkpoint branches:

- `topology/paths.py` owns filesystem path naming.
- `runtime/sessions.py` owns runtime-session lookup and probing.
- `hooks/git_boundary.py` owns managed Git hook templates, git metadata, and
  dirty-boundary checks.
- `promotion/targets.py` owns reviewed promotion target writers.
- `render/markdown.py` owns checkpoint note markdown rendering.
- `review/after_commit.py` owns after-commit reports and auto-observations.
- `review/agent_review.py` owns review-note autofill and semantic review carry.
- `ledger/notes.py` owns checkpoint note assembly, rotation, runtime note
  loading, and session-end derivation.
- `closeout/bridge.py` owns reviewed closeout context, evidence, receipt,
  progression, quest, and owner-handoff bridge helpers.
- `kinds.py`, `naming.py`, and `timestamps.py` own small shared helper
  families used across those branches.

## Rationale

The split follows the checkpoint mechanic boundary: SDK checkpoint behavior is
session-local capture, review, closeout context, and handoff support. It does
not become durable memory, proof verdict, progression truth, quest acceptance,
or owner approval.

Branch names describe the operation an agent should route toward, not the
temporary size of a file. The generated topology remains a read model; source
files and decisions remain stronger.

## Consequences

- Public imports stay stable: `aoa_sdk.checkpoints.CheckpointsAPI` remains the
  entrypoint.
- `registry.py` no longer owns broad helper families and drops below high
  split pressure in `generated/source_topology.min.json`.
- Closeout bridge remains the next medium-pressure checkpoint branch. If it
  grows again, split it by context, evidence, execution, and owner-handoff
  routes.
- New checkpoint behavior should land in the branch that owns its route role,
  not in the facade by default.

## Source Surfaces

- `src/aoa_sdk/checkpoints/registry.py`
- `src/aoa_sdk/checkpoints/topology/paths.py`
- `src/aoa_sdk/checkpoints/runtime/sessions.py`
- `src/aoa_sdk/checkpoints/hooks/git_boundary.py`
- `src/aoa_sdk/checkpoints/promotion/targets.py`
- `src/aoa_sdk/checkpoints/render/markdown.py`
- `src/aoa_sdk/checkpoints/review/after_commit.py`
- `src/aoa_sdk/checkpoints/review/agent_review.py`
- `src/aoa_sdk/checkpoints/ledger/notes.py`
- `src/aoa_sdk/checkpoints/closeout/bridge.py`
- `generated/source_topology.min.json`
- `tests/test_source_topology_index.py`
- `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/`

## Follow-Up Route

Keep the next checkpoint cut narrow. The likely next route is splitting
`closeout/bridge.py` into `context`, `evidence`, `execution`, and
`owner_handoff` only when new closeout behavior needs one of those owners.

## Verification

```bash
python -m ruff check src/aoa_sdk/checkpoints
python -m pytest -q mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_session_growth_checkpoint_cycle_cli.py mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_session_growth_checkpoint_cycle_api.py mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_session_growth_checkpoint_cycle_dirty_gate.py mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_checkpoint_path_topology.py
python scripts/build_source_topology_index.py --check
python scripts/validate_source_topology_index.py
python -m pytest -q tests/test_source_topology_index.py
python scripts/release_check.py
```
