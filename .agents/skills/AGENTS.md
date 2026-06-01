# AGENTS.md

## Applies To

Checked-in `.agents/skills/` exports.

## Role

This directory carries bundled skill export surfaces for local SDK routing and
test fixtures. It is not the source of truth for skill doctrine.

## Read Before Editing

1. Root `AGENTS.md`
2. `mechanics/boundary-bridge/parts/skill-runtime-bridge/README.md`
3. `mechanics/boundary-bridge/parts/skill-runtime-bridge/VALIDATION.md`
4. The owning `aoa-skills` source surface when skill meaning changes

## Boundaries

- Keep skill meaning in `aoa-skills`.
- Treat checked-in exports as consumed surfaces or fixtures, not activation
  authority.
- Do not add runtime-local secrets, workstation paths, or hidden activation
  state.
- Route SDK behavior changes through `skill-runtime-bridge`.

## Validation

```bash
python -m pytest -q mechanics/boundary-bridge/parts/skill-runtime-bridge/tests
python scripts/validate_nested_agents.py
```

## Closeout

Report whether a change only refreshed an export, changed SDK consumption, or
requires an `aoa-skills` owner update.
