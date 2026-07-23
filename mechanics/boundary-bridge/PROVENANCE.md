# Boundary Bridge Provenance

## Source Surfaces

- `docs/boundaries.md`
- `src/aoa_sdk/AGENTS.md`
- `src/aoa_sdk/__init__.py`
- `src/aoa_sdk/api.py`
- `src/aoa_sdk/errors.py`
- `src/aoa_sdk/models.py`
- `src/aoa_sdk/agents/`
- `src/aoa_sdk/artifacts/`
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
- `mechanics/boundary-bridge/parts/skill-environment-inspector/`
- `mechanics/boundary-bridge/parts/technique-promotion-readiness-reader/`
- `mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_agent_phase_binding_surface_reader.py`
- `mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_consumed_surface_compatibility_gate.py`
- `mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_consumed_surface_posture_cli.py`
- `mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_eval_surface_reader.py`
- `mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_governed_run_surface_reader.py`
- `mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_kag_surface_reader.py`
- `mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_memo_surface_reader.py`
- `mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_playbook_surface_reader.py`
- `mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_routing_surface_actions.py`
- `mechanics/boundary-bridge/parts/consumed-surface-posture-gate/docs/routing-succession-r0-baseline.md`
- `mechanics/boundary-bridge/parts/consumed-surface-posture-gate/evidence/routing-succession-r0-baseline.json`
- `mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_routing_succession_r0_baseline.py`
- `mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_stats_surface_reader.py`
- `mechanics/boundary-bridge/parts/consumed-surface-posture-gate/tests/test_workspace_control_plane_compatibility.py`
- `mechanics/boundary-bridge/parts/technique-promotion-readiness-reader/tests/test_technique_promotion_readiness_reader.py`
- `mechanics/boundary-bridge/parts/skill-environment-inspector/tests/test_skill_environment_inspector.py`
- `mechanics/boundary-bridge/parts/skill-environment-inspector/tests/test_skill_environment_inspector_cli.py`

## Stronger Owners

Sibling repositories own their domain semantics. The SDK owns typed access,
validation, and handoff readability.

## Notes

This shared mechanic name matches the repeated AoA boundary pattern: bridge the
surface, keep ownership outside.

Former parent-name candidates for this package live only in
`legacy/INDEX.md`. Active Boundary Bridge routes name the operation: consumed
surface posture gate, skill environment inspector, and owner-layer signal handoff.

The former skill runtime bridge was retired by AOA-SDK-D-0067 after owner
profiles and the typed capability graph replaced SDK dispatch and session
state. Its active replacement is
`mechanics/boundary-bridge/parts/skill-environment-inspector/`. Old root paths such as
`docs/skill-runtime-recommendation-gap.md`,
`docs/skill-runtime-recommendation-gap-fix-spec.md`, and
`tests/test_skills.py` are provenance only, not active routes.

Former root technique facade regression `tests/test_techniques.py` moved into
`mechanics/boundary-bridge/parts/technique-promotion-readiness-reader/`. The
active route reads promotion readiness; it does not own technique promotion.

Former root sibling facade and compatibility regressions moved into
`mechanics/boundary-bridge/parts/consumed-surface-posture-gate/`. Old root
test names such as `tests/test_compatibility.py`, `tests/test_memo.py`, and
`tests/test_stats.py` are provenance only, not active routes.

Former root CLI cases from `tests/test_cli.py` moved into
`consumed-surface-posture-gate` for compatibility commands and
`skill-environment-inspector` for skill commands. The old root CLI test file is
provenance only, not an active route.
