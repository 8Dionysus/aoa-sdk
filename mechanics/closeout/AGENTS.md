# AGENTS.md

## Applies to

`mechanics/closeout/`.

## Role

Route the shared closeout mechanic for reviewed request assembly, manifest
assembly, inbox processing, owner followthrough, and bounded local automation.

## Read before editing

- `mechanics/AGENTS.md`
- `mechanics/closeout/README.md`
- `docs/session-closeout.md`
- `docs/closeout-followthrough-map.md`
- `src/aoa_sdk/closeout/`
- `systemd/AGENTS.md`

## Boundaries

- Stay on the control plane.
- Keep closeout mechanical unless a Codex agent actually applies the skill.
- Do not make closeout packets proof, memory, progression, or owner truth.
- Keep user units optional and bounded.

## Validation

```bash
python scripts/validate_mechanics_topology.py
python -m pytest -q tests/test_closeout.py
```

## Closeout

Report whether request, manifest, inbox, owner handoff, or unit behavior
changed.
