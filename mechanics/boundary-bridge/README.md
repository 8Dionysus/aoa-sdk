# Boundary Bridge Mechanic

Status: active topology with part-local payload.

## Mechanic Card

### Operation

Keep SDK typed facades as handles over source-owned sibling surfaces while the
sibling repositories retain meaning.

### Trigger

Use this mechanic when a typed facade, registry, consumed-surface posture gate,
skill runtime bridge, technique promotion readiness reader, owner-layer signal
handoff, route hint, stats read, or sibling-owned generated reader changes.

### SDK owns

- typed loading and facade shape
- local truth labels
- source references and route hints
- consumed-surface posture gates
- skill runtime bridge behavior below `aoa-skills`
- technique promotion readiness reader behavior below `aoa-techniques`
- additive owner-layer signal review and handoff
- owner return path after stronger claims appear

### Stronger owner split

`aoa-routing`, `aoa-skills`, `aoa-evals`, `aoa-memo`, `aoa-agents`,
`aoa-playbooks`, `aoa-techniques`, stats/KAG owners, and other sibling repos
retain their domain meaning.

### Current source surfaces

- `docs/boundaries.md`
- `src/aoa_sdk/AGENTS.md`
- `src/aoa_sdk/__init__.py`
- `src/aoa_sdk/api.py`
- `src/aoa_sdk/errors.py`
- `src/aoa_sdk/models.py`
- `src/aoa_sdk/agents/`
- `src/aoa_sdk/cli/`
- `src/aoa_sdk/evals/`
- `src/aoa_sdk/governed_runs/`
- `src/aoa_sdk/kag/`
- `src/aoa_sdk/loaders/`
- `src/aoa_sdk/memo/`
- `src/aoa_sdk/playbooks/`
- `src/aoa_sdk/routing/`
- `src/aoa_sdk/compatibility/`
- `src/aoa_sdk/skills/`
- `src/aoa_sdk/stats/`
- `src/aoa_sdk/surfaces/`
- `src/aoa_sdk/techniques/`
- `mechanics/boundary-bridge/parts/consumed-surface-posture-gate/`
- `mechanics/boundary-bridge/parts/skill-runtime-bridge/`
- `mechanics/boundary-bridge/parts/technique-promotion-readiness-reader/`
- `mechanics/boundary-bridge/parts/owner-layer-signal-handoff/`
- facade and compatibility tests under `mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/`
- skill runtime bridge tests under `mechanics/boundary-bridge/parts/skill-runtime-bridge/tests/`
- skill reference contract tests under `mechanics/boundary-bridge/parts/skill-runtime-bridge/tests/`

### Candidate parts

- consumed-surface-posture-gate
- skill-runtime-bridge
- technique-promotion-readiness-reader
- owner-layer-signal-handoff

### Must not claim

This mechanic must not turn loaded sibling catalogs, compatibility checks,
skill wrappers, or surface hints into SDK source truth.

### Validation

```bash
python -m pytest -q mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_agent_phase_binding_surface_reader.py mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_consumed_surface_compatibility_gate.py mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_consumed_surface_posture_cli.py mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_eval_surface_reader.py mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_governed_run_surface_reader.py mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_kag_surface_reader.py mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_memo_surface_reader.py mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_playbook_surface_reader.py mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_routing_surface_actions.py mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_stats_surface_reader.py mechanics/boundary-bridge/parts/skill-runtime-bridge/tests/test_skill_runtime_bridge.py mechanics/boundary-bridge/parts/skill-runtime-bridge/tests/test_skill_runtime_bridge_cli.py mechanics/boundary-bridge/parts/skill-runtime-bridge/tests/test_skill_reference_contracts.py mechanics/boundary-bridge/parts/technique-promotion-readiness-reader/tests/test_technique_promotion_readiness_reader.py mechanics/boundary-bridge/parts/owner-layer-signal-handoff/tests/test_owner_layer_signal_handoff.py mechanics/boundary-bridge/parts/owner-layer-signal-handoff/tests/test_owner_layer_signal_handoff_cli.py
```

### Next route

For new sibling-owned meaning, update the owning sibling repo first, then the
SDK facade and compatibility path.
