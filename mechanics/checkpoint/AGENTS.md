# AGENTS.md

## Applies to

`mechanics/checkpoint/`.

## Role

Route the shared checkpoint mechanic for session-local note capture, git
boundary checks, review-note gates, promotion stop-lines, and closeout-context
bridge assembly.

## Read before editing

- `mechanics/AGENTS.md`
- `mechanics/checkpoint/README.md`
- `docs/session-growth-checkpoints.md`
- `docs/checkpoint-note-promotion.md`
- `githooks/AGENTS.md`
- `src/aoa_sdk/checkpoints/`

## Boundaries

- Stay on the control plane.
- Keep checkpoint notes session-local until reviewed promotion.
- Do not make checkpoint hints memory, proof, progression, or owner verdicts.
- Do not let hooks run closeout, harvest, push, merge, or release logic.

## Validation

```bash
python scripts/validate_mechanics_topology.py
python -m pytest -q tests/test_checkpoint_cli.py tests/test_checkpoints.py
```

## Closeout

Report whether capture, hook guard, review-note, promotion, or closeout-context
behavior changed.
