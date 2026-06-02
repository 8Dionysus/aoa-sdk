# AGENTS.md

## Applies to

`mechanics/boundary-bridge/`.

## Role

Route the shared boundary-bridge mechanic for typed SDK facades that keep SDK
handles separate from sibling-owned meaning.

## Read before editing

- `mechanics/AGENTS.md`
- `mechanics/boundary-bridge/README.md`
- `mechanics/boundary-bridge/ROADMAP.md`
- `mechanics/boundary-bridge/parts/AGENTS.md`
- `mechanics/boundary-bridge/parts/consumed-surface-posture-gate/README.md`
- `mechanics/boundary-bridge/parts/skill-runtime-bridge/README.md`
- `docs/boundaries.md`
- `src/aoa_sdk/*/registry.py`
- `src/aoa_sdk/routing/`
- `src/aoa_sdk/skills/`

## Boundaries

- Stay on the control plane.
- Do not make a facade a source owner.
- Preserve truth labels and owner return routes.
- Keep skill runtime reporting below `aoa-skills` meaning and do not claim
  router-only skill execution.
- Keep sibling policy, proof, memory, role, and routing meaning outside SDK
  source truth.

## Validation

```bash
python scripts/validate_mechanics_topology.py
python -m pytest -q mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_agent_phase_binding_surface_reader.py mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_consumed_surface_posture_cli.py mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_eval_surface_reader.py mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_memo_surface_reader.py mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_routing_surface_actions.py mechanics/boundary-bridge/parts/skill-runtime-bridge/tests/test_skill_runtime_bridge.py mechanics/boundary-bridge/parts/skill-runtime-bridge/tests/test_skill_runtime_bridge_cli.py mechanics/boundary-bridge/parts/skill-runtime-bridge/tests/test_skill_reference_contracts.py
```

## Closeout

Report which facade or bridge changed and which sibling owner still owns
meaning.
