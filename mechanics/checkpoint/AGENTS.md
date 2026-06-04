# AGENTS.md

## Applies to

`mechanics/checkpoint/`.

## Role

Route the shared checkpoint mechanic for session-local note capture, git
boundary checks, review-note gates, promotion stop-lines, and review-context
bundle assembly, reviewed session handoff runner behavior, and reviewed
closeout context carry below owner truth. It also owns checkpoint lifecycle
audit and close/archive routing so stale `current/` scopes are visible and
movable without deleting evidence. It may attach read-only
aoa-session-memory archive refs to checkpoint closeout context, but it does not
promote memory claims. It may reconcile session-memory-backed checkpoint scopes
whose Codex session ended without reviewed closeout, but that route archives
local evidence only and does not create reviewed closeout. It may also derive
candidate-intelligence route evidence for repeated action signatures, wrapper
gaps, and owner pressure, but those classifier outputs stay unreviewed
navigation until an owner route accepts them.

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
- Do not close or archive checkpoint scopes with pending semantic review.
- Do not mutate aoa-session-memory when reading session-memory refs for
  checkpoint lifecycle or closeout evidence.
- Do not treat `archived_without_closeout` as `closed`.
- Do not treat candidate-intelligence signatures, repetition clusters, wrapper
  gaps, or generated indexes as accepted wrappers, memory, proof, or owner
  verdicts.
- Do not let hooks run closeout, harvest, push, merge, or release logic.

## Validation

```bash
python scripts/validate_mechanics_topology.py
python -m pytest -q mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_session_growth_checkpoint_cycle_cli.py mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_session_growth_checkpoint_cycle_api.py mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_session_growth_checkpoint_cycle_dirty_gate.py mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_checkpoint_session_memory.py mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_checkpoint_candidate_intelligence.py mechanics/checkpoint/parts/session-growth-checkpoint-cycle/tests/test_checkpoint_carrier_intelligence.py mechanics/checkpoint/parts/reviewed-session-handoff-runner/tests/test_reviewed_session_handoff_runner.py mechanics/checkpoint/parts/reviewed-closeout-context-carry/tests/test_reviewed_closeout_context_carry.py mechanics/checkpoint/parts/reviewed-closeout-context-carry/tests/test_component_refresh_followthrough.py
aoa checkpoint lifecycle-audit /srv/AbyssOS/aoa-sdk --root /srv/AbyssOS --json
aoa checkpoint close-archive /srv/AbyssOS/aoa-sdk --root /srv/AbyssOS --dry-run --json
aoa checkpoint reconcile-sessions /srv/AbyssOS/aoa-sdk --root /srv/AbyssOS --dry-run --json
aoa checkpoint candidate-intelligence /srv/AbyssOS/aoa-sdk --root /srv/AbyssOS --sample-limit 3 --write-index --json
```

## Closeout

Report whether capture, hook guard, review-note, promotion, review-context,
session-memory attachment, reviewed session handoff runner, or reviewed
closeout context carry, lifecycle audit, close/archive, or no-closeout
reconcile behavior changed. If candidate intelligence changed, report whether
the classifier stayed navigation-only and whether single-event promotion
remains blocked.
