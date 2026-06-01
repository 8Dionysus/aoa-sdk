# Consumed Surface Posture Gate Test Localization

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0025
- Original date: 2026-06-01
- Surface classes: topology, mechanics, test placement
- SDK facets: mechanics topology, compatibility, typed facades
- Mechanic parents: boundary-bridge
- Guard families: mechanics topology, active naming, source-owner boundary
- Posture: accepted

## Context

Root `tests/` still carried active sibling-facade and compatibility tests:

- `tests/test_agents.py`
- `tests/test_compatibility.py`
- `tests/test_evals.py`
- `tests/test_governed_runs.py`
- `tests/test_kag.py`
- `tests/test_memo.py`
- `tests/test_playbooks.py`
- `tests/test_routing.py`
- `tests/test_stats.py`

These tests do not own sibling meaning. They verify that the SDK reads
source-owned surfaces through explicit compatibility rules and typed facades
without promoting the loaded data into SDK truth.

## Decision

Activate the existing Boundary Bridge part name
`consumed-surface-posture-gate` as the home for those tests:

- `mechanics/boundary-bridge/parts/consumed-surface-posture-gate/`

Keep `src/aoa_sdk/*` as the importable SDK implementation lane. The part owns the
operation topology and validation route, not a duplicated source package.

## Rationale

The part name states the operational map: consumed surfaces enter, posture is
checked, typed SDK readouts exit, and sibling repositories remain the authority
for meaning. Root filenames like `tests/test_memo.py` or
`tests/test_stats.py` hide that boundary and make the active owner ambiguous.

## Consequences

- Root `tests/` no longer carries active sibling-facade test homes.
- Boundary Bridge now has a part-local test surface for compatibility gates,
  typed facade readers, routing action checks, governed-run readers, and stats
  readouts.
- Compatibility fixtures and facade expectations still point to source-owned
  sibling contracts; this part only verifies SDK consumption posture.

## Source Surfaces

- `mechanics/boundary-bridge/README.md`
- `mechanics/boundary-bridge/PARTS.md`
- `mechanics/boundary-bridge/PROVENANCE.md`
- `mechanics/boundary-bridge/parts/AGENTS.md`
- `mechanics/boundary-bridge/parts/consumed-surface-posture-gate/`
- `mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_agent_phase_binding_surface_reader.py`
- `mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_consumed_surface_compatibility_gate.py`
- `mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_consumed_surface_posture_cli.py`
- `mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_eval_surface_reader.py`
- `mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_governed_run_surface_reader.py`
- `mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_kag_surface_reader.py`
- `mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_memo_surface_reader.py`
- `mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_playbook_surface_reader.py`
- `mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_routing_surface_actions.py`
- `mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_stats_surface_reader.py`
- `mechanics/ARTIFACT_TOPOLOGY.md`
- `mechanics/topology.json`

## Follow-Up Route

Continue root test audit for runtime-seam, release-support, decision/design,
and repo-wide validator surfaces.

## Verification

```bash
python -m pytest -q mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_agent_phase_binding_surface_reader.py mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_consumed_surface_compatibility_gate.py mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_consumed_surface_posture_cli.py mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_eval_surface_reader.py mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_governed_run_surface_reader.py mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_kag_surface_reader.py mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_memo_surface_reader.py mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_playbook_surface_reader.py mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_routing_surface_actions.py mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_stats_surface_reader.py
python scripts/validate_mechanics_topology.py
python scripts/generate_decision_indexes.py --check
python -m ruff check .
```
