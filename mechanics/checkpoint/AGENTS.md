# AGENTS.md

## Applies to

`mechanics/checkpoint/`.

## Role

Route the shared checkpoint mechanic for session-local note capture, git
boundary checks, review-note gates, promotion stop-lines, and review-context
bundle assembly, reviewed session handoff runner behavior, and reviewed
closeout context carry below owner truth.

## Read before editing

- `mechanics/AGENTS.md`
- `mechanics/checkpoint/README.md`
- `mechanics/checkpoint/ROADMAP.md`
- `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/README.md`
- `mechanics/checkpoint/parts/AGENTS.md`
- `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/docs/session-growth-checkpoint-cycle.md`
- `mechanics/checkpoint/parts/reviewed-session-handoff-runner/README.md`
- `mechanics/checkpoint/parts/reviewed-closeout-context-carry/README.md`
- `mechanics/checkpoint/parts/session-growth-checkpoint-cycle/git-boundary-hook-templates/AGENTS.md`
- `mechanics/checkpoint/parts/reviewed-session-handoff-runner/closeout-inbox-user-units/AGENTS.md`
- `src/aoa_sdk/checkpoints/`

## Boundaries

- Stay on the control plane.
- Keep checkpoint notes session-local until reviewed promotion.
- Do not make checkpoint hints memory, proof, progression, or owner verdicts.
- Do not make reviewed closeout carry mint candidate, seed, object,
  continuity, component-refresh, or owner-acceptance truth.
- Do not let hooks run closeout, harvest, push, merge, or release logic.

## Validation

```bash
python scripts/validate_mechanics_topology.py
python -m pytest -q mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_session_growth_checkpoint_cycle_cli.py mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_session_growth_checkpoint_cycle_api.py mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_session_growth_checkpoint_cycle_dirty_gate.py mechanics/checkpoint/parts/reviewed-session-handoff-runner/tests/test_reviewed_session_handoff_runner.py mechanics/checkpoint/parts/reviewed-closeout-context-carry/tests/test_reviewed_closeout_context_carry.py mechanics/checkpoint/parts/reviewed-closeout-context-carry/tests/test_component_refresh_followthrough.py
```

## Closeout

Report whether capture, hook guard, review-note, promotion, review-context,
reviewed session handoff runner, or reviewed closeout context carry behavior
changed.
